// App-owned HTMX 2 validation hook, not shipped as Syntyr runtime JavaScript.
// HTMX does not swap HTTP 422 responses by default. Allow only our own
// explicitly marked validation fragment to update the accessible field error.
document.addEventListener('htmx:beforeSwap', (event) => {
  if (event.detail.xhr.status === 422 &&
      event.detail.xhr.getResponseHeader('X-Syntyr-Validation') === 'invalid') {
    event.detail.shouldSwap = true;
    event.detail.isError = false;
  }
});
