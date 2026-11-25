<script>
  import { enhance } from '$app/forms';
  import { onDestroy } from 'svelte';
  import AppPanel from '../../lib/AppPanel.svelte';

  let { form } = $props();
  let submitting = $state(false);

  let pageActive = true;
  onDestroy(() => { pageActive = false; });

  // Optional enhancement. The same POST works without hydration or JavaScript.
  function enhanceSubmission() {
    submitting = true;
    return async ({ result, update }) => {
      try {
        // A late action must not navigate back to this page after leaving it.
        if (!pageActive) return;
        // Keep the validated value on success; browser-native submission
        // remains the fallback if enhancement is unavailable.
        await update({ reset: false });
        if (pageActive && result.type === 'failure') {
          document.getElementById('settings-errors')?.focus();
        }
      } finally {
        if (pageActive) submitting = false;
      }
    };
  }
</script>

<AppPanel title="Workspace profile">
  {#snippet actions()}
    <a class="syn-button" href="/">Back to overview</a>
  {/snippet}

  <p>The form uses a real server action. For this reference, success is acknowledged but not persisted.</p>

  {#if form?.errors?.name}
    <div class="syn-error-summary" id="settings-errors" tabindex="-1" role="alert"
         aria-labelledby="settings-errors-title">
      <h3 id="settings-errors-title">Check the submitted details</h3>
      <ul><li><a href="#workspace-name">{form.errors.name}</a></li></ul>
    </div>
  {:else if form?.success}
    <div class="syn-operation-feedback" data-syn-state="saved" role="status">
      <strong>Validated</strong>
      <p>“{form.value}” passed server validation. Nothing was saved.</p>
    </div>
  {/if}

  {#if submitting}
    <div class="syn-operation-feedback" data-syn-state="pending" role="status">
      <p>Checking account details…</p>
    </div>
  {/if}

  <form class="syn-form" method="POST" action="/settings"
        use:enhance={enhanceSubmission} aria-busy={submitting}>
    <div class="syn-field">
      <label class="syn-label" for="workspace-name">Workspace name</label>
      <input class="syn-input" type="text" id="workspace-name" name="name"
             autocomplete="organization"
             required readonly={submitting}
             value={form?.value ?? ''}
             aria-invalid={form?.errors?.name ? 'true' : undefined}
             aria-describedby={form?.errors?.name ? 'workspace-help workspace-error' : 'workspace-help'} />
      <p class="syn-help" id="workspace-help">Between 2 and 80 characters.</p>
      {#if form?.errors?.name}
        <p class="syn-error" id="workspace-error">{form.errors.name}</p>
      {/if}
    </div>
    <div class="syn-form-actions">
      <button class="syn-button syn-button--primary" type="submit" disabled={submitting}>
        {submitting ? 'Checking…' : 'Validate name'}
      </button>
    </div>
  </form>

  {#snippet footer()}
    <p class="syn-caption">The server owns authorization, durable persistence and validation.</p>
  {/snippet}
</AppPanel>
