# Agy runtime contract

Requirements: Google Antigravity CLI (`agy`) 1.1.5 or newer, a completed local Google OAuth session, Python 3, local command execution, and access to the target project files.

The runner sends Agy only the designed image prompt and paths to reference images explicitly selected for the task. Agy reads those references when generating. The runner does not read OAuth tokens and collects no telemetry.

Headless Agy may auto-deny a required command permission because it cannot display an interactive prompt. In that case, add only the narrow allow-rule named in Agy's diagnostic to the user's Agy settings and retry. The runner never edits permission settings or falls back to `--dangerously-skip-permissions`.

Artifact resolution is intentionally simple:

1. Prefer a real image path printed by Agy stdout for the unique run ID.
2. If stdout has no usable path, search recent image files containing the run ID under the configured artifact roots or common Antigravity `brain` locations.
3. Read the actual PNG/JPEG/WebP dimensions for layout metadata.

This is correlation, not backend-model verification. Do not inspect protobuf records, conversation databases, credentials, internal endpoints, C2PA, SynthID, or provenance metadata.
