/**
 * CivicSense - Interactive Complaint Detail Modal & Batch Resolution System
 */
let currentModalCid = null;
let currentModalData = null;

function formatDate(isoStr) {
  if (!isoStr) return '—';
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + 
           ' · ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  } catch (e) {
    return isoStr;
  }
}

function showModalToast(message) {
  const toast = document.getElementById('modal-toast');
  if (!toast) return;
  toast.innerHTML = `<span>✓ ${message}</span><button onclick="this.parentElement.style.display='none'" style="background:none;border:none;color:#fff;font-size:16px;cursor:pointer;">&times;</button>`;
  toast.style.display = 'flex';
  setTimeout(() => {
    if (toast.style.display === 'flex') toast.style.display = 'none';
  }, 4500);
}

window.openComplaintModal = function(cid) {
  currentModalCid = cid;
  const modal = document.getElementById('complaint-detail-modal');
  if (!modal) return;

  // Set loading placeholder
  document.getElementById('m-cid-badge').textContent = '#' + cid;
  document.getElementById('m-title').textContent = 'Loading Grievance #' + cid + '...';
  document.getElementById('m-description').textContent = 'Fetching multimodal grievance details and clustering similar complaints...';
  document.getElementById('m-permalink-btn').href = '/complaints/' + cid;
  document.getElementById('m-similar-list').innerHTML = '<div class="muted text-center" style="padding: 24px;">Scanning database for similar complaints...</div>';
  document.getElementById('m-photo-card').style.display = 'none';
  document.getElementById('modal-toast').style.display = 'none';

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';

  fetch('/api/complaints/' + cid + '/details')
    .then(res => {
      if (!res.ok) throw new Error('Failed to load complaint');
      return res.json();
    })
    .then(data => {
      currentModalData = data;
      renderModalContent(data);
    })
    .catch(err => {
      document.getElementById('m-title').textContent = 'Error loading complaint';
      document.getElementById('m-description').textContent = err.message || 'Unable to retrieve complaint details.';
    });
};

window.closeComplaintModal = function() {
  const modal = document.getElementById('complaint-detail-modal');
  if (modal) modal.classList.remove('active');
  document.body.style.overflow = '';
};

window.handleModalOverlayClick = function(event) {
  if (event.target && event.target.id === 'complaint-detail-modal') {
    closeComplaintModal();
  }
};

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    const lightbox = document.getElementById('lightbox-modal');
    if (lightbox && lightbox.classList.contains('active')) {
      if (typeof window.closeLightbox === 'function') {
        window.closeLightbox();
      } else {
        lightbox.classList.remove('active');
      }
      return;
    }
    closeComplaintModal();
  }
});

