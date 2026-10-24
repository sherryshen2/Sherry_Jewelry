<script>
  import { asset } from '$hangarkit';
  import { onMount } from 'svelte';

  let frame;
  let ready = $state(false);
  const poster = asset('d64b377fad6b2743c779c866_boutique-poster.webp');

  onMount(() => {
    const receive = (event) => {
      if (event.origin === location.origin && event.source === frame?.contentWindow && event.data?.type === 'sherry:static-ready') ready = true;
    };
    window.addEventListener('message', receive);
    revealLoadedFrame();
    return () => window.removeEventListener('message', receive);
  });

  function revealLoadedFrame() {
    const doc = frame?.contentDocument;
    const image = doc?.getElementById('boutique-poster');
    if (doc?.getElementById('app-shell') && image?.complete && image.naturalWidth) {
      requestAnimationFrame(() => requestAnimationFrame(() => { ready = true; }));
    }
  }
</script>

<svelte:head>
  <title>Sherry Jewelry — A little world of wonder</title>
  <meta
    name="description"
    content="Step into Sherry Jewelry’s miniature boutique. Discover four delicate pieces, explore every angle, and find your favourite on Shopee."
  />
  <meta name="theme-color" content="#F4EDE3" />
  <link rel="preload" as="image" href={poster} fetchpriority="high" />
</svelte:head>

{#if !ready}
  <div class="startup" aria-hidden="true">
    <header><span class="wordmark"><span class="monogram">S<span>J</span></span>SHERRY JEWELRY</span><span class="collection-link">The collection ↗</span></header>
    <div class="hero">
      <div class="copy"><h1>Sherry <em>Jewelry</em></h1><p>Small treasures. A world of quiet wonder.</p><span class="explore">Explore <span>⟶</span></span></div>
      <div class="visual"><img src={poster} width="817" height="630" alt="" fetchpriority="high" decoding="async" /></div>
    </div>
    <footer><span>SHERRY JEWELRY</span><span class="star">✧</span><em>Made for the moments you keep.</em></footer>
  </div>
{/if}

<iframe
  bind:this={frame}
  class="site-frame"
  class:ready
  title="Sherry Jewelry interactive storefront"
  src={asset('42f96bbf7ddc27b74eca05d8_index.html')}
  onload={revealLoadedFrame}
  inert={!ready}
  allow="fullscreen"
></iframe>

<style>
  :global(html),
  :global(body) {
    background: #f4ede3;
    margin: 0;
    min-height: 100%;
  }

  :global(body) {
    overflow: hidden;
  }

  .site-frame {
    background: #f4ede3;
    border: 0;
    display: block;
    height: 100vh;
    height: 100dvh;
    min-height: 100%;
    width: 100%;
    opacity: 0;
  }
  .site-frame.ready { opacity: 1; }
  .startup { position: fixed; inset: 0; background: #f4ede3; color: #493d37; overflow: auto; pointer-events: none; font-family: Arial, sans-serif; }
  .startup * { box-sizing: border-box; }
  header { height: 108px; padding: 0 5.7%; display: flex; align-items: center; justify-content: space-between; }
  .wordmark { display: flex; align-items: center; gap: 16px; font-size: 10px; letter-spacing: 2.7px; }
  .monogram { font: 36px/45px Georgia, serif; letter-spacing: -8px; width: 45px; height: 45px; border: 1px solid #c7af8a; border-radius: 50%; padding-left: 8px; }
  .monogram span { font-size: 24px; }
  .collection-link { font-size: 13px; }
  .hero { max-width: 1680px; margin: auto; display: grid; grid-template-columns: 40% 60%; align-items: center; padding: 0 5.7% 62px; min-height: calc(100svh - 155px); }
  .copy { padding: 0 0 26px 6%; z-index: 1; }
  h1 { font: 400 clamp(48px, 6.1vw, 92px)/1 Georgia, serif; letter-spacing: -2px; white-space: nowrap; margin: 0; }
  h1 em { font-weight: 400; }
  p { font: clamp(14px, 1.25vw, 18px)/1.55 Georgia, serif; margin: 30px 0 21px; color: #796762; white-space: nowrap; }
  .explore { font: 29px/1.2 Georgia, serif; display: inline-flex; gap: 35px; padding: 9px 0; }
  .explore span { color: #a78959; }
  .visual { position: relative; height: min(70vh, 760px); min-height: 470px; background: radial-gradient(ellipse, #eadbc777, transparent 68%); }
  .visual img { width: 100%; height: 100%; object-fit: contain; transform: scale(1.1); }
  footer { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; margin: 0 5.7%; height: 47px; border-top: 1px solid #b59d7c30; color: #9b887e; font-size: 8px; letter-spacing: 1.5px; }
  footer em { justify-self: end; text-align: right; font: italic 13px Georgia, serif; letter-spacing: .3px; }
  .star { font-size: 24px; color: #bda477; }
  @media (max-width: 767px) {
    header { height: 80px; padding: 0 6%; }
    .wordmark { gap: 10px; font-size: 8px; letter-spacing: 1.7px; }
    .monogram { width: 36px; height: 36px; line-height: 36px; font-size: 30px; }
    .monogram span { font-size: 20px; }
    .collection-link { font-size: 11px; }
    .hero { display: flex; flex-direction: column; padding: clamp(40px, 9svh, 86px) 5% 20px; min-height: calc(100svh - 125px); }
    .copy { padding: 0; text-align: center; align-self: stretch; }
    h1 { font-size: 48px; letter-spacing: -1.5px; }
    p { font-size: clamp(13px, 4.16vw, 15px); margin: 13px 0 7px; }
    .explore { font-size: 26px; gap: 23px; }
    .visual { width: 100%; height: 48svh; min-height: 320px; max-height: 550px; margin-top: 2px; }
    .visual img { transform: none; }
    footer { height: 45px; font-size: 6px; letter-spacing: 1px; }
    footer em { font-size: 11px; }
  }
</style>
