import { Terminal, AlertTriangle, Loader2 } from 'lucide-react';
import { useI18n } from '../i18n.jsx';

const LEVEL_CLASS = { log: 'run-log', warn: 'run-warn', error: 'run-error', result: 'run-result' };
const LEVEL_PREFIX = { log: '›', warn: '⚠', error: '✕', result: '←' };

export default function RunOutput({ logs, isRunning, runError, hasRun }) {
  const { t } = useI18n();
  if (!isRunning && !hasRun && logs.length === 0 && !runError) return null;

  return (
    <div className="run-output">
      <div className="run-output-header">
        <Terminal size={14} />
        <span>{t.runOutputTitle}</span>
        {isRunning && <Loader2 size={13} className="spin" style={{ marginLeft: 'auto' }} />}
      </div>
      <div className="run-output-body">
        {logs.length === 0 && !isRunning && !runError && (
          <p className="run-empty">{t.runOutputEmpty}</p>
        )}
        {logs.map((entry, i) => (
          <div key={i} className={`run-line ${LEVEL_CLASS[entry.level]}`}>
            <span className="run-prefix">{LEVEL_PREFIX[entry.level]}</span>
            {entry.text}
          </div>
        ))}
        {runError && (
          <div className="run-line run-error">
            <AlertTriangle size={13} style={{ display: 'inline', marginRight: 4, verticalAlign: -2 }} />
            {runError}
          </div>
        )}
        {isRunning && logs.length === 0 && <p className="run-empty">{t.runOutputRunning}</p>}
      </div>
    </div>
  );
}
