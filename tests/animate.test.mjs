import test, { afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { animate, stagger, observeReveals } from '../src/animate.mjs';

const previous = {
  matchMedia: globalThis.matchMedia,
  getComputedStyle: globalThis.getComputedStyle,
  IntersectionObserver: globalThis.IntersectionObserver,
};
afterEach(() => {
  for (const [key, value] of Object.entries(previous)) {
    if (value === undefined) delete globalThis[key];
    else globalThis[key] = value;
  }
});

function target(tokens = {}) {
  const calls = [];
  const element = {
    animate(frames, options) {
      calls.push({ frames, options });
      return { finished: Promise.resolve(), cancel() {} };
    },
    dataset: {},
  };
  globalThis.getComputedStyle = () => ({
    getPropertyValue: (key) => tokens[key] ?? '',
  });
  globalThis.matchMedia = () => ({ matches: false });
  return { element, calls };
}

test('animation is always opt-in and safe with no DOM globals at import', () => {
  const { element, calls } = target();
  assert.equal(animate(element, 'fade').finished instanceof Promise, true);
  assert.equal(calls.length, 1);
});

test('reduced-motion and missing native animate leave content untouched', () => {
  const { element, calls } = target();
  globalThis.matchMedia = () => ({ matches: true });
  assert.equal(animate(element, 'enter'), null);
  assert.equal(calls.length, 0);
  globalThis.matchMedia = () => ({ matches: false });
  assert.equal(animate({ }, 'fade'), null);
});

test('fade is one-shot and releases its properties after completion', () => {
  const { element, calls } = target({ '--syn-motion-duration': '0.3s', '--syn-ease-out': 'ease-in-out' });
  animate(element, 'fade', { delay: 40 });
  assert.deepEqual(calls[0].frames, [{ opacity: 0 }, { opacity: 1 }]);
  assert.deepEqual(calls[0].options, {
    duration: 300, easing: 'ease-in-out', delay: 40, iterations: 1, fill: 'none',
  });
});

test('enter directions use independent translate and overrideable distance', () => {
  const { element, calls } = target({ '--syn-motion-distance': '2rem' });
  animate(element, 'enter', { direction: 'left' });
  assert.deepEqual(calls[0].frames, [
    { opacity: 0, translate: 'calc(-1 * 2rem) 0' },
    { opacity: 1, translate: '0 0' },
  ]);
  animate(element, 'enter', { direction: 'down', distance: '16px' });
  assert.equal(calls[1].frames[0].translate, '0 calc(-1 * 16px)');
});

test('scale is a finite compositor-friendly entrance', () => {
  const { element, calls } = target();
  animate(element, 'scale', { duration: 180 });
  assert.deepEqual(calls[0].frames, [
    { opacity: 0, scale: '0.96' }, { opacity: 1, scale: '1' },
  ]);
  assert.equal(calls[0].options.duration, 180);
  assert.equal(calls[0].options.iterations, 1);
});

test('unknown presets and directions fail explicitly', () => {
  const { element } = target();
  assert.throws(() => animate(element, 'wiggle'), /Unknown Syntyr animation/);
  assert.throws(() => animate(element, 'enter', { direction: 'diagonal' }), /Invalid direction/);
});

test('stagger applies a finite native delay without timers or mutation observers', () => {
  const { element: first, calls: a } = target({ '--syn-motion-stagger': '65ms' });
  const { element: second, calls: b } = target({ '--syn-motion-stagger': '65ms' });
  const result = stagger([first, second], 'fade', { delay: 20 });
  assert.equal(result.length, 2);
  assert.equal(a[0].options.delay, 20);
  assert.equal(b[0].options.delay, 85);
});

test('observeReveals observes only opted-in scoped elements once, and can disconnect', () => {
  const { element: first, calls: a } = target();
  const { element: second, calls: b } = target();
  first.dataset.synReveal = 'enter';
  second.dataset.synReveal = 'scale';
  const events = [];
  let observer;
  globalThis.IntersectionObserver = class {
    constructor(callback, options) { this.callback = callback; this.options = options; observer = this; }
    observe(e) { events.push(['observe', e]); }
    unobserve(e) { events.push(['unobserve', e]); }
    disconnect() { events.push(['disconnect']); }
  };
  const root = {
    querySelectorAll(selector) {
      assert.equal(selector, '.syn-root [data-syn-reveal]');
      return [first, second];
    },
  };
  const stop = observeReveals(root);
  assert.equal(typeof stop, 'function');
  assert.equal(observer.options.threshold, 0.1);
  observer.callback([{ target: first, isIntersecting: false }]);
  assert.equal(a.length, 0);
  observer.callback([{ target: first, isIntersecting: true }, { target: second, isIntersecting: true }]);
  assert.equal(a.length, 1);
  assert.equal(b.length, 1);
  assert.equal(events.filter(([event]) => event === 'unobserve').length, 2);
  stop();
  assert.equal(events.at(-1)[0], 'disconnect');
});

test('observer fallback avoids hiding content when JS features or motion are unavailable', () => {
  const { element, calls } = target();
  const root = { querySelectorAll: () => [element] };
  delete globalThis.IntersectionObserver;
  assert.equal(typeof observeReveals(root), 'function');
  globalThis.matchMedia = () => ({ matches: true });
  assert.equal(typeof observeReveals(root), 'function');
  assert.equal(calls.length, 0);
});

test('package subpath exposes only the optional native animation module', async () => {
  const api = await import('@syntyr/css/animate');
  assert.deepEqual(Object.keys(api).sort(), ['animate', 'observeReveals', 'stagger']);
});


test('functional and negative distances are correctly negated by CSS calc', () => {
  const { element, calls } = target({ '--syn-motion-distance': 'calc(1rem + 2px)' });
  animate(element, 'enter', { direction: 'left' });
  assert.equal(calls[0].frames[0].translate, 'calc(-1 * calc(1rem + 2px)) 0');
  animate(element, 'enter', { direction: 'down', distance: '-16px' });
  assert.equal(calls[1].frames[0].translate, '0 calc(-1 * -16px)');
  animate(element, 'enter', { direction: 'right', distance: 'calc(1rem + 2px)' });
  assert.equal(calls[2].frames[0].translate, 'calc(1rem + 2px) 0');
});

test('rescan only observes and animates new elements, even with queued duplicate entries', () => {
  const { element: first, calls: one } = target();
  const { element: second, calls: two } = target();
  first.dataset.synReveal = 'enter';
  second.dataset.synReveal = 'fade';
  let nodes = [first];
  const observers = [];
  globalThis.IntersectionObserver = class {
    constructor(callback) {
      this.callback = callback;
      this.targets = [];
      observers.push(this);
    }
    observe(element) { this.targets.push(element); }
    unobserve() {}
    disconnect() {}
  };
  const root = { querySelectorAll: () => nodes };
  const firstStop = observeReveals(root);
  observers[0].callback([{ target: first, isIntersecting: true }]);
  assert.equal(one.length, 1);
  nodes = [first, second];
  const secondStop = observeReveals(root);
  assert.deepEqual(observers[1].targets, [second]);
  observers[1].callback([
    { target: first, isIntersecting: true },
    { target: second, isIntersecting: true },
  ]);
  assert.equal(one.length, 1);
  assert.equal(two.length, 1);
  firstStop();
  secondStop();
});

test('two observers racing for the same element still animate it once', () => {
  const { element, calls } = target();
  element.dataset.synReveal = 'fade';
  const observers = [];
  globalThis.IntersectionObserver = class {
    constructor(callback) { this.callback = callback; observers.push(this); }
    observe() {}
    unobserve() {}
    disconnect() {}
  };
  const root = { querySelectorAll: () => [element] };
  const stopOne = observeReveals(root);
  const stopTwo = observeReveals(root);
  const entry = { target: element, isIntersecting: true };
  observers[0].callback([entry]);
  observers[1].callback([entry]);
  assert.equal(calls.length, 1);
  stopOne();
  stopTwo();
});

test('standard website presets generate named entrance, exit, and emphasis frames', () => {
  const { element, calls } = target({ '--syn-motion-distance': '1.5rem' });
  for (const name of ['fade-in', 'fade-out', 'slide-up', 'slide-down',
    'slide-left', 'slide-right', 'zoom-in', 'zoom-out', 'pop',
    'bounce', 'pulse', 'shake', 'rotate-in', 'flip-in']) {
    animate(element, name);
  }
  assert.equal(calls.length, 14);
  const frames = Object.fromEntries(
    ['fade-in', 'fade-out', 'slide-up', 'slide-down',
      'slide-left', 'slide-right', 'zoom-in', 'zoom-out', 'pop',
      'bounce', 'pulse', 'shake', 'rotate-in', 'flip-in']
      .map((name, index) => [name, calls[index].frames]));
  assert.deepEqual(frames['fade-in'], [{ opacity: 0 }, { opacity: 1 }]);
  assert.deepEqual(frames['fade-out'], [{ opacity: 1 }, { opacity: 0 }]);
  assert.equal(frames['slide-up'][0].translate, '0 1.5rem');
  assert.equal(frames['slide-down'][0].translate, '0 calc(-1 * 1.5rem)');
  assert.equal(frames['slide-left'][0].translate, '1.5rem 0');
  assert.equal(frames['slide-right'][0].translate, 'calc(-1 * 1.5rem) 0');
  assert.equal(frames['zoom-in'][0].scale, '0.96');
  assert.equal(frames['zoom-out'].at(-1).opacity, 0);
  assert.ok(frames['pop'].length >= 3);
  assert.ok(frames['bounce'].some(frame => frame.translate));
  assert.ok(frames['pulse'].some(frame => frame.scale));
  assert.ok(frames['shake'].some(frame => frame.translate));
  assert.equal(frames['rotate-in'][0].rotate, '-12deg');
  assert.equal(frames['flip-in'][0].rotate, 'y -80deg');
});

test('loops are opt-in, accept finite counts or infinity, and support alternating playback', () => {
  const { element, calls } = target();
  animate(element, 'pulse');
  animate(element, 'pulse', { iterations: 3, iterationDirection: 'alternate' });
  animate(element, 'bounce', { loop: true });
  animate(element, 'fade-in', { iterations: Infinity });
  assert.equal(calls[0].options.iterations, 1);
  assert.equal(calls[1].options.iterations, 3);
  assert.equal(calls[1].options.direction, 'alternate');
  assert.equal(calls[2].options.iterations, Infinity);
  assert.equal(calls[3].options.iterations, Infinity);
  assert.equal(calls[2].options.fill, 'none');
});

test('CSS iteration tokens can control JS loops without forcing mandatory runtime', () => {
  const { element, calls } = target({ '--syn-animation-iterations': '4' });
  animate(element, 'bounce');
  assert.equal(calls[0].options.iterations, 4);
  animate(element, 'bounce', { iterations: 2 });
  assert.equal(calls[1].options.iterations, 2);
  assert.equal(stagger([element], 'bounce')[0] != null, true);
  assert.equal(calls[2].options.iterations, 4);
});

test('invalid loop settings fail instead of silently hanging animations', () => {
  const { element } = target();
  for (const iterations of [0, -1, 1.5, NaN, '3', null]) {
    assert.throws(() => animate(element, 'pulse', { iterations }), /iterations/i);
  }
  assert.throws(() => animate(element, 'pulse', { loop: 'forever' }), /loop/i);
  assert.throws(() => animate(element, 'pulse', { loop: true, iterations: 2 }), /loop|iterations/i);
  assert.throws(() => animate(element, 'pulse', { iterationDirection: 'diagonal' }), /iteration direction/i);
});

test('rotate spins a full turn and supports customizable clockwise/counterclockwise angles', () => {
  const { element, calls } = target();
  animate(element, 'rotate', { loop: true });
  animate(element, 'rotate', { rotation: -180, iterations: 2 });
  assert.deepEqual(calls[0].frames, [
    { rotate: '0deg' }, { rotate: '360deg' },
  ]);
  assert.deepEqual(calls[1].frames, [
    { rotate: '0deg' }, { rotate: '-180deg' },
  ]);
  assert.equal(calls[1].options.iterations, 2);
});

test('speed multiplier changes native playback rate without changing timing options', () => {
  const { element, calls } = target({ '--syn-animation-speed': '0.5' });
  const slow = animate(element, 'rotate', { loop: true });
  assert.equal(slow.playbackRate, 0.5);
  const fast = animate(element, 'rotate', { speed: 2 });
  assert.equal(fast.playbackRate, 2);
  assert.equal(calls[1].options.duration, 220);
  assert.equal(calls[1].options.iterations, 1);
  const neutral = animate(element, 'rotate', { speed: 1 });
  assert.equal(neutral.playbackRate, 1);
});

test('invalid speed and rotation are rejected with clear type errors', () => {
  const { element } = target();
  for (const speed of [-3, 0, NaN, Infinity, '2', null]) {
    assert.throws(() => animate(element, 'rotate', { speed }), /speed/i);
  }
  for (const rotation of [NaN, Infinity, '360deg', null]) {
    assert.throws(() => animate(element, 'rotate', { rotation }), /rotation/i);
  }
});

test('invalid CSS speed tokens fall back to normal playback', () => {
  const { element } = target({ '--syn-animation-speed': 'untrusted-token' });
  assert.equal(animate(element, 'rotate').playbackRate, 1);
});
