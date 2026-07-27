import { useState } from 'react';
import { ChevronDown, Clock } from 'lucide-react';
import AnalysisResult, { severityCounts } from './AnalysisResult';
import { useI18n } from '../i18n.jsx';

function HistoryRow({ log, defaultOpen }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(defaultOpen);
  const { high, medium, low } = severityCounts(log.issues || []);

  return (
    <article className="history-row">
      <button type="button" className="history-row-toggle" onClick={() => setOpen((o) => !o)}>
        <ChevronDown size={16} className={`history-chevron ${open ? '' : 'closed'}`} />
        <div className="history-row-body">
          <div className="history-row-top">
            <span className="history-row-title">{log.language || 'code'} analysis</span>
            <span className="history-row-time"><Clock size={12} /> {new Date(log.createdAt).toLocaleString()}</span>
          </div>
          <div className="history-row-tags">
            {high > 0 && <span className="sev-chip high">{high} HIGH</span>}
            {medium > 0 && <span className="sev-chip medium">{medium} MED</span>}
            {low > 0 && <span className="sev-chip low">{low} LOW</span>}
            {(log.issues?.length || 0) === 0 && <span className="history-no-issues">{t.noIssues}</span>}
          </div>
        </div>
      </button>

      {open && (
        <AnalysisResult view={{
          issues: log.issues || [],
          docsUsed: log.docsUsed || [],
          cached: log.cached,
          explanation: log.explanation,
          analyzeTimeMs: log.analyzeTimeMs,
          code: log.inputCode || '',
        }} />
      )}
    </article>
  );
}

export default function HistoryList({ history }) {
  return (
    <div className="history-list">
      {history.map((log, i) => <HistoryRow key={log._id} log={log} defaultOpen={i === 0} />)}
    </div>
  );
}
