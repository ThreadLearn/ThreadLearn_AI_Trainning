import { useState, useEffect, useCallback } from 'react';
import { MOCK_CASES } from './mockCases';
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

function PipelineProgress({ steps }) {
  if (!steps || steps.length === 0) return null;
  return (
    <div className="pipeline-progress">
      {steps.map((s, i) => {
        const meta = STAGE_META[s.stage] || { icon: '●', label: s.stage };
        const isDone = s.status === 'done';
        const isRunning = s.status === 'running';
        return (
          <div key={i} className={`pipeline-step ${s.status}`}>
            <div className="pipeline-step-icon">
              {isRunning ? <span className="step-spinner" /> : meta.icon}
            </div>
            <div className="pipeline-step-body">
              <div className="pipeline-step-name">{meta.label}</div>
              <div className="pipeline-step-label">{s.label}</div>
              {s.stage === 'race_detector' && s.found && s.found.length > 0 && (
                <div className="pipeline-step-badges">
                  {s.found.map((p) => (
                    <span key={p} className="race-badge">{p.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              )}
            </div>
            <div className={`pipeline-step-dot ${s.status}`} />
          </div>
        );
      })}
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState('mock');
  const [caseIdx, setCaseIdx] = useState(0);
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

  const mockCases   = MOCK_CASES.filter(c => !c.liveOnly);
  const liveSamples = MOCK_CASES.filter(c => c.liveOnly);

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
  }

  function handleModeChange(m) {
    setMode(m);
    reset();
  }

  function handleCaseChange(idx) {
    setCaseIdx(idx);
    reset();
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

    if (mode === 'mock') {
      setLoadingText('Analyzing concurrency patterns…');
      await new Promise(r => setTimeout(r, 600 + Math.random() * 800));
      const resp = mockCases[caseIdx].response;
      setIssues(resp.issues);
      setHlMap(buildHlMap(resp.issues));
      setDocsUsed(resp.docs_used);
      setExplanation(resp.explanation);
      setCached(false);
      setLoading(false);
      return;
    }

    const code = liveCode.trim();
    if (!code) {
      setError('Code is empty. Paste some JavaScript to analyze.');
      setLoading(false);
      return;
    }

    setPipelineSteps([]);

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

  const currentCode = mode === 'mock' ? (mockCases[caseIdx]?.code || '') : liveCode;

  return (
    <div className="app">

      <header className="topbar">
        <div className="logo">
          <div className="logo-dot" />
          ThreadLearn
        </div>
        <div className="sep" />

        <div className="mode-tabs">
          <button className={`mode-tab${mode === 'mock' ? ' active' : ''}`} onClick={() => handleModeChange('mock')}>Mock</button>
          <button className={`mode-tab${mode === 'live' ? ' active' : ''}`} onClick={() => handleModeChange('live')}>Live AI2</button>
        </div>
        <div className="sep" />

        {mode === 'mock' && (
          <>
            <span className="case-label">Test case:</span>
            <select className="case-select" value={caseIdx} onChange={e => handleCaseChange(Number(e.target.value))}>
              {mockCases.map((c, i) => <option key={i} value={i}>{c.title}</option>)}
            </select>
          </>
        )}

        {mode === 'live' && (
          <>
            <span className="case-label">Sample code:</span>
            <select className="case-select" value={liveSampleIdx} onChange={e => handleLiveSampleChange(Number(e.target.value))}>
              <option value={-1}>— paste your own code —</option>
              {liveSamples.map((c, i) => <option key={i} value={i}>{c.title}</option>)}
            </select>
          </>
        )}

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

      <div className="main">
        <div className="editor-pane">
          <div className="pane-header">
            <span className="pane-title">Editor</span>
            <span className="lang-badge">JavaScript</span>
            {cached && <span className="cached-badge" style={{ marginLeft: 'auto' }}>⚡ cached</span>}
          </div>
          <div className="editor-scroll" style={{ position: 'relative' }}>
            {mode === 'mock'
              ? <CodeDisplay code={currentCode} hlMap={hlMap} />
              : <LiveEditor code={liveCode} onChange={setLiveCode} hlMap={hlMap} />
            }
            {loading && (
              <div className="loading-overlay visible">
                {mode === 'live' && pipelineSteps.length > 0
                  ? <PipelineProgress steps={pipelineSteps} />
                  : <><div className="spinner" /><div className="loading-text">{loadingText}</div></>
                }
              </div>
            )}
          </div>
        </div>

        <div className="issues-pane">
          <div className="pane-header">
            <span className="pane-title">Issues</span>
            <span className={`count-badge ${issues && issues.length > 0 ? 'has' : 'none'}`}>
              {issues ? issues.length : 0}
            </span>
          </div>
          {error && <div className="error-banner visible">{error}</div>}
          <div className="issues-scroll">
            {issues === null ? (
              <div className="empty-state">
                <div className="empty-icon">⏳</div>
                <div className="empty-text">Click <strong>Analyze</strong> to detect<br />concurrency bugs.</div>
              </div>
            ) : issues.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">✓</div>
                <div className="empty-text">No concurrency issues detected.</div>
              </div>
            ) : (
              issues.map((issue, i) => <IssueCard key={i} issue={issue} />)
            )}
          </div>
        </div>
      </div>

      <div className="explain-pane">
        <div className="explain-scroll">
          <div className="explain-label">
            AI Explanation
            <span className="rag-tag">RAG</span>
            <span className={`mode-tag ${mode}`}>{mode}</span>
          </div>
          {explanation ? (
            <div className="explain-text" dangerouslySetInnerHTML={{ __html: explanation }} />
          ) : (
            <div className="explain-text" style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>
              Run analysis to see explanation and knowledge-base references.
            </div>
          )}
          {docsUsed.length > 0 && (
            <div className="docs-used">
              {docsUsed.map((d, i) => <span key={i} className="doc-chip">{d.title || d.id}</span>)}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
