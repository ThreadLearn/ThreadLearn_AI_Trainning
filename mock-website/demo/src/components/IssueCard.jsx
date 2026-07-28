import { useState } from 'react';
import { AlertTriangle, Check, CheckCheck } from 'lucide-react';
import DiffView from './DiffView';
import { useI18n } from '../i18n.jsx';

function extractFixCode(fix) {
  const match = fix.match(/```(?:javascript|js)?\n?([\s\S]*?)```/);
  if (match) return { code: match[1].trim(), isCodeBlock: true };
  return { code: fix, isCodeBlock: false };
}

export default function IssueCard({ issue, index, originalCode, onResolve }) {
  const { t } = useI18n();
  const patternId = issue.pattern_id || issue.pattern || 'unknown';
  const { code, isCodeBlock } = extractFixCode(issue.fix || '');
  const [resolved, setResolved] = useState(false);
  const canDiff = isCodeBlock && !!originalCode;
  const isUnchanged = canDiff && originalCode.trim() === code.trim();

  function handleResolve() {
    onResolve?.(code);
    setResolved(true);
  }

  return (
    <div className={`issue-card ${issue.severity}`}>
      <div className="issue-top">
        <span className={`sev-pill ${issue.severity}`}>{issue.severity}</span>
        <span className="issue-pattern-id">{patternId}</span>
        <span className="issue-line">line {issue.line_range}</span>
        {typeof index === 'number' && <span className="issue-index">#{index + 1}</span>}
      </div>

      <div className="issue-desc-row">
        <AlertTriangle size={13} className="issue-warn-icon" />
        <span className="issue-desc">{issue.description}</span>
      </div>

      <div className="issue-fix-header">
        <span className="issue-fix-label">{isCodeBlock ? t.suggestedRewrite : t.fix}</span>
        {isUnchanged && <span className="issue-badge-muted">{t.noChangesSuggested}</span>}
        {isCodeBlock && onResolve && !isUnchanged && (
          <button type="button" className={`resolve-btn ${resolved ? 'applied' : ''}`} disabled={resolved} onClick={handleResolve}>
            {resolved ? <CheckCheck size={12} /> : <Check size={12} />}
            {resolved ? t.applied : t.resolve}
          </button>
        )}
      </div>

      {canDiff ? (
        <DiffView oldCode={originalCode} newCode={code} />
      ) : isCodeBlock ? (
        <pre className="issue-fix-code"><code>{code}</code></pre>
      ) : (
        <div className="issue-fix">{code}</div>
      )}
    </div>
  );
}
