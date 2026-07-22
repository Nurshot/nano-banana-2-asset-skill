# Prompt and composition playbook

## Native ratio mapping

Use the closest ratio from `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, and `21:9`. Match by logarithmic ratio distance so portrait and landscape choices are treated symmetrically.

Run:

```bash
python3 scripts/nano_banana_assets.py plan --desktop 1440x720 --mobile 390x520
```

Two art-directed variants are required when the relative ratio difference is greater than 20%. Generate both from a shared art direction, but move/resize the focal subject and safe-zone for each slot.

## Photograph template

Write one coherent English prompt containing:

- subject identity and visually relevant attributes;
- environment, time, weather, and action;
- composition, crop, focal placement, and copy safe-zone;
- camera viewpoint, plausible lens/focal length, depth of field;
- lighting direction and quality;
- brand-compatible color palette and contrast;
- desired realism and texture;
- exclusions: no text, letters, watermarks, logos, UI, unwanted props, malformed anatomy, or duplicated subjects;
- exact aspect ratio and intended interface role.

Example: “Editorial commercial photograph for a construction management landing-page hero. A diverse site supervisor and two workers reviewing plans beside an excavator at early morning, authentic PPE and realistic active worksite. Wide eye-level composition, 35 mm lens, subjects concentrated in the right 45%, generous uncluttered darker negative space on the left for HTML heading and CTA, warm directional sunrise with cool steel-blue shadows, restrained amber and navy palette, crisp material detail, believable proportions. No visible words, signs, logos, watermarks, UI, duplicated people, staged handshake, or unsafe behavior. 16:9.”

## Illustration template

Specify subject, medium, visual language, shape vocabulary, line treatment, palette tokens, texture, detail density, depth, composition, safe-zone, ratio, and exclusions. Describe a durable design system rather than citing a living artist.

## Editing template

State:

1. what is editable;
2. what must remain pixel-consistent in identity, composition, colors, and geometry;
3. the intended output ratio and crop;
4. prohibited additions.

Use up to three references. The user must have selected or supplied them; never discover and transmit unrelated local files.

## Responsive composition

- Put the focal subject opposite the copy block.
- Reserve 35–50% calm negative space for large hero copy when possible.
- Avoid critical faces, products, hands, or marks near crop boundaries.
- Keep image text out of product UI; render it as accessible HTML/native text.
- Use separate portrait art direction when a wide hero cannot crop without losing meaning.