function renderModalContent(data) {
  const c = data.complaint;
  const similar = data.similar || [];
  const meta = data.image_metadata || {};

  // Header info
  document.getElementById('m-cid-badge').textContent = '#' + c.id;
  document.getElementById('m-title').textContent = c.title || 'Untitled Grievance';
  document.getElementById('m-description').textContent = c.description || '';
  document.getElementById('m-timestamp').textContent = 'Submitted ' + formatDate(c.created_at);
  document.getElementById('m-permalink-btn').href = '/complaints/' + c.id;

  // Status badge & select
  const statusBadge = document.getElementById('m-status-badge');
  statusBadge.className = 'badge badge-' + (c.status || 'open').toLowerCase().replace(/\s+/g, '-');
  statusBadge.textContent = c.status || 'Open';

  const statusSelect = document.getElementById('m-status-select');
  if (statusSelect) statusSelect.value = c.status || 'Open';

  const quickResolveBtn = document.getElementById('m-btn-quick-resolve');
  if (c.status === 'Resolved') {
    quickResolveBtn.textContent = '✓ Resolved';
    quickResolveBtn.disabled = true;
    quickResolveBtn.style.background = '#2b8a3e';
  } else {
    quickResolveBtn.textContent = '✓ Mark Resolved';
    quickResolveBtn.disabled = false;
    quickResolveBtn.style.background = '';
  }

  // Location tags
  document.getElementById('m-ward').textContent = c.ward || 'Campus';
  
  const floorChip = document.getElementById('m-floor-chip');
  if (c.floor) {
    document.getElementById('m-floor').textContent = c.floor;
    floorChip.style.display = 'inline-block';
  } else {
    floorChip.style.display = 'none';
  }

  const roomChip = document.getElementById('m-room-chip');
  if (c.room_number) {
    document.getElementById('m-room').textContent = c.room_number;
    roomChip.style.display = 'inline-block';
  } else {
    roomChip.style.display = 'none';
  }

  const sublocChip = document.getElementById('m-subloc-chip');
  if (c.sub_location) {
    document.getElementById('m-subloc').textContent = c.sub_location;
    sublocChip.style.display = 'inline-block';
  } else {
    sublocChip.style.display = 'none';
  }

  document.getElementById('m-source').textContent = c.source || 'Portal';

  // Photo evidence
  const photoCard = document.getElementById('m-photo-card');
  if (c.image_url) {
    photoCard.style.display = 'block';
    const imgEl = document.getElementById('m-evidence-img');
    imgEl.src = c.image_url;

    let metaHtml = '';
    if (meta.sharpness_score) {
      metaHtml += `<div class="meta-kv-item"><span class="meta-label">Sharpness:</span> <span class="meta-val">${meta.sharpness_score} (${meta.sharpness_label || 'Sharp'})</span></div>`;
    }
    if (meta.defect_tags && meta.defect_tags.length) {
      metaHtml += `<div class="meta-kv-item"><span class="meta-label">Defect Tags:</span> <span class="meta-val">${meta.defect_tags.join(', ')}</span></div>`;
    }
    if (meta.dimensions) {
      metaHtml += `<div class="meta-kv-item"><span class="meta-label">Resolution:</span> <span class="meta-val">${meta.dimensions}</span></div>`;
    }
    if (meta.perceptual_hash) {
      metaHtml += `<div class="meta-kv-item"><span class="meta-label">dHash:</span> <span class="meta-val mono" style="font-size:11px;">${meta.perceptual_hash}</span></div>`;
    }
    document.getElementById('m-evidence-meta').innerHTML = metaHtml || '<div class="muted">Verified photo evidence</div>';
  } else {
    photoCard.style.display = 'none';
  }

  // Category & Confidence
  const catBadge = document.getElementById('m-cat-badge');
  catBadge.textContent = c.category || 'General';
  const confPct = c.confidence ? (c.confidence * 100).toFixed(1) : '—';
  document.getElementById('m-conf-val').textContent = confPct !== '—' ? confPct + '%' : '—';
  document.getElementById('m-conf-fill').style.width = (c.confidence ? Math.min(100, c.confidence * 100) : 0) + '%';

  // Conformal prediction
  const confBox = document.getElementById('m-conformal-box');
  const confTags = document.getElementById('m-conformal-tags');
  if (data.conformal_prediction && data.conformal_prediction.prediction_set) {
    confBox.style.display = 'block';
    confTags.innerHTML = data.conformal_prediction.prediction_set.map(s => 
      `<span class="badge" style="background:#e8f4fd;color:#1971c2;font-size:11px;">${s}</span>`
    ).join(' ');
  } else {
    confBox.style.display = 'none';
  }

  // Priority & Neuro-symbolic safety
  const prioBadge = document.getElementById('m-prio-badge');
  prioBadge.className = 'badge badge-' + (c.priority || 'medium').toLowerCase();
  prioBadge.textContent = c.priority || 'Medium';
  document.getElementById('m-prio-score').textContent = (c.score !== undefined && c.score !== null) ? c.score : '—';
  document.getElementById('m-prio-explanation').textContent = data.explanation || 'Assigned by priority model.';

  const symRules = document.getElementById('m-symbolic-rules');
  if (data.breakdown && data.breakdown._symbolic_res && data.breakdown._symbolic_res.escalated) {
    symRules.innerHTML = `
      <div class="symbolic-axiom-alert">
        <div style="font-weight:700; font-size:12px;">⚡ Neuro-Symbolic Safety Axiom Triggered:</div>
        <div style="font-size:11.5px; margin-top:2px;">${data.breakdown._symbolic_res.explanation}</div>
      </div>
    `;
    symRules.style.display = 'block';
  } else {
    symRules.style.display = 'none';
  }

  // Spatial & Fraud
  document.getElementById('m-geo-coords').textContent = (c.lat && c.lon) ? `${c.lat}, ${c.lon}` : 'Campus Center';
  document.getElementById('m-geo-source').textContent = c.geo_source || 'Campus GIS';
  document.getElementById('m-fraud-status').textContent = c.is_suspicious ? `⚠️ Anomaly (${Math.round((c.suspicion_score||0)*100)}%)` : 'Clean / Verified';
  
  const dupInfo = document.getElementById('m-dup-info');
  if (c.is_duplicate) {
    dupInfo.style.display = 'flex';
    document.getElementById('m-dup-text').textContent = 'Duplicate of #' + c.duplicate_of;
  } else {
    dupInfo.style.display = 'none';
  }

  // Similar Complaints & Batch Resolution List
  renderSimilarList(similar);
}

