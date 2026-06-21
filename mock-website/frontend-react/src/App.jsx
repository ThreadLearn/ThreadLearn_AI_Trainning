import { useState, useEffect, useCallback, useRef } from 'react';
import { LIVE_SAMPLES } from './mockCases';
import './App.css';

const BACKEND_URL = 'http://localhost:3001';

const KW  = new Set(['async','await','function','const','let','var','return','if','else','for','new','this','class','constructor','try','catch','throw','of','in','require']);
const FNS = new Set(['console','setTimeout','Promise','app','db','res','req','connection','fs','emailService','cache','payment','zlib']);

function syntaxHL(line) {
  if (!line) return ' ';

  // Comment line — escape and wrap whole line
  if (/^\s*\/\//.test(line)) {
    const esc = line.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    return `<span class="cmt">${esc}</span>`;
  }

  // Tokenize: strings, then word tokens, then rest
  const tokens = [];
  let i = 0;
  while (i < line.length) {
    // String literals: "...", '...', `...`
    const q = line[i];
    if (q === '"' || q === "'" || q === '`') {
      let end = i + 1;
      while (end < line.length && line[end] !== q) {
        if (line[end] === '\\') end++;
        end++;
      }
      end++;
      const raw = line.slice(i, end);
      const esc = raw.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      tokens.push(`<span class="str">${esc}</span>`);
      i = end;
      continue;
    }
    // Word token (identifier / keyword)
    if (/[a-zA-Z_$]/.test(line[i])) {
      let end = i;
      while (end < line.length && /[\w$]/.test(line[end])) end++;
      const word = line.slice(i, end);
      if (KW.has(word))  tokens.push(`<span class="kw">${word}</span>`);
      else if (FNS.has(word)) tokens.push(`<span class="fn">${word}</span>`);
      else tokens.push(word);
      i = end;
      continue;
    }
    // Number
    if (/[0-9]/.test(line[i])) {
      let end = i;
      while (end < line.length && /[\d.]/.test(line[end])) end++;
      tokens.push(`<span class="num">${line.slice(i, end)}</span>`);
      i = end;
      continue;
    }
    // Everything else — escape HTML special chars
    const ch = line[i];
    if (ch === '&') tokens.push('&amp;');
    else if (ch === '<') tokens.push('&lt;');
    else if (ch === '>') tokens.push('&gt;');
    else tokens.push(ch);
    i++;
  }

  return tokens.join('');
}

function buildHlMap(issues) {
  const map = {};
  (issues || []).forEach(issue => {
    const cls = issue.severity === 'high' ? 'hl-high'
              : issue.severity === 'medium' ? 'hl-med' : 'hl-low';
    const range = String(issue.line_range);
    if (range.includes('-')) {
      const [a, b] = range.split('-').map(Number);
      for (let i = a; i <= b; i++) map[i] = cls;
    } else {
      map[parseInt(range)] = cls;
    }
  });
  return map;
}

function CodeDisplay({ code, hlMap }) {
  const lines = code.split('\n');
  return (
    <div className="editor-inner">
      <div className="line-numbers">
        {lines.map((_, i) => {
          const ln = i + 1;
          const cls = hlMap[ln];
          const dotCls = cls === 'hl-high' ? 'h' : cls === 'hl-med' ? 'm' : cls === 'hl-low' ? 'l' : '';
          const numCls = cls === 'hl-high' ? 'hl-h' : cls === 'hl-med' ? 'hl-m' : cls === 'hl-low' ? 'hl-l' : '';
          return (
            <div key={i} className={`line-num ${numCls}`}>
              {dotCls && <span className={`gutter-dot ${dotCls}`} />}
              {ln}
            </div>
          );
        })}
      </div>
      <div className="code-area">
        {lines.map((line, i) => {
          const ln = i + 1;
          const hlCls = hlMap[ln];
          const lineCls = hlCls === 'hl-high' ? 'hl-high'
                        : hlCls === 'hl-med'  ? 'hl-med'
                        : hlCls === 'hl-low'  ? 'hl-low' : '';
          return (
            <span
              key={i}
              className={`code-line${lineCls ? ` ${lineCls}` : ''}`}
              dangerouslySetInnerHTML={{ __html: syntaxHL(line) || ' ' }}
            />
          );
        })}
      </div>
    </div>
  );
}

