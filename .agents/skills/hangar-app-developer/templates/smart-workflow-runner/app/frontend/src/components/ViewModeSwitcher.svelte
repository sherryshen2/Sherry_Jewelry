<script lang="ts">
	let { value = 'parsed', parsed_label = 'Parsed view', on_select = () => {} } = $props()
</script>

<div class="switcher" role="tablist" aria-label="View format">
	<button class:active={value === 'parsed'} role="tab" aria-selected={value === 'parsed'} onclick={() => on_select('parsed')}>{parsed_label}</button>
	<button class:active={value === 'raw'} role="tab" aria-selected={value === 'raw'} onclick={() => on_select('raw')}>Raw JSON</button>
</div>

<style>
	.switcher { display:inline-flex; padding:3px; border:1px solid #dbe3f0; border-radius:9px; background:#f7f9fc; }
	button { border:0; border-radius:6px; padding:.34rem .62rem; color:#637083; background:transparent; font:inherit; font-size:.75rem; font-weight:550; cursor:pointer; }
	button.active { color:#3159db; background:#fff; box-shadow:0 1px 2px #17203318; }
</style>
