/**
 * Optional Syntyr animation companion. Native Web Animations API only.
 * No imports, DOM side effects, hidden initial states, or implicit observers.
 *
 * Import only where application-driven motion is needed. CSS-first consumers
 * can continue using syntyr.motion.css without loading any JavaScript.
 */

const PRESETS = new Set([
  'fade', 'enter', 'scale',
  'fade-in', 'fade-out', 'slide-up', 'slide-down', 'slide-left', 'slide-right',
  'zoom-in', 'zoom-out', 'pop', 'bounce', 'pulse', 'shake', 'rotate-in', 'flip-in',
]);
const ITERATION_DIRECTIONS = new Set(['normal', 'reverse', 'alternate', 'alternate-reverse']);
const DIRECTIONS = new Set(['up', 'down', 'left', 'right']);
const NOOP = () => {};
// Tracks one-shot reveals without retaining detached DOM nodes.
const revealedElements = new WeakSet();

function reducedMotion() {
  return globalThis.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches === true;
}

function styleOf(element) {
  return globalThis.getComputedStyle?.(element);
}

function token(style, name, fallback) {
  return style?.getPropertyValue(name)?.trim() || fallback;
}

function milliseconds(value, fallback) {
  if (typeof value === 'number') return Number.isFinite(value) && value >= 0 ? value : fallback;
  if (typeof value !== 'string') return fallback;
  const match = /^([0-9]*\.?[0-9]+)\s*(ms|s)$/.exec(value.trim());
  return match ? Number(match[1]) * (match[2] === 's' ? 1000 : 1) : fallback;
}

function keyframes(preset, options, style) {
  if (preset === 'fade' || preset === 'fade-in') return [{ opacity: 0 }, { opacity: 1 }];
  if (preset === 'fade-out') return [{ opacity: 1 }, { opacity: 0 }];
  if (preset === 'zoom-out') {
    const to = options.scaleFrom ?? token(style, '--syn-motion-scale-from', '0.96');
    return [{ opacity: 1, scale: '1' }, { opacity: 0, scale: String(to) }];
  }
  if (preset === 'pop') return [
    { opacity: 0, scale: '0.85' },
    { opacity: 1, scale: '1.06', offset: 0.65 },
    { opacity: 1, scale: '1' },
  ];
  if (preset === 'pulse') return [{ scale: '1' }, { scale: '1.06' }, { scale: '1' }];
  if (preset === 'bounce') {
    const distance = options.distance ?? token(style, '--syn-motion-distance', '.75rem');
    return [{ translate: '0 0' },
      { translate: '0 calc(-.3 * ' + String(distance) + ')' },
      { translate: '0 0' }];
  }
  if (preset === 'shake') return [
    { translate: '0 0' }, { translate: '-.35rem 0' },
    { translate: '.35rem 0' }, { translate: '-.35rem 0' },
    { translate: '.35rem 0' }, { translate: '0 0' },
  ];
  if (preset === 'rotate-in') return [
    { opacity: 0, rotate: '-12deg' }, { opacity: 1, rotate: '0deg' },
  ];
  if (preset === 'flip-in') return [
    { opacity: 0, rotate: 'y -80deg' }, { opacity: 1, rotate: 'y 0deg' },
  ];
  if (preset === 'scale' || preset === 'zoom-in') {
    const from = options.scaleFrom ?? token(style, '--syn-motion-scale-from', '0.96');
    return [{ opacity: 0, scale: String(from) }, { opacity: 1, scale: '1' }];
  }

  if (preset.startsWith('slide-')) {
    const distance = options.distance ?? token(style, '--syn-motion-distance', '.75rem');
    const offset = String(distance);
    const origins = {
      'slide-up': '0 ' + offset,
      'slide-down': '0 calc(-1 * ' + offset + ')',
      'slide-left': offset + ' 0',
      'slide-right': 'calc(-1 * ' + offset + ') 0',
    };
    return [{ opacity: 0, translate: origins[preset] },
      { opacity: 1, translate: '0 0' }];
  }

  const direction = options.direction ?? 'up';
  if (!DIRECTIONS.has(direction)) throw new TypeError('Invalid direction: ' + direction);
  const distance = options.distance ?? token(style, '--syn-motion-distance', '.75rem');
  const offset = String(distance);
  // CSS math works with both functional lengths (calc/var) and signed values.
  // Prefixing '-' to 'calc(...)' produces invalid keyframes.
  const negative = 'calc(-1 * ' + offset + ')';
  const origin = {
    up: '0 ' + offset,
    down: '0 ' + negative,
    left: negative + ' 0',
    right: offset + ' 0',
  }[direction];
  return [{ opacity: 0, translate: origin }, { opacity: 1, translate: '0 0' }];
}

