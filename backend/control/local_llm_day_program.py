"""Generic, evidence-first Day 1-14 orchestration for LocalLLM-Lab.

The runbook supplies the Day contract (what must be true).  A bounded planner
supplies work items (how to collect or create evidence).  This module never
derives a shell command, source scope, or completion decision from browser
input or an LLM response.
"""

from __future__ import annotations

import subprocess
import sys
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, RLock, Thread
from typing import Callable
from uuid import uuid4

import yaml

from backend.control.local_ollama_repair import LocalOllamaRepairBuilder
from backend.control.evidence_registry import REGISTRY, EvidenceRegistry
from backend.control.retained_evidence import RetainedEvidenceResolver
from backend.control.solution_catalog import RepairEpisodeStore, SolutionCatalog, SolutionCatalogEntry
from backend.models.local_llm_day import (
    DayCriterion,
    DayIssueClassification,
    LocalLLMDayContract,
    LocalLLMDayReport,
    LocalLLMDaySnapshot,
    LocalLLMDayState,
    LocalLLMDayWorkItem,
    LocalLLMRepairCard,
    RepairEpisode,
    RepairProposalAttempt,
    LocalLLMWorkItemState,
)


Planner = Callable[[LocalLLMDayContract, dict[str, object]], list[LocalLLMDayWorkItem]]
WorkOrderExecutor = Callable[[dict[str, object]], dict[str, object]]


