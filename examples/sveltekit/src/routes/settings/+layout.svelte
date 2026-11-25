<script>
  let { children } = $props();
</script>

<header class="syn-app-topbar">
  <div>
    <h1 class="syn-heading">Account settings</h1>
    <p>Nested SvelteKit layout, existing Syntyr detail composition.</p>
  </div>
  <a class="syn-button" href="/">Overview</a>
</header>

<div class="syn-detail-layout">
  <section class="syn-detail-main" aria-label="Settings form">
    {@render children()}
  </section>
  <aside class="syn-detail-aside syn-app-card" aria-labelledby="info-title">
    <h2 id="info-title" class="syn-heading">About this example</h2>
    <p>SvelteKit handles form submissions, validation responses and optional client enhancement.</p>
    <p>There is no database. A successful POST is only acknowledged, not saved.</p>
  </aside>
</div>
