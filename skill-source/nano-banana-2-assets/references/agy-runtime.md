# Agy runtime contract

Requirements: Google Antigravity CLI (`agy`) 1.1.5 or newer, a completed local Google OAuth session, Python 3, local command execution, and access to the target project files.

The runner sends Agy only the designed image prompt and paths to reference images explicitly selected for the task. Agy reads those references when generating. The runner does not read OAuth tokens and collects no telemetry.

Headless Agy may auto-deny a required command permission because it cannot display an interactive prompt. In that case, add only the narrow allow-rule named in Agy's diagnostic to the user's Agy settings and retry. The runner never edits permission settings or falls back to `--dangerously-skip-permissions`.

## Quotas and rate limits

Treat `429`, `RESOURCE_EXHAUSTED`, quota-exhausted, and rate-limit-reset text as a rate limit even when Agy exits with status 0. Return a structured `rate_limit` error with any model and reset hint found in the response. Do not copy a hypothetical artifact path, edit application code, loop retries, sleep for hours, change the user's credit settings, or attempt to bypass the quota. Direct the user to Agy `/usage` (alias `/quota`). The backend's reported reset hint is authoritative for that request.

Antigravity documents that Pro and Ultra baseline quota generally refreshes every five hours until a weekly limit is reached; other plans may refresh weekly. Capacity and task complexity affect consumption, so never promise a fixed number of generations. See [Antigravity plans](https://antigravity.google/docs/plans) and [the CLI quota command](https://antigravity.google/docs/cli/commands/usage).

Artifact resolution is intentionally simple:

1. Prefer a real image path printed by Agy stdout for the unique run ID.
2. If stdout has no usable path, search recent image files containing the run ID under the configured artifact roots or common Antigravity `brain` locations.
3. Read the actual PNG/JPEG/WebP dimensions for layout metadata.

This is correlation, not backend-model verification. Do not inspect protobuf records, conversation databases, credentials, internal endpoints, C2PA, SynthID, or provenance metadata.
