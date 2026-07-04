// History: delete analyses with confirmation.
(function () {
  document.querySelectorAll('.delete-analysis').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.id;
      if (!confirm('Delete this analysis? This cannot be undone.')) return;
      fetch('/history/' + id, { method: 'DELETE' })
        .then((r) => r.json())
        .then((data) => {
          if (data.ok) {
            const row = document.querySelector('tr[data-id="' + id + '"]');
            if (row) row.remove();
          } else {
            alert('Could not delete the analysis.');
          }
        })
        .catch(() => alert('Network error while deleting.'));
    });
  });
})();
