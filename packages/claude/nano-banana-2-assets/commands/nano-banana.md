---
description: Generate or edit a project visual with Nano Banana 2 and integrate it into the current app
argument-hint: <visual request> [target=path] [desktop=WxH] [mobile=WxH] [reference=path]
---

# Nano Banana

Use the `nano-banana-2-assets` skill for this request.

User request: $ARGUMENTS

Inspect the current web or mobile project and the target UI before designing the image. Infer the most suitable target component, composition, responsive ratios, safe-zone, filename, and asset directory when the arguments omit them. If no arguments are provided, find the most important visible placeholder or unmet raster-visual need in the current project; ask one concise question only when no safe target can be inferred.

Route simple SVG icons, gradients, glows, shadows, charts, and code-native effects to native code without Agy. For photography, illustration, textures, complex raster effects, or bitmap edits, write the detailed English prompt, generate through Agy, inspect the result, and integrate it with accessible and responsive framework conventions.

Do not modify application code unless generation succeeds. Never silently overwrite an existing asset. Run the relevant build or lint check and report the generated path, measured dimensions, integration point, and warnings.

When the request needs multiple assets, generate at most two concurrently, wait for that pair, then continue with the next pair. Stop the batch immediately on a `rate_limit` result and honor its reported dynamic cooldown; do not assume a fixed reset duration.
