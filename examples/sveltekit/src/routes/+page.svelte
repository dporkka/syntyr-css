<script>
  import AppPanel from '../lib/AppPanel.svelte';
</script>

<h1 class="syn-heading">Workspace overview</h1>
<p class="syn-lede">The shell is server-rendered HTML with Syntyr CSS. Follow Settings to try a native POST form.</p>

<AppPanel title="Next action">
  {#snippet actions()}
    <a class="syn-button syn-button--primary" href="/settings">Edit account</a>
  {/snippet}
  <p>No Syntyr JavaScript, provider, router, or state store is required.</p>
</AppPanel>
