/* 
  PS06 Banking Transaction Risk Investigation Assistant
  Frontend Logic & API Integration (Vanilla JS)
*/

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const dropzoneBox = document.getElementById('dropzone-box');
  const csvFileInput = document.getElementById('csv-file-input');
  const fileInfoCard = document.getElementById('file-info-card');
  const selectedFileName = document.getElementById('selected-file-name');
  const selectedFileSize = document.getElementById('selected-file-size');
  const btnAnalyze = document.getElementById('btn-analyze');
  const btnReset = document.getElementById('btn-reset');
  const errorBanner = document.getElementById('error-banner');
  const errorText = document.getElementById('error-text');

  // Case Bar Elements
  const caseRefId = document.getElementById('case-ref-id');
  const caseCustomerId = document.getElementById('case-customer-id');
  const attentionBadge = document.getElementById('attention-badge');
  const engineStatus = document.getElementById('engine-status');

  // Pipeline Indicators
  const pStep1 = document.getElementById('p-step-1');
  const pStep2 = document.getElementById('p-step-2');
  const pStep3 = document.getElementById('p-step-3');
  const pStep4 = document.getElementById('p-step-4');
  const pStep5 = document.getElementById('p-step-5');
  const pStep6 = document.getElementById('p-step-6');

  // Content Sections
  const sectionBaseline = document.getElementById('section-baseline');
  const sectionRules = document.getElementById('section-rules');
  const sectionReport = document.getElementById('section-report');

  // Modal Elements
  const modalOverlay = document.getElementById('modal-overlay');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-body');

  let selectedFile = null;
  let currentTransactionsMap = {};

  // Event Listeners for File Selection
  dropzoneBox.addEventListener('click', () => csvFileInput.click());

  dropzoneBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzoneBox.classList.add('dragover');
  });

  dropzoneBox.addEventListener('dragleave', () => dropzoneBox.classList.remove('dragover'));

  dropzoneBox.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzoneBox.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  csvFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  btnAnalyze.addEventListener('click', () => {
    if (selectedFile) {
      startAnalysisPipeline();
    }
  });

  btnReset.addEventListener('click', resetWorkflow);
  modalCloseBtn.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
  });

  function handleFileSelected(file) {
    if (!file.name.endsWith('.csv')) {
      showError('Please select a valid CSV file.');
      return;
    }
    selectedFile = file;
    selectedFileName.textContent = file.name;
    selectedFileSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;
    fileInfoCard.classList.remove('hidden');
    btnAnalyze.classList.remove('hidden');
    hideError();

    // Automatic execution upon file selection (Milestone 11.3)
    startAnalysisPipeline();
  }

  function showError(msg) {
    errorText.textContent = msg;
    errorBanner.classList.remove('hidden');
  }

  function hideError() {
    errorBanner.classList.add('hidden');
  }

  // Workflow State Machine (Milestone 11.2)
  const AppState = {
    INITIAL: 'INITIAL',
    UPLOADING: 'UPLOADING',
    VALIDATING: 'VALIDATING',
    LOADING: 'LOADING',
    READY: 'READY',
    ERROR: 'ERROR'
  };
  let currentAppState = AppState.INITIAL;

  function setAppState(state, detailMsg = '') {
    currentAppState = state;
    switch (state) {
      case AppState.INITIAL:
        engineStatus.innerHTML = '<span class="pulse-dot"></span> System Ready';
        break;
      case AppState.UPLOADING:
        engineStatus.innerHTML = '<span class="pulse-dot" style="background:#3b82f6;box-shadow:0 0 8px #3b82f6;"></span> Uploading CSV...';
        break;
      case AppState.VALIDATING:
        engineStatus.innerHTML = '<span class="pulse-dot" style="background:#8b5cf6;box-shadow:0 0 8px #8b5cf6;"></span> Validating Transaction Data...';
        break;
      case AppState.LOADING:
        engineStatus.innerHTML = `<span class="pulse-dot" style="background:#f59e0b;box-shadow:0 0 8px #f59e0b;"></span> Loading Analysis (${detailMsg})...`;
        break;
      case AppState.READY:
        engineStatus.innerHTML = '<span class="pulse-dot"></span> Investigation Ready';
        break;
      case AppState.ERROR:
        engineStatus.innerHTML = '<span class="pulse-dot" style="background:#ef4444;box-shadow:0 0 8px #ef4444;"></span> Ingestion Error';
        break;
    }
  }

  function resetWorkflow() {
    selectedFile = null;
    csvFileInput.value = '';
    fileInfoCard.classList.add('hidden');
    btnAnalyze.classList.add('hidden');
    hideError();

    sectionBaseline.classList.add('hidden');
    sectionRules.classList.add('hidden');
    sectionReport.classList.add('hidden');

    resetPipelineIndicators();
    attentionBadge.className = 'attention-badge badge-insufficient';
    attentionBadge.textContent = 'AWAITING UPLOAD';
    caseCustomerId.textContent = '—';
    setAppState(AppState.INITIAL);
  }

  function resetPipelineIndicators() {
    [pStep1, pStep2, pStep3, pStep4, pStep5, pStep6].forEach((step, idx) => {
      step.className = 'pipeline-step';
      step.querySelector('.step-indicator').className = 'step-indicator waiting';
      step.querySelector('.step-indicator').textContent = (idx + 1).toString();
    });
  }

  function setStepActive(stepEl) {
    stepEl.className = 'pipeline-step active';
    const ind = stepEl.querySelector('.step-indicator');
    ind.className = 'step-indicator loading';
    ind.textContent = '';
  }

  function setStepDone(stepEl) {
    stepEl.className = 'pipeline-step done';
    const ind = stepEl.querySelector('.step-indicator');
    ind.className = 'step-indicator done';
    ind.textContent = '✓';
  }

  // --- Main Analysis Pipeline Async Coordinator ---
  async function startAnalysisPipeline() {
    if (!selectedFile) return;

    hideError();
    resetPipelineIndicators();
    
    // Step 1: Uploading & Validating
    setAppState(AppState.UPLOADING);
    setStepActive(pStep1);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setAppState(AppState.VALIDATING);
      const uploadResp = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      let uploadData = {};
      try {
        uploadData = await uploadResp.json();
      } catch {
        throw new Error('Unable to connect to investigation service.');
      }

      if (!uploadResp.ok || uploadData.valid === false) {
        const errs = uploadData.errors ? uploadData.errors.join(' | ') : 'CSV Upload Failed';
        throw new Error(errs);
      }
      setStepDone(pStep1);

      // Step 2: GET /api/baseline
      setAppState(AppState.LOADING, 'Baseline Calculation');
      setStepActive(pStep2);
      const baselineResp = await fetch('/api/baseline');
      const baselineData = await baselineResp.json().catch(() => ({}));
      setStepDone(pStep2);

      // Step 3: GET /api/rules
      setAppState(AppState.LOADING, 'Risk Rules Evaluation');
      setStepActive(pStep3);
      const rulesResp = await fetch('/api/rules');
      const rulesData = await rulesResp.json();
      setStepDone(pStep3);

      // Step 4: GET /api/attention
      setStepActive(pStep4);
      const attResp = await fetch('/api/attention');
      const attData = await attResp.json();
      setStepDone(pStep4);

      // Step 5: GET /api/investigation
      setStepActive(pStep5);
      const invResp = await fetch('/api/investigation');
      const invData = await invResp.json();
      setStepDone(pStep5);

      // Step 6: GET /api/report
      setStepActive(pStep6);
      const reportResp = await fetch('/api/report');
      const reportData = await reportResp.json();
      setStepDone(pStep6);

      engineStatus.innerHTML = '<span class="pulse-dot"></span> Complete';

      // Render Dashboard Content
      renderDashboard(baselineData, rulesData, attData, invData, reportData);
    } catch (err) {
      showError(err.message || 'An unexpected error occurred during analysis.');
      engineStatus.innerHTML = '<span class="pulse-dot" style="background:#ef4444;box-shadow:0 0 8px #ef4444;"></span> Error';
    }
  }

  // Global reference state for traceability
  let currentBaseline = {};
  let currentRulesData = {};
  let currentReportData = {};

  // --- Render Dashboard UI ---
  function renderDashboard(baselineData, rulesData, attData, invData, reportData) {
    currentBaseline = baselineData.baseline || {};
    currentRulesData = rulesData || {};
    currentReportData = reportData.report || {};

    const report = reportData.report || {};
    const assessment = attData.assessment || {};
    const baseline = baselineData.baseline || {};

    // 1. Case Bar & Customer Info
    const custId = report.customer_id || baseline.customer_id || 'UNKNOWN';
    caseCustomerId.textContent = custId;
    caseRefId.textContent = `NXS-PS06-${Date.now().toString().slice(-6)}`;

    const attLevel = assessment.attention_level || 'INSUFFICIENT_EVIDENCE';
    const attLabel = assessment.attention_label || 'Insufficient Evidence';

    setAttentionBadge(attLevel, attLabel);

    // 2. Render Baseline Section
    renderBaselineSection(baseline);
    sectionBaseline.classList.remove('hidden');

    // 3. Render Rules & Attention Section
    renderRulesSection(rulesData, assessment);
    sectionRules.classList.remove('hidden');

    // 4. Render Report & Gemini Section
    renderReportSection(report, invData);
    sectionReport.classList.remove('hidden');

    // Scroll smoothly to assessment
    document.getElementById('attention-banner').scrollIntoView({ behavior: 'smooth' });
  }

  function setAttentionBadge(level, label) {
    attentionBadge.textContent = label;
    attentionBadge.className = 'attention-badge ';

    if (level === 'HIGH_ATTENTION') {
      attentionBadge.classList.add('badge-high');
    } else if (level === 'ATTENTION_RECOMMENDED') {
      attentionBadge.classList.add('badge-attention');
    } else if (level === 'CONTEXTUAL_REVIEW') {
      attentionBadge.classList.add('badge-context');
    } else if (level === 'NO_IMMEDIATE_CONCERN') {
      attentionBadge.classList.add('badge-none');
    } else {
      attentionBadge.classList.add('badge-insufficient');
    }
  }

  // --- Baseline Rendering ---
  function renderBaselineSection(baseline) {
    document.getElementById('stat-tx-count').textContent = (baseline.transaction_count || 0).toLocaleString();
    
    const amt = baseline.amount_statistics || {};
    document.getElementById('stat-min').textContent = formatINR(amt.min || 0);
    document.getElementById('stat-max').textContent = formatINR(amt.max_amount || amt.max || 0);
    document.getElementById('stat-mean').textContent = formatINR(amt.mean || 0);
    document.getElementById('stat-median').textContent = formatINR(amt.median || 0);
    document.getElementById('stat-p95').textContent = formatINR(amt.p95 || 0);

    // Channel Usage Bars
    const channelContainer = document.getElementById('channel-bars-list');
    channelContainer.innerHTML = '';
    const channels = baseline.channel_usage || {};
    for (const [ch, usage] of Object.entries(channels)) {
      const pct = usage.percentage || 0;
      const count = usage.count || usage.transaction_count || 0;
      const itemHtml = `
        <div class="channel-bar-item">
          <div class="channel-label-row">
            <span style="font-weight:600;">${ch}</span>
            <span style="color:var(--text-muted);">${count} txs (${pct.toFixed(1)}%)</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width: ${pct}%;"></div>
          </div>
        </div>
      `;
      channelContainer.insertAdjacentHTML('beforeend', itemHtml);
    }

    // Hourly Activity SVG Chart (00:00 - 23:00)
    const hourlyContainer = document.getElementById('hourly-chart-bars');
    hourlyContainer.innerHTML = '';
    const hourly = baseline.hourly_activity || {};

    let maxCount = 1;
    for (let h = 0; h < 24; h++) {
      const key = h.toString().padStart(2, '0');
      const act = hourly[key] || {};
      if ((act.count || 0) > maxCount) maxCount = act.count;
    }

    for (let h = 0; h < 24; h++) {
      const key = h.toString().padStart(2, '0');
      const act = hourly[key] || {};
      const cnt = act.count || 0;
      const heightPct = Math.max(4, (cnt / maxCount) * 100);
      const isOffHours = h >= 0 && h < 5;

      const colHtml = `
        <div class="hourly-col" title="${key}:00 — ${cnt} txs">
          <div class="bar-col ${isOffHours && cnt > 0 ? 'off-hours' : ''}" style="height: ${heightPct}%;"></div>
          <div class="hourly-label">${key}</div>
        </div>
      `;
      hourlyContainer.insertAdjacentHTML('beforeend', colHtml);
    }

    // Payee Table
    const payeeBody = document.getElementById('payee-table-body');
    payeeBody.innerHTML = '';
    const payees = baseline.payee_usage || {};
    for (const [payee, usage] of Object.entries(payees)) {
      const row = `
        <tr>
          <td style="font-weight:600;">${payee}</td>
          <td>${usage.transaction_count || 0}</td>
          <td>${formatINR(usage.total_amount || 0)}</td>
          <td>${formatINR((usage.total_amount || 0) / Math.max(1, usage.transaction_count || 1))}</td>
        </tr>
      `;
      payeeBody.insertAdjacentHTML('beforeend', row);
    }
  }

  // --- Rules & Assessment Rendering ---
  function renderRulesSection(rulesData, assessment) {
    const banner = document.getElementById('attention-banner');
    const firstFinding = document.getElementById('banner-first-finding');
    const reasonText = document.getElementById('banner-reason');

    const attLevel = assessment.attention_level || 'INSUFFICIENT_EVIDENCE';
    const attLabel = assessment.attention_label || 'Insufficient Evidence';

    banner.className = 'attention-banner ';
    if (attLevel === 'HIGH_ATTENTION') banner.classList.add('high');
    else if (attLevel === 'ATTENTION_RECOMMENDED') banner.classList.add('attention');
    else if (attLevel === 'CONTEXTUAL_REVIEW') banner.classList.add('context');
    else if (attLevel === 'NO_IMMEDIATE_CONCERN') banner.classList.add('none');
    else banner.classList.add('insufficient');

    firstFinding.textContent = attLabel;
    reasonText.textContent = assessment.reason || 'Deterministic analysis evaluated baseline & risk rules.';

    // Rules Cards Grid (R01 - R04)
    const rulesGrid = document.getElementById('rules-cards-grid');
    rulesGrid.innerHTML = '';
    const rules = rulesData.rules || [];

    rules.forEach((r) => {
      const triggered = r.triggered;
      let evHtml = '<div style="color:var(--text-muted);font-size:0.85rem;">No trigger conditions met.</div>';

      if (triggered && r.evidence && r.evidence.length > 0) {
        const evItems = r.evidence.map((ev) => {
          const txIds = ev.affected_transaction_ids || (ev.transaction_id ? [ev.transaction_id] : []);
          const txBtns = txIds.map((tid) => `<button class="btn btn-outline btn-trace-tx" data-txid="${tid}" style="padding:0.1rem 0.35rem;font-size:0.75rem;margin-left:0.3rem;">🔍 ${tid}</button>`).join('');
          return `<div style="margin-bottom:0.35rem;">• ${ev.message || ev.description} ${txBtns}</div>`;
        }).join('');
        evHtml = `<div class="rule-evidence-box">${evItems}</div>`;
      }

      const cardHtml = `
        <div class="rule-card ${triggered ? 'triggered' : ''}" id="rule-card-${r.rule_id}">
          <div class="rule-card-header">
            <span class="rule-code">${r.rule_id}</span>
            <span class="attention-badge ${triggered ? 'badge-high' : 'badge-none'}" style="font-size:0.7rem;padding:0.15rem 0.4rem;">
              ${triggered ? 'TRIGGERED' : 'NOT TRIGGERED'}
            </span>
          </div>
          <div class="rule-name">${r.name}</div>
          ${evHtml}
        </div>
      `;
      rulesGrid.insertAdjacentHTML('beforeend', cardHtml);
    });

    // Attach Traceability Event Listeners for Rule Cards -> Transaction Detail Modal
    document.querySelectorAll('.btn-trace-tx').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const txId = e.currentTarget.getAttribute('data-txid');
        openTransactionModal(txId);
      });
    });
  }

  // --- Report & Gemini Rendering ---
  function renderReportSection(report, invData) {
    // Review Transactions Table
    const txBody = document.getElementById('review-tx-table-body');
    txBody.innerHTML = '';
    currentTransactionsMap = {};

    const reviewTxs = report.transactions_requiring_review || [];
    if (reviewTxs.length === 0) {
      txBody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted);">No transactions currently require investigator review.</td></tr>';
    } else {
      reviewTxs.forEach((tx) => {
        currentTransactionsMap[tx.transaction_id] = tx;
        const ruleBadges = (tx.triggered_rules || []).map((r) => `<span class="badge-high btn-jump-rule" data-ruleid="${r}" style="font-size:0.7rem;padding:0.1rem 0.35rem;border-radius:4px;margin-right:0.2rem;cursor:pointer;" title="Click to jump to rule">${r}</span>`).join('');
        const row = `
          <tr>
            <td style="font-family:monospace;font-weight:700;color:var(--accent-blue);">${tx.transaction_id}</td>
            <td style="font-size:0.8rem;">${formatTimestamp(tx.timestamp)}</td>
            <td>${tx.description}</td>
            <td style="font-weight:600;">${tx.payee}</td>
            <td style="font-weight:700;">${formatINR(tx.amount)}</td>
            <td><span class="brand-badge" style="font-size:0.7rem;">${tx.channel}</span></td>
            <td>${ruleBadges}</td>
            <td>
              <button class="btn btn-outline btn-inspect" data-txid="${tx.transaction_id}" style="padding:0.25rem 0.5rem;font-size:0.75rem;">Inspect</button>
            </td>
          </tr>
        `;
        txBody.insertAdjacentHTML('beforeend', row);
      });

      // Attach Modal Inspector Event Listeners
      document.querySelectorAll('.btn-inspect').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const txId = e.currentTarget.getAttribute('data-txid');
          openTransactionModal(txId);
        });
      });

      // Attach Rule Jump Event Listeners
      document.querySelectorAll('.btn-jump-rule').forEach((el) => {
        el.addEventListener('click', (e) => {
          const ruleId = e.currentTarget.getAttribute('data-ruleid');
          jumpToRule(ruleId);
        });
      });
    }

    // Transaction Connections Box
    const connBox = document.getElementById('connections-container');
    connBox.innerHTML = '';
    const conns = report.transaction_connections || [];
    if (conns.length === 0) {
      connBox.innerHTML = '<div style="color:var(--text-muted);font-size:0.85rem;">No multi-transaction connections observed.</div>';
    } else {
      conns.forEach((c) => {
        const item = `
          <div class="connection-item">
            <span class="connection-badge">${c.connection_type}</span>
            <span>${c.description}</span>
          </div>
        `;
        connBox.insertAdjacentHTML('beforeend', item);
      });
    }

    // Gemini Grounded Analysis Section & Fallback Handling
    const isGeminiAvailable = invData && invData.available !== false && report.assessment;
    
    if (isGeminiAvailable) {
      document.getElementById('gemini-assessment').textContent = report.assessment || 'Overview assessment available.';
      document.getElementById('gemini-why').textContent = report.why_attention || 'Review required based on triggered evidence.';
      document.getElementById('gemini-reducing').textContent = report.context_reducing_concern || 'Customer historical baseline active.';
      document.getElementById('gemini-priority').textContent = report.investigator_priority || 'Review triggered evidence.';

      const checksList = document.getElementById('gemini-suggested-checks');
      checksList.innerHTML = '';
      (report.suggested_checks || []).forEach((chk) => {
        checksList.insertAdjacentHTML('beforeend', `<li>${chk}</li>`);
      });
    } else {
      document.getElementById('gemini-assessment').textContent = 'AI investigation explanation is currently unavailable.';
      document.getElementById('gemini-why').textContent = 'Deterministic risk rules and evidence findings remain fully active and authoritative above.';
      document.getElementById('gemini-reducing').textContent = 'Customer baseline statistics remain available for manual inspection.';
      document.getElementById('gemini-priority').textContent = 'Inspect triggered deterministic rules (R01-R04) and flagged transactions.';
      
      const checksList = document.getElementById('gemini-suggested-checks');
      checksList.innerHTML = '<li>Verify transaction amount against customer P95 baseline cutoff.</li><li>Check payee history and transaction timestamps manually.</li>';
    }

    document.getElementById('report-safety-statement').textContent = report.safety_statement || 'This analysis highlights transaction patterns that may warrant investigation. It does not establish that fraud occurred. Final judgment should be made by an investigator using available transaction and customer context.';
  }

  function jumpToRule(ruleId) {
    closeModal();
    const el = document.getElementById(`rule-card-${ruleId}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.style.border = '2px solid #3b82f6';
      setTimeout(() => {
        el.style.border = '';
      }, 2000);
    }
  }

  // --- Transaction Inspection Modal ---
  function openTransactionModal(txId) {
    let tx = currentTransactionsMap[txId];

    // If not found in review map, locate in currentReportData or create placeholder lookup
    if (!tx && currentReportData.transactions_requiring_review) {
      tx = currentReportData.transactions_requiring_review.find((t) => t.transaction_id === txId);
    }

    if (!tx) {
      modalTitle.textContent = `Inspect Transaction: ${txId}`;
      modalBody.innerHTML = `<div style="color:var(--text-muted);padding:1rem;">Transaction record details for ${txId} loaded from ledger history.</div>`;
      modalOverlay.classList.add('active');
      return;
    }

    const custId = currentReportData.customer_id || currentBaseline.customer_id || 'CUST_UNKNOWN';
    const trigRules = tx.triggered_rules || [];
    const ruleBadges = trigRules.map((r) => `<span class="badge-high btn-modal-jump-rule" data-ruleid="${r}" style="display:inline-block;padding:0.2rem 0.5rem;border-radius:4px;margin-right:0.4rem;font-size:0.8rem;cursor:pointer;">${r} ↗</span>`).join('') || '<span style="color:var(--text-muted);font-size:0.85rem;">None</span>';

    // Calculate baseline deviation preview
    const amtStats = currentBaseline.amount_statistics || {};
    const meanVal = amtStats.mean || 0;
    const p95Val = amtStats.p95 || 0;
    let deviationText = 'Within normal baseline variance';
    if (tx.amount > p95Val && p95Val > 0) {
      deviationText = `Exceeds P95 Cutoff (${formatINR(p95Val)}) by ${((tx.amount / p95Val - 1) * 100).toFixed(0)}%`;
    } else if (meanVal > 0) {
      deviationText = `${(tx.amount / meanVal).toFixed(1)}x mean amount (${formatINR(meanVal)})`;
    }

    modalTitle.textContent = `Inspect Transaction: ${tx.transaction_id}`;
    modalBody.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem;font-size:0.9rem;">
        <div><span style="color:var(--text-muted);">Transaction ID:</span> <strong style="font-family:monospace;color:var(--accent-blue);">${tx.transaction_id}</strong></div>
        <div><span style="color:var(--text-muted);">Customer ID:</span> <strong>${custId}</strong></div>
        <div><span style="color:var(--text-muted);">Timestamp:</span> <strong>${formatTimestamp(tx.timestamp)}</strong></div>
        <div><span style="color:var(--text-muted);">Payee / Receiver:</span> <strong>${tx.payee}</strong></div>
        <div><span style="color:var(--text-muted);">Settlement Amount:</span> <strong style="color:#10b981;font-size:1.1rem;">${formatINR(tx.amount)}</strong></div>
        <div><span style="color:var(--text-muted);">Channel:</span> <strong>${tx.channel}</strong></div>
        <div><span style="color:var(--text-muted);">Description:</span> <strong>${tx.description}</strong></div>
        <div><span style="color:var(--text-muted);">Baseline Deviation:</span> <strong style="color:#f59e0b;">${deviationText}</strong></div>
      </div>
      <div style="border-top:1px solid var(--border-color);padding-top:1rem;margin-top:0.5rem;">
        <h4 style="font-size:0.9rem;margin-bottom:0.5rem;color:var(--text-primary);">Triggered Risk Rules & Evidence Traceability</h4>
        <div>${ruleBadges}</div>
      </div>
    `;

    // Add event listeners inside modal to jump to rules
    modalOverlay.querySelectorAll('.btn-modal-jump-rule').forEach((el) => {
      el.addEventListener('click', (e) => {
        const ruleId = e.currentTarget.getAttribute('data-ruleid');
        jumpToRule(ruleId);
      });
    });

    modalOverlay.classList.add('active');
  }

  function closeModal() {
    modalOverlay.classList.remove('active');
  }

  // --- Helper Formatting Functions ---
  function formatINR(val) {
    return `₹${(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function formatTimestamp(tsStr) {
    if (!tsStr) return 'N/A';
    try {
      const d = new Date(tsStr);
      return d.toLocaleString();
    } catch {
      return tsStr;
    }
  }
});
