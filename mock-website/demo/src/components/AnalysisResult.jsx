import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Database, Zap, CheckCircle2 } from 'lucide-react';
import IssueCard from './IssueCard';
import { useI18n } from '../i18n.jsx';

export function severityCounts(issues) {
  return {
    high: issues.filter((i) => i.severity === 'high').length,
    medium: issues.filter((i) => i.severity === 'medium').length,
    low: issues.filter((i) => i.severity === 'low').length,
  };
}

const DOC_MD_COMPONENTS = {
  p: ({ children }) => <p style={{ margin: '0 0 6px 0' }}>{children}</p>,
  code: ({ className, children }) => {
    const isBlock = /language-/.test(className || '');
    if (!isBlock) return <code className="inline-code">{children}</code>;
    return <code className={className}>{children}</code>;
  },
  pre: ({ children }) => <pre className="doc-pre">{children}</pre>,
};

export default function AnalysisResult({ view, onResolve }) {
  const { t } = useI18n();
  const { issues, docsUsed, cached, explanation, analyzeTimeMs, patternsChecked, code } = view;
  const { high, medium, low } = severityCounts(issues);
  const lines = code.trim().split('\n').length;
  const chars = code.length;

  return (
    <div className="analysis-result">
      <div className="report-section">
        <div className="report-section-title">{t.codeStats}</div>
        <div className="report-stats-row">
          <div className="report-stat"><span className="report-stat-val">{lines}</span><span className="report-stat-lbl">{t.lines}</span></div>
          <div className="report-stat"><span className="report-stat-val">{chars}</span><span className="report-stat-lbl">{t.chars}</span></div>
          <div className="report-stat"><span className="report-stat-val">{issues.length}</span><span className="report-stat-lbl">{t.issuesLbl}</span></div>
          {analyzeTimeMs != null && <div className="report-stat"><span className="report-stat-val">{(analyzeTimeMs / 1000).toFixed(1)}s</span><span className="report-stat-lbl">{t.totalTime}</span></div>}
          {patternsChecked != null && <div className="report-stat"><span className="report-stat-val">{patternsChecked}</span><span className="report-stat-lbl">{t.patternsScanned}</span></div>}
        </div>
        <div className="report-sev-bar">
          {cached && <span className="cached-badge"><Zap size={11} /> {t.cached}</span>}
          {high > 0 && <span className="sev-chip high">{high} HIGH</span>}
          {medium > 0 && <span className="sev-chip medium">{medium} MED</span>}
          {low > 0 && <span className="sev-chip low">{low} LOW</span>}
        </div>
      </div>

      {issues.length === 0 ? (
        <div className="report-section">
          <div className="analysis-empty">
            <CheckCircle2 size={22} />
            <p>{t.noIssuesFound}</p>
          </div>
        </div>
      ) : (
        <div className="report-section">
          <div className="report-section-title">{t.issueFound(issues.length)}</div>
          {issues.map((issue, i) => <IssueCard key={i} issue={issue} index={i} originalCode={code} onResolve={onResolve} />)}
        </div>
      )}

      {explanation && (
        <div className="report-section">
          <div className="report-section-title">{t.aiExplanation}</div>
          <div className="explain-text" dangerouslySetInnerHTML={{ __html: explanation }} />
        </div>
      )}

      {docsUsed.length > 0 && (
        <div className="report-section">
          <div className="report-section-title"><Database size={13} style={{ display: 'inline', marginRight: 6, verticalAlign: -2 }} />{t.kbReferences}</div>
          <div className="report-docs">
            {docsUsed.map((doc, i) => (
              <div key={i} className="kb-doc-card">
                <div className="report-doc-row">
                  {doc.category && <span className="report-doc-cat">{doc.category}</span>}
                  <span className="report-doc-title-full">{doc.title}</span>
                </div>
                {doc.content && (
                  <div className="kb-doc-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={DOC_MD_COMPONENTS}>{doc.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
