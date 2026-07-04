// Lightweight vanilla-canvas charts: circular gauges and a bar chart.
// No external libraries.
(function () {
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function scoreColor(v) {
    if (v >= 75) return '#16a34a';
    if (v >= 50) return '#d97706';
    return '#dc2626';
  }

  // Animated circular gauge.
  window.drawGauge = function (canvas, value) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    const cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 16;
    const track = cssVar('--surface-2') || '#eee';
    const text = cssVar('--text') || '#111';
    const color = scoreColor(value);
    const target = Math.max(0, Math.min(100, value));
    let cur = 0;

    function frame() {
      cur += Math.max(1, (target - cur) * 0.12);
      if (cur > target) cur = target;
      ctx.clearRect(0, 0, w, h);
      // Track
      ctx.beginPath();
      ctx.lineWidth = 14;
      ctx.strokeStyle = track;
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
      // Progress
      ctx.beginPath();
      ctx.lineCap = 'round';
      ctx.strokeStyle = color;
      const start = -Math.PI / 2;
      ctx.arc(cx, cy, r, start, start + (Math.PI * 2 * cur) / 100);
      ctx.stroke();
      // Label
      ctx.fillStyle = text;
      ctx.font = '700 34px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(Math.round(cur), cx, cy - 4);
      ctx.font = '600 12px Inter, sans-serif';
      ctx.fillStyle = cssVar('--muted') || '#888';
      ctx.fillText('/ 100', cx, cy + 20);
      if (cur < target) requestAnimationFrame(frame);
    }
    frame();
  };

  // Horizontal-ish vertical bar chart for category scores.
  window.drawBarChart = function (canvas, labels, values) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    // Handle device pixel ratio for crisp text.
    const cssW = canvas.clientWidth || 800;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = cssW * dpr;
    canvas.height = (canvas.getAttribute('height') || 260) * dpr;
    ctx.scale(dpr, dpr);
    const W = cssW, H = canvas.height / dpr;

    const text = cssVar('--text') || '#111';
    const muted = cssVar('--muted') || '#888';
    const grid = cssVar('--border') || '#eee';
    const pad = { l: 34, r: 12, t: 12, b: 46 };
    const chartW = W - pad.l - pad.r;
    const chartH = H - pad.t - pad.b;
    const n = labels.length;
    const gap = 14;
    const barW = (chartW - gap * (n - 1)) / n;

    ctx.clearRect(0, 0, W, H);
    // Grid lines + y labels.
    ctx.strokeStyle = grid; ctx.fillStyle = muted;
    ctx.font = '11px Inter, sans-serif'; ctx.textAlign = 'right';
    for (let g = 0; g <= 100; g += 25) {
      const y = pad.t + chartH - (g / 100) * chartH;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
      ctx.fillText(g, pad.l - 6, y + 3);
    }

    labels.forEach((label, i) => {
      const v = Math.max(0, Math.min(100, values[i]));
      const x = pad.l + i * (barW + gap);
      const bh = (v / 100) * chartH;
      const y = pad.t + chartH - bh;
      const grad = ctx.createLinearGradient(0, y, 0, y + bh);
      grad.addColorStop(0, '#6366f1');
      grad.addColorStop(1, '#0ea5e9');
      ctx.fillStyle = grad;
      roundRect(ctx, x, y, barW, bh, 6);
      ctx.fill();
      // Value on top.
      ctx.fillStyle = text; ctx.textAlign = 'center';
      ctx.font = '700 12px Inter, sans-serif';
      ctx.fillText(v, x + barW / 2, y - 6);
      // Label below (rotated if narrow).
      ctx.fillStyle = muted; ctx.font = '11px Inter, sans-serif';
      ctx.save();
      ctx.translate(x + barW / 2, H - pad.b + 14);
      if (barW < 60) { ctx.rotate(-Math.PI / 5); ctx.textAlign = 'right'; }
      ctx.fillText(label, 0, 0);
      ctx.restore();
    });
  };

  function roundRect(ctx, x, y, w, h, r) {
    if (h < 1) h = 1;
    r = Math.min(r, w / 2, h);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
})();
