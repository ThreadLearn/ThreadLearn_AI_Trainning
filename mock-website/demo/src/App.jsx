import { useState, useEffect, useCallback, useRef } from 'react';
import { LIVE_SAMPLES } from './mockCases';
import { MOCK_RESULTS } from './mockAnalysisResults';
import './App.css';

import LiveEditor, { buildHlMap } from './components/LiveEditor';
import IssueCard from './components/IssueCard';
import { PipelineSummary } from './components/PipelineProgress';

// Delay (ms) between each pipeline stage reveal — mimics real inference latency
// so the demo *feels* like a live model call, not an instant lookup.
const STAGE_DELAYS = [350, 550, 700, 300, 1400];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default function App() {
  const [liveCode, setLiveCode] = useState(LIVE_SAMPLES[0]?.code || '');
  const [liveSampleIdx, setLiveSampleIdx] = useState(0);

  const [issues, setIssues] = useState(null);
  const [docsUsed, setDocsUsed] = useState([]);
  const [explanation, setExplanation] = useState('');
  const [hlMap, setHlMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pipelineSteps, setPipelineSteps] = useState([]);
  const [promptInlineOpen, setPromptInlineOpen] = useState(false);
  const [analyzeTime, setAnalyzeTime] = useState(null);
  const analyzeStart = useRef(null);
  const runToken = useRef(0);

  const liveSamples = LIVE_SAMPLES;

  // ── Resizable split ──
  const [issuesPaneWidth, setIssuesPaneWidth] = useState(440);
  const dragging = useRef(false);
  const startX = useRef(0);
  const startW = useRef(440);

  const onDragStart = useCallback((e) => {
    dragging.current = true;
    startX.current = e.clientX;
    startW.current = issuesPaneWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [issuesPaneWidth]);

  useEffect(() => {
    function onMove(e) {
      if (!dragging.current) return;
      const delta = startX.current - e.clientX;
      const next = Math.min(Math.max(startW.current + delta, 280), 1400);
      setIssuesPaneWidth(next);
    }
    function onUp() {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, []);

  function reset() {
    setIssues(null);
    setDocsUsed([]);
    setExplanation('');
    setHlMap({});
    setError('');
    setPipelineSteps([]);
    setPromptInlineOpen(false);
    setAnalyzeTime(null);
  }

  function handleLiveSampleChange(idx) {
    setLiveSampleIdx(idx);
    if (idx >= 0) setLiveCode(liveSamples[idx]?.code || '');
    reset();
  }

  async function runAnalysis() {
    const myToken = ++runToken.current;
    setLoading(true);
    setError('');
    setIssues(null);
    setHlMap({});
    setPipelineSteps([]);

    const code = liveCode.trim();
    if (!code) {
      setError('Code is empty. Paste some JavaScript to analyze.');
      setLoading(false);
      return;
    }

    // Demo mode only replays pre-computed results for the built-in samples —
    // this mirrors the real AI2 pipeline's output exactly, without needing a
    // live GPU-backed model server. Select a sample above to see it in action.
    if (liveSampleIdx < 0 || !MOCK_RESULTS[liveSampleIdx]) {
      setError('Demo mode only supports the built-in samples above.\nSelect one from "Sample code" to see ThreadLearn analyze it.');
      setLoading(false);
      return;
    }

    const mock = MOCK_RESULTS[liveSampleIdx];
    analyzeStart.current = Date.now();

    const steps = [];
    for (let i = 0; i < mock.pipeline.length; i++) {
      await sleep(STAGE_DELAYS[i] ?? 400);
      if (runToken.current !== myToken) return; // user switched sample mid-run
      steps.push({ ...mock.pipeline[i], _startTime: Date.now() - 50, _endTime: Date.now() });
      setPipelineSteps([...steps]);
    }

    if (runToken.current !== myToken) return;

    const issueList = mock.issues;
    setIssues(issueList);
    setHlMap(buildHlMap(issueList));
    setDocsUsed(mock.docsUsed || []);
    setAnalyzeTime(Date.now() - analyzeStart.current);
    const docs = mock.docsUsed || [];
    setExplanation(
      issueList.length > 0
        ? `ThreadLearn detected <strong>${issueList.length} issue${issueList.length > 1 ? 's' : ''}</strong> using RAG retrieval from ${docs.length} knowledge-base document${docs.length !== 1 ? 's' : ''}. Review each issue card for details and fixes.`
        : 'No concurrency issues detected in this code.'
    );

    setLoading(false);
  }

  const currentCode = liveCode;

  return (
    <div className="app">

      <header className="topbar">
        <div className="logo">
          <div className="logo-dot" />
          ThreadLearn
        </div>
        <div className="sep" />

        <div className="mode-tabs">
          <button className="mode-tab active">Demo</button>
        </div>
        <div className="sep" />

        <>
          <span className="case-label">Sample code:</span>
          <select className="case-select" value={liveSampleIdx} onChange={e => handleLiveSampleChange(Number(e.target.value))}>
            {liveSamples.map((c, i) => <option key={i} value={i}>{c.title}</option>)}
          </select>
        </>

        <div className="topbar-right">
          <div className="ai2-indicator">
            <div className="ai2-dot online" />
            <span>Demo mode · pre-computed AI results</span>
          </div>
          <div className="sep" />
          <button className="btn-analyze" disabled={loading} onClick={runAnalysis}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M2 2l8 4-8 4V2z" fill="currentColor" />
            </svg>
            Analyze
          </button>
        </div>
      </header>

      <div className="main" style={{ gridTemplateColumns: `1fr 5px ${issuesPaneWidth}px` }}>
        <div className="editor-pane">
          <div className="pane-header">
            <span className="pane-title">Editor</span>
            <span className="lang-badge">JavaScript</span>
          </div>
          <div className="editor-scroll" style={{ position: 'relative' }}>
            <LiveEditor code={liveCode} onChange={setLiveCode} hlMap={hlMap} />
          </div>
        </div>

        <div className="resize-handle" onMouseDown={onDragStart} />
        <div className="issues-pane">
          <div className="pane-header">
            <span className="pane-title">Analysis Report</span>
            <span className={`count-badge ${issues && issues.length > 0 ? 'has' : 'none'}`}>
              {issues ? issues.length : 0}
            </span>
            <span className="rag-tag" style={{ marginLeft: 'auto' }}>RAG</span>
            <span className="mode-tag live">DEMO</span>
          </div>
          {error && <div className="error-banner visible" style={{ whiteSpace: 'pre-line' }}>{error}</div>}
          <div className="issues-scroll">
            {issues === null && pipelineSteps.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">⏳</div>
                <div className="empty-text">Click <strong>Analyze</strong> to detect<br />concurrency bugs.</div>
              </div>
            ) : (
              <>
                {issues !== null && (() => {
                  const lines = currentCode.trim().split('\n');
                  const chars = currentCode.length;
                  const high = (issues || []).filter(x => x.severity === 'high').length;
                  const med = (issues || []).filter(x => x.severity === 'medium').length;
                  const low = (issues || []).filter(x => x.severity === 'low').length;
                  return (
                    <div className="report-section">
                      <div className="report-section-title">Code Stats</div>
                      <div className="report-stats-row">
                        <div className="report-stat"><span className="report-stat-val">{lines.length}</span><span className="report-stat-lbl">lines</span></div>
                        <div className="report-stat"><span className="report-stat-val">{chars}</span><span className="report-stat-lbl">chars</span></div>
                        <div className="report-stat"><span className="report-stat-val">{(issues || []).length}</span><span className="report-stat-lbl">issues</span></div>
                        {analyzeTime && <div className="report-stat"><span className="report-stat-val">{(analyzeTime / 1000).toFixed(1)}s</span><span className="report-stat-lbl">total time</span></div>}
                      </div>
                      {(issues || []).length > 0 && (
                        <div className="report-sev-bar">
                          {high > 0 && <span className="sev-chip high">{high} HIGH</span>}
                          {med > 0 && <span className="sev-chip medium">{med} MED</span>}
                          {low > 0 && <span className="sev-chip low">{low} LOW</span>}
                        </div>
                      )}
                    </div>
                  );
                })()}

                {pipelineSteps.length > 0 && (
                  <PipelineSummary pipelineSteps={pipelineSteps} promptInlineOpen={promptInlineOpen} setPromptInlineOpen={setPromptInlineOpen} />
                )}

                {issues !== null && (issues.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">✓</div>
                    <div className="empty-text">No concurrency issues detected.</div>
                  </div>
                ) : (
                  <div className="report-section">
                    <div className="report-section-title">
                      {issues.length} Issue{issues.length > 1 ? 's' : ''} Found
                    </div>
                    {issues.map((issue, i) => <IssueCard key={i} issue={issue} />)}
                  </div>
                ))}

                {issues !== null && explanation && (
                  <div className="report-section">
                    <div className="report-section-title">AI Explanation</div>
                    <div className="explain-text" dangerouslySetInnerHTML={{ __html: explanation }} />
                  </div>
                )}

                {docsUsed.length > 0 && (
                  <div className="report-section">
                    <div className="report-section-title">Knowledge Base References</div>
                    <div className="report-docs">
                      {docsUsed.map((d, i) => {
                        const ctxMatch = d.title?.match(/\[([^\]]+)\]\s*$/);
                        const ctx = ctxMatch ? ctxMatch[1] : null;
                        const title = d.title?.replace(/\s*\[.*?\]\s*$/, '').trim() || d.id;
                        return (
                          <div key={i} className="report-doc-row">
                            <span className="report-doc-cat">{d.category || 'ref'}</span>
                            <span className="report-doc-title">{title}</span>
                            {ctx && <span className="report-doc-ctx-badge">{ctx}</span>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
