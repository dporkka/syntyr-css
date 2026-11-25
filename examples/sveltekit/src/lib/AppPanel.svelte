<script>
  /** @typedef {import('svelte').Snippet} Snippet */
  /** @type {{ title: string; children: Snippet; actions?: Snippet; footer?: Snippet }} */
  let { title, children, actions, footer } = $props();
</script>

<section class="syn-panel syn-flow" aria-label={title}>
  <header class="syn-inline" style="--syn-inline-justify: space-between">
    <h2 class="syn-heading">{title}</h2>
    {#if actions}{@render actions()}{/if}
  </header>
  {@render children()}
  {#if footer}
    <footer class="syn-inline">{@render footer()}</footer>
  {/if}
</section>
