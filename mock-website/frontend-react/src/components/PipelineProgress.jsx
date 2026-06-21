import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

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

function ElapsedTimer({ s }) {
  const [now, setNow] = useState(Date.now());
  const active = s.status === 'running';

  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => setNow(Date.now()), 100);
    return () => clearInterval(id);
  }, [active]);

  if (!s._startTime) return null;
  const end = s._endTime || now;
  const elapsed = Math.max(0, end - s._startTime);
  const secs = (elapsed / 1000).toFixed(1);

  return <span className="elapsed-timer" style={{ marginLeft: 8, fontSize: '0.85em', color: 'var(--text-dim)' }}>{secs}s</span>;
}

function StepDetail({ s, promptInlineOpen, setPromptInlineOpen }) {
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
    const chips = s.keywords.trim().split(/\s+/);
    return (
      <div className="pipeline-step-badges">
        {chips.map(k => <span key={k} className="kw-chip">{k}</span>)}
      </div>
    );
  }
  if (s.stage === 'bm25' && s.docs && s.docs.length > 0) {
    return (
      <ul className="step-doc-list">
        {s.docs.map((dObj, i) => {
          const d = typeof dObj === 'string' ? dObj : dObj.title;
          const ctxMatch = d.match(/\[([^\]]+)\]\s*$/);
          const ctx   = ctxMatch ? ctxMatch[1] : null;
          const title = d.replace(/\s*\[.*?\]\s*$/, '').trim();
          const score = typeof dObj === 'string' ? null : dObj.score;
          return (
            <li key={i} title={d}>
              {score !== null && <span className="score-badge" style={{padding:0, border: 'none', marginRight: 2}}>({score.toFixed(2)})</span>}
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

export function PipelineProgress({ steps, promptInlineOpen, setPromptInlineOpen }) {
  if (!steps || steps.length === 0) return null;
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
                <ElapsedTimer s={s} />
              </div>
              <div className="pipeline-step-label">{s.label}</div>
              <StepDetail s={s} promptInlineOpen={promptInlineOpen} setPromptInlineOpen={setPromptInlineOpen} />
            </div>
            <div className={`pipeline-step-dot ${s.status}`} />
          </div>
        );
      })}
    </div>
  );
}

export function PipelineSummary({ pipelineSteps, promptInlineOpen, setPromptInlineOpen }) {
  if (!pipelineSteps || pipelineSteps.length === 0) return null;
  return (
    <div className="report-section">
      <div className="report-section-title">Pipeline Summary</div>
      <div className="report-pipeline-summary">
        {pipelineSteps.map((s, i) => {
          const meta = STAGE_META[s.stage] || { icon: '●', label: s.stage };
          let detail = null;
          let subDetail = null;
          if (s.status === 'running') {
            detail = s.label || 'Processing...';
          } else if (s.stage === 'race_detector') {
            detail = s.found?.length > 0
              ? `${s.found.length} pattern(s) matched`
              : 'no patterns matched';
            if (s.found?.length > 0)
              subDetail = s.found.map(p => p.replace(/_/g,' ')).join(' · ');
          } else if (s.stage === 'ast' && s.keywords) {
            const kws = s.keywords.trim().split(/\s+/);
            detail = `${kws.length} keyword(s) extracted`;
            subDetail = (
              <>
                <ul className="process-flow-list">
                  {(s.process_flow || []).map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
                <div style={{ marginTop: 4, fontStyle: 'italic', color: 'var(--text-mid)', wordBreak: 'break-all' }}>
                  {kws.join(', ')}
                </div>
              </>
            );
          } else if (s.stage === 'bm25' && s.docs?.length > 0) {
            detail = `${s.docs.length} doc(s) retrieved`;
            subDetail = (
              <ul className="process-flow-list">
                {s.docs.map((d, idx) => {
                  const title = typeof d === 'string' ? d : d.title;
                  const score = typeof d === 'string' ? null : d.score;
                  return (
                    <li key={idx}>
                      {score !== null && <span className="score-badge">[{score.toFixed(3)}]</span>}
                      {title}
                    </li>
                  );
                })}
              </ul>
            );
          } else if (s.stage === 'prompt' && s.chars) {
            detail = `~${Math.round(s.chars/4)} tokens · ${s.chars} chars`;
            subDetail = s.full_prompt ? (
              <div className="prompt-inline-wrapper">
                <button className="view-prompt-btn" onClick={() => setPromptInlineOpen(!promptInlineOpen)}>
                  {promptInlineOpen ? '▲ Hide Full Prompt' : '👁 View Full Prompt'}
                </button>
                {promptInlineOpen && (
                  <div className="prompt-inline-body">
                    <ReactMarkdown
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              {...props}
                              children={String(children).replace(/\n$/, '')}
                              style={vscDarkPlus}
                              language={match[1]}
                              PreTag="div"
                            />
                          ) : (
                            <code {...props} className={className}>
                              {children}
                            </code>
                          )
                        }
                      }}
                    >
                      {s.full_prompt}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            ) : null;
          } else if (s.stage === 'llm') {
            detail = s.label;
          }
          return (
            <div key={i} className="report-pipeline-row-block">
              <div className="report-pipeline-row">
                <span className="report-pipeline-icon">
                  {s.status === 'running' ? <span className="step-spinner" style={{width: 14, height: 14, borderWidth: 2}} /> : meta.icon}
                </span>
                <span className="report-pipeline-name">
                  {meta.label}
                  <ElapsedTimer s={s} />
                </span>
                {detail && <span className="report-pipeline-detail">{detail}</span>}
              </div>
              {subDetail && <div className="report-pipeline-sub">{subDetail}</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
