/**
 * Smart Queue Manager - Interactive Client-Side Features
 */

// Web Audio API chime for queue calling
function playQueueChime() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    
    // First tone (E5)
    const osc1 = audioCtx.createOscillator();
    const gain1 = audioCtx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(659.25, audioCtx.currentTime);
    gain1.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain1.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
    osc1.connect(gain1);
    gain1.connect(audioCtx.destination);
    osc1.start();
    osc1.stop(audioCtx.currentTime + 0.5);

    // Second tone (G#5)
    setTimeout(() => {
      const osc2 = audioCtx.createOscillator();
      const gain2 = audioCtx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(830.61, audioCtx.currentTime);
      gain2.gain.setValueAtTime(0.35, audioCtx.currentTime);
      gain2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.6);
      osc2.connect(gain2);
      gain2.connect(audioCtx.destination);
      osc2.start();
      osc2.stop(audioCtx.currentTime + 0.6);
    }, 180);
  } catch (e) {
    console.log('Audio chime not supported or allowed', e);
  }
}

// Business filtering on home page
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('businessSearch');
  const categoryPills = document.querySelectorAll('.category-pill');
  const cards = document.querySelectorAll('.business-card');

  if (searchInput && cards.length) {
    function filterBusinesses() {
      const query = searchInput.value.toLowerCase().trim();
      const activePill = document.querySelector('.category-pill.active');
      const activeCat = activePill ? activePill.getAttribute('data-category') : 'all';

      cards.forEach(card => {
        const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
        const desc = card.querySelector('.card-description')?.textContent.toLowerCase() || '';
        const location = card.querySelector('.card-location')?.textContent.toLowerCase() || '';
        const category = card.getAttribute('data-category') || '';

        const matchesQuery = !query || title.includes(query) || desc.includes(query) || location.includes(query);
        const matchesCategory = activeCat === 'all' || category.toLowerCase() === activeCat.toLowerCase();

        if (matchesQuery && matchesCategory) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    }

    searchInput.addEventListener('input', filterBusinesses);

    categoryPills.forEach(pill => {
      pill.addEventListener('click', () => {
        categoryPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        filterBusinesses();
      });
    });
  }

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // Mobile navigation drawer toggle
  const navToggle = document.getElementById('navToggle');
  const navDrawer = document.getElementById('mobileNavDrawer');
  const navBackdrop = document.getElementById('mobileNavBackdrop');
  const navClose = document.getElementById('mobileNavClose');

  function openMobileNav() {
    if (navDrawer && navBackdrop) {
      navDrawer.classList.add('active');
      navBackdrop.classList.add('active');
      navDrawer.setAttribute('aria-hidden', 'false');
      if (navToggle) navToggle.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeMobileNav() {
    if (navDrawer && navBackdrop) {
      navDrawer.classList.remove('active');
      navBackdrop.classList.remove('active');
      navDrawer.setAttribute('aria-hidden', 'true');
      if (navToggle) navToggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  }

  if (navToggle) navToggle.addEventListener('click', openMobileNav);
  if (navClose) navClose.addEventListener('click', closeMobileNav);
  if (navBackdrop) navBackdrop.addEventListener('click', closeMobileNav);

  // Close mobile nav on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileNav();
      closeAuthModal();
      document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
    }
  });

  // Close mobile nav when clicking any link inside it
  if (navDrawer) {
    navDrawer.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        closeMobileNav();
      });
    });
  }

  // Backdrop click to close Auth Modal
  const authModal = document.getElementById('authModal');
  if (authModal) {
    authModal.addEventListener('click', (e) => {
      if (e.target === authModal) {
        closeAuthModal();
      }
    });

    // Handle AJAX submission for Login in Modal
    const loginForm = document.getElementById('modalLoginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('modalLoginSubmitBtn');
        const alertEl = document.getElementById('authModalAlert');
        const alertText = document.getElementById('authModalAlertText');

        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
        if (alertEl) alertEl.style.display = 'none';

        try {
          const formData = new FormData(loginForm);
          const res = await fetch(loginForm.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
          });

          const data = await res.json();
          if (res.ok && data.success) {
            window.location.href = data.redirect || '/';
          } else {
            if (alertEl && alertText) {
              alertText.textContent = data.error || 'Invalid username or password.';
              alertEl.style.display = 'flex';
            }
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
          }
        } catch (err) {
          console.warn('AJAX login failed, submitting standard form', err);
          loginForm.submit();
        }
      });
    }

    // Handle AJAX submission for Register in Modal
    const regForm = document.getElementById('modalRegisterForm');
    if (regForm) {
      regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('modalRegisterSubmitBtn');
        const alertEl = document.getElementById('authModalAlert');
        const alertText = document.getElementById('authModalAlertText');

        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
        if (alertEl) alertEl.style.display = 'none';

        try {
          const formData = new FormData(regForm);
          const res = await fetch(regForm.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
          });

          const data = await res.json();
          if (res.ok && data.success) {
            window.location.href = data.redirect || '/';
          } else {
            if (alertEl && alertText) {
              alertText.textContent = data.error || 'Could not create account. Please check your information.';
              alertEl.style.display = 'flex';
            }
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
          }
        } catch (err) {
          console.warn('AJAX register failed, submitting standard form', err);
          regForm.submit();
        }
      });
    }
  }
});

