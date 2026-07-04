// Theme toggle (light/dark) with persistence + global helpers.
(function () {
  const root = document.documentElement;
  const btn = document.getElementById('theme-toggle');

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
  }

  if (btn) {
    apply(root.getAttribute('data-theme') || 'light');
    btn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(next);
      // Re-render any charts so colors follow the theme.
      if (window.__renderCharts) window.__renderCharts();
    });
  }

  // Auto-dismiss flash messages.
  document.querySelectorAll('.flash').forEach((el) => {
    setTimeout(() => el.remove(), 5000);
  });

  // Copy-to-clipboard buttons ([data-copy="#selector"]).
  document.querySelectorAll('[data-copy]').forEach((b) => {
    b.addEventListener('click', () => {
      const target = document.querySelector(b.getAttribute('data-copy'));
      if (!target) return;
      const text = target.innerText || target.textContent;
      navigator.clipboard.writeText(text).then(() => {
        const old = b.textContent;
        b.textContent = '✓ Copied';
        setTimeout(() => (b.textContent = old), 1500);
      });
    });
  });
})();
