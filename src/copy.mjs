/**
 * Optional, framework-neutral clipboard enhancement. No imports, observers,
 * initialization on import, or dependency on Syntyr's CSS bundles.
 *
 * Mark a button hidden until enhanced, then call enhanceCopyButtons(root).
 * Source and announcement IDs must resolve in the button's document.
 */
const bound = new WeakMap();
const NOOP = () => {};

/** Copy exact text using the browser's secure-context Clipboard API. */
export async function copyText(text, clipboard = globalThis.navigator?.clipboard) {
  if (typeof text !== 'string') throw new TypeError('Text to copy must be a string.');
  if (typeof clipboard?.writeText !== 'function') {
    throw new Error('Clipboard API unavailable. Select and copy the text manually.');
  }
  await clipboard.writeText(text);
}

/**
 * Enhance explicit [data-syn-copy-target] buttons in a host-owned DOM subtree.
 * Requires an associated role=status region via data-syn-copy-status.
 * No auto-discovery, event delegation, global listeners, or DOM injection.
 *
 * @param {Document|Element|DocumentFragment} [root]
 * @param {{writeText(text: string): Promise<void>}} [clipboard]
 * @returns {() => void} Remove only listeners registered by this invocation.
 */
export function enhanceCopyButtons(root = globalThis.document, clipboard = globalThis.navigator?.clipboard) {
  if (!root?.querySelectorAll || typeof clipboard?.writeText !== 'function') return NOOP;

  const added = [];
  for (const button of root.querySelectorAll('[data-syn-copy-target][data-syn-copy-status]')) {
    if (bound.has(button) || typeof button.addEventListener !== 'function') continue;
    const document = button.ownerDocument;
    const targetId = button.dataset?.synCopyTarget;
    const statusId = button.dataset?.synCopyStatus;
    if (!targetId || !statusId || targetId === statusId) continue;
    if (!document?.getElementById?.(targetId) || !document.getElementById(statusId)) continue;

    const wasHidden = button.hidden;
    const mount = { busy: false, disabledBeforeCopy: false };
    const isCurrent = () => bound.get(button) === mount;
    async function onClick(event) {
      event?.preventDefault(); // A copy action must not submit its enclosing form.
      if (button.disabled) return;
      mount.disabledBeforeCopy = button.disabled;
      mount.busy = true;
      button.disabled = true;
      const status = document.getElementById(statusId);
      try {
        const target = document.getElementById(targetId);
        if (!target) throw new Error('Copy source no longer exists.');
        const tag = target.tagName?.toUpperCase?.();
        const value = tag === 'INPUT' || tag === 'TEXTAREA' ? target.value : target.textContent;
        await copyText(value ?? '', clipboard);
        if (isCurrent() && status) status.textContent = 'Copied to clipboard.';
      } catch {
        if (isCurrent() && status) status.textContent = 'Copy failed. Select and copy the text manually.';
      } finally {
        // A previous mount must never mutate a remounted button or status.
        if (isCurrent()) {
          mount.busy = false;
          button.disabled = mount.disabledBeforeCopy;
        }
      }
    }
    button.addEventListener('click', onClick);
    button.hidden = false;
    bound.set(button, mount);
    added.push({ button, onClick, wasHidden, mount });
  }

  return () => {
    for (const { button, onClick, wasHidden, mount } of added) {
      if (bound.get(button) !== mount) continue;
      button.removeEventListener('click', onClick);
      bound.delete(button);
      // Release our in-flight disabled state before another mount attaches.
      if (mount.busy) {
        mount.busy = false;
        button.disabled = mount.disabledBeforeCopy;
      }
      button.hidden = wasHidden;
    }
  };
}