function renderSimilarList(similar) {
  const listEl = document.getElementById('m-similar-list');
  const badgeEl = document.getElementById('m-similar-badge');
  badgeEl.textContent = similar.length + ' Similar Found';

  if (!similar.length) {
    listEl.innerHTML = '<div class="empty" style="padding: 24px; text-align:center;">No other similar complaints found in this campus location or category.</div>';
    document.getElementById('m-open-count').textContent = '0';
    document.getElementById('m-select-all-checkbox').checked = false;
    document.getElementById('m-select-all-checkbox').disabled = true;
    updateModalSelectedCount();
    return;
  }

  document.getElementById('m-select-all-checkbox').disabled = false;
  let openCount = 0;
  let html = '';

  similar.forEach(sim => {
    const isResolved = sim.status === 'Resolved';
    if (!isResolved) openCount++;

    const thumbHtml = sim.image_url ? `
      <div class="similar-item-thumb" onclick="openLightbox('${sim.image_url}')" title="Zoom evidence photo">
        <img src="${sim.image_url}" alt="Evidence">
      </div>
    ` : '';

    const checkHtml = isResolved 
      ? '<span class="text-success" style="font-weight:700;">✓</span>'
      : `<input type="checkbox" class="modal-sim-check" value="${sim.id}" onchange="updateModalSelectedCount()">`;

    const actionHtml = isResolved
      ? '<span class="badge badge-resolved">Resolved</span>'
      : `<button type="button" class="btn secondary small btn-resolve-single" onclick="resolveSingleSimilarComplaint(${sim.id}, this)">Resolve</button>`;

    html += `
      <div class="similar-item-card ${isResolved ? 'item-resolved' : ''}" id="m-sim-item-${sim.id}">
        <div class="similar-item-check">${checkHtml}</div>
        ${thumbHtml}
        <div class="similar-item-content">
          <div class="similar-item-header">
            <a href="javascript:void(0)" onclick="openComplaintModal(${sim.id})" class="similar-item-title">
              <b>#${sim.id}</b> · ${sim.title}
            </a>
            <span class="similar-match-pill">${sim.similarity_pct}% · ${sim.relation_type}</span>
          </div>
          <div class="similar-item-desc">${sim.description.substring(0, 95)}${sim.description.length > 95 ? '...' : ''}</div>
          <div class="similar-item-meta">
            <span>📍 ${sim.ward}${sim.floor ? ' · ' + sim.floor : ''}${sim.room_number ? ' · ' + sim.room_number : ''}</span>
            <span class="badge badge-${(sim.priority||'medium').toLowerCase()}">${sim.priority}</span>
            <span class="badge badge-${(sim.status||'open').toLowerCase().replace(/\s+/g, '-')}" id="m-sim-badge-${sim.id}">${sim.status}</span>
            <span class="muted">${formatDate(sim.created_at)}</span>
          </div>
        </div>
        <div class="similar-item-action">${actionHtml}</div>
      </div>
    `;
  });

  listEl.innerHTML = html;
  document.getElementById('m-open-count').textContent = openCount;
  updateModalSelectedCount();
}

window.toggleSelectAllSimilar = function(checked) {
  document.querySelectorAll('.modal-sim-check').forEach(cb => cb.checked = checked);
  updateModalSelectedCount();
};

window.updateModalSelectedCount = function() {
  const selected = document.querySelectorAll('.modal-sim-check:checked');
  const countSpan = document.getElementById('m-selected-count');
  const btn = document.getElementById('m-btn-batch-resolve');
  if (countSpan) countSpan.textContent = selected.length;
  if (btn) btn.disabled = (selected.length === 0);
};

window.resolveBatchSelectedSimilar = function() {
  const checks = Array.from(document.querySelectorAll('.modal-sim-check:checked'));
  const ids = checks.map(cb => parseInt(cb.value));
  if (!ids.length) return;

  const btn = document.getElementById('m-btn-batch-resolve');
  if (btn) btn.disabled = true;

  fetch('/api/complaints/batch-status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids: ids, status: 'Resolved' })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      ids.forEach(id => {
        markSimilarItemAsResolved(id);
        syncStatusBadgeOnPage(id, 'Resolved');
      });
      showModalToast(`Successfully marked ${ids.length} similar complaint(s) as Resolved!`);
      
      // Update open count
      const remainingOpen = document.querySelectorAll('.modal-sim-check').length;
      document.getElementById('m-open-count').textContent = remainingOpen;
      updateModalSelectedCount();
    }
  })
  .catch(err => {
    alert('Error resolving batch complaints: ' + err.message);
    if (btn) btn.disabled = false;
  });
};

