export default function IssueCard({ issue }) {
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
