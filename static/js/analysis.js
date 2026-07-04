// Reads the embedded analysis JSON and renders all charts.
(function () {
  const dataEl = document.getElementById('analysis-data');
  if (!dataEl) return;
  let data = {};
  try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }

  function render() {
    window.drawGauge(document.getElementById('gauge-overall'), data.overall_score || 0);
    window.drawGauge(document.getElementById('gauge-ats'), data.ats_score || 0);
    window.drawGauge(document.getElementById('gauge-keyword'), data.keyword_match || 0);

    const cats = data.category_scores || {};
    const labels = Object.keys(cats);
    const values = labels.map((k) => cats[k]);
    window.drawBarChart(document.getElementById('bar-categories'), labels, values);
  }

  // Expose for theme re-render + handle resize.
  window.__renderCharts = render;
  window.addEventListener('resize', () => {
    clearTimeout(window.__rz);
    window.__rz = setTimeout(render, 150);
  });
  render();
})();
