/** Optional, dependency-free animation primitives for browser DOM elements. */
export type SyntyrAnimationPreset =
  | 'fade' | 'enter' | 'scale'
  | 'fade-in' | 'fade-out'
  | 'slide-up' | 'slide-down' | 'slide-left' | 'slide-right'
  | 'zoom-in' | 'zoom-out' | 'pop' | 'bounce' | 'pulse'
  | 'shake' | 'rotate-in' | 'flip-in';
export type SyntyrAnimationDirection = 'up' | 'down' | 'left' | 'right';

export interface SyntyrAnimationOptions {
  /** Milliseconds. Falls back to --syn-motion-duration or 220ms. */
  duration?: number;
  /** Milliseconds before playback. */
  delay?: number;
  easing?: string;
  direction?: SyntyrAnimationDirection;
  /** CSS length, e.g. '1rem'. */
  distance?: string;
  scaleFrom?: string | number;
  /** Number of cycles, at least 1, or Infinity. Defaults to --syn-animation-iterations / 1. */
  iterations?: number;
  /** Shorthand for infinite repetition; cannot combine true with iterations. */
  loop?: boolean;
  /** Native WAAPI iteration direction; separate from entrance direction. */
  iterationDirection?: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
}

export interface SyntyrStaggerOptions extends SyntyrAnimationOptions {
  /** Milliseconds between elements; fallback --syn-motion-stagger / 65ms. */
  interval?: number;
}

export declare function animate(
  element: Element | null | undefined,
  preset?: SyntyrAnimationPreset,
  options?: SyntyrAnimationOptions,
): Animation | null;

export declare function stagger(
  elements: Iterable<Element> | null | undefined,
  preset?: SyntyrAnimationPreset,
  options?: SyntyrStaggerOptions,
): Array<Animation | null>;

export declare function observeReveals(root?: Document | Element | null): () => void;
