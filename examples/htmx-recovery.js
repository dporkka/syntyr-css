/* Example application code only. Not distributed with Syntyr's CSS core.
   HTMX handles requests; this only exposes a native-navigation escape hatch. */
(() => {
  "use strict";
  const form = document.getElementById("customer-search");
  const error = document.getElementById("search-error");
  const link = document.getElementById("native-search-link");
  if (!form || !error || !link) return;

  const clearFailure = () => { error.hidden = true; };
  const showFailure = () => {
    const destination = new URL(form.action, window.location.href);
    destination.search = new URLSearchParams(new FormData(form)).toString();
    link.href = destination.pathname + destination.search + destination.hash;
    error.hidden = false;
  };

  form.addEventListener("htmx:beforeRequest", clearFailure);
  for (const event of ["htmx:responseError", "htmx:sendError", "htmx:timeout"]) {
    form.addEventListener(event, showFailure);
  }
  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail?.target?.id === "results") clearFailure();
  });
})();
