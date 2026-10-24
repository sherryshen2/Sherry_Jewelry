# $content editable content fields

ID: `frontend.content`
Category: `content`

CMS-like app content values editable from the Content panel without code changes.

## Import

`import content from '$content'`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `content.field_name`

## Details

Use `$content` for user-facing copy and editable images: titles, labels, empty states, descriptions, nav text, hero images, logos, and similar app content.

Create content fields before relying on them in code so non-technical users can edit the app from Craft without source changes.

When changing existing copy, labels, placeholders, markdown, editable images, booleans, numbers, or JSON content, update the existing Content field value. Do not only patch code that references `content.some_key`; the rendered app will keep using the current Content field value until that field is changed.

Important for local development: `$content` is a virtual Hangar module, not a normal npm dependency.
## Quick examples

- `<h1>{content.hero_title}</h1>`
- `<img src={content.logo} alt={content.logo_alt} />`
