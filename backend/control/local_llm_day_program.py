"""Generic, evidence-first Day 1-14 orchestration for LocalLLM-Lab.

The runbook supplies the Day contract (what must be true).  A bounded planner
supplies work items (how to collect or create evidence).  This module never
derives a shell command, source scope, or completion decision from browser
input or an LLM response.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, RLock, Thread
from typing import Callable

import yaml

from backend.control.local_ollama_repair import LocalOllamaRepairBuilder
from backend.models.local_llm_day import (
    DayCriterion,
    DayIssueClassification,
    LocalLLMDayContract,
    LocalLLMDayReport,
    LocalLLMDaySnapshot,
    LocalLLMDayState,
    LocalLLMDayWorkItem,
    LocalLLMRepairCard,
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
    ) -> None:
        self.root = root.resolve()
        self.persist, self.audit = persist, audit
        self.snapshot = LocalLLMDaySnapshot.model_validate(saved or {})
        self.planner = planner or self._deterministic_plan
        self.work_order_executor = work_order_executor or self._read_only_executor
        self.repair_builder = repair_builder or LocalOllamaRepairBuilder()
        self._lock, self._stop = RLock(), Event()
        self._thread: Thread | None = None
        if self.snapshot.state == LocalLLMDayState.RUNNING:
            self.snapshot.state = LocalLLMDayState.PAUSED
            self.snapshot.stop_reason = "INTERRUPTED_REQUIRES_RESUME"
            self.snapshot.activity = "Interrupted by restart; Resume continues from the persisted contract and task states."
            self._save()

    def days(self) -> list[dict[str, object]]:
        return [{"day": contract.day, "objective": contract.objective} for contract in self._load_contracts().values()]

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
            self.snapshot.selected_day, self.snapshot.objective = day, contract.objective
            self.snapshot.contract = contract
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
            # Do not discard trusted completed work on Resume/start of the same Day.
            if self.snapshot.selected_day != day or self.snapshot.contract is None:
                self.snapshot = LocalLLMDaySnapshot(selected_day=day, objective=contract.objective, contract=contract)
            else:
                self.snapshot.contract = contract.model_copy(update={
                    "satisfied_criteria": self.snapshot.contract.satisfied_criteria,
                    "remaining_gaps": self.snapshot.contract.remaining_gaps,
                    "completion_criteria": self._merge_criteria(contract.completion_criteria, self.snapshot.contract.completion_criteria),
                })
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
        """Ask LocalLLM for bounded proposals; only the guarded executor may act."""
        with self._lock:
            if self.snapshot.state != LocalLLMDayState.FAILED or self.snapshot.issue_classification != DayIssueClassification.IMPLEMENTATION_DEFECT:
                return {"error_code": "AUTONOMOUS_REPAIR_NOT_AVAILABLE", **self.view()}
            item = next((value for value in self.snapshot.work_items if value.state == LocalLLMWorkItemState.FAILED), None)
            if item is None:
                return {"error_code": "REPAIR_TARGET_MISSING", **self.view()}
            files = self._bounded_repair_files(item)
            excerpt = str(item.evidence.get("failure_excerpt", ""))[:2000]
        proposal = self.repair_builder.propose(failure_excerpt=excerpt, files=files, timeout_seconds=120)
        if proposal is None:
            return self._record_repair_rejection(item, "LOCAL_LLM_NO_PROPOSAL")
        # LocalLLM output becomes an auditable proposal.  It never changes a file here.
        card = LocalLLMRepairCard(
            problem_id=f"proposal-{item.item_id}", title="LocalLLM countermeasure proposal",
            cause=proposal.diagnosis, investigation="Codex/engine must inspect the supplied source and deterministic failure.",
            resolution_logic="Proposal retained for guarded WorkOrder review; no direct edit was applied.",
            verification="Run the configured deterministic postcheck after an in-scope Builder result.",
            failure_class=DayIssueClassification.IMPLEMENTATION_DEFECT.value, failed_work_item=item.item_id,
        )
        work_order = {"kind": "LOCAL_LLM_COUNTERMEASURE", "task_id": item.item_id, "proposal": proposal, "files": sorted(files), "dynamic_work_order": item.dynamic_work_order.model_dump(mode="json") if item.dynamic_work_order else None}
        result = self.work_order_executor(work_order)
        if result.get("final_result") not in {"COMPLETE", "COMPLETE_NO_CHANGE"}:
            return self._record_repair_rejection(item, str(result.get("error_code") or "CODEX_REJECTED_PROPOSAL"), card=card, executor_result=result)
        with self._lock:
            self.snapshot.repair_knowledge.append(card.model_copy(update={"status": "CODEX_ACCEPTED"}))
            item.state, item.evidence = LocalLLMWorkItemState.COMPLETE, {"countermeasure": "CODEX_ACCEPTED", "executor_result": self._bounded(result)}
            self.snapshot.repair_attempted = True
            self.snapshot.state = LocalLLMDayState.PAUSED
            self.snapshot.activity = "Codex accepted a bounded countermeasure; Resume re-evaluates the Day Contract."
            self._save()
            return self.view()

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
                    self.snapshot.work_items.extend(proposed)
                    self.snapshot.replan_count += 1
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
        result = self.work_order_executor({"kind": item.kind, "task_id": item.item_id, "engine_task_id": item.engine_task_id, "dynamic_work_order": item.dynamic_work_order.model_dump(mode="json") if item.dynamic_work_order else None, "criterion_ids": item.criterion_ids, "contract": contract.model_dump(mode="json"), "inventory": inventory})
        final = result.get("final_result")
        if final in {"COMPLETE", "COMPLETE_NO_CHANGE"}:
            item.state, item.evidence = LocalLLMWorkItemState.COMPLETE, self._bounded(result)
            for criterion in contract.completion_criteria:
                if criterion.criterion_id in item.criterion_ids and result.get("evidence", {}).get(criterion.criterion_id):
                    criterion.satisfied = True
                    criterion.evidence = self._bounded(result.get("evidence", {}).get(criterion.criterion_id))
            self._update_progress(contract)
            self._save()
            return
        classification = self._classify_result(result)
        item.state = LocalLLMWorkItemState.FAILED
        item.evidence = self._bounded(result)
        if classification == DayIssueClassification.IMPLEMENTATION_DEFECT and item.dynamic_work_order is not None and not self.snapshot.repair_attempted:
            # Ordinary engineering failures receive one bounded automatic
            # countermeasure review. Research findings never enter this path.
            self.snapshot.state = LocalLLMDayState.FAILED
            self.snapshot.issue_classification = classification
            self._save()
            repaired = self.repair_and_go()
            if repaired.get("state") == LocalLLMDayState.PAUSED.value:
                self.snapshot.state = LocalLLMDayState.RUNNING
                self.snapshot.activity = "Codex reviewed the LocalLLM countermeasure; re-evaluating trusted evidence."
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
        # Evidence created by a completed guarded task is the only satisfier.
        for criterion in contract.completion_criteria:
            if criterion.satisfied:
                continue
            matching = [item for item in self.snapshot.work_items if criterion.criterion_id in item.criterion_ids and item.state == LocalLLMWorkItemState.COMPLETE]
            for item in matching:
                if item.evidence.get("evidence", {}).get(criterion.criterion_id):
                    criterion.satisfied, criterion.evidence = True, self._bounded(item.evidence["evidence"][criterion.criterion_id])
                    break
        # A read-only resolver recognizes retained, named result manifests.
        # It never reruns inference, reads model output, or infers success from
        # a directory alone.
        for criterion_id, evidence in self._existing_evidence(contract).items():
            criterion = next((value for value in contract.completion_criteria if value.criterion_id == criterion_id), None)
            if criterion and not criterion.satisfied:
                criterion.satisfied, criterion.evidence = True, evidence
        contract.satisfied_criteria = [item.criterion_id for item in contract.completion_criteria if item.satisfied]
        contract.remaining_gaps = [item.criterion_id for item in contract.completion_criteria if not item.satisfied]
        self._update_progress(contract)

    def _existing_evidence(self, contract: LocalLLMDayContract) -> dict[str, dict[str, object]]:
        """Resolve only retained manifest/summary records known to be evidence."""
        evidence: dict[str, dict[str, object]] = {}
        def latest(pattern: str, required: tuple[str, ...]) -> Path | None:
            candidates = sorted((path for path in self.root.glob(pattern) if path.is_dir() and all((path / name).is_file() for name in required)), key=lambda path: path.name)
            return candidates[-1] if candidates else None
        drap = latest("results/decision-reasoning-v0.4/DRAP-*", ("manifest.json", "validation.jsonl", "action-gate-summary.json"))
        dagb = latest("results/decision-generalization/DAGB2-*", ("manifest.json",))
        if contract.day == 2 and drap:
            for suffix in ("feasibility_gate", "relevance_gate", "deterministic_validation"):
                evidence[f"d2-{suffix}"] = {"source": str(drap.relative_to(self.root)).replace("\\", "/"), "manifest": "manifest.json", "validation": "validation.jsonl", "mode": "existing_evidence"}
        if contract.day == 4 and dagb:
            for suffix in ("frozen_holdout", "evaluation_results"):
                evidence[f"d4-{suffix}"] = {"source": str(dagb.relative_to(self.root)).replace("\\", "/"), "manifest": "manifest.json", "mode": "existing_evidence"}
        return evidence

    def _validated_plan(self, contract: LocalLLMDayContract, inventory: dict[str, object]) -> list[LocalLLMDayWorkItem]:
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
            validated.append(item)
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
        return {**self._git_state(), "source_presence": source_presence, "missing_sources": [path for path, present in source_presence.items() if not present]}

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
    def _merge_criteria(current: list[DayCriterion], saved: list[DayCriterion]) -> list[DayCriterion]:
        old = {item.criterion_id: item for item in saved}
        return [item.model_copy(update={"satisfied": old[item.criterion_id].satisfied, "evidence": old[item.criterion_id].evidence}) if item.criterion_id in old else item for item in current]

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
