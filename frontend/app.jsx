/* 
  PS06 Banking Transaction Risk Investigation Assistant
  Dynamic React 18 Application (State-Driven Component Architecture)
*/

const { useState, useEffect, useRef, useCallback } = React;

// --- Helper Formatting Functions ---
const formatINR = (val) => {
  return `₹${(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const formatTimestamp = (tsStr) => {
  if (!tsStr) return 'N/A';
  try {
    const d = new Date(tsStr);
    return d.toLocaleString();
  } catch {
    return tsStr;
  }
};

// --- App State Enum ---
const AppState = {
  INITIAL: 'INITIAL',
  UPLOADING: 'UPLOADING',
  VALIDATING: 'VALIDATING',
  LOADING: 'LOADING',
  READY: 'READY',
  ERROR: 'ERROR'
};

// --- Main Root Component ---
function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [appState, setAppState] = useState(AppState.INITIAL);
  const [loadingStepMsg, setLoadingStepMsg] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  
  // Pipeline Step Indicators (1-6)
  const [pipelineSteps, setPipelineSteps] = useState([
    { id: 1, name: 'Transaction Validation & Deduplication', status: 'waiting' },
    { id: 2, name: 'Baseline Statistical Calculation', status: 'waiting' },
    { id: 3, name: 'Deterministic Risk Rules Evaluation (R01-R04)', status: 'waiting' },
    { id: 4, name: 'Attention Trigger Calibration', status: 'waiting' },
    { id: 5, name: 'Gemini Grounded Traceability Matrix', status: 'waiting' },
    { id: 6, name: 'Evidence Dossier & Report Assembly', status: 'waiting' },
  ]);

  // Loaded API Data
  const [baselineData, setBaselineData] = useState(null);
  const [rulesData, setRulesData] = useState(null);
  const [attData, setAttData] = useState(null);
  const [invData, setInvData] = useState(null);
  const [reportData, setReportData] = useState(null);
  
  // Modal Inspector State
  const [inspectedTx, setInspectedTx] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [highlightedRuleId, setHighlightedRuleId] = useState(null);

  const fileInputRef = useRef(null);

  // Helper to update a pipeline step status
  const updateStepStatus = (stepId, status) => {
    setPipelineSteps(prev => prev.map(s => s.id === stepId ? { ...s, status } : s));
  };

  const resetPipelineSteps = () => {
    setPipelineSteps([
      { id: 1, name: 'Transaction Validation & Deduplication', status: 'waiting' },
      { id: 2, name: 'Baseline Statistical Calculation', status: 'waiting' },
      { id: 3, name: 'Deterministic Risk Rules Evaluation (R01-R04)', status: 'waiting' },
      { id: 4, name: 'Attention Trigger Calibration', status: 'waiting' },
      { id: 5, name: 'Gemini Grounded Traceability Matrix', status: 'waiting' },
      { id: 6, name: 'Evidence Dossier & Report Assembly', status: 'waiting' },
    ]);
  };

  // Reset entire workflow
  const handleResetWorkflow = () => {
    setSelectedFile(null);
    setAppState(AppState.INITIAL);
    setErrorMessage('');
    setBaselineData(null);
    setRulesData(null);
    setAttData(null);
    setInvData(null);
    setReportData(null);
    setIsModalOpen(false);
    setInspectedTx(null);
    resetPipelineSteps();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Main Async Pipeline Execution
  const runAnalysisPipeline = async (file) => {
    if (!file) return;

    setErrorMessage('');
    resetPipelineSteps();
    setAppState(AppState.UPLOADING);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Step 1: Uploading & Validating CSV
      updateStepStatus(1, 'loading');
      setAppState(AppState.VALIDATING);
      const uploadResp = await fetch('/api/upload', { method: 'POST', body: formData });
      let uploadResData = {};
      try {
        uploadResData = await uploadResp.json();
      } catch {
        throw new Error('Unable to connect to investigation service.');
      }

      if (!uploadResp.ok || uploadResData.valid === false) {
        const errs = uploadResData.errors ? uploadResData.errors.join(' | ') : 'CSV Upload Failed';
        throw new Error(errs);
      }
      updateStepStatus(1, 'done');

      // Step 2: Baseline
      setLoadingStepMsg('Baseline Calculation');
      setAppState(AppState.LOADING);
      updateStepStatus(2, 'loading');
      const bResp = await fetch('/api/baseline');
      const bData = await bResp.json().catch(() => ({}));
      setBaselineData(bData.baseline || {});
      updateStepStatus(2, 'done');

      // Step 3: Rules
      setLoadingStepMsg('Risk Rules Evaluation');
      updateStepStatus(3, 'loading');
      const rResp = await fetch('/api/rules');
      const rData = await rResp.json().catch(() => ({}));
      setRulesData(rData);
      updateStepStatus(3, 'done');

      // Step 4: Attention
      setLoadingStepMsg('Attention Assessment');
      updateStepStatus(4, 'loading');
      const aResp = await fetch('/api/attention');
      const aData = await aResp.json().catch(() => ({}));
      setAttData(aData.assessment || {});
      updateStepStatus(4, 'done');

      // Step 5: Gemini Investigation Explanation
      setLoadingStepMsg('Gemini Explanation');
      updateStepStatus(5, 'loading');
      const iResp = await fetch('/api/investigation');
      const iData = await iResp.json().catch(() => ({ available: false }));
      setInvData(iData);
      updateStepStatus(5, 'done');

      // Step 6: Final Report
      setLoadingStepMsg('Dossier Assembly');
      updateStepStatus(6, 'loading');
      const repResp = await fetch('/api/report');
      const repData = await repResp.json().catch(() => ({}));
      setReportData(repData.report || {});
      updateStepStatus(6, 'done');

      setAppState(AppState.READY);

      // Smooth scroll to findings
      setTimeout(() => {
        const bannerEl = document.getElementById('attention-banner');
        if (bannerEl) bannerEl.scrollIntoView({ behavior: 'smooth' });
      }, 100);

    } catch (err) {
      setAppState(AppState.ERROR);
      setErrorMessage(err.message || 'An unexpected error occurred during analysis.');
    }
  };

  // Handle File Selection
  const handleFileSelected = (file) => {
    if (!file.name.endsWith('.csv')) {
      setErrorMessage('Please select a valid CSV file.');
      return;
    }
    setSelectedFile(file);
    runAnalysisPipeline(file);
  };

  // Traceability: Open Transaction Detail Inspector Modal
  const openInspectModal = (txId) => {
    const reviewTxs = reportData?.transactions_requiring_review || [];
    let tx = reviewTxs.find(t => t.transaction_id === txId);
    if (!tx) {
      tx = { transaction_id: txId, description: 'Ledger Record', payee: 'Counterparty', amount: 0, channel: 'N/A' };
    }
    setInspectedTx(tx);
    setIsModalOpen(true);
  };

  // Traceability: Jump to Rule Card
  const jumpToRuleCard = (ruleId) => {
    setIsModalOpen(false);
    setHighlightedRuleId(ruleId);
    const ruleCardEl = document.getElementById(`rule-card-${ruleId}`);
    if (ruleCardEl) {
      ruleCardEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    setTimeout(() => {
      setHighlightedRuleId(null);
    }, 2500);
  };

  return (
    <div className="react-app-root">
      {/* Header */}
      <Header appState={appState} loadingMsg={loadingStepMsg} />

      {/* Case Bar */}
      <CaseMetadataBar 
        customer_id={reportData?.customer_id || baselineData?.customer_id}
        attention={attData}
        onReset={handleResetWorkflow}
      />

      {/* Main Content */}
      <main className="main-content">
        {/* Step 01: Ingestion & Upload */}
        <UploadSection 
          selectedFile={selectedFile}
          onFileSelect={handleFileSelected}
          fileInputRef={fileInputRef}
          pipelineSteps={pipelineSteps}
          errorMessage={errorMessage}
          appState={appState}
          onAnalyzeClick={() => runAnalysisPipeline(selectedFile)}
        />

        {/* Step 02: Baseline Section */}
        {baselineData && (
          <BaselineSection baseline={baselineData} />
        )}

        {/* Step 03: Rules & Attention */}
        {rulesData && (
          <RulesSection 
            rulesData={rulesData} 
            assessment={attData} 
            onInspectTx={openInspectModal}
            highlightedRuleId={highlightedRuleId}
          />
        )}

        {/* Step 04-06: Report & Gemini */}
        {reportData && (
          <ReportSection 
            report={reportData} 
            invData={invData} 
            onInspectTx={openInspectModal}
            onJumpRule={jumpToRuleCard}
          />
        )}
      </main>

      {/* Detail Inspector Modal */}
      {isModalOpen && inspectedTx && (
        <TransactionModal 
          tx={inspectedTx}
          baseline={baselineData}
          report={reportData}
          onClose={() => setIsModalOpen(false)}
          onJumpRule={jumpToRuleCard}
        />
      )}
    </div>
  );
}

// --- Subcomponent: Header ---
function Header({ appState, loadingMsg }) {
  let statusHtml = <><span className="pulse-dot"></span> System Ready</>;
  if (appState === AppState.UPLOADING) {
    statusHtml = <><span className="pulse-dot" style={{ background: '#3b82f6', boxShadow: '0 0 8px #3b82f6' }}></span> Uploading CSV...</>;
  } else if (appState === AppState.VALIDATING) {
    statusHtml = <><span className="pulse-dot" style={{ background: '#8b5cf6', boxShadow: '0 0 8px #8b5cf6' }}></span> Validating Data...</>;
  } else if (appState === AppState.LOADING) {
    statusHtml = <><span className="pulse-dot" style={{ background: '#f59e0b', boxShadow: '0 0 8px #f59e0b' }}></span> Loading ({loadingMsg})...</>;
  } else if (appState === AppState.READY) {
    statusHtml = <><span className="pulse-dot"></span> Investigation Ready</>;
  } else if (appState === AppState.ERROR) {
    statusHtml = <><span className="pulse-dot" style={{ background: '#ef4444', boxShadow: '0 0 8px #ef4444' }}></span> Ingestion Error</>;
  }

  return (
    <header className="header">
      <div className="header-container">
        <div className="brand-section">
          <span className="brand-badge">PS06</span>
          <div>
            <div className="brand-title">Banking Transaction Risk Investigation Assistant</div>
            <div className="brand-subtitle">Automated Evidence Assembly & Grounded Intelligence Terminal (React 18 Engine)</div>
          </div>
        </div>
        <div className="status-section">
          <div className="engine-status">{statusHtml}</div>
        </div>
      </div>
    </header>
  );
}

// --- Subcomponent: Case Metadata Bar ---
function CaseMetadataBar({ customer_id, attention, onReset }) {
  const attLevel = attention?.attention_level || 'INSUFFICIENT_EVIDENCE';
  const attLabel = attention?.attention_label || 'AWAITING UPLOAD';

  let badgeClass = 'badge-insufficient';
  if (attLevel === 'HIGH_ATTENTION') badgeClass = 'badge-high';
  else if (attLevel === 'ATTENTION_RECOMMENDED') badgeClass = 'badge-attention';
  else if (attLevel === 'CONTEXTUAL_REVIEW') badgeClass = 'badge-context';
  else if (attLevel === 'NO_IMMEDIATE_CONCERN') badgeClass = 'badge-none';

  return (
    <div className="case-bar">
      <div className="case-container">
        <div className="case-info">
          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>CASE REF:</span>
          <span className="case-ref">NXS-PS06-LIVE</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600, marginLeft: '0.5rem' }}>CUSTOMER:</span>
          <strong style={{ color: 'white', fontSize: '0.9rem' }}>{customer_id || '—'}</strong>
          <span className={`attention-badge ${badgeClass}`}>{attLabel}</span>
        </div>
        <div className="action-buttons">
          <button className="btn btn-secondary" onClick={onReset}>Reset Workflow</button>
          <button className="btn btn-primary" onClick={() => {
            const el = document.getElementById('attention-banner');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }}>Jump to Findings</button>
        </div>
      </div>
    </div>
  );
}

// --- Subcomponent: Upload Section ---
function UploadSection({ selectedFile, onFileSelect, fileInputRef, pipelineSteps, errorMessage, appState, onAnalyzeClick }) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <section className="step-card">
      <div className="step-header">
        <div>
          <span className="step-tag">STEP 01</span>
          <span className="step-title">Upload Transaction History & Ingestion</span>
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Deterministic Status: In-Memory Ledger</span>
      </div>

      <div className="upload-grid">
        <div>
          <div 
            className={`dropzone-box ${isDragOver ? 'dragover' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
          >
            <div className="upload-icon">📁</div>
            <div>
              <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>Drag and drop bank ledger CSV</strong>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Supports multi-column banking exports up to 10 MB (UTF-8)
              </div>
            </div>
            <button className="btn btn-outline" type="button">Browse System Files</button>
            <input 
              type="file" 
              ref={fileInputRef} 
              accept=".csv" 
              className="hidden" 
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) onFileSelect(e.target.files[0]);
              }}
            />
          </div>

          {selectedFile && (
            <div className="file-info-card" style={{ marginTop: '1rem' }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{selectedFile.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{(selectedFile.size / 1024).toFixed(1)} KB</div>
              </div>
              <button className="btn btn-primary" onClick={onAnalyzeClick}>Re-Analyze</button>
            </div>
          )}

          <div style={{ marginTop: '1rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>REQUIRED 7 CORE COLUMNS:</span>
            <div className="schema-checklist">
              {['transaction_id', 'customer_id', 'timestamp', 'description', 'payee', 'amount', 'channel'].map(c => (
                <span key={c} className="schema-tag">{c}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Real-time Ingestion Stepper */}
        <div className="pipeline-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: '0.95rem' }}>Real-Time Ingestion Pipeline</strong>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>STAGE 1-6</span>
          </div>

          <div className="pipeline-list">
            {pipelineSteps.map(step => (
              <div key={step.id} className={`pipeline-step ${step.status === 'loading' ? 'active' : step.status === 'done' ? 'done' : ''}`}>
                <span>{step.name}</span>
                <span className={`step-indicator ${step.status}`}>
                  {step.status === 'done' ? '✓' : step.status === 'loading' ? '' : step.id}
                </span>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)', background: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            🔒 <strong>Confidential & Secure:</strong> All transaction history is analyzed locally in memory against established account activity patterns. No unencrypted ledger records are retained.
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="error-banner" style={{ marginTop: '1rem' }}>
          <strong>Validation Error:</strong> <span>{errorMessage}</span>
        </div>
      )}
    </section>
  );
}

// --- Subcomponent: Baseline Section ---
function BaselineSection({ baseline }) {
  const amt = baseline?.amount_statistics || {};
  const channels = baseline?.channel_usage || {};
  const hourly = baseline?.hourly_activity || {};
  const payees = baseline?.payee_usage || {};

  // Find max count for SVG hourly bars
  let maxHourlyCount = 1;
  for (let h = 0; h < 24; h++) {
    const key = h.toString().padStart(2, '0');
    const cnt = hourly[key]?.count || 0;
    if (cnt > maxHourlyCount) maxHourlyCount = cnt;
  }

  return (
    <section className="step-card">
      <div className="step-header">
        <div>
          <span className="step-tag">STEP 02</span>
          <span className="step-title">Customer Baseline & Longitudinal Behavior</span>
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Active Window: Loaded History</span>
      </div>

      {/* Metrics Grid */}
      <div className="baseline-metrics-grid">
        <div className="metric-card">
          <div className="metric-label">TOTAL TRANSACTIONS</div>
          <div className="metric-value">{(baseline.transaction_count || 0).toLocaleString()}</div>
          <div className="metric-sub">Verified Ledger Rows</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">MIN AMOUNT</div>
          <div className="metric-value">{formatINR(amt.min || 0)}</div>
          <div className="metric-sub">Lowest Settlement</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">MAX AMOUNT</div>
          <div className="metric-value">{formatINR(amt.max_amount || amt.max || 0)}</div>
          <div className="metric-sub">Peak Settlement</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">MEAN VALUE</div>
          <div className="metric-value">{formatINR(amt.mean || 0)}</div>
          <div className="metric-sub">Average Activity</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">MEDIAN (P50)</div>
          <div className="metric-value">{formatINR(amt.median || 0)}</div>
          <div className="metric-sub">Central Cluster</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">P95 CUTOFF LIMIT</div>
          <div className="metric-value" style={{ color: '#f59e0b' }}>{formatINR(amt.p95 || 0)}</div>
          <div className="metric-sub">R01 Trigger Threshold</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="baseline-charts-grid">
        {/* Channel Usage Breakdown */}
        <div className="chart-card">
          <div className="chart-title">
            <span>Channel Usage Breakdown</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>Payment Channels</span>
          </div>
          <div className="channel-bar-list">
            {Object.entries(channels).map(([ch, usage]) => {
              const pct = usage.percentage || 0;
              const count = usage.count || usage.transaction_count || 0;
              return (
                <div key={ch} className="channel-bar-item">
                  <div className="channel-label-row">
                    <span style={{ fontWeight: 600 }}>{ch}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{count} txs ({pct.toFixed(1)}%)</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Hourly Distribution Chart */}
        <div className="chart-card">
          <div className="chart-title">
            <span>Hourly Activity Distribution (00:00 - 23:00)</span>
            <span style={{ fontSize: '0.75rem', color: '#ef4444', fontWeight: 600 }}>● Off-Hours (00:00-05:00)</span>
          </div>
          <div className="hourly-bar-container">
            {Array.from({ length: 24 }).map((_, h) => {
              const key = h.toString().padStart(2, '0');
              const cnt = hourly[key]?.count || 0;
              const heightPct = Math.max(4, (cnt / maxHourlyCount) * 100);
              const isOffHours = h >= 0 && h < 5;
              return (
                <div key={key} className="hourly-col" title={`${key}:00 — ${cnt} txs`}>
                  <div className={`bar-col ${isOffHours && cnt > 0 ? 'off-hours' : ''}`} style={{ height: `${heightPct}%` }}></div>
                  <div className="hourly-label">{key}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Payee Table */}
      <div className="chart-card">
        <div className="chart-title">
          <span>Dominant Counterparty Interaction Matrix</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>Top Payee Entities</span>
        </div>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Counterparty / Payee</th>
                <th>Historical Txs</th>
                <th>Cumulative Volume</th>
                <th>Mean Settlement</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(payees).map(([payee, usage]) => {
                const count = usage.transaction_count || 0;
                const total = usage.total_amount || 0;
                return (
                  <tr key={payee}>
                    <td style={{ fontWeight: 600 }}>{payee}</td>
                    <td>{count}</td>
                    <td>{formatINR(total)}</td>
                    <td>{formatINR(total / Math.max(1, count))}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

// --- Subcomponent: Rules & Attention Section ---
function RulesSection({ rulesData, assessment, onInspectTx, highlightedRuleId }) {
  const attLevel = assessment?.attention_level || 'INSUFFICIENT_EVIDENCE';
  const attLabel = assessment?.attention_label || 'Insufficient Evidence';

  let bannerClass = 'insufficient';
  if (attLevel === 'HIGH_ATTENTION') bannerClass = 'high';
  else if (attLevel === 'ATTENTION_RECOMMENDED') bannerClass = 'attention';
  else if (attLevel === 'CONTEXTUAL_REVIEW') bannerClass = 'context';
  else if (attLevel === 'NO_IMMEDIATE_CONCERN') bannerClass = 'none';

  const rules = rulesData?.rules || [];

  return (
    <section className="step-card">
      <div className="step-header">
        <div>
          <span className="step-tag">STEP 03</span>
          <span className="step-title">Forensic Investigation & Deterministic Risk Rules</span>
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Deterministic Evaluation</span>
      </div>

      {/* Attention Banner */}
      <div className={`attention-banner ${bannerClass}`} id="attention-banner">
        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          FIRST FINDING — INVESTIGATION ASSESSMENT
        </div>
        <div className="first-finding-text">{attLabel}</div>
        <div style={{ marginTop: '0.5rem', fontSize: '0.95rem' }}>
          {assessment?.reason || 'Deterministic analysis evaluated baseline & risk rules.'}
        </div>
      </div>

      {/* Rule Cards Grid */}
      <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem' }}>Deterministic Risk Rule Results (R01–R04)</div>
      <div className="rules-grid">
        {rules.map(r => {
          const triggered = r.triggered;
          const isHighlighted = highlightedRuleId === r.rule_id;
          return (
            <div 
              key={r.rule_id} 
              className={`rule-card ${triggered ? 'triggered' : ''}`}
              id={`rule-card-${r.rule_id}`}
              style={isHighlighted ? { border: '2px solid #3b82f6', transform: 'scale(1.02)' } : {}}
            >
              <div className="rule-card-header">
                <span className="rule-code">{r.rule_id}</span>
                <span className={`attention-badge ${triggered ? 'badge-high' : 'badge-none'}`} style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem' }}>
                  {triggered ? 'TRIGGERED' : 'NOT TRIGGERED'}
                </span>
              </div>
              <div className="rule-name">{r.name}</div>
              
              {triggered && r.evidence && r.evidence.length > 0 ? (
                <div className="rule-evidence-box">
                  {r.evidence.map((ev, idx) => {
                    const txIds = ev.affected_transaction_ids || (ev.transaction_id ? [ev.transaction_id] : []);
                    return (
                      <div key={idx} style={{ marginBottom: '0.35rem' }}>
                        • {ev.message || ev.description}
                        {txIds.map(tid => (
                          <button 
                            key={tid} 
                            className="btn btn-outline" 
                            onClick={() => onInspectTx(tid)}
                            style={{ padding: '0.1rem 0.35rem', fontSize: '0.75rem', marginLeft: '0.3rem' }}
                          >
                            🔍 {tid}
                          </button>
                        ))}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No trigger conditions met.</div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

// --- Subcomponent: Report Section ---
function ReportSection({ report, invData, onInspectTx, onJumpRule }) {
  const reviewTxs = report?.transactions_requiring_review || [];
  const conns = report?.transaction_connections || [];
  const isGeminiAvailable = invData && invData.available !== false && report.assessment;

  return (
    <section className="step-card">
      <div className="step-header">
        <div>
          <span className="step-tag">STEP 04</span>
          <span className="step-title">Transactions Requiring Review & Traceability</span>
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Investigator Review List</span>
      </div>

      {/* Review Transactions Table */}
      <div className="data-table-container" style={{ marginBottom: '1.5rem' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Transaction ID</th>
              <th>Timestamp</th>
              <th>Description</th>
              <th>Payee</th>
              <th>Amount</th>
              <th>Channel</th>
              <th>Triggered Rules</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {reviewTxs.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No transactions currently require investigator review.
                </td>
              </tr>
            ) : (
              reviewTxs.map(tx => (
                <tr key={tx.transaction_id}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--accent-blue)' }}>{tx.transaction_id}</td>
                  <td style={{ fontSize: '0.8rem' }}>{formatTimestamp(tx.timestamp)}</td>
                  <td>{tx.description}</td>
                  <td style={{ fontWeight: 600 }}>{tx.payee}</td>
                  <td style={{ fontWeight: 700 }}>{formatINR(tx.amount)}</td>
                  <td><span className="brand-badge" style={{ fontSize: '0.7rem' }}>{tx.channel}</span></td>
                  <td>
                    {(tx.triggered_rules || []).map(r => (
                      <span 
                        key={r} 
                        className="badge-high" 
                        onClick={() => onJumpRule(r)}
                        style={{ fontSize: '0.7rem', padding: '0.1rem 0.35rem', borderRadius: '4px', marginRight: '0.2rem', cursor: 'pointer' }}
                        title="Click to jump to rule card"
                      >
                        {r} ↗
                      </span>
                    ))}
                  </td>
                  <td>
                    <button 
                      className="btn btn-outline" 
                      onClick={() => onInspectTx(tx.transaction_id)}
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Connections Box */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.5rem' }}>Transaction Connections</div>
        <div>
          {conns.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No multi-transaction connections observed.</div>
          ) : (
            conns.map((c, idx) => (
              <div key={idx} className="connection-item">
                <span className="connection-badge">{c.connection_type}</span>
                <span>{c.description}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Gemini Grounded Analysis Panel */}
      <div className="gemini-panel">
        <div className="gemini-header">
          <span>✨ Gemini Grounded Risk Analysis & Investigator Guidance</span>
        </div>

        {isGeminiAvailable ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.25rem' }}>
              <div>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-blue)', marginBottom: '0.4rem' }}>Investigation Assessment</h4>
                <div style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>{report.assessment || 'Overview assessment available.'}</div>
              </div>
              <div>
                <h4 style={{ fontSize: '0.85rem', color: '#f59e0b', marginBottom: '0.4rem' }}>Why This Needs Attention</h4>
                <div style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>{report.why_attention || 'Review required based on triggered evidence.'}</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.25rem' }}>
              <div>
                <h4 style={{ fontSize: '0.85rem', color: '#10b981', marginBottom: '0.4rem' }}>Context That May Reduce Concern</h4>
                <div style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>{report.context_reducing_concern || 'Customer historical baseline active.'}</div>
              </div>
              <div>
                <h4 style={{ fontSize: '0.85rem', color: '#a78bfa', marginBottom: '0.4rem' }}>What Investigator Should Look At First (Priority)</h4>
                <div className="directive-box">
                  <strong style={{ fontSize: '0.9rem', color: 'white' }}>{report.investigator_priority || 'Review triggered evidence.'}</strong>
                </div>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Actionable Suggested Investigator Checks</h4>
              <ul style={{ fontSize: '0.85rem', paddingLeft: '1.25rem', lineHeight: 1.7, color: 'var(--text-primary)' }}>
                {(report.suggested_checks || []).map((chk, idx) => (
                  <li key={idx}>{chk}</li>
                ))}
              </ul>
            </div>
          </>
        ) : (
          <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <h4 style={{ color: '#ef4444', marginBottom: '0.5rem' }}>AI investigation explanation is currently unavailable.</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Deterministic risk rules (R01–R04), baseline statistics, and attention assessments remain fully active above.
            </p>
          </div>
        )}

        <div className="safety-disclaimer" style={{ marginTop: '1.25rem' }}>
          {report.safety_statement || 'This analysis highlights transaction patterns that may warrant investigation. It does not establish that fraud occurred. Final judgment should be made by an investigator using available transaction and customer context.'}
        </div>
      </div>
    </section>
  );
}

// --- Subcomponent: Transaction Inspector Modal ---
function TransactionModal({ tx, baseline, report, onClose, onJumpRule }) {
  const custId = report?.customer_id || baseline?.customer_id || 'CUST_UNKNOWN';
  const trigRules = tx.triggered_rules || [];
  const amtStats = baseline?.amount_statistics || {};
  const p95Val = amtStats.p95 || 0;
  const meanVal = amtStats.mean || 0;

  let deviationText = 'Within normal baseline variance';
  if (tx.amount > p95Val && p95Val > 0) {
    deviationText = `Exceeds P95 Cutoff (${formatINR(p95Val)}) by ${((tx.amount / p95Val - 1) * 100).toFixed(0)}%`;
  } else if (meanVal > 0) {
    deviationText = `${(tx.amount / meanVal).toFixed(1)}x mean amount (${formatINR(meanVal)})`;
  }

  return (
    <div className="modal-overlay active" onClick={(e) => { if (e.target.className.includes('modal-overlay')) onClose(); }}>
      <div className="modal-container">
        <div className="modal-header">
          <h3 style={{ fontSize: '1.1rem', color: 'white' }}>Inspect Transaction: {tx.transaction_id}</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div style={{ padding: '1.25rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem', fontSize: '0.9rem' }}>
            <div><span style={{ color: 'var(--text-muted)' }}>Transaction ID:</span> <strong style={{ fontFamily: 'monospace', color: 'var(--accent-blue)' }}>{tx.transaction_id}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Customer ID:</span> <strong>{custId}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Timestamp:</span> <strong>{formatTimestamp(tx.timestamp)}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Payee / Receiver:</span> <strong>{tx.payee}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Settlement Amount:</span> <strong style={{ color: '#10b981', fontSize: '1.1rem' }}>{formatINR(tx.amount)}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Channel:</span> <strong>{tx.channel}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Description:</span> <strong>{tx.description}</strong></div>
            <div><span style={{ color: 'var(--text-muted)' }}>Baseline Deviation:</span> <strong style={{ color: '#f59e0b' }}>{deviationText}</strong></div>
          </div>
          
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem', marginTop: '0.5rem' }}>
            <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Triggered Risk Rules & Evidence Traceability</h4>
            <div>
              {trigRules.length > 0 ? trigRules.map(r => (
                <span 
                  key={r} 
                  className="badge-high" 
                  onClick={() => onJumpRule(r)}
                  style={{ display: 'inline-block', padding: '0.2rem 0.5rem', borderRadius: '4px', marginRight: '0.4rem', fontSize: '0.8rem', cursor: 'pointer' }}
                >
                  {r} ↗
                </span>
              )) : <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>None</span>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Render React App into DOM Root
const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);
root.render(<App />);