function LiveEditor({ code, onChange }) {
  const lines = code.split('\n');
  const minLines = Math.max(lines.length, 20);

  function handleKeyDown(e) {
    if (e.key === 'Tab') {
      e.preventDefault();
      const ta = e.target;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const next = code.substring(0, start) + '  ' + code.substring(end);
      onChange(next);
      // restore cursor after React re-render
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = start + 2;
      });
    }
  }

  return (
    <div className="editor-inner live-editor-inner">
      {/* Line numbers */}
      <div className="line-numbers live-line-numbers">
        {Array.from({ length: minLines }, (_, i) => (
          <div key={i} className="line-num">{i + 1}</div>
        ))}
      </div>

      {/* Highlight layer (visual only) */}
      <div className="live-hl-layer" aria-hidden="true">
        {lines.map((line, i) => (
          <span
            key={i}
            className="code-line"
            dangerouslySetInnerHTML={{ __html: syntaxHL(line) || ' ' }}
          />
        ))}
        {/* padding lines so textarea and overlay same height */}
        {lines.length < minLines && Array.from({ length: minLines - lines.length }, (_, i) => (
          <span key={`pad-${i}`} className="code-line">{' '}</span>
        ))}
      </div>

      {/* Transparent textarea on top for input */}
      <textarea
        className="live-textarea-overlay"
        value={code}
        onChange={e => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        spellCheck={false}
        autoCorrect="off"
        autoCapitalize="off"
      />
    </div>
  );
}