function repeatCount(options, style) {
  if (options.loop !== undefined && typeof options.loop !== 'boolean') {
    throw new TypeError('loop must be a boolean');
  }
  if (options.loop === true && options.iterations !== undefined) {
    throw new TypeError('Use either loop: true or iterations, not both');
  }
  if (options.iterations !== undefined) {
    const count = options.iterations;
    if (typeof count !== 'number' || !(count === Infinity || (Number.isInteger(count) && count >= 1))) {
      throw new TypeError('iterations must be a positive integer or Infinity');
    }
    return count;
  }
  if (options.loop === true) return Infinity;
  if (options.loop === false) return 1;
  const value = token(style, '--syn-animation-iterations', '1');
  if (value === 'infinite') return Infinity;
  const count = Number(value);
  return /^\d+$/.test(value) && Number.isSafeInteger(count) && count >= 1 ? count : 1;
}

/**
 * Animate a single already-rendered element. Returns an Animation (or null when
 * reduced motion / native support is unavailable). Never mutates inline styles.
 * @param {Element} element
 * @param {string} [preset='enter'] A built-in animation name.
 * @param {{duration?: number, delay?: number, easing?: string,
 *  direction?: 'up'|'down'|'left'|'right', distance?: string, scaleFrom?: string,
 *  iterations?: number, loop?: boolean,
 *  iterationDirection?: 'normal'|'reverse'|'alternate'|'alternate-reverse'}} [options]
 */
export function animate(element, preset = 'enter', options = {}) {
  if (!PRESETS.has(preset)) throw new TypeError('Unknown Syntyr animation: ' + preset);
  if (!element || typeof element.animate !== 'function' || reducedMotion()) return null;

  const style = styleOf(element);
  const duration = milliseconds(options.duration,
    milliseconds(token(style, '--syn-motion-duration', '220ms'), 220));
  const delay = milliseconds(options.delay, 0);
  const easing = options.easing ?? token(style, '--syn-ease-out', 'cubic-bezier(.22, 1, .36, 1)');
  const iterations = repeatCount(options, style);
  const iterationDirection = options.iterationDirection;
  if (iterationDirection !== undefined && !ITERATION_DIRECTIONS.has(iterationDirection)) {
    throw new TypeError('Invalid iteration direction: ' + iterationDirection);
  }

  // fill:none prevents completed animations from capturing focus, disabled,
  // transform, or opacity styles after their one-shot effect has finished.
  return element.animate(keyframes(preset, options, style), {
    duration, easing, delay, iterations, fill: 'none',
    ...(iterationDirection === undefined ? {} : { direction: iterationDirection }),
  });
}

/**
 * Coordinate independent animations through WAAPI delays, with no timers.
 * @param {Iterable<Element>} elements
 * @param {string} [preset='enter']
 * @param {object} [options] Supports animate() options plus interval (ms).
 * @returns {Array<Animation|null>}
 */
export function stagger(elements, preset = 'enter', options = {}) {
  const targets = Array.from(elements ?? []);
  const style = targets.length ? styleOf(targets[0]) : null;
  const interval = milliseconds(options.interval,
    milliseconds(token(style, '--syn-motion-stagger', '65ms'), 65));
  const initialDelay = milliseconds(options.delay, 0);
  return targets.map((element, index) =>
    animate(element, preset, { ...options, delay: initialDelay + interval * index }));
}

/**
 * Progressive one-time viewport animations. Elements remain visible until their
 * intersection actually triggers; unsupported APIs do not hide content.
 * Call explicitly after rendering an HTML fragment. No MutationObserver.
 *
 * <div class="syn-root"><p data-syn-reveal="enter">New feature</p></div>
 *
 * @param {Document|Element} [root=document] Query scope.
 * @returns {() => void} Disconnects the observer.
 */
export function observeReveals(root = globalThis.document) {
  if (!root?.querySelectorAll || !globalThis.IntersectionObserver || reducedMotion()) return NOOP;

  const targets = Array.from(root.querySelectorAll('.syn-root [data-syn-reveal]'))
    .filter(element => !revealedElements.has(element));
  if (!targets.length) return NOOP;

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      observer.unobserve(entry.target);
      // Two observers can queue callbacks for the same target. Mark before
      // animating so rescans and queued entries cannot replay a reveal.
      if (revealedElements.has(entry.target)) continue;
      revealedElements.add(entry.target);
      const preset = entry.target.dataset?.synReveal || 'enter';
      animate(entry.target, PRESETS.has(preset) ? preset : 'enter', { iterations: 1 });
    }
  }, { threshold: 0.1 });

  for (const element of targets) observer.observe(element);
  return () => observer.disconnect();
}
