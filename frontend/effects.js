/* ============================================================
   ASCII LAB — REAL-TIME INTERACTIVE EFFECTS ENGINE
   ============================================================ */

'use strict';

class ASCIIEffectEngine {
  constructor(container, width, height) {
    this.container = container;

    this.width = width;
    this.height = height;

    this.canvas = null;
    this.ctx = null;

    this.animationId = null;

    this.effect = 'none';

    this.baseFrame = [];
    this.colorData = null;

    this.time = 0;
    this.lastTimestamp = 0;

    this.particles = [];
    this.heat = [];

    this.charSize = 8;

    this.cols = 0;
    this.rows = 0;

    this.pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

    this.mouse = {
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      pressed: false,
      active: false
    };

    this.lastMouse = {
      x: 0,
      y: 0
    };

    this.resizeObserver = null;

    this.destroyed = false;

    this.bindPointer();
  }

  /* ========================================================
     INITIALIZATION
     ======================================================== */

  init(cols, rows, charSize = 8) {
    this.cols = Math.max(1, Math.floor(cols));
    this.rows = Math.max(1, Math.floor(rows));
    this.charSize = Math.max(2, Number(charSize) || 8);

    this.destroyed = false;

    /* Remove previous canvas */
    this.stop();

    if (this.canvas) {
      this.canvas.remove();
    }

    /* Create canvas */
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'effect-canvas';
    this.canvas.setAttribute('aria-hidden', 'true');

    this.ctx = this.canvas.getContext('2d', {
      alpha: false,
      desynchronized: true
    });

    this.configureCanvas();

    /*
     * Replace container content.
     */
    this.container.innerHTML = '';
    this.container.appendChild(this.canvas);

    /* Heat map */
    this.heat = this.createHeatMap();

    /* Particles */
    this.particles = [];

    /* Mouse */
    this.centerMouse();

    /*
     * Resize if container changes size.
     */
    this.observeContainer();

    this.renderStatic();
  }

  configureCanvas() {
    if (!this.canvas || !this.ctx) {
      return;
    }

    const logicalWidth = this.cols * this.charSize;
    const logicalHeight = this.rows * this.charSize;

    /*
     * CSS dimensions.
     */
    this.canvas.style.width = `${logicalWidth}px`;
    this.canvas.style.height = `${logicalHeight}px`;

    /*
     * High-DPI backing buffer.
     */
    this.canvas.width = Math.max(1, Math.floor(logicalWidth * this.pixelRatio));
    this.canvas.height = Math.max(1, Math.floor(logicalHeight * this.pixelRatio));

    /*
     * Draw using logical coordinates.
     */
    this.ctx.setTransform(this.pixelRatio, 0, 0, this.pixelRatio, 0, 0);

    this.ctx.font = `${this.charSize}px "JetBrains Mono", "SFMono-Regular", Consolas, monospace`;
    this.ctx.textBaseline = 'top';
    this.ctx.textAlign = 'left';
    this.ctx.imageSmoothingEnabled = false;
  }

  observeContainer() {
    if (typeof ResizeObserver === 'undefined') {
      return;
    }

    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }

    this.resizeObserver = new ResizeObserver(() => {
      this.configureCanvas();
    });

