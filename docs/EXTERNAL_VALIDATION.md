# External validation checklist

## Already proven externally

- Real Codex smoke
- Configured LocalLLM project smoke
- Controlled Codex repair
- Deterministic PASS with no Codex execution
- Multi-task deterministic single-step
- Mock continuous Day

## Remaining sequence

1. **Human Gate: Real Architect single-step.** Start the production launcher
   with `OPENAI_API_KEY` available to that process, then call only
   `week1-day3-local-llm-v2-real-architect` in `single-step` mode. Confirm one
   Architect call uses `gpt-5.6-terra` at `medium`, evaluator stays `mock`, the
   task deterministically passes, and Codex remains unused.

```powershell
$env:OPENAI_API_KEY = '<set-your-key-in-this-session>'; & C:\AI-Control-Center\scripts\start.ps1
```

In a separate PowerShell session after the server is ready:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/day/start/week1-day3-local-llm-v2-real-architect?mode=single-step" | ConvertTo-Json -Depth 20
```
2. Real Architect resume step, only after the first step passes.
3. Enable and validate real-Architect continuous mode only after the two
   single-step validations are accepted.
4. Real Evaluator semantic validation only if a real semantic task is approved.
5. Human Review stop behavior.
6. Budget stop behavior.
7. Restart/resume behavior.

No item in this checklist authorizes a live call from the development sandbox.
