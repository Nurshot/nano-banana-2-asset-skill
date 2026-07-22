# Framework integration guide

Generate successfully before editing application code. Follow the project's existing conventions over these defaults.

## Web

- Next.js: prefer `next/image`, supply intrinsic `width`/`height` or `fill` with a sized parent, a truthful `sizes`, and `priority` only for the likely LCP image.
- React/Vue/Svelte/HTML: use `<picture>` for art-directed mobile/desktop variants, explicit dimensions or CSS `aspect-ratio`, meaningful `alt`, `object-fit: cover`, and deliberate `object-position`. Use eager loading only above the fold.
- Imported assets belong under `src/assets`; public URL assets belong under `public/images` or the established equivalent.

Example art direction:

```html
<picture>
  <source media="(max-width: 767px)" srcset="/images/hero-mobile.jpg">
  <img src="/images/hero-desktop.jpg" width="1600" height="900"
       alt="Site supervisor reviewing plans with a construction team"
       fetchpriority="high" decoding="async">
</picture>
```

## React Native and Expo

Place bundled files under the existing assets tree and use `require(...)`; use `{ uri }` only when the app already has a remote asset pipeline. Set a stable `aspectRatio`, `resizeMode`, and accessibility label. Use platform-aware variants if the layout changes materially.

## Flutter

Register new bundled assets in `pubspec.yaml` when required. Use `Image.asset`, semantic labels, `fit: BoxFit.cover`, `alignment`, and an `AspectRatio` or constrained parent.

## SwiftUI

Add the asset to the appropriate asset catalog when the project uses one. Use `Image`, `resizable`, `scaledToFill`/`scaledToFit`, clipping, alignment, and an accessibility label or `accessibilityHidden(true)` for decoration.

## Android Compose

Put resources in the correct density-independent or drawable resource location. Use `Image`/`painterResource`, a localized content description or `null` for decoration, `contentScale`, alignment, and a constrained aspect ratio.

## Validation

Run the repository's build and lint commands. Inspect the rendered breakpoint/device when tooling permits. Check crop, legibility, layout shift, alt/semantic behavior, LCP priority, and bundle/resource references. A generation failure must leave code untouched.