    this.resizeObserver.observe(this.container);
  }

  createHeatMap() {
    return Array.from({ length: this.rows }, () => new Float32Array(this.cols));
  }

  centerMouse() {
    this.mouse.x = this.cols / 2;
    this.mouse.y = this.rows / 2;

    this.lastMouse.x = this.mouse.x;
    this.lastMouse.y = this.mouse.y;
  }

  /* ========================================================
     POINTER INPUT
     ======================================================== */

  bindPointer() {
    if (!this.container) {
      return;
    }

    this.container.addEventListener('pointermove', event => {
      const rect = this.container.getBoundingClientRect();

      const width = rect.width || this.cols * this.charSize;
      const height = rect.height || this.rows * this.charSize;

      const nextX = ((event.clientX - rect.left) / Math.max(width, 1)) * this.cols;
      const nextY = ((event.clientY - rect.top) / Math.max(height, 1)) * this.rows;

      this.mouse.vx = nextX - this.mouse.x;
      this.mouse.vy = nextY - this.mouse.y;

      this.mouse.x = clamp(nextX, 0, this.cols - 1);
      this.mouse.y = clamp(nextY, 0, this.rows - 1);

      this.mouse.active = true;

      this.lastMouse.x = this.mouse.x;
      this.lastMouse.y = this.mouse.y;
    });

    this.container.addEventListener('pointerdown', event => {
      this.mouse.pressed = true;
      this.mouse.active = true;

      /*
       * Explosion should trigger
       * immediately on click.
       */
      if (this.effect === 'explosion') {
        this.createExplosion();
      }

      try {
        this.container.setPointerCapture(event.pointerId);
      } catch {
        /* Pointer capture unsupported */
      }
    });

    this.container.addEventListener('pointerup', event => {
      this.mouse.pressed = false;

      try {
        this.container.releasePointerCapture(event.pointerId);
      } catch {
        /* Ignore */
      }
    });

    this.container.addEventListener('pointercancel', () => {
      this.mouse.pressed = false;
    });

    this.container.addEventListener('pointerleave', () => {
      this.mouse.active = false;
      this.mouse.pressed = false;

      this.mouse.vx = 0;
      this.mouse.vy = 0;
    });

    /*
     * Prevent browser scrolling while
     * interacting with the effect canvas.
     */
    this.container.style.touchAction = 'none';
  }

  /* ========================================================
     FRAME MANAGEMENT
     ======================================================== */

  setFrame(asciiText, colorData = null) {
    if (typeof asciiText !== 'string') {
      return;
    }

    this.baseFrame = asciiText
      .replace(/\r/g, '')
      .split('\n')
      .map(row => row.split(''));

    this.colorData = Array.isArray(colorData) ? colorData : null;

    /*
     * Resize internal dimensions to
     * the actual ASCII frame.
     */
    this.rows = this.baseFrame.length;

    this.cols = this.baseFrame.reduce((max, row) => Math.max(max, row.length), 0);

    if (this.rows <= 0 || this.cols <= 0) {
      return;
    }

    this.configureCanvas();

    this.heat = this.createHeatMap();

    this.particles = [];

    this.centerMouse();

    if (this.effect !== 'none') {
      this.start();
    } else {
      this.renderStatic();
    }
  }

  setEffect(name) {
    const effects = ['none', 'gravity', 'vortex', 'ripple', 'explosion', 'fire'];

    if (!effects.includes(name)) {
      name = 'none';
    }

    this.effect = name;

    this.particles = [];
    this.time = 0;
    this.lastTimestamp = 0;

    if (name === 'none') {
      this.stop();
      this.renderStatic();
      return;
    }

    if (name === 'fire') {
      this.heat = this.createHeatMap();
    }

    this.start();
  }

  /* ========================================================
     ANIMATION LOOP
     ======================================================== */

  start() {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
    }

    this.lastTimestamp = performance.now();

    const loop = timestamp => {
      if (this.destroyed) {
        return;
      }

      const delta = Math.min((timestamp - this.lastTimestamp) / 1000, 0.05);

      this.lastTimestamp = timestamp;
      this.time += delta;

      this.render();

      this.animationId = requestAnimationFrame(loop);
    };

    this.animationId = requestAnimationFrame(loop);
  }

  stop() {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  /* ========================================================
     DRAWING HELPERS
     ======================================================== */

  clearCanvas() {
    if (!this.ctx) {
      return;
    }

    this.ctx.save();

    this.ctx.setTransform(this.pixelRatio, 0, 0, this.pixelRatio, 0, 0);

    this.ctx.fillStyle = '#0f1115';

    this.ctx.fillRect(0, 0, this.cols * this.charSize, this.rows * this.charSize);

    this.ctx.restore();
  }

  getChar(x, y) {
    return this.baseFrame[y]?.[x] || ' ';
  }

  getColor(x, y) {
    const color = this.colorData?.[y]?.[x];

    if (Array.isArray(color) && color.length >= 3) {
      const r = clamp(Number(color[0]) || 0, 0, 255);
      const g = clamp(Number(color[1]) || 0, 0, 255);
      const b = clamp(Number(color[2]) || 0, 0, 255);

      return `rgb(${r},${g},${b})`;
    }

    return '#e4e6eb';
  }

  drawChar(char, x, y, color = '#e4e6eb', alpha = 1) {
    if (!this.ctx || !char) {
      return;
    }

    if (char === ' ') {
      return;
    }

    this.ctx.globalAlpha = alpha;
    this.ctx.fillStyle = color;

    this.ctx.fillText(char, x * this.charSize, y * this.charSize);

    this.ctx.globalAlpha = 1;
  }

  drawSourceChar(x, y, sourceX = x, sourceY = y, alpha = 1) {
    const char = this.getChar(sourceX, sourceY);

    if (char === ' ') {
      return;
    }

    const color = this.getColor(sourceX, sourceY);

    this.drawChar(char, x, y, color, alpha);
  }

  /* ========================================================
     STATIC RENDER
     ======================================================== */

  renderStatic() {
    if (!this.ctx || !this.baseFrame.length) {
      return;
    }

    this.clearCanvas();

    for (let y = 0; y < this.rows; y++) {
      const row = this.baseFrame[y];

      for (let x = 0; x < row.length; x++) {
        this.drawSourceChar(x, y);
      }
    }
  }

  /* ========================================================
     MAIN RENDER
     ======================================================== */

  render() {
    if (!this.ctx || !this.baseFrame.length) {
      return;
    }

    this.clearCanvas();

    switch (this.effect) {
      case 'gravity':
        this.renderGravity();
        break;

      case 'vortex':
        this.renderVortex();
        break;

      case 'ripple':
        this.renderRipple();
        break;

      case 'explosion':
        this.renderExplosion();
        break;

      case 'fire':
        this.renderFire();
        break;

      default:
        this.renderStatic();
    }
  }

  /* ========================================================
     GRAVITY
     ======================================================== */

  renderGravity() {
    const strength = this.mouse.pressed ? 1.6 : 0.75;
    const radius = this.mouse.pressed ? 16 : 10;

    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        const dx = this.mouse.x - x;
        const dy = this.mouse.y - y;

        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > radius) {
          this.drawSourceChar(x, y);
          continue;
        }

        const force = (1 - dist / radius) * strength;

        const sourceX = clamp(Math.round(x + dx * force), 0, this.cols - 1);
        const sourceY = clamp(Math.round(y + dy * force), 0, this.rows - 1);

        this.drawSourceChar(x, y, sourceX, sourceY);
      }
    }
  }

  /* ========================================================
     VORTEX
     ======================================================== */

  renderVortex() {
    const radius = Math.max(8, Math.min(this.cols, this.rows) * 0.75);
    const strength = this.mouse.pressed ? 1.8 : 0.9;

    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        const dx = x - this.mouse.x;
        const dy = y - this.mouse.y;

        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > radius) {
          this.drawSourceChar(x, y);
          continue;
        }

        /*
         * Strongest rotation near
         * the cursor.
         */
        const normalized = 1 - dist / radius;
        const angle = strength * normalized * normalized;

        const cos = Math.cos(angle);
        const sin = Math.sin(angle);

        const sourceX = clamp(
          Math.round(this.mouse.x + (dx * cos - dy * sin)),
          0,
          this.cols - 1
        );

        const sourceY = clamp(
          Math.round(this.mouse.y + (dx * sin + dy * cos)),
          0,
          this.rows - 1
        );

        this.drawSourceChar(x, y, sourceX, sourceY);
      }
    }
  }

  /* ========================================================
     RIPPLE
     ======================================================== */

  renderRipple() {
    const amplitude = this.mouse.pressed ? 4.5 : 2.5;
    const frequency = 0.65;
    const speed = 4.5;

    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        const dx = x - this.mouse.x;
        const dy = y - this.mouse.y;

        const distance = Math.sqrt(dx * dx + dy * dy);

        const wave = Math.sin(distance * frequency - this.time * speed);

        const falloff = Math.max(0, 1 - distance / Math.max(this.cols, this.rows));

        const offset = wave * amplitude * falloff;

        const angle = Math.atan2(dy, dx);

        const sourceX = clamp(
          Math.round(x + Math.cos(angle) * offset),
          0,
          this.cols - 1
        );

        const sourceY = clamp(
          Math.round(y + Math.sin(angle) * offset),
          0,
          this.rows - 1
        );

        this.drawSourceChar(x, y, sourceX, sourceY);
      }
    }
  }

  /* ========================================================
     EXPLOSION
     ======================================================== */

  createExplosion() {
    if (!this.baseFrame.length) {
      return;
    }

    /*
     * Avoid creating a second explosion
     * while particles are still alive.
     */
    if (this.particles.length > 0) {
      return;
    }

    const maxParticles = 5000;

    let count = 0;

    /*
     * Convert only visible characters
     * into particles.
     */
    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        const char = this.getChar(x, y);

        if (char === ' ') {
          continue;
        }

        if (count >= maxParticles) {
          break;
        }

        const dx = x - this.mouse.x;
        const dy = y - this.mouse.y;

        const distance = Math.sqrt(dx * dx + dy * dy) || 1;

        /*
         * Add random angle so the
         * explosion feels organic.
         */
        const angle = Math.atan2(dy, dx) + (Math.random() - 0.5) * 0.65;

        const force =
          (2.5 + Math.random() * 5) * (1 + Math.min(distance / 50, 1));

        this.particles.push({
          x,
          y,

          vx: Math.cos(angle) * force,
          vy: Math.sin(angle) * force,

          char,

          color: this.getColor(x, y),

          life: 1,

          decay: 0.35 + Math.random() * 0.55,

          gravity: 0.08 + Math.random() * 0.12
        });

        count++;
      }
    }
  }

  renderExplosion() {
    /*
     * If there is no explosion yet,
     * display the source frame.
     */
    if (this.particles.length === 0) {
      this.renderStatic();
      return;
    }

    const delta = 1 / 60;

    const remaining = [];

    for (const particle of this.particles) {
      particle.x += particle.vx * delta * 60;
      particle.y += particle.vy * delta * 60;

      particle.vy += particle.gravity;

      particle.vx *= 0.985;
      particle.vy *= 0.985;

      particle.life -= particle.decay * delta;

      if (particle.life <= 0) {
        continue;
      }

      if (
        particle.x < -2 ||
        particle.x > this.cols + 2 ||
        particle.y < -2 ||
        particle.y > this.rows + 2
      ) {
        continue;
      }

      this.drawChar(particle.char, particle.x, particle.y, particle.color, particle.life);

      remaining.push(particle);
    }

    this.particles = remaining;

    /*
     * Automatically return to the
     * source image after explosion.
     */
    if (this.particles.length === 0) {
      this.renderStatic();
      this.mouse.pressed = false;
    }
  }

  /* ========================================================
     FIRE
     ======================================================== */

  renderFire() {
    /*
     * Fire uses the source ASCII as a
     * silhouette while applying heat
     * and animated character variation.
     */

    const fireChars = ' .:-=+*#%@';

    const sourceChars = this.baseFrame;

    for (let y = 0; y < this.rows; y++) {
      for (let x = 0; x < this.cols; x++) {
        const source = sourceChars[y]?.[x] || ' ';

        /*
         * Preserve empty spaces so
         * fire follows the image shape.
         */
        if (source === ' ') {
          continue;
        }

        /*
         * Base heat is stronger
         * toward the bottom.
         */
        let heat = 0.15 + ((this.rows - y) / Math.max(this.rows, 1)) * 0.45;

        /*
         * Mouse creates a heat source.
         */
        const dx = x - this.mouse.x;
        const dy = y - this.mouse.y;

        const distance = Math.sqrt(dx * dx + dy * dy);

        const mouseHeat = Math.max(0, 1 - distance / 15);

        heat += mouseHeat * (this.mouse.pressed ? 1.1 : 0.55);

        /*
         * Animated turbulence.
         */
        heat += Math.sin(x * 0.45 + this.time * 5) * 0.08;
        heat += Math.sin(y * 0.25 - this.time * 3) * 0.06;
        heat += (Math.random() - 0.5) * 0.12;

        heat = clamp(heat, 0, 1);

        /*
         * Pick a fire character.
         */
        const charIndex = Math.floor(heat * (fireChars.length - 1));

        const char = fireChars[charIndex];

        /*
         * Fire palette generated
         * mathematically.
         */
        const r = Math.round(80 + heat * 175);
        const g = Math.round(heat * heat * 210);
        const b = Math.round(heat * heat * heat * 90);

        this.drawChar(char, x, y, `rgb(${r},${g},${b})`, 0.35 + heat * 0.65);
      }
    }
  }

  /* ========================================================
     EFFECT RESET
     ======================================================== */

  reset() {
    this.particles = [];

    this.heat = this.createHeatMap();

    this.time = 0;

    this.mouse.pressed = false;

    this.setEffect('none');
  }

  /* ========================================================
     DESTROY
     ======================================================== */

  destroy() {
    this.destroyed = true;

    this.stop();

    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }

    if (this.canvas) {
      this.canvas.remove();
      this.canvas = null;
    }

    this.ctx = null;

    this.baseFrame = [];
    this.colorData = null;
    this.particles = [];
    this.heat = [];
  }
}

/* ============================================================
   GLOBAL UTILITIES
   ============================================================ */

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

/* ============================================================
   GLOBAL EXPORT
   ============================================================ */

window.ASCIIEffectEngine = ASCIIEffectEngine;