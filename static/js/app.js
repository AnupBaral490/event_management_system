/* ── EventSphere App JS ───────────────────────────── */

// === Page progress bar ===
(function () {
  const bar = document.createElement('div');
  bar.id = 'page-progress';
  document.body.prepend(bar);
  let w = 0;
  const iv = setInterval(() => {
    w += Math.random() * 18;
    if (w >= 90) { clearInterval(iv); w = 90; }
    bar.style.width = w + '%';
  }, 120);
  window.addEventListener('load', () => {
    clearInterval(iv);
    bar.style.width = '100%';
    setTimeout(() => { bar.style.opacity = '0'; }, 350);
  });
})();

// === Navbar scroll effect ===
(function () {
  const nav = document.querySelector('.nav-shell');
  if (!nav) return;
  const onScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
})();

// === Intersection Observer — staggered entrance ===
document.addEventListener('DOMContentLoaded', () => {
  const targets = document.querySelectorAll(
    '.feature-card, .event-card, .kpi-card, .glass-card, .chart-card, .quick-action, .auth-card, .ticket-card'
  );

  if (!targets.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const idx = Number(el.dataset.revealIdx || 0);
        el.style.animationDelay = `${idx * 0.07}s`;
        el.classList.add('reveal');
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.08 });

  targets.forEach((el, i) => {
    el.style.opacity = '0';
    el.dataset.revealIdx = i;
    observer.observe(el);
  });
});

// === Animated counter for KPI numbers ===
function animateCounter(el) {
  const target = parseFloat(el.dataset.target || el.textContent.replace(/[^0-9.]/g, ''));
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const isDecimal = String(target).includes('.');
  const duration = 900;
  const start = performance.now();

  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = target * eased;
    el.textContent = prefix + (isDecimal ? current.toFixed(2) : Math.round(current).toLocaleString()) + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
  const kpiValues = document.querySelectorAll('.kpi-value[data-target]');
  if (!kpiValues.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  kpiValues.forEach((el) => observer.observe(el));
});

// === Toast notification helper ===
window.showToast = function (message, type = 'info') {
  const colors = {
    info:    { bg: '#eff6ff', border: '#bfdbfe', text: '#1e40af', icon: 'ℹ️' },
    success: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534', icon: '✅' },
    error:   { bg: '#fef2f2', border: '#fecaca', text: '#991b1b', icon: '❌' },
    warning: { bg: '#fffbeb', border: '#fde68a', text: '#92400e', icon: '⚠️' },
  };
  const c = colors[type] || colors.info;

  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:.6rem;max-width:340px;';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.style.cssText = `
    background:${c.bg};border:1px solid ${c.border};color:${c.text};
    border-radius:0.875rem;padding:.85rem 1.1rem;font-size:.875rem;font-weight:500;
    display:flex;align-items:flex-start;gap:.6rem;
    box-shadow:0 10px 40px rgba(15,23,42,.12);
    animation:toastIn .35s cubic-bezier(.16,1,.3,1) forwards;
    font-family:'Sora',sans-serif;
  `;
  toast.innerHTML = `<span style="flex-shrink:0;font-size:1rem">${c.icon}</span><span>${message}</span><button onclick="this.parentNode.remove()" style="margin-left:auto;background:none;border:none;cursor:pointer;color:inherit;font-size:1rem;padding:0;opacity:.6">×</button>`;

  if (!document.getElementById('toast-style')) {
    const s = document.createElement('style');
    s.id = 'toast-style';
    s.textContent = '@keyframes toastIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}';
    document.head.appendChild(s);
  }

  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
};

// === Active nav link highlight ===
document.addEventListener('DOMContentLoaded', () => {
  const links = document.querySelectorAll('.navbar .nav-link');
  const path = window.location.pathname;
  links.forEach((link) => {
    if (link.getAttribute('href') === path || (link.getAttribute('href') !== '/' && path.startsWith(link.getAttribute('href')))) {
      link.classList.add('active');
    }
  });
});