window.resolveSingleSimilarComplaint = function(cid, btn) {
  if (btn) btn.disabled = true;

  fetch('/api/complaints/' + cid + '/status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Resolved' })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      markSimilarItemAsResolved(cid);
      syncStatusBadgeOnPage(cid, 'Resolved');
      showModalToast(`Grievance #${cid} marked as Resolved!`);
      
      const remainingOpen = document.querySelectorAll('.modal-sim-check').length;
      document.getElementById('m-open-count').textContent = remainingOpen;
      updateModalSelectedCount();
    }
  });
};

function markSimilarItemAsResolved(id) {
  const itemCard = document.getElementById('m-sim-item-' + id);
  if (itemCard) {
    itemCard.classList.add('item-resolved');
    const checkWrap = itemCard.querySelector('.similar-item-check');
    if (checkWrap) checkWrap.innerHTML = '<span class="text-success" style="font-weight:700;">✓</span>';
    const badge = document.getElementById('m-sim-badge-' + id);
    if (badge) {
      badge.className = 'badge badge-resolved';
      badge.textContent = 'Resolved';
    }
    const actionWrap = itemCard.querySelector('.similar-item-action');
    if (actionWrap) actionWrap.innerHTML = '<span class="badge badge-resolved">Resolved</span>';
  }
}

window.resolveCurrentModalComplaint = function() {
  if (!currentModalCid) return;
  const btn = document.getElementById('m-btn-quick-resolve');
  btn.disabled = true;

  fetch('/api/complaints/' + currentModalCid + '/status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Resolved' })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      const badge = document.getElementById('m-status-badge');
      badge.className = 'badge badge-resolved';
      badge.textContent = 'Resolved';

      const select = document.getElementById('m-status-select');
      if (select) select.value = 'Resolved';

      btn.textContent = '✓ Resolved';
      btn.style.background = '#2b8a3e';

      syncStatusBadgeOnPage(currentModalCid, 'Resolved');
      showModalToast(`Grievance #${currentModalCid} marked as Resolved!`);
    }
  });
};

window.updateModalComplaintStatus = function(newStatus) {
  if (!currentModalCid) return;

  fetch('/api/complaints/' + currentModalCid + '/status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: newStatus })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      const badge = document.getElementById('m-status-badge');
      badge.className = 'badge badge-' + newStatus.toLowerCase().replace(/\s+/g, '-');
      badge.textContent = newStatus;

      const quickBtn = document.getElementById('m-btn-quick-resolve');
      if (newStatus === 'Resolved') {
        quickBtn.textContent = '✓ Resolved';
        quickBtn.disabled = true;
        quickBtn.style.background = '#2b8a3e';
      } else {
        quickBtn.textContent = '✓ Mark Resolved';
        quickBtn.disabled = false;
        quickBtn.style.background = '';
      }

      syncStatusBadgeOnPage(currentModalCid, newStatus);
      showModalToast(`Status updated to '${newStatus}'!`);
    }
  });
};

function syncStatusBadgeOnPage(cid, status) {
  // Update status select if present on complaints page table
  const formSelects = document.querySelectorAll(`form[action*="/complaints/${cid}/status"] select`);
  formSelects.forEach(sel => {
    sel.value = status;
    sel.className = 'status-select badge badge-' + status.toLowerCase().replace(/\s+/g, '-');
  });

  // Update badge on standalone detail view if present
  const simBadge = document.getElementById('sim-badge-' + cid);
  if (simBadge) {
    simBadge.className = 'badge badge-' + status.toLowerCase().replace(/\s+/g, '-');
    simBadge.textContent = status;
  }
}

window.openLightboxFromModal = function() {
  const img = document.getElementById('m-evidence-img');
  if (img && img.src) {
    if (typeof window.openLightbox === 'function') {
      window.openLightbox(img.src);
    } else {
      const modal = document.getElementById('lightbox-modal');
      const lbImg = document.getElementById('lightbox-img');
      if (modal && lbImg) {
        lbImg.src = img.src;
        modal.classList.add('active');
      }
    }
  }
};
