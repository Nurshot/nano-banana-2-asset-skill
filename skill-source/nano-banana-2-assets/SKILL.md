---
name: nano-banana-2-assets
description: Proactively design, generate, edit, and integrate project-ready raster visuals through Google Antigravity's Agy CLI and Nano Banana 2 whenever the user requests an image or an agent decides a web/mobile project needs photography, illustration, texture, background, onboarding art, product imagery, a raster effect, a replacement for a placeholder/stock asset, or an edit to an existing bitmap. Use even when the user did not explicitly ask for image generation. Route icons, simple vectors, gradients, shadows, glows, and charts to native code instead of Agy.
---

# Nano Banana 2 Assets

Act as the project's visual router and asset integrator. Make the visual decision proactively, generate only when raster imagery is the right medium, and leave the project in a working state.

## Route the visual request

Use Agy for photographs, illustrations, textured backgrounds, product scenes, people, onboarding art, editorial/content imagery, complex raster effects, and edits to existing bitmaps.

Do not use Agy for a small SVG icon, logo-system extension, simple gradient, glow, shadow, divider, geometric decoration, chart, or effect that is clearer and more responsive in HTML/CSS/canvas/native drawing code. Implement those directly. If a request mixes both kinds, use Agy only for the raster portion.

Do not ask for per-image approval. Ask the user to intervene only when Agy has no authenticated session or the operating system presents a permission prompt.

## Analyze before generating

1. Inspect the target component or screen, neighboring copy, responsive layout, design tokens, brand palette, existing assets, and framework conventions.
2. Decide the subject, setting, action, medium, composition, camera/lens when photographic, lighting, palette, focal point, and copy safe-zone.
3. Keep headings, buttons, labels, logos, and UI text in code. Do not bake them into the image unless the image itself is explicitly typographic artwork.
4. Measure the rendered slot. Map it to a supported native ratio using the runner. When desktop and mobile slot ratios differ by more than 20%, generate separate art-directed variants rather than relying only on cropping.
5. Use at most three user-selected reference images. Never send source code, conversation databases, credentials, or unrelated project files to Agy.

Read [prompt-playbook.md](references/prompt-playbook.md) for prompt construction and ratio rules. Read [framework-integration.md](references/framework-integration.md) before modifying application code.

## Generate with Agy

Write the generation prompt in detailed English by default, even when the user speaks another language. Include subject, environment, action, composition, lens/camera or illustration medium, lighting, palette, focal point, safe-zone, exclusions, and the required aspect ratio.

Run the dependency-free helper from the skill directory:

```bash
python3 scripts/nano_banana_assets.py generate \
  --prompt-file /tmp/nano-banana-prompt.txt \
  --target-width 1600 --target-height 900 \
  --output public/images/construction-hero.jpg
```

Prefer `--prompt-file` for detailed prompts. Add `--reference PATH` no more than three times. Use `--desktop WIDTHxHEIGHT --mobile WIDTHxHEIGHT` with `plan` to decide whether two variants are required. Run `doctor` when Agy availability or authentication is uncertain.

The helper invokes `agy --print --print-timeout 5m` without a shell. It assigns a unique run ID, asks Agy to use its built-in `generate_image` tool, extracts the returned artifact path, and only then copies the image atomically. It never uses an API key, internal Google endpoint, conversation database, protobuf record, C2PA/SynthID check, model-name check, provenance manifest, or `--dangerously-skip-permissions`.

If generation fails or no artifact can be found, do not alter application code. Report the error and preserve the existing UI. If the real image dimensions are below the requested slot, integrate it only when still useful and clearly warn the user; do not claim that it is 2K/4K and do not fake an upscale.

## Integrate transactionally

1. Generate and inspect the asset before editing code.
2. Place it in the project's established asset directory, such as `public/images`, `src/assets`, `assets/images`, or the platform equivalent. Use a semantic filename. Never silently overwrite an existing file; use `--overwrite` only for an explicit replacement.
3. Add the framework-appropriate import/reference, meaningful accessible alt text (or intentionally empty alt for decoration), intrinsic width/height or aspect ratio, responsive sizing, object fit/position, and correct loading priority.
4. Use art-directed desktop/mobile sources when two variants were generated. Preserve the safe-zone with `object-position` or platform alignment.
5. Run the relevant build and lint checks, then inspect a browser/mobile render when available. Fix layout or cropping regressions.

For an edit, pass the existing bitmap as a reference and state exactly what must remain unchanged. Do not overwrite the original unless replacement is explicit.

## Report the result

State which assets were generated, their measured dimensions, where they were integrated, what checks ran, and any resolution warning. Do not claim that the backend model was independently verified; “Nano Banana 2” describes the Agy image-generation route requested by this skill.
