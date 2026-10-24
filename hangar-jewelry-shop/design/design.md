# Sherry Jewelry

## Purpose

Publish the existing Sherry Jewelry storefront from `sherry-jewelry-site/dist`.
The site opens on its miniature boutique and provides the four-piece collection,
interactive 3D views, product photos, and Shopee purchase links.

## Runtime

The frontend is the existing static site, served through Hangar app assets. Its
HTML, JavaScript, styles, product configuration, photos, fonts, and 3D models
remain in the Hangar asset store. The FastAPI health route remains available for
Hangar runtime checks. The page does not use an app database or external API.

## Access

Keep the app Private. Product purchase links open the corresponding Shopee
listing from the storefront.

## Progressive startup

Show the cream background, brand and 31,880-byte boutique WebP immediately in
the outer app while the storefront frame loads. Preload that same image in
both documents; use the existing asset URL so the browser can reuse it.
The storefront embeds its small stylesheet to remove one blocking request.
After the static poster has decoded and painted, allow 600 ms plus a bounded
idle callback before importing Three.js and loading the boutique model.
Draw the complete first 3D frame before fading out the poster. Keep the static
image and working navigation if 3D fails, and provide an explicit retry.
Cancel scheduled initialization when hidden or leaving the home page.

Load collection models only on entry to the collection. Hidden product-list
photos are lazy-loaded. Detail models still load on product interaction.
Preserve reduced-motion behavior, photo fallback, and current access controls.
First-load latency also includes Hangar authentication and shell startup, which
the storefront cannot eliminate. DOM timing attributes record the static-ready,
3D-start and 3D-ready milestones for representative browser verification.
