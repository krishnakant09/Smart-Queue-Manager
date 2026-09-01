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
});

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
