# Nano Banana 2 Assets for Codex & Claude Code

`nano-banana-2-asset-skill` is a portable Agent Skill for Codex/ChatGPT desktop and Claude Code. [Antigravity officially states that its generative image tool uses Nano Banana 2 for UI mockups and images that populate web pages or applications](https://antigravity.google/docs/models#additional-models); local generation records identify that step as `gemini-3.1-flash-image` (Nano Banana 2). The plugin does not re-verify the model on every run. It proactively notices when a project needs raster artwork, designs a layout-aware prompt, generates it through Agy, and integrates the result into code.

It is also a visual router: photography, illustration, textures, and bitmap edits go to Agy; SVG icons, simple gradients, glows, shadows, charts, and code-native effects stay in code.

## Requirements

- Google Antigravity CLI (`agy`) 1.1.5 or newer
- A completed local Google OAuth session in Agy
- Python 3
- Local command execution and project-file access

The skill does not use a Gemini API key, internal Google endpoint, or unsafe permission bypass. It does not verify the backend model. “Nano Banana 2” names the requested Agy image-generation route, not an independent provenance claim.

> **Compatibility notice:** Google currently says that using third-party software—including Claude Code—with an Antigravity login may violate its terms. Review the [Antigravity FAQ](https://antigravity.google/docs/faq#why-cant-i-use-third-party-software-eg-claude-code-openclaw-opencode-with-my-antigravity-login) before use. This community plugin does not bypass authentication, permissions, credits, or quotas.

## Install

### Codex / ChatGPT desktop

Install from this GitHub marketplace, just like the Claude flow:

```bash
codex plugin marketplace add Nurshot/nano-banana-2-asset-skill
codex plugin add nano-banana-2-assets@nano-banana-assets
```

Then start `codex` and enter `/plugins` to inspect, enable, or disable the plugin. In the ChatGPT desktop app, restart the app, open **Plugins**, select the **Nano Banana Assets** marketplace, and install the plugin.

### Claude Code

```text
/plugin marketplace add Nurshot/nano-banana-2-asset-skill
/plugin install nano-banana-2-assets@nano-banana-assets
/reload-plugins
```

## Use

The skill activates automatically when the agent decides the project needs raster artwork. You can also invoke it explicitly:

```text
/nano-banana Create a cinematic construction hero, target=src/components/Hero.tsx desktop=1600x900 mobile=900x1200
```

Claude Code namespaces plugin commands:

```text
/nano-banana-2-assets:nano-banana Create a three-step onboarding illustration, mobile=900x1200
```

Natural-language requests work too:

```text
Replace the placeholder in this product hero with a production-ready image.
```

## Quotas

The runner detects `429 RESOURCE_EXHAUSTED` even when Agy exits successfully, returns a structured `rate_limit` error with the reported reset time, and leaves assets and application code unchanged. Reset times are dynamic—not fixed at three hours—and the reported cooldown prevents new requests until it expires. Multi-image work runs at most two generations concurrently and proceeds pair by pair. Check current quota with Agy `/usage` or `/quota`; plan behavior is documented on [Antigravity Plans](https://antigravity.google/docs/plans).

## Data and permissions

Only the designed visual prompt and reference images explicitly selected for the task are sent through Google Antigravity. The skill does not read OAuth tokens and collects no telemetry. See [privacy](docs/PRIVACY.md) and [security](SECURITY.md).

Tests, CI, release tooling, and store-review material remain in the repository for maintainers but are not included in the installable plugin ZIPs.

## License

MIT
