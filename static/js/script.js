/**
 * Pick4Me - Client-Side Interactive Scripts
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

  // 2. Auto-Dismiss Alert Messages
  const alertCloseBtns = document.querySelectorAll('.alert-close');
  alertCloseBtns.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 200);
      }
    });
  });

  // 3. Request Creation - Live Total Price Calculation
  const estimatedPriceInput = document.getElementById('estimated_price');
  const rewardInput = document.getElementById('reward');
  const totalDisplay = document.getElementById('live_total_amount');

  function calculateTotal() {
    if (estimatedPriceInput && rewardInput && totalDisplay) {
      const price = parseFloat(estimatedPriceInput.value) || 0;
      const reward = parseFloat(rewardInput.value) || 0;
      const total = price + reward;
      totalDisplay.textContent = '₹' + total.toFixed(2);
    }
  }

  if (estimatedPriceInput && rewardInput) {
    estimatedPriceInput.addEventListener('input', calculateTotal);
    rewardInput.addEventListener('input', calculateTotal);
    calculateTotal();
  }

  // 4. Copy to Clipboard Utility (for UPI ID)
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

  // 5. Quick Fill Demo Accounts on Login Page
  window.quickFillLogin = function (email, password) {
    const emailField = document.getElementById('login_email');
    const passwordField = document.getElementById('login_password');
    if (emailField && passwordField) {
      emailField.value = email;
      passwordField.value = password;
      emailField.focus();
    }
  };

  // 6. Table Search and Live Filter
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

  // 7. QR Code File Preview
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
