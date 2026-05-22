// ── Modal helpers ─────────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).style.display = 'none';
  document.body.style.overflow = '';
}

// Close modal on overlay click
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.style.display = 'none';
    document.body.style.overflow = '';
  }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay').forEach(m => {
      if (m.style.display !== 'none') {
        m.style.display = 'none';
        document.body.style.overflow = '';
      }
    });
  }
});

// ── Toast notifications ───────────────────────────────────────────────────────
(function() {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  document.body.appendChild(container);
})();

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// ── Auto-dismiss flash messages ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.4s';
      setTimeout(() => alert.remove(), 400);
    }, 4500);
  });
});

// ── Generic table search filter ───────────────────────────────────────────────
function filterTable(tableId, inputId) {
  const q = document.getElementById(inputId).value.toLowerCase();
  document.querySelectorAll('#' + tableId + ' tbody tr').forEach(row => {
    const text = (row.dataset.search || row.textContent).toLowerCase();
    row.style.display = !q || text.includes(q) ? '' : 'none';
  });
}

// ── Number formatting helper ──────────────────────────────────────────────────
function fmtNum(n) {
  return Number(n || 0).toLocaleString('en-NG', { minimumFractionDigits: 0 });
}

// ── Confirm delete helper ─────────────────────────────────────────────────────
document.addEventListener('submit', function(e) {
  const form = e.target;
  if (form.dataset.confirm) {
    if (!confirm(form.dataset.confirm)) e.preventDefault();
  }
});
