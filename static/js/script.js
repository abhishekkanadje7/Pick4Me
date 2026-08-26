/**
 * Pick4Me — Interactive Scripts & Micro-Animations
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const navToggle = document.getElementById('navToggle');
  const navMenu = document.getElementById('navMenu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      navMenu.classList.toggle('show');
    });
  }

  // 2. Auto-Dismiss Alert Messages with Smooth Slide-Up
  const alertCloseBtns = document.querySelectorAll('.alert-close');
  alertCloseBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 3. Smooth Scroll Reveal on Cards and Sections
  const revealElements = document.querySelectorAll('.card, .stat-card, .hero-section, .section');
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('reveal-item', 'is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: '0px 0px -40px 0px',
      threshold: 0.1
    });

    revealElements.forEach((el) => {
      el.classList.add('reveal-item');
      revealObserver.observe(el);
    });
  } else {
    revealElements.forEach((el) => el.classList.add('reveal-item', 'is-visible'));
  }

  // 4. Animated Number Counters for Stats
  const counterElements = document.querySelectorAll('.count-up');
  if (counterElements.length > 0 && 'IntersectionObserver' in window) {
    const countObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.getAttribute('data-target'), 10) || 0;
          const duration = 1200;
          const start = 0;
          const startTime = performance.now();

          function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (target - start) * easeProgress);
            el.innerText = current + '+';

            if (progress < 1) {
              requestAnimationFrame(updateCounter);
            } else {
              el.innerText = target + '+';
            }
          }

          requestAnimationFrame(updateCounter);
          observer.unobserve(el);
        }
      });
    }, { threshold: 0.5 });

    counterElements.forEach((el) => countObserver.observe(el));
  }

  // 5. Button Click Ripple Effect
  const rippleButtons = document.querySelectorAll('.btn-primary, .btn-accent');
  rippleButtons.forEach((button) => {
    button.addEventListener('click', function (e) {
      const circle = document.createElement('span');
      const diameter = Math.max(button.clientWidth, button.clientHeight);
      const radius = diameter / 2;

      const rect = button.getBoundingClientRect();
      circle.style.width = circle.style.height = `${diameter}px`;
      circle.style.left = `${e.clientX - rect.left - radius}px`;
      circle.style.top = `${e.clientY - rect.top - radius}px`;
      circle.style.position = 'absolute';
      circle.style.borderRadius = '50%';
      circle.style.background = 'rgba(255, 255, 255, 0.4)';
      circle.style.pointerEvents = 'none';
      circle.style.animation = 'rippleEffect 0.6s linear';

      const existingRipple = button.querySelector('.ripple');
      if (existingRipple) {
        existingRipple.remove();
      }

      circle.classList.add('ripple');
      button.appendChild(circle);

      setTimeout(() => {
        circle.remove();
      }, 600);
    });
  });

  // 6. Copy to Clipboard Utility
  window.copyToClipboard = function (text, btnElement) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      const originalText = btnElement.innerHTML;
      btnElement.innerHTML = '✓ Copied!';
      btnElement.classList.add('btn-primary');
      setTimeout(() => {
        btnElement.innerHTML = originalText;
        btnElement.classList.remove('btn-primary');
      }, 2000);
    }).catch((err) => {
      console.error('Failed to copy: ', err);
    });
  };

  // 7. Table Search and Live Filter
  const tableSearchInput = document.getElementById('tableSearchInput');
  if (tableSearchInput) {
    tableSearchInput.addEventListener('input', (e) => {
      const filter = e.target.value.toLowerCase();
      const rows = document.querySelectorAll('.searchable-table tbody tr');
      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
      });
    });
  }

  // 8. QR Code File Preview
  const qrFileInput = document.getElementById('qr_code_file');
  const qrPreview = document.getElementById('qr_preview');
  if (qrFileInput && qrPreview) {
    qrFileInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          qrPreview.src = e.target.result;
          qrPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  }
});
