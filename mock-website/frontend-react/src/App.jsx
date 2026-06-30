import { useState, useEffect, useCallback, useRef } from 'react';
import { LIVE_SAMPLES } from './mockCases';
import './App.css';

import LiveEditor, { buildHlMap } from './components/LiveEditor';
import IssueCard from './components/IssueCard';
import { PipelineProgress, PipelineSummary } from './components/PipelineProgress';

const BACKEND_URL = 'http://localhost:3001';

const STAGE_META = {
  race_detector: { icon: '⚡', label: 'Race Detector' },
  ast:           { icon: '🌲', label: 'AST Parser' },
  bm25:          { icon: '🔍', label: 'BM25 Search' },
  prompt:        { icon: '📝', label: 'Prompt Builder' },
  llm:           { icon: '🤖', label: 'LLM Inference' },
};

export default function App() {
  const [liveCode, setLiveCode] = useState('// Paste your JavaScript code here\n// then click Analyze\n');
  const [liveSampleIdx, setLiveSampleIdx] = useState(-1);

  const [issues, setIssues] = useState(null);
  const [docsUsed, setDocsUsed] = useState([]);
  const [explanation, setExplanation] = useState('');
  const [hlMap, setHlMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('Analyzing…');
  const [error, setError] = useState('');
  const [cached, setCached] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState([]);
  const [promptInlineOpen, setPromptInlineOpen] = useState(false);
  const [ai2Status, setAi2Status] = useState({ state: 'checking', label: 'checking…' });
  const [analyzeTime, setAnalyzeTime] = useState(null); // ms
  const analyzeStart = useRef(null);

  const liveSamples = LIVE_SAMPLES;

  // ── Resizable split ──
  const [issuesPaneWidth, setIssuesPaneWidth] = useState(440);
  const dragging = useRef(false);
  const startX   = useRef(0);
  const startW   = useRef(440);

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
      const delta = startX.current - e.clientX; // drag left = wider
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

  const checkHealth = useCallback(async () => {
    try {
      const r = await fetch(`${BACKEND_URL}/health`, { signal: AbortSignal.timeout(3000) });
      const d = await r.json();
      if (d.ai2_server === 'ok') {
        setAi2Status({ state: 'online', label: `AI2 online · ${d.retriever_docs} docs` });
      } else {
        setAi2Status({ state: 'offline', label: 'AI2 degraded' });
      }
    } catch {
      setAi2Status({ state: 'offline', label: 'AI2 offline' });
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 15000);
    return () => clearInterval(id);
  }, [checkHealth]);

  function reset() {
    setIssues(null);
    setDocsUsed([]);
    setExplanation('');
    setHlMap({});
    setError('');
    setCached(false);
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
    setLoading(true);
    setError('');
    setIssues(null);
    setHlMap({});

    const code = liveCode.trim();
    if (!code) {
      setError('Code is empty. Paste some JavaScript to analyze.');
      setLoading(false);
      return;
    }

    setPipelineSteps([]);
    analyzeStart.current = Date.now();

    try {
      setLoadingText('Connecting to AI2 server…');

      const r = await fetch(`${BACKEND_URL}/api/analyze/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language: 'javascript' }),
      });

      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        setError(data.message || data.detail || `Error ${r.status}`);
        setLoading(false);
        return;
      }

      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        // Parse SSE chunks — split on double newline
        const parts = buf.split('\n\n');
        buf = parts.pop(); // keep incomplete chunk

        for (const part of parts) {
          const eventMatch = part.match(/^event:\s*(.+)$/m);
          const dataMatch  = part.match(/^data:\s*(.+)$/m);
          if (!eventMatch || !dataMatch) continue;

          const evtType = eventMatch[1].trim();
          let evtData;
          try { evtData = JSON.parse(dataMatch[1]); } catch { continue; }

          if (evtType === 'step') {
            setLoadingText(evtData.label || evtData.stage);
            setPipelineSteps(prev => {
              const existing = prev.findIndex(s => s.stage === evtData.stage);
              if (existing >= 0) {
                const next = [...prev];
                const oldStep = next[existing];
                next[existing] = {
                  ...oldStep,
                  ...evtData,
                  _endTime: evtData.status === 'done' && oldStep.status === 'running' ? Date.now() : oldStep._endTime
                };
                return next;
              }
              return [...prev, { ...evtData, _startTime: Date.now() }];
            });
          } else if (evtType === 'result') {
            const issueList = evtData.issues || [];
            setIssues(issueList);
            setHlMap(buildHlMap(issueList));
            setDocsUsed(evtData.docs_used || []);
            setCached(!!evtData.cached);
            setAnalyzeTime(Date.now() - (analyzeStart.current || Date.now()));
            const docs = evtData.docs_used || [];
            setExplanation(
              issueList.length > 0
                ? `AI2 detected <strong>${issueList.length} issue${issueList.length > 1 ? 's' : ''}</strong> using RAG retrieval from ${docs.length} knowledge-base document${docs.length !== 1 ? 's' : ''}. Review each issue card for details and fixes.`
                : 'No concurrency issues detected in this code.'
            );
          } else if (evtType === 'error') {
            setError(evtData.message || 'Unknown error');
          }
        }
      }
    } catch (err) {
      setError(
        `Cannot reach backend at ${BACKEND_URL}.\nMake sure Express server is running:\n  cd mock-website/backend && node server.js`
      );
    }

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
          <button className="mode-tab active">Live AI2</button>
        </div>
        <div className="sep" />

        <>
          <span className="case-label">Sample code:</span>
          <select className="case-select" value={liveSampleIdx} onChange={e => handleLiveSampleChange(Number(e.target.value))}>
            <option value={-1}>— paste your own code —</option>
            {liveSamples.map((c, i) => <option key={i} value={i}>{c.title}</option>)}
          </select>
        </>

        <div className="topbar-right">
          <div className="ai2-indicator">
            <div className={`ai2-dot ${ai2Status.state}`} />
            <span>{ai2Status.label}</span>
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
            {cached && <span className="cached-badge" style={{ marginLeft: 'auto' }}>⚡ cached</span>}
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
            <span className="rag-tag" style={{marginLeft:'auto'}}>RAG</span>
            <span className="mode-tag live">LIVE</span>
          </div>
          {error && <div className="error-banner visible">{error}</div>}
          <div className="issues-scroll">
            {issues === null && pipelineSteps.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">⏳</div>
                <div className="empty-text">Click <strong>Analyze</strong> to detect<br />concurrency bugs.</div>
              </div>
            ) : (
              <>
                {/* ── Code Stats ── */}
                {issues !== null && (() => {
                  const lines = currentCode.trim().split('\n');
                  const chars = currentCode.length;
                  const high  = (issues||[]).filter(x=>x.severity==='high').length;
                  const med   = (issues||[]).filter(x=>x.severity==='medium').length;
                  const low   = (issues||[]).filter(x=>x.severity==='low').length;
                  return (
                    <div className="report-section">
                      <div className="report-section-title">Code Stats</div>
                      <div className="report-stats-row">
                        <div className="report-stat"><span className="report-stat-val">{lines.length}</span><span className="report-stat-lbl">lines</span></div>
                        <div className="report-stat"><span className="report-stat-val">{chars}</span><span className="report-stat-lbl">chars</span></div>
                        <div className="report-stat"><span className="report-stat-val">{(issues||[]).length}</span><span className="report-stat-lbl">issues</span></div>
                        {analyzeTime && <div className="report-stat"><span className="report-stat-val">{(analyzeTime/1000).toFixed(1)}s</span><span className="report-stat-lbl">total time</span></div>}
                      </div>
                      {(issues||[]).length > 0 && (
                        <div className="report-sev-bar">
                          {high > 0 && <span className="sev-chip high">{high} HIGH</span>}
                          {med  > 0 && <span className="sev-chip medium">{med} MED</span>}
                          {low  > 0 && <span className="sev-chip low">{low} LOW</span>}
                        </div>
                      )}
                    </div>
                  );
                })()}

                 {/* ── Pipeline Summary ── */}
                {pipelineSteps.length > 0 && (
                  <PipelineSummary pipelineSteps={pipelineSteps} promptInlineOpen={promptInlineOpen} setPromptInlineOpen={setPromptInlineOpen} />
                )}
                {/* ── Issues ── */}
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

                {/* ── AI Explanation ── */}
                {issues !== null && explanation && (
                  <div className="report-section">
                    <div className="report-section-title">AI Explanation</div>
                    <div className="explain-text" dangerouslySetInnerHTML={{ __html: explanation }} />
                  </div>
                )}

                {/* ── Knowledge Base Used ── */}
                {docsUsed.length > 0 && (
                  <div className="report-section">
                    <div className="report-section-title">Knowledge Base References</div>
                    <div className="report-docs">
                      {docsUsed.map((d, i) => {
                        const ctxMatch = d.title?.match(/\[([^\]]+)\]\s*$/);
                        const ctx   = ctxMatch ? ctxMatch[1] : null;
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
