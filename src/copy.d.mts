/** Optional browser Clipboard API enhancement. No runtime dependencies. */
export declare function copyText(
  text: string,
  clipboard?: Pick<Clipboard, 'writeText'>,
): Promise<void>;
/**
 * Enhances explicit data-syn-copy-target/status buttons. Call after DOM
 * updates (including HTMX swaps); the returned function detaches listeners.
 */
export declare function enhanceCopyButtons(
  root?: Document | Element | DocumentFragment,
  clipboard?: Pick<Clipboard, 'writeText'>,
): () => void;
