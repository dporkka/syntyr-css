<script>
  // These CSS files are built once in the Syntyr repository; no CSS runtime.
  import '../../../../dist/syntyr.core.css';
  import '../../../../dist/syntyr.recipes.css';
  import { page } from '$app/state';
  let { children } = $props();
</script>

<svelte:head><title>Syntyr · SvelteKit reference</title></svelte:head>

<div class="syn-root" data-syn-theme="studio">
  <header class="syn-shell syn-header">
    <a href="/" class="syn-heading" aria-label="Syntyr demo home">Syntyr demo</a>
    <span class="syn-caption">Native HTML + optional SvelteKit enhancement</span>
  </header>
  <div class="syn-app-shell">
    <aside class="syn-app-rail">
      <nav class="syn-app-nav" aria-label="Primary">
        <a href="/" aria-current={page.url.pathname === '/' ? 'page' : undefined}>Overview</a>
        <a href="/settings" aria-current={page.url.pathname.startsWith('/settings') ? 'page' : undefined}>Settings</a>
      </nav>
    </aside>
    <main class="syn-workspace" id="main">
      {@render children()}
    </main>
  </div>
</div>
