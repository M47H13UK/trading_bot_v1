// Step-through state machine: play/pause, step forward/back
import { WARMUP } from './constants.js';

const LS_SPEED_KEY = 'peakshaver_speed';

export class StepController {
  constructor(onStep) {
    this.onStep = onStep;  // callback(currentIndex)
    this.currentIndex = WARMUP;
    this.maxIndex = WARMUP;
    this.playing = false;
    this.timer = null;

    this.els = {
      stepBack: document.getElementById('btn-step-back'),
      play: document.getElementById('btn-play'),
      stepFwd: document.getElementById('btn-step-fwd'),
      stepSize: document.getElementById('step-size'),
      speed: document.getElementById('speed-slider'),
      counter: document.getElementById('step-counter'),
      total: document.getElementById('step-total'),
    };

    // Restore speed from localStorage
    const saved = localStorage.getItem(LS_SPEED_KEY);
    if (saved != null) {
      this.els.speed.value = saved;
    }
    this.speed = 201 - parseInt(this.els.speed.value);

    this.bind();
  }

  bind() {
    this.els.stepBack.addEventListener('click', () => this.step(-this.getStepSize()));
    this.els.stepFwd.addEventListener('click', () => this.step(this.getStepSize()));
    this.els.play.addEventListener('click', () => this.togglePlay());
    this.els.speed.addEventListener('input', () => {
      const val = parseInt(this.els.speed.value);
      this.speed = 201 - val;
      localStorage.setItem(LS_SPEED_KEY, val);
      if (this.playing) { this.stopTimer(); this.startTimer(); }
    });
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
      if (e.key === 'ArrowRight') this.step(this.getStepSize());
      else if (e.key === 'ArrowLeft') this.step(-this.getStepSize());
      else if (e.key === ' ') { e.preventDefault(); this.togglePlay(); }
    });
  }

  getStepSize() {
    return Math.max(1, parseInt(this.els.stepSize.value) || 1);
  }

  reset(totalBars) {
    this.stop();
    this.maxIndex = totalBars - 1;
    this.currentIndex = WARMUP;
    this.els.total.textContent = this.maxIndex;
    this.update();
  }

  step(delta) {
    this.currentIndex = Math.max(WARMUP, Math.min(this.maxIndex, this.currentIndex + delta));
    this.update();
  }

  jumpTo(idx) {
    this.currentIndex = Math.max(WARMUP, Math.min(this.maxIndex, idx));
    this.update();
  }

  update() {
    this.els.counter.textContent = this.currentIndex;
    this.onStep(this.currentIndex);
  }

  togglePlay() {
    this.playing ? this.stop() : this.play();
  }

  play() {
    if (this.currentIndex >= this.maxIndex) this.currentIndex = WARMUP;
    this.playing = true;
    this.els.play.textContent = '⏸';
    this.startTimer();
  }

  stop() {
    this.playing = false;
    this.els.play.textContent = '▶';
    this.stopTimer();
  }

  startTimer() {
    this.timer = setInterval(() => {
      if (this.currentIndex >= this.maxIndex) { this.stop(); return; }
      this.currentIndex++;
      this.update();
    }, this.speed);
  }

  stopTimer() {
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
  }
}
