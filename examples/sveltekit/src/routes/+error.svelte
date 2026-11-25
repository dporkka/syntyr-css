<script>
  import { page } from '$app/state';
</script>

<section class="syn-result-state" aria-labelledby="failure-title">
  <h1 id="failure-title">{page.status}: Unable to open this page</h1>
  <p>{page.error?.message ?? 'The page could not be loaded.'}</p>
  <a class="syn-button" href="/">Return to overview</a>
</section>
