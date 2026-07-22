# Security

Report security issues privately to the repository owner before opening a public issue.

The runner executes `agy` as an argument array without a shell. It never requests `--dangerously-skip-permissions`, reads OAuth tokens, queries conversation databases, calls internal Google endpoints, or sends project source code to Agy. Reference files must be explicitly selected for the visual task.

Generated content is untrusted input. Inspect assets before shipping them and follow the application platform's content and accessibility requirements.