// ==========================================
// Global Auth Modal Functions
// ==========================================

function openAuthModal(event, businessId, businessName, initialTab = 'login') {
  if (event && event.preventDefault) {
    event.preventDefault();
  }

  const modal = document.getElementById('authModal');
  if (!modal) {
    // Fallback if modal not in DOM: navigate to login page
    const nextUrl = businessId ? `/queue/${encodeURIComponent(businessId)}` : '';
    window.location.href = `/login${nextUrl ? '?next=' + encodeURIComponent(nextUrl) : ''}`;
    return;
  }

  // Update business context in modal
  const subtitleEl = document.getElementById('authModalSubtitle');
  if (subtitleEl) {
    if (businessName) {
      subtitleEl.innerHTML = `Sign in or create an account to join the line at <strong style="color: #fff;">${businessName}</strong> and take your digital ticket.`;
    } else {
      subtitleEl.textContent = 'Sign in or create an account to take your ticket and track your turn in line.';
    }
  }

  // Update redirect target
  const nextTarget = businessId ? `/queue/${businessId}` : '/my-queues';
  const loginNext = document.getElementById('modalLoginNext');
  const regNext = document.getElementById('modalRegisterNext');
  if (loginNext) loginNext.value = nextTarget;
  if (regNext) regNext.value = nextTarget;

  // Clear any previous error
  const alertEl = document.getElementById('authModalAlert');
  if (alertEl) alertEl.style.display = 'none';

  // Set active tab
  switchAuthTab(initialTab);

  // Show modal
  modal.classList.add('active');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';

  // Autofocus appropriate field
  setTimeout(() => {
    if (initialTab === 'register') {
      const regInput = document.getElementById('modalRegFullName');
      if (regInput) regInput.focus();
    } else {
      const loginInput = document.getElementById('modalLoginId');
      if (loginInput) loginInput.focus();
    }
  }, 100);
}

function closeAuthModal() {
  const modal = document.getElementById('authModal');
  if (modal) {
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }
}

function switchAuthTab(tab) {
  const btnLogin = document.getElementById('tabBtnLogin');
  const btnRegister = document.getElementById('tabBtnRegister');
  const panelLogin = document.getElementById('authPanelLogin');
  const panelRegister = document.getElementById('authPanelRegister');
  const alertEl = document.getElementById('authModalAlert');

  if (alertEl) alertEl.style.display = 'none';

  if (tab === 'register') {
    if (btnLogin) {
      btnLogin.classList.remove('active');
      btnLogin.setAttribute('aria-selected', 'false');
    }
    if (btnRegister) {
      btnRegister.classList.add('active');
      btnRegister.setAttribute('aria-selected', 'true');
    }
    if (panelLogin) panelLogin.classList.remove('active');
    if (panelRegister) panelRegister.classList.add('active');
  } else {
    if (btnRegister) {
      btnRegister.classList.remove('active');
      btnRegister.setAttribute('aria-selected', 'false');
    }
    if (btnLogin) {
      btnLogin.classList.add('active');
      btnLogin.setAttribute('aria-selected', 'true');
    }
    if (panelRegister) panelRegister.classList.remove('active');
    if (panelLogin) panelLogin.classList.add('active');
  }
}

function toggleModalPwd(inputId, iconId) {
  const pwd = document.getElementById(inputId);
  const icon = document.getElementById(iconId);
  if (!pwd || !icon) return;
  if (pwd.type === 'password') {
    pwd.type = 'text';
    icon.classList.remove('fa-eye');
    icon.classList.add('fa-eye-slash');
  } else {
    pwd.type = 'password';
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }
}

// Modal helpers
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Copy to clipboard helper
function copyToClipboard(text, btnElement) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      if (btnElement) {
        const originalText = btnElement.innerHTML;
        btnElement.innerHTML = '<i class="fas fa-check"></i> Copied!';
        setTimeout(() => {
          btnElement.innerHTML = originalText;
        }, 2000);
      }
    });
  }
}

// Admin API operations
async function completeQueueItem(itemId, businessId) {
  try {
    playQueueChime();
    const res = await fetch(`/api/queue/${itemId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    if (data.success) {
      window.location.reload();
    } else {
      alert(data.error || 'Failed to complete item');
    }
  } catch (err) {
    console.error(err);
    alert('Error completing queue item');
  }
}

async function removeQueueItem(itemId) {
  if (!confirm('Are you sure you want to remove this customer from the queue?')) return;
  try {
    const res = await fetch(`/api/queue/${itemId}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (data.success) {
      window.location.reload();
    } else {
      alert(data.error || 'Failed to remove item');
    }
  } catch (err) {
    console.error(err);
    alert('Error removing item');
  }
}

async function resetBusinessQueue(businessId) {
  if (!confirm('Warning: This will clear all waiting customers in this queue! Proceed?')) return;
  try {
    const res = await fetch('/api/queue/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ business_id: businessId })
    });
    const data = await res.json();
    if (data.success) {
      window.location.reload();
    } else {
      alert(data.error || 'Failed to reset queue');
    }
  } catch (err) {
    console.error(err);
    alert('Error resetting queue');
  }
}

