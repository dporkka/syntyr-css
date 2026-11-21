import { animate, stagger, observeReveals } from '../dist/syntyr.animate.mjs';

const cards = Array.from(document.querySelectorAll('#motion-cards .syn-panel'));
const status = document.querySelector('#animation-status');

document.querySelector('#animate-one')?.addEventListener('click', () => {
  const result = animate(cards[0], 'enter', { direction: 'up' });
  status.textContent = result ? 'Animated the first card.' : 'Animation skipped by browser preference or support.';
});

document.querySelector('#animate-all')?.addEventListener('click', () => {
  const results = stagger(cards, 'scale', { interval: 90 });
  status.textContent = results.some(Boolean) ? 'Animated all three cards.' : 'Animation skipped by browser preference or support.';
});

// The explicit call is the entire initialization contract; no hidden state,
// global listener, or observer exists for ordinary Syntyr pages.
observeReveals(document);

// This showcase is opt-in. Controls stay hidden for no-JS visitors.
const controls = document.querySelector('#website-animation-controls');
const preview = document.querySelector('#website-animation-target');
const feedback = document.querySelector('#website-animation-status');
const presetInput = document.querySelector('#website-animation-preset');
const repeatInput = document.querySelector('#website-animation-repeat');
const directionInput = document.querySelector('#website-animation-direction');
const speedInput = document.querySelector('#website-animation-speed');
const speedOutput = document.querySelector('#website-animation-speed-value');
const rotationInput = document.querySelector('#website-animation-rotation');
let activePreview = null;

if (controls && preview && feedback && presetInput && repeatInput && directionInput && speedInput && speedOutput && rotationInput) {
  controls.hidden = false;
  feedback.textContent = 'Choose an animation and press Play.';
  speedInput.addEventListener('input', () => {
    const speed = Number(speedInput.value);
    speedOutput.textContent = speed + '×';
    // Native playback rate can be adjusted while a loop is running.
    if (activePreview) activePreview.playbackRate = speed;
  });

  document.querySelector('#website-animation-play')?.addEventListener('click', () => {
    activePreview?.cancel();
    const repeat = repeatInput.value;
    activePreview = animate(preview, presetInput.value, {
      ...(repeat === 'infinite' ? { loop: true } : { iterations: Number(repeat) }),
      iterationDirection: directionInput.value,
      duration: 900,
      speed: Number(speedInput.value),
      rotation: Number(rotationInput.value),
    });
    feedback.textContent = activePreview
      ? 'Playing ' + presetInput.value + ' at ' + speedInput.value + '× (' + repeat + ' cycle setting).'
      : 'Motion skipped by browser preference or API support.';
  });
  document.querySelector('#website-animation-pause')?.addEventListener('click', () => {
    activePreview?.pause();
    feedback.textContent = activePreview ? 'Animation paused.' : 'No active animation to pause.';
  });
  document.querySelector('#website-animation-resume')?.addEventListener('click', () => {
    activePreview?.play();
    feedback.textContent = activePreview ? 'Animation resumed.' : 'No active animation to resume.';
  });
  document.querySelector('#website-animation-stop')?.addEventListener('click', () => {
    activePreview?.cancel();
    activePreview = null;
    feedback.textContent = 'Animation stopped.';
  });
}
