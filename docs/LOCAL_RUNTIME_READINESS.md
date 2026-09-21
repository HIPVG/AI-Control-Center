# Local Runtime Readiness

M28 makes the configured local Ollama experiment ready as part of a normal
Zero-Touch execution. This is a fixed server-side contract, not a browser
command surface.

## Approved operation

Before a trusted LocalLLM experiment is executed, Control Center checks the
fixed `ollama list` readiness command. If Ollama is already ready, execution
continues. If the approved `ollama` executable is installed but its server is
not ready, Control Center starts only the fixed `ollama serve` command and
checks readiness at most eight times, once per second.

The resulting bounded state is one of:

- `READY` — the approved runtime was already available.
- `STARTED` — Control Center started the approved runtime and verified it.
- `EXTERNAL_ACTION_REQUIRED` — the runtime was not installed, could not start,
  or was not ready before the bounded wait expired.

Only the state, stable reason code, wait count, and whether Control Center
started the runtime are recorded. Executable paths, command output, prompts,
and environment values are not exposed through the Dashboard.

## Explicit limits

The readiness operation never installs a runtime, downloads a model, starts a
cloud provider, or accepts an executable path, command, timeout, model, or
configuration from the browser. A failure stops the trusted flow with
`EXTERNAL_ACTION_REQUIRED`; it does not retry the experiment or invoke Builder.

The API, enum values, and audit identifiers remain English. The Dashboard
translates their user-facing presentation to Japanese.