function IssueCard({ issue }) {
  const patternId = issue.pattern_id || issue.pattern || 'unknown';
  const isRewrite = typeof issue.fix === 'string' && issue.fix.includes('```');
  const fixLabel = isRewrite ? 'Suggested Rewrite' : 'Fix';

  // Extract code from markdown code block if present
  let fixContent;
  if (isRewrite) {
    const match = issue.fix.match(/```(?:javascript|js)?\n?([\s\S]*?)```/);
    const code = match ? match[1].trim() : issue.fix.replace(/```(?:javascript|js)?/g, '').trim();
    fixContent = <pre className="issue-fix-code"><code>{code}</code></pre>;
  } else {
    fixContent = <div className="issue-fix">{issue.fix}</div>;
  }

  return (
    <div className={`issue-card ${issue.severity}`}>
      <div className="issue-top">
        <span className={`sev-pill ${issue.severity}`}>{issue.severity}</span>
        <span className="issue-pattern-id">{patternId}</span>
        <span className="issue-line">line {issue.line_range}</span>
      </div>
      <div className="issue-desc">{issue.description}</div>
      <div className="issue-fix-label">{fixLabel}</div>
      {fixContent}
    </div>
  );
}

const STAGE_META = {
  race_detector: { icon: '⚡', label: 'Race Detector' },
  ast:           { icon: '🌲', label: 'AST Parser' },
  bm25:          { icon: '🔍', label: 'BM25 Search' },
  prompt:        { icon: '📝', label: 'Prompt Builder' },
  llm:           { icon: '🤖', label: 'LLM Inference' },
};

const RACE_DESC = {
  closure_loop_var:    'closure captures loop var by reference',
  double_callback:     'callback called twice on error path',
  sequential_awaits:   'independent awaits run sequentially',
  unhandled_rejection: 'async function missing try/catch',
  unbounded_promise_all: 'Promise.all fires all items at once',
  missing_error_handler: 'stream missing error handler',
};

function ElapsedTimer({ active }) {
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    if (!active) return;
    setSecs(0);
    const id = setInterval(() => setSecs(s => s + 1), 1000);
    return () => clearInterval(id);
  }, [active]);
  if (!active) return null;
  return <span className="elapsed-timer">{secs}s</span>;
}

function StepDetail({ s }) {
  if (s.stage === 'race_detector' && s.status === 'done') {
    if (!s.found || s.found.length === 0)
      return <div className="step-detail step-detail-ok">No patterns matched</div>;
    return (
      <div className="pipeline-step-badges">
        {s.found.map(p => (
          <span key={p} className="race-badge" title={RACE_DESC[p] || p}>
            {p.replace(/_/g, ' ')}
          </span>
        ))}
      </div>
    );
  }
  if (s.stage === 'ast' && s.keywords) {
    const chips = s.keywords.trim().split(/\s+/).slice(0, 8);
    return (
      <div className="pipeline-step-badges">
        {chips.map(k => <span key={k} className="kw-chip">{k}</span>)}
      </div>
    );
  }
  if (s.stage === 'bm25' && s.docs && s.docs.length > 0) {
    return (
      <ul className="step-doc-list">
        {s.docs.map((d, i) => {
          const ctxMatch = d.match(/\[([^\]]+)\]\s*$/);
          const ctx   = ctxMatch ? ctxMatch[1] : null;
          const title = d.replace(/\s*\[.*?\]\s*$/, '').trim();
          return (
            <li key={i} title={d}>
              {title}{ctx && <span className="step-doc-ctx">[{ctx}]</span>}
            </li>
          );
        })}
      </ul>
    );
  }
  if (s.stage === 'prompt' && s.chars) {
    const tokens = Math.round(s.chars / 4);
    return <div className="step-detail">~{tokens} tokens · {s.chars} chars</div>;
  }
  return null;
}

function PipelineProgress({ steps }) {
  if (!steps || steps.length === 0) return null;
  const llmStep = steps.find(s => s.stage === 'llm');
  const llmRunning = llmStep?.status === 'running';
  return (
    <div className="pipeline-progress">
      {steps.map((s, i) => {
        const meta = STAGE_META[s.stage] || { icon: '●', label: s.stage };
        const isRunning = s.status === 'running';
        return (
          <div key={i} className={`pipeline-step ${s.status}`}>
            <div className="pipeline-step-icon">
              {isRunning ? <span className="step-spinner" /> : meta.icon}
            </div>
            <div className="pipeline-step-body">
              <div className="pipeline-step-name">
                {meta.label}
                {s.stage === 'llm' && <ElapsedTimer active={llmRunning} />}
              </div>
              <div className="pipeline-step-label">{s.label}</div>
              <StepDetail s={s} />
            </div>
            <div className={`pipeline-step-dot ${s.status}`} />
          </div>
        );
      })}
    </div>
  );
}

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
      const next = Math.min(Math.max(startW.current + delta, 280), 720);
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
                next[existing] = evtData;
                return next;
              }
              return [...prev, evtData];
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
            {loading && (
              <div className="loading-overlay visible">
                {pipelineSteps.length > 0
                  ? <PipelineProgress steps={pipelineSteps} />
                  : <><div className="spinner" /><div className="loading-text">{loadingText}</div></>
                }
              </div>
            )}
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
            {issues === null ? (
              <div className="empty-state">
                <div className="empty-icon">⏳</div>
                <div className="empty-text">Click <strong>Analyze</strong> to detect<br />concurrency bugs.</div>
              </div>
            ) : (
              <>
                {/* ── Code Stats ── */}
                {(() => {
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
                  <div className="report-section">
                    <div className="report-section-title">Pipeline Summary</div>
                    <div className="report-pipeline-summary">
                      {pipelineSteps.map((s, i) => {
                        const meta = STAGE_META[s.stage] || { icon: '●', label: s.stage };
                        let detail = null;
                        let subDetail = null;
                        if (s.stage === 'race_detector') {
                          detail = s.found?.length > 0
                            ? `${s.found.length} pattern(s) matched`
                            : 'no patterns matched';
                          if (s.found?.length > 0)
                            subDetail = s.found.map(p => p.replace(/_/g,' ')).join(' · ');
                        } else if (s.stage === 'ast' && s.keywords) {
                          const kws = s.keywords.trim().split(/\s+/);
                          detail = `${kws.length} keyword(s) extracted`;
                          subDetail = kws.slice(0,6).join(', ') + (kws.length > 6 ? '…' : '');
                        } else if (s.stage === 'bm25' && s.docs?.length > 0) {
                          detail = `${s.docs.length} doc(s) retrieved`;
                          subDetail = [...new Set(s.docs.map(d => d.replace(/\s*\[.*?\]\s*$/,'').trim()))].join(', ');
                        } else if (s.stage === 'prompt' && s.chars) {
                          detail = `~${Math.round(s.chars/4)} tokens · ${s.chars} chars`;
                        } else if (s.stage === 'llm' && s.status === 'done') {
                          detail = s.label;
                        }
                        return (
                          <div key={i} className="report-pipeline-row-block">
                            <div className="report-pipeline-row">
                              <span className="report-pipeline-icon">{meta.icon}</span>
                              <span className="report-pipeline-name">{meta.label}</span>
                              {detail && <span className="report-pipeline-detail">{detail}</span>}
                            </div>
                            {subDetail && <div className="report-pipeline-sub">{subDetail}</div>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* ── Issues ── */}
                {issues.length === 0 ? (
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
                )}

                {/* ── AI Explanation ── */}
                {explanation && (
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