class LocalLLMDayProgram:
    """A durable Day controller layered over trusted task execution.

    ``planner`` may be a Codex Architect adapter.  Its output is data only and
    is checked before execution.  ``work_order_executor`` is the existing
    guarded engine boundary; the default intentionally permits read-only
    evidence work only.
    """

    PROGRAM_PATH = Path(__file__).resolve().parents[2] / "config" / "local_llm_day_program.yaml"
    MAX_TASKS = 3
    MAX_REPLANS = 2
    MAX_LOCAL_PROPOSALS = 3

    def __init__(
        self,
        root: Path,
        *,
        saved: dict[str, object] | None = None,
        persist: Callable[[dict[str, object]], None] | None = None,
        audit: Callable[[str, str, dict[str, object]], None] | None = None,
        planner: Planner | None = None,
        work_order_executor: WorkOrderExecutor | None = None,
        repair_builder: LocalOllamaRepairBuilder | None = None,
        solution_catalog: SolutionCatalog | None = None,
        repair_episode_store: RepairEpisodeStore | None = None,
        retained_evidence_resolver: RetainedEvidenceResolver | None = None,
        clock: Callable[[], float] = time.time,
        project_id: str = "local_llm_lab",
    ) -> None:
        self.root = root.resolve()
        self.persist, self.audit = persist, audit
        self.snapshot = LocalLLMDaySnapshot.model_validate(saved or {})
        self.planner = planner or self._deterministic_plan
        self.work_order_executor = work_order_executor or self._read_only_executor
        self.repair_builder = repair_builder or LocalOllamaRepairBuilder()
        self.solution_catalog = solution_catalog or SolutionCatalog()
        self.repair_episode_store = repair_episode_store or RepairEpisodeStore()
        self.retained_evidence_resolver = retained_evidence_resolver or RetainedEvidenceResolver(self.root)
        self.clock, self.project_id, self.evidence_registry = clock, project_id, REGISTRY
        self._lock, self._stop = RLock(), Event()
        self._thread: Thread | None = None
        self._restore_snapshot()
        if self.snapshot.state == LocalLLMDayState.RUNNING:
            self.snapshot.state = LocalLLMDayState.PAUSED
            self.snapshot.stop_reason = "INTERRUPTED_REQUIRES_RESUME"
            self.snapshot.activity = "Interrupted by restart; Resume continues from the persisted contract and task states."
            self._save()

    def days(self) -> list[dict[str, object]]:
        return [{"day": contract.day, "objective": contract.objective} for contract in self._load_contracts().values()]

    def day_one_read_only_diagnostic(self) -> dict[str, object]:
        """Collect inspectable Day 1 facts without running the regression suite."""
        contract = self._load_contracts().get(1)
        if contract is None:
            return {"error_code": "DAY_NOT_CONFIGURED"}
        return self._collect_day_one_evidence(contract, execute_tests=False)

    def view(self) -> dict[str, object]:
        with self._lock:
            return {**self.snapshot.model_dump(mode="json"), "recommended_action": self._recommended_action()}

    def smoke(self, day: int) -> dict[str, object]:
        contract = self._load_contracts().get(day)
        if contract is None:
            return {"error_code": "DAY_NOT_CONFIGURED", **self.view()}
        inventory = self._inventory(contract)
        missing = inventory["missing_sources"]
        result = "SMOKE_PASS" if not missing else "SMOKE_SOURCE_MISSING"
        with self._lock:
            # Selecting a different contract is not a resume.  Do not permit
            # old work, repair state, or claimed evidence to cross that boundary.
            if self.snapshot.selected_day != day or self.snapshot.contract is None or self.snapshot.contract.version != contract.version:
                self.snapshot = LocalLLMDaySnapshot(selected_day=day, objective=contract.objective, contract=contract)
            else:
                self.snapshot.contract = self._restore_contract(contract, self.snapshot.contract)
                self.snapshot.work_items = self._valid_work_items(self.snapshot.work_items, contract)
            self.snapshot.smoke_report = LocalLLMDayReport(
                day=day, objective=contract.objective, result=result,
                summary="Authoritative sources and target Git state were inventoried; no Day task was started.",
                evidence=inventory,
            )
            self.snapshot.state = LocalLLMDayState.IDLE
            self.snapshot.activity = self.snapshot.smoke_report.summary
            self.snapshot.progress = 0
            self.snapshot.report = None
            self.snapshot.stop_reason = None
            self._save()
            return self.view()

    def start(self, day: int) -> dict[str, object]:
        contracts = self._load_contracts()
        contract = contracts.get(day)
        if contract is None:
            return {"error_code": "DAY_NOT_CONFIGURED", **self.view()}
        with self._lock:
            if self.snapshot.state == LocalLLMDayState.RUNNING:
                return {"error_code": "DAY_ALREADY_RUNNING", **self.view()}
            # Only same-version, validated same-Day evidence may survive Resume.
            if (self.snapshot.selected_day != day or self.snapshot.contract is None
                    or self.snapshot.contract.version != contract.version):
                self.snapshot = LocalLLMDaySnapshot(selected_day=day, objective=contract.objective, contract=contract)
            else:
                self.snapshot.contract = self._restore_contract(contract, self.snapshot.contract)
                self.snapshot.work_items = self._valid_work_items(self.snapshot.work_items, contract)
            self._stop.clear()
            self.snapshot.state = LocalLLMDayState.RUNNING
            self.snapshot.activity = "Loading the Day Contract and current trusted evidence."
            self.snapshot.stop_reason = None
            self._audit("LOCAL_LLM_DAY_STARTED", {"day": day, "objective": contract.objective})
            self._save()
            self._thread = Thread(target=self._execute, name=f"local-llm-day-{day}", daemon=True)
            self._thread.start()
            return self.view()

    def resume(self) -> dict[str, object]:
        with self._lock:
            if self.snapshot.selected_day is None or self.snapshot.state not in {LocalLLMDayState.PAUSED, LocalLLMDayState.STOPPED}:
                return {"error_code": "DAY_NOT_RESUMABLE", **self.view()}
            day = self.snapshot.selected_day
        return self.start(day)

    def stop(self) -> dict[str, object]:
        with self._lock:
            if self.snapshot.state == LocalLLMDayState.RUNNING:
                self._stop.set()
                self.snapshot.activity = "Stop requested; preserving the current task result."
                self._save()
        return self.view()

    def join(self, timeout: float | None = None) -> None:
        if self._thread:
            self._thread.join(timeout)

    def repair_and_go(self) -> dict[str, object]:
        """Resume a persisted automatic repair episode only when interrupted."""
        with self._lock:
            if self.snapshot.state != LocalLLMDayState.FAILED or self.snapshot.issue_classification != DayIssueClassification.IMPLEMENTATION_DEFECT:
                return {"error_code": "AUTONOMOUS_REPAIR_NOT_AVAILABLE", **self.view()}
            item = next((value for value in self.snapshot.work_items if value.state == LocalLLMWorkItemState.FAILED), None)
            contract = self.snapshot.contract
            if item is None or contract is None:
                return {"error_code": "REPAIR_TARGET_MISSING", **self.view()}
        self._supervise_repair(item, contract)
        return self.view()

    def _supervise_repair(self, item: LocalLLMDayWorkItem, contract: LocalLLMDayContract) -> bool:
        """Run the entire bounded local-to-expert repair control loop."""
        excerpt = str(item.evidence.get("failure_excerpt", ""))[:2000]
        fingerprint = self._failure_fingerprint(item, excerpt)
        now = self.clock()
        matches = self.solution_catalog.find(
            project_id=self.project_id, failure_class=DayIssueClassification.IMPLEMENTATION_DEFECT.value,
            fingerprint=fingerprint, component=item.item_id,
        )
        episode = RepairEpisode(
            episode_id=uuid4().hex, project_id=self.project_id, day=contract.day,
            work_item_id=item.item_id, failure_class=DayIssueClassification.IMPLEMENTATION_DEFECT,
            failure_fingerprint=fingerprint, failure_excerpt=excerpt, component=item.item_id,
            started_at_epoch=now, repair_deadline_epoch=now + self.snapshot.repair_deadline_seconds,
            catalog_match_ids=[entry.catalog_id for entry in matches],
        )
        self.repair_episode_store.save(episode)
        self.snapshot.repair_episode_ids.append(episode.episode_id)
        files = self._bounded_repair_files(item)
        seen_proposals: set[str] = set()
        while len(episode.proposal_attempts) < self.MAX_LOCAL_PROPOSALS and self.clock() < episode.repair_deadline_epoch:
            remaining = max(1, int(episode.repair_deadline_epoch - self.clock()))
            proposal = self.repair_builder.propose(
                failure_excerpt=excerpt, files=files, timeout_seconds=min(120, remaining),
                rejection_feedback="\n".join(episode.rejection_feedback[-2:]) or None,
                repair_knowledge=[self._catalog_guidance(entry) for entry in matches],
            )
            if proposal is None:
                episode.proposal_attempts.append(RepairProposalAttempt(proposal_fingerprint=self._text_fingerprint("NO_PROPOSAL"), outcome="NO_PROPOSAL", feedback="LocalLLM returned no bounded proposal."))
                episode.rejection_feedback.append("No parseable LocalLLM proposal was returned.")
                self.repair_episode_store.save(episode)
                continue
            proposal_fingerprint = self._proposal_fingerprint(proposal)
            if proposal_fingerprint in seen_proposals:
                episode.proposal_attempts.append(RepairProposalAttempt(proposal_fingerprint=proposal_fingerprint, outcome="DUPLICATE", feedback="Duplicate proposal fingerprint."))
                episode.rejection_feedback.append("The same proposal fingerprint repeated; escalate independently.")
                self.repair_episode_store.save(episode)
                break
            seen_proposals.add(proposal_fingerprint)
            result = self.work_order_executor({
                "kind": "LOCAL_LLM_COUNTERMEASURE", "task_id": item.item_id, "proposal": proposal,
                "files": sorted(files), "dynamic_work_order": item.dynamic_work_order.model_dump(mode="json") if item.dynamic_work_order else None,
                "repair_episode_id": episode.episode_id,
            })
            if result.get("final_result") in {"COMPLETE", "COMPLETE_NO_CHANGE"}:
                episode.proposal_attempts.append(RepairProposalAttempt(proposal_fingerprint=proposal_fingerprint, outcome="VERIFIED"))
                episode.codex_review_outcome = "ACCEPTED_AND_VERIFIED"
                episode.verification_result = "PASS"
                episode.final_outcome = "LOCAL_VERIFIED"
                self.repair_episode_store.save(episode)
                self._accept_repair(item, result, episode, source="LOCAL_VERIFIED", diagnosis=proposal.diagnosis)
                return True
            feedback = str(result.get("error_code") or result.get("final_result") or "CODEX_REJECTED_PROPOSAL")[:1000]
            episode.proposal_attempts.append(RepairProposalAttempt(proposal_fingerprint=proposal_fingerprint, outcome="REJECTED", feedback=feedback))
            episode.rejection_feedback.append(feedback)
            self.repair_episode_store.save(episode)
        expert = self.work_order_executor({
            "kind": "CODEX_EXPERT_SOLVER", "task_id": item.item_id,
            "dynamic_work_order": item.dynamic_work_order.model_dump(mode="json") if item.dynamic_work_order else None,
            "failure_excerpt": excerpt, "failure_fingerprint": fingerprint,
            "catalog_matches": [self._catalog_guidance(entry) for entry in matches], "repair_episode_id": episode.episode_id,
        })
        if expert.get("final_result") in {"COMPLETE", "COMPLETE_NO_CHANGE"}:
            episode.expert_solver_outcome, episode.verification_result, episode.final_outcome = "VERIFIED", "PASS", "CODEX_VERIFIED"
            self._accept_repair(item, expert, episode, source="CODEX_VERIFIED", diagnosis="Codex Expert Solver independently repaired the verified failure.")
            return True
        episode.expert_solver_outcome = str(expert.get("error_code") or "FAILED")[:80]
        episode.final_outcome = "EXPERT_FAILED"
        self.repair_episode_store.save(episode)
        return False

    @staticmethod
    def _text_fingerprint(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()

    @staticmethod
    def _file_fingerprint(path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return "missing"

    def _failure_fingerprint(self, item: LocalLLMDayWorkItem, excerpt: str) -> str:
        return self._text_fingerprint(f"{item.item_id}|{item.dynamic_work_order.task_id if item.dynamic_work_order else ''}|{excerpt[:1200]}")

    def _inventory_fingerprint(self, inventory: dict[str, object]) -> str:
        return self._text_fingerprint(repr({key: inventory.get(key) for key in ("head", "branch", "status_count", "source_presence")}))

    def _proposal_fingerprint(self, proposal: object) -> str:
        edits = getattr(proposal, "edits", ())
        serialized = "|".join(f"{getattr(edit, 'path', '')}:{getattr(edit, 'find', '')}:{getattr(edit, 'replace', '')}" for edit in edits)
        return self._text_fingerprint(f"{getattr(proposal, 'diagnosis', '')}|{serialized}")

    @staticmethod
    def _catalog_guidance(entry: SolutionCatalogEntry) -> dict[str, object]:
        return {
            "catalog_id": entry.catalog_id, "cause": entry.root_cause,
            "investigation": entry.diagnostic_steps, "resolution_logic": entry.resolution_strategy,
            "verification": entry.verification, "preconditions": entry.preconditions,
        }

    def _accept_repair(self, item: LocalLLMDayWorkItem, result: dict[str, object], episode: RepairEpisode, *, source: str, diagnosis: str) -> None:
        entry = SolutionCatalogEntry(
            scope="project", project_id=self.project_id,
            failure_class=episode.failure_class.value, failure_fingerprint=episode.failure_fingerprint,
            component=episode.component, title=f"Verified repair for {item.item_id}",
            symptoms=episode.failure_excerpt or "deterministic engineering failure",
            root_cause=diagnosis[:1000], diagnostic_steps="Inspect the bounded failure excerpt and configured source/test scope.",
            resolution_strategy="Apply only an in-scope repair through the guarded worktree executor.",
            preconditions=["IMPLEMENTATION_DEFECT", "deterministic postcheck"],
            affected_files_or_scope=list(item.dynamic_work_order.allowed_files) if item.dynamic_work_order else [],
            verification="Configured deterministic postcheck passed.", source=source,
            success_count=1,
        )
        entry = self.solution_catalog.add_verified(entry)
        episode.catalog_update_id = entry.catalog_id
        self.repair_episode_store.save(episode)
        self.snapshot.repair_knowledge.append(LocalLLMRepairCard(
            problem_id=entry.catalog_id, title=entry.title, cause=entry.root_cause,
            investigation=entry.diagnostic_steps, resolution_logic=entry.resolution_strategy,
            verification=entry.verification, status=entry.status, uses=entry.uses,
            failure_class=entry.failure_class, failed_work_item=item.item_id,
        ))
        item.state = LocalLLMWorkItemState.COMPLETE
        item.evidence = self._bounded(result)
        self.snapshot.repair_attempted = True
        self.snapshot.issue_classification = None
        self.snapshot.codex_handoff = None
        self._save()

    def _execute(self) -> None:
        try:
            while not self._stop.is_set():
                contract = self.snapshot.contract
                if contract is None:
                    raise RuntimeError("missing persisted Day contract")
                inventory = self._inventory()
                self._evaluate_contract(contract, inventory)
                if not contract.remaining_gaps:
                    self._complete(contract, inventory)
                    return
                pending = next((item for item in self.snapshot.work_items if item.state == LocalLLMWorkItemState.PENDING), None)
                if pending is None:
                    if self.snapshot.replan_count >= self.MAX_REPLANS:
                        self._fail(contract, "DAY_INSUFFICIENT_EVIDENCE", "The bounded replanning limit was reached before all criteria gained evidence.", DayIssueClassification.INSUFFICIENT_EVIDENCE, inventory)
                        return
                    proposed = self._validated_plan(contract, inventory)
                    action_fingerprint = self._text_fingerprint(
                        f"{self._inventory_fingerprint(inventory)}|{','.join(contract.remaining_gaps)}|{','.join(sorted(item.item_id for item in proposed))}"
                    )
                    if action_fingerprint in self.snapshot.replan_fingerprints:
                        self._fail(contract, "DAY_NO_OP_REPLAN", "The unchanged repository state would repeat an identical evidence action.", DayIssueClassification.INSUFFICIENT_EVIDENCE, inventory)
                        return
                    self.snapshot.work_items.extend(proposed)
                    self.snapshot.replan_count += 1
                    self.snapshot.replan_fingerprints.append(action_fingerprint)
                    self.snapshot.activity = "Codex Architect produced a bounded plan for the remaining evidence gaps."
                    self._save()
                    continue
                self._run_item(pending, contract, inventory)
                if self.snapshot.state != LocalLLMDayState.RUNNING:
                    return
        except Exception as exc:
            contract = self.snapshot.contract
            if contract:
                self._fail(contract, "DAY_HARNESS_FAILURE", f"Day runner stopped safely: {type(exc).__name__}.", DayIssueClassification.IMPLEMENTATION_DEFECT, self._inventory())
        if self._stop.is_set() and self.snapshot.contract:
            self.snapshot.state = LocalLLMDayState.STOPPED
            self.snapshot.stop_reason = "STOP_REQUESTED"
            self.snapshot.activity = "Stopped; completed tasks and evidence remain persisted for Resume."
            self._save()

    def _run_item(self, item: LocalLLMDayWorkItem, contract: LocalLLMDayContract, inventory: dict[str, object]) -> None:
        item.state = LocalLLMWorkItemState.RUNNING
        self.snapshot.activity = item.title
        self._save()
        if item.kind == "EVIDENCE_CHECK" and contract.day == 1:
            result = self._collect_day_one_evidence(contract)
        else:
            result = self.work_order_executor({"kind": item.kind, "task_id": item.item_id, "engine_task_id": item.engine_task_id, "dynamic_work_order": item.dynamic_work_order.model_dump(mode="json") if item.dynamic_work_order else None, "criterion_ids": item.criterion_ids, "contract": contract.model_dump(mode="json"), "inventory": inventory})
        final = result.get("final_result")
        if final in {"COMPLETE", "COMPLETE_NO_CHANGE"}:
            item.state, item.evidence = LocalLLMWorkItemState.COMPLETE, self._bounded(result)
            self._evaluate_contract(contract, inventory)
            self._update_progress(contract)
            self._save()
            return
        classification = self._classify_result(result)
        item.state = LocalLLMWorkItemState.FAILED
        item.evidence = self._bounded(result)
        if classification == DayIssueClassification.IMPLEMENTATION_DEFECT and item.dynamic_work_order is not None:
            # Ordinary engineering failures automatically run the full bounded
            # repair episode. Research findings never enter this path.
            self.snapshot.state = LocalLLMDayState.FAILED
            self.snapshot.issue_classification = classification
            self._save()
            if self._supervise_repair(item, contract):
                self.snapshot.state = LocalLLMDayState.RUNNING
                self.snapshot.activity = "Repair verification succeeded; re-evaluating the Day Contract."
                self._save()
                return
        self._fail(contract, "DAY_TASK_FAILED", "A planned task did not produce trusted evidence.", classification, inventory)

    def _complete(self, contract: LocalLLMDayContract, inventory: dict[str, object]) -> None:
        self.snapshot.state = LocalLLMDayState.COMPLETE
        self.snapshot.progress = 100
        self.snapshot.report = LocalLLMDayReport(day=contract.day, objective=contract.objective, result="DAY_COMPLETE", summary="Completion criteria are supported by persisted evidence.", evidence={"satisfied_criteria": contract.satisfied_criteria, "inventory": inventory})
        self.snapshot.activity = self.snapshot.report.summary
        self._audit("LOCAL_LLM_DAY_COMPLETE", {"day": contract.day, "criteria": contract.satisfied_criteria})
        self._save()

    def _fail(self, contract: LocalLLMDayContract, result: str, summary: str, classification: DayIssueClassification, inventory: dict[str, object]) -> None:
        self.snapshot.state, self.snapshot.issue_classification = LocalLLMDayState.FAILED, classification
        self.snapshot.report = LocalLLMDayReport(day=contract.day, objective=contract.objective, result=result, summary=summary, evidence={"issue_classification": classification.value, "remaining_gaps": contract.remaining_gaps, "inventory": inventory})
        self.snapshot.activity = summary
        self._save()

    def _evaluate_contract(self, contract: LocalLLMDayContract, inventory: dict[str, object]) -> None:
        # Task state is never proof.  A criterion is recomputed exclusively
        # from named evidence records passing server-owned validators.
        for criterion in contract.completion_criteria:
            candidates: list[dict[str, object]] = [criterion.evidence]
            retained = inventory.get("retained_evidence")
            if isinstance(retained, dict):
                candidates.append(retained)
            matching = [item for item in self.snapshot.work_items
                        if criterion.criterion_id in item.criterion_ids
                        and item.state == LocalLLMWorkItemState.COMPLETE
                        and item.contract_day == contract.day
                        and item.contract_version == contract.version]
            for item in matching:
                evidence = item.evidence.get("evidence")
                if isinstance(evidence, dict):
                    candidates.append(evidence)
            chosen = next((evidence for evidence in candidates if self._criterion_evidence_valid(criterion, evidence)), None)
            criterion.satisfied = chosen is not None
            criterion.evidence = self._bounded(chosen or {})
        contract.satisfied_criteria = [item.criterion_id for item in contract.completion_criteria if item.satisfied]
        contract.remaining_gaps = [item.criterion_id for item in contract.completion_criteria if not item.satisfied]
        self._update_progress(contract)

    def _validated_plan(self, contract: LocalLLMDayContract, inventory: dict[str, object]) -> list[LocalLLMDayWorkItem]:
        # Day 1 evidence is collected only by the server-owned Git/document/
        # deterministic-test collector.  Configured process-smoke tasks have
        # no capability to prove this contract.
        if contract.day == 1:
            return [item.model_copy(update={"contract_day": contract.day, "contract_version": contract.version})
                    for item in self._deterministic_plan(contract, inventory)]
        proposed = self.planner(contract, inventory)
        known = {criterion.criterion_id for criterion in contract.completion_criteria}
        if not isinstance(proposed, list) or not 1 <= len(proposed) <= self.MAX_TASKS:
            raise ValueError("planner did not return a bounded task list")
        seen: set[str] = set()
        validated: list[LocalLLMDayWorkItem] = []
        for item in proposed:
            if not isinstance(item, LocalLLMDayWorkItem) or item.item_id in seen or item.kind not in {"EVIDENCE_CHECK", "ENGINE_WORK_ORDER", "DYNAMIC_ENGINEERING_WORK"}:
                raise ValueError("planner proposed an untrusted task")
            if item.kind == "ENGINE_WORK_ORDER" and not item.engine_task_id:
                raise ValueError("engine work order has no trusted task identifier")
            if item.kind == "DYNAMIC_ENGINEERING_WORK" and item.dynamic_work_order is None:
                raise ValueError("dynamic engineering work has no bounded work order")
            if item.kind == "DYNAMIC_ENGINEERING_WORK" and item.engine_task_id is not None:
                raise ValueError("dynamic engineering work cannot select a configured task")
            if item.kind == "EVIDENCE_CHECK" and item.engine_task_id is not None:
                raise ValueError("evidence check cannot select an engine task")
            if item.kind == "EVIDENCE_CHECK" and item.dynamic_work_order is not None:
                raise ValueError("evidence check cannot create an engineering work order")
            if not item.criterion_ids or not set(item.criterion_ids).issubset(set(contract.remaining_gaps) & known):
                raise ValueError("planner expanded Day authority")
            seen.add(item.item_id)
            validated.append(item.model_copy(update={"contract_day": contract.day, "contract_version": contract.version}))
        return validated

    def _deterministic_plan(self, contract: LocalLLMDayContract, _inventory: dict[str, object]) -> list[LocalLLMDayWorkItem]:
        # This is a safe fallback when Codex is unavailable.  Production may
        # replace it with a Codex Architect adapter; Python validates either.
        return [
            LocalLLMDayWorkItem(item_id=f"evidence-{contract.day}-{criterion.criterion_id}", title="Collect trusted completion evidence", objective=criterion.statement, criterion_ids=[criterion.criterion_id])
            for criterion in contract.completion_criteria if criterion.criterion_id in contract.remaining_gaps
        ][: self.MAX_TASKS]

    def _read_only_executor(self, work_order: dict[str, object]) -> dict[str, object]:
        """Default executor proves completion only from existing trusted sources."""
        if work_order.get("kind") != "EVIDENCE_CHECK":
            return {"final_result": "FAILED", "error_code": "ENGINE_WORK_ORDER_REQUIRED"}
        # Source presence tells the planner where to inspect; it is never
        # enough to claim a research or implementation criterion is met.
        return {"final_result": "COMPLETE", "evidence": {}, "inspection": "sources inventoried; delivery evidence not inferred"}

    def _load_contracts(self) -> dict[int, LocalLLMDayContract]:
        path = self.PROGRAM_PATH
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            return {}
        if not isinstance(document, dict):
            return {}
        sources = document.get("authoritative_sources")
        shared_constraints = document.get("shared_constraints")
        definitions = document.get("days")
        if not isinstance(sources, list) or not isinstance(shared_constraints, list) or not isinstance(definitions, list):
            return {}
        declared = {
            evidence for definition in definitions if isinstance(definition, dict)
            for criterion in (definition.get("completion_criteria") or []) if isinstance(criterion, dict)
            for evidence in (criterion.get("evidence") or [])
        }
        if not declared or not declared.issubset(self.evidence_registry.names):
            return {}
        contracts: dict[int, LocalLLMDayContract] = {}
        for definition in definitions:
            if not isinstance(definition, dict):
                return {}
            day = definition.get("day")
            raw_criteria = definition.get("completion_criteria")
            if not isinstance(day, int) or not isinstance(raw_criteria, list):
                return {}
            criteria = [DayCriterion(criterion_id=f"d{day}-{entry['id']}", statement=entry["statement"], required_evidence=entry["evidence"])
                        for entry in raw_criteria if isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("statement"), str) and isinstance(entry.get("evidence"), list)]
            if len(criteria) != len(raw_criteria):
                return {}
            contracts[day] = LocalLLMDayContract(day=day, title=str(definition.get("title", "")), version=str(document.get("version", "v1")), objective=str(definition.get("objective", "")), completion_criteria=criteria, constraints=[str(value) for value in shared_constraints], authoritative_sources=[str(value).replace("\\", "/") for value in sources], remaining_gaps=[criterion.criterion_id for criterion in criteria])
        return contracts if set(contracts) == set(range(1, 15)) else {}

    def _inventory(self, contract: LocalLLMDayContract | None = None) -> dict[str, object]:
        contract = contract or self.snapshot.contract
        sources = contract.authoritative_sources if contract else []
        source_presence = {source: (self.root / source).is_file() for source in sources}
        retained_evidence = self.retained_evidence_resolver.resolve(contract.day) if contract else {}
        return {**self._git_state(), "source_presence": source_presence,
                "missing_sources": [path for path, present in source_presence.items() if not present],
                "retained_evidence": retained_evidence}

    def _git_state(self) -> dict[str, object]:
        def output(args: list[str]) -> str:
            try:
                return subprocess.run(["git", "-C", str(self.root), "-c", f"safe.directory={self.root}", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, check=False).stdout.strip()
            except (OSError, subprocess.TimeoutExpired):
                return ""
        status = output(["status", "--short"])
        tracked = output(["ls-files"]).splitlines()
        safe_context = [path.replace("\\", "/") for path in tracked if path.startswith(("src/", "scripts/", "tests/", "config/", "docs/")) and Path(path).suffix.lower() in {".py", ".yaml", ".yml", ".json", ".md"}]
        return {"branch": output(["branch", "--show-current"]), "head": output(["rev-parse", "HEAD"]), "origin": output(["remote", "get-url", "origin"]), "working_tree_clean": not bool(status), "status_count": len(status.splitlines()) if status else 0, "tracked_context_files": safe_context[:80]}

    @staticmethod
    def _record(name: str, value: object, source: str, passed: bool) -> dict[str, object]:
        return {
            "evidence_type": name,
            "value": value,
            "source": source,
            "verified": True,
            "validation": {"passed": passed, "validator": f"deterministic:{name}"},
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _non_empty(value: object) -> bool:
        return value is not None and value != "" and value != {} and value != []

    def _criterion_evidence_valid(self, criterion: DayCriterion, evidence: object) -> bool:
        if not isinstance(evidence, dict) or not criterion.required_evidence:
            return False
        return all(self._validate_evidence_record(name, evidence.get(name)) for name in criterion.required_evidence)

    def _validate_evidence_record(self, name: str, record: object) -> bool:
        """Registry-owned semantic validation; no verified-envelope fallback."""
        return self.evidence_registry.validate(name, record)

    def _git(self, *args: str) -> tuple[int, str, str]:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.root), "-c", f"safe.directory={self.root}", *args],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, check=False,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 1, "", type(exc).__name__

    @staticmethod
    def _is_generated_path(path: str) -> bool:
        normalized = path.replace("\\", "/").lower()
        return normalized.startswith(("results/", "artifacts/", "models/", "datasets/", "teacher/", "telemetry/", "logs/", "cache/")) or normalized.endswith((".zip", ".gguf", ".safetensors"))

    def _day_one_status_audit(self) -> dict[str, object]:
        _code, output, _error = self._git("status", "--porcelain=v1", "-uall")
        staged: list[str] = []
        unstaged: list[str] = []
        untracked: list[str] = []
        generated: list[str] = []
        for line in output.splitlines():
            if len(line) < 4:
                continue
            state, path = line[:2], line[3:].replace("\\", "/")
            if " -> " in path:
                path = path.split(" -> ")[-1]
            if state == "??":
                untracked.append(path)
            else:
                if state[0] not in {" ", "?"}:
                    staged.append(path)
                if state[1] not in {" ", "?"}:
                    unstaged.append(path)
            if self._is_generated_path(path):
                generated.append(path)
        relevant_prefixes = ("src/", "backend/", "scripts/", "tests/", "config/", "docs/", "schemas/")
        relevant = sorted({path for path in [*staged, *unstaged] if path.startswith(relevant_prefixes)})
        return {
            "staged_tracked_paths": sorted(set(staged)), "unstaged_tracked_paths": sorted(set(unstaged)),
            "untracked_paths": sorted(set(untracked)), "relevant_dirty_paths": relevant,
            "generated_paths": sorted(set(generated)),
        }

    def _day_one_documentation_check(self, contract: LocalLLMDayContract) -> dict[str, object]:
        expected = ["docs/runbooks/work-plan-day1-14.md", "docs/README.md", "docs/architecture/decision-reasoning-architecture.md", "docs/handoff/handoff-2026-09-18.md"]
        failures: list[str] = []
        readable: dict[str, str] = {}
        for relative in expected:
            try:
                readable[relative] = (self.root / relative).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                failures.append(f"unreadable:{relative}")
        readme = readable.get("docs/README.md", "")
        current_execution_lines = [line for line in readme.splitlines() if "Current execution sequence" in line]
        checks = [
            {"name": "authoritative_files_readable", "passed": not failures},
            {"name": "readme_current_execution_sequence", "passed": any("runbooks/work-plan-day1-14.md" in line for line in current_execution_lines)},
            {"name": "readme_current_architecture", "passed": "architecture/decision-reasoning-architecture.md" in readme},
            {"name": "readme_current_handoff", "passed": "handoff/handoff-2026-09-18.md" in readme},
            {"name": "week1_not_current_execution_source", "passed": all("week1" not in line.lower() for line in current_execution_lines)},
        ]
        failures.extend(check["name"] for check in checks if not check["passed"])
        return {"checked_files": expected, "checks": checks, "failures": failures, "contract_sources": contract.authoritative_sources}

    def _day_one_test_result(self, *, execute: bool = True, cache_key: str | None = None) -> dict[str, object]:
        candidates = ["tests/test_process_consistency_smoke.py", "tests/test_process_consistency_review_set.py"]
        selected = [path for path in candidates if (self.root / path).is_file()]
        if not selected:
            return {"commands": [], "exit_code": 1, "passed": 0, "failed": 0, "deterministic_only": True, "timestamp": datetime.now(timezone.utc).isoformat(), "reason": "no approved deterministic regression tests found"}
        command = [sys.executable, "-m", "pytest", "-q", *selected]
        if not execute:
            return {"commands": [command], "exit_code": None, "passed": 0, "failed": 0, "deterministic_only": True, "timestamp": datetime.now(timezone.utc).isoformat(), "reason": "read-only diagnostic; command not run"}
        cached = self.snapshot.evidence_cache.get(cache_key) if cache_key else None
        if isinstance(cached, dict) and cached.get("exit_code") == 0 and isinstance(cached.get("passed"), int) and cached["passed"] > 0:
            return {**cached, "cache_hit": True}
        try:
            result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, check=False)
            combined = f"{result.stdout}\n{result.stderr}"
            import re
            passed = next((int(value) for value in re.findall(r"(\d+) passed", combined)), 0)
            failed = next((int(value) for value in re.findall(r"(\d+) failed", combined)), 0)
            evidence = {"commands": [command], "exit_code": result.returncode, "passed": passed, "failed": failed, "deterministic_only": True, "timestamp": datetime.now(timezone.utc).isoformat(), "cache_hit": False}
            if cache_key and result.returncode == 0 and passed > 0 and failed == 0:
                self.snapshot.evidence_cache[cache_key] = evidence
            return evidence
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"commands": [command], "exit_code": 1, "passed": 0, "failed": 0, "deterministic_only": True, "timestamp": datetime.now(timezone.utc).isoformat(), "reason": type(exc).__name__}

    def _collect_day_one_evidence(self, contract: LocalLLMDayContract, *, execute_tests: bool = True) -> dict[str, object]:
        branch_code, branch, _ = self._git("branch", "--show-current")
        head_code, head, _ = self._git("rev-parse", "HEAD")
        commit_code, _commit, _ = self._git("cat-file", "-e", f"{head}^{{commit}}") if head else (1, "", "")
        is_commit = head_code == 0 and commit_code == 0
        status = self._day_one_status_audit()
        upstream_code, upstream, _ = self._git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
        origin_code, origin, _ = self._git("remote", "get-url", "origin")
        upstream_sha_code, upstream_sha, _ = self._git("rev-parse", "@{upstream}") if upstream_code == 0 else (1, "", "")
        ahead, behind = None, None
        if upstream_sha_code == 0:
            count_code, counts, _ = self._git("rev-list", "--left-right", "--count", f"HEAD...@{{upstream}}")
            if count_code == 0 and len(counts.split()) == 2:
                ahead, behind = counts.split()
        git_head = {"branch": branch, "head": head, "is_commit": is_commit}
        origin_ref = {"origin_url": origin, "upstream_ref": upstream, "upstream_sha": upstream_sha, "ahead": ahead, "behind": behind}
        staging = {"staged_paths": status["staged_tracked_paths"], "staged_generated_paths": [path for path in status["staged_tracked_paths"] if self._is_generated_path(path)]}
        staging["generated_artifacts_not_staged"] = not staging["staged_generated_paths"]
        documentation = self._day_one_documentation_check(contract)
        test_paths = [self.root / path for path in ("tests/test_process_consistency_smoke.py", "tests/test_process_consistency_review_set.py")]
        cache_material = "|".join([head, *status["relevant_dirty_paths"], *[
            f"{path.relative_to(self.root).as_posix()}:{self._file_fingerprint(path)}" for path in test_paths
        ]])
        tests = self._day_one_test_result(execute=execute_tests, cache_key=self._text_fingerprint(cache_material))
        commit_ref = {"branch": branch, "head": head, "is_commit": is_commit, "relevant_dirty_paths": status["relevant_dirty_paths"], "reproducible": not status["relevant_dirty_paths"]}
        evidence = {
            "git_head": self._record("git_head", git_head, "git branch --show-current; git rev-parse HEAD; git cat-file -e HEAD^{commit}", branch_code == 0 and is_commit),
            "origin_ref": self._record("origin_ref", origin_ref, "git remote get-url origin; git rev-parse @{upstream}; git rev-list --left-right --count", origin_code == 0 and upstream_sha_code == 0 and bool(origin) and bool(upstream) and bool(upstream_sha)),
            "status_audit": self._record("status_audit", status, "git status --porcelain=v1 -uall", True),
            "staging_audit": self._record("staging_audit", staging, "git status --porcelain=v1 -uall (index column)", bool(staging["generated_artifacts_not_staged"])),
            "documentation_check": self._record("documentation_check", documentation, "deterministic authoritative-document relationship checks", not documentation["failures"]),
            "test_result": self._record("test_result", tests, " ".join(str(part) for part in tests["commands"][0]) if tests["commands"] else "no approved command", tests["exit_code"] == 0),
            "commit_ref": self._record("commit_ref", commit_ref, "git rev-parse HEAD; git cat-file -e HEAD^{commit}; git status --porcelain=v1 -uall", is_commit and commit_ref["reproducible"]),
        }
        return {"final_result": "COMPLETE", "evidence": evidence, "collection": "day1_deterministic"}

    def _record_repair_rejection(self, item: LocalLLMDayWorkItem, code: str, *, card: LocalLLMRepairCard | None = None, executor_result: dict[str, object] | None = None) -> dict[str, object]:
        with self._lock:
            if card:
                self.snapshot.repair_knowledge.append(card.model_copy(update={"status": "CODEX_REJECTED"}))
            self.snapshot.codex_handoff = {"status": "READY", "failed_work_item": item.item_id, "issue_classification": DayIssueClassification.IMPLEMENTATION_DEFECT.value, "local_llm_result": code, "executor_result": self._bounded(executor_result or {})}
            self.snapshot.activity = "LocalLLM proposal was not applied; a bounded Codex handoff is ready."
            self._save()
            return self.view()

    def _bounded_repair_files(self, item: LocalLLMDayWorkItem) -> dict[str, str]:
        """Provide only declared work-order context to the local repair model."""
        if item.dynamic_work_order is None:
            return {}
        protected = ("results/", "artifacts/", "models/", "datasets/", ".env")
        files: dict[str, str] = {}
        for relative in [*item.dynamic_work_order.context_files, *item.dynamic_work_order.allowed_files]:
            if relative in files or relative.startswith(protected):
                continue
            path = (self.root / relative).resolve()
            try:
                path.relative_to(self.root)
                if path.is_file():
                    files[relative] = path.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                continue
            if len(files) >= 3:
                break
        return files

    @staticmethod
    def _classify_result(result: dict[str, object]) -> DayIssueClassification:
        value = result.get("issue_classification")
        try:
            return DayIssueClassification(str(value))
        except ValueError:
            return DayIssueClassification.INSUFFICIENT_EVIDENCE

    @staticmethod
    def _criterion_ids(contract: LocalLLMDayContract) -> set[str]:
        return {criterion.criterion_id for criterion in contract.completion_criteria}

    def _restore_contract(self, current: LocalLLMDayContract, saved: LocalLLMDayContract) -> LocalLLMDayContract:
        """Restore only evidence that validates under the current contract."""
        prior = {criterion.criterion_id: criterion for criterion in saved.completion_criteria}
        criteria: list[DayCriterion] = []
        for criterion in current.completion_criteria:
            old = prior.get(criterion.criterion_id)
            evidence = old.evidence if old and self._criterion_evidence_valid(criterion, old.evidence) else {}
            criteria.append(criterion.model_copy(update={"evidence": evidence, "satisfied": bool(evidence)}))
        restored = current.model_copy(update={"completion_criteria": criteria})
        restored.satisfied_criteria = [criterion.criterion_id for criterion in criteria if criterion.satisfied]
        restored.remaining_gaps = [criterion.criterion_id for criterion in criteria if not criterion.satisfied]
        return restored

    def _valid_work_items(self, items: list[LocalLLMDayWorkItem], contract: LocalLLMDayContract) -> list[LocalLLMDayWorkItem]:
        known = self._criterion_ids(contract)
        return [item for item in items if item.contract_day == contract.day and item.contract_version == contract.version
                and item.criterion_ids and set(item.criterion_ids).issubset(known)]

    def _restore_snapshot(self) -> None:
        """A persisted boolean is never authority after process restart."""
        day = self.snapshot.selected_day
        current = self._load_contracts().get(day) if day is not None else None
        if current is None:
            return
        if self.snapshot.contract is None or self.snapshot.contract.version != current.version:
            self.snapshot = LocalLLMDaySnapshot(
                selected_day=day, objective=current.objective, contract=current,
                activity="Saved Day state requires evidence revalidation under the current contract.",
            )
            return
        self.snapshot.contract = self._restore_contract(current, self.snapshot.contract)
        self.snapshot.work_items = self._valid_work_items(self.snapshot.work_items, current)
        self._evaluate_contract(self.snapshot.contract, self._inventory(current))
        if self.snapshot.state == LocalLLMDayState.COMPLETE and self.snapshot.contract.remaining_gaps:
            self.snapshot.state = LocalLLMDayState.PAUSED
            self.snapshot.activity = "Saved completion was invalidated because required evidence does not validate."

    @staticmethod
    def _bounded(value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            return {"value": str(value)[:1000]}
        return {str(key): value[key] for key in list(value)[:20]}

    def _update_progress(self, contract: LocalLLMDayContract) -> None:
        total = len(contract.completion_criteria)
        self.snapshot.progress = round(len(contract.satisfied_criteria) * 100 / total) if total else 0

    def _recommended_action(self) -> dict[str, object]:
        if self.snapshot.state in {LocalLLMDayState.PAUSED, LocalLLMDayState.STOPPED}:
            return {"action_id": "RESUME", "label": "Resume", "enabled": True, "reason": "Continue persisted incomplete work."}
        if self.snapshot.state == LocalLLMDayState.FAILED and self.snapshot.issue_classification == DayIssueClassification.IMPLEMENTATION_DEFECT:
            return {"action_id": "REPAIR_AND_GO", "label": "Repair and Go", "enabled": True, "reason": "A controlled implementation defect may receive a proposal-only LocalLLM review."}
        if self.snapshot.state == LocalLLMDayState.COMPLETE:
            return {"action_id": "SELECT_NEXT_DAY", "label": "Select next Day", "enabled": True, "reason": "The selected Day has sufficient evidence."}
        return {"action_id": "GO", "label": "Go", "enabled": self.snapshot.state != LocalLLMDayState.RUNNING, "reason": "Load a Day Contract and plan only remaining evidence gaps."}

    def _save(self) -> None:
        self.snapshot.updated_at = datetime.now(timezone.utc)
        if self.persist:
            self.persist(self.snapshot.model_dump(mode="json"))

    def _audit(self, event: str, details: dict[str, object]) -> None:
        if self.audit:
            self.audit("LOCAL_LLM_DAY", event, details)
