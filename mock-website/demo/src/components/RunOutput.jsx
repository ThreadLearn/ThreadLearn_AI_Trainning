import { Terminal, AlertTriangle, Loader2 } from 'lucide-react';

const LEVEL_CLASS = { log: 'run-log', warn: 'run-warn', error: 'run-error', result: 'run-result' };
const LEVEL_PREFIX = { log: '›', warn: '⚠', error: '✕', result: '←' };

export default function RunOutput({ logs, isRunning, runError, hasRun }) {
  if (!isRunning && !hasRun && logs.length === 0 && !runError) return null;

  return (
    <div className="run-output">
      <div className="run-output-header">
        <Terminal size={14} />
        <span>Console output</span>
        {isRunning && <Loader2 size={13} className="spin" style={{ marginLeft: 'auto' }} />}
      </div>
      <div className="run-output-body">
        {logs.length === 0 && !isRunning && !runError && (
          <p className="run-empty">Code ran with no console output (nothing logged, no errors).</p>
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
        {isRunning && logs.length === 0 && <p className="run-empty">Running…</p>}
      </div>
    </div>
  );
}
