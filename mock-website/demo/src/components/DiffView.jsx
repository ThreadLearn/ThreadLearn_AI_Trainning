import { diffLines } from 'diff';

export default function DiffView({ oldCode, newCode }) {
  const parts = diffLines(oldCode, newCode);

  return (
    <pre className="diff-view">
      <code>
        {parts.map((part, i) => {
          const lines = part.value.replace(/\n$/, '').split('\n');
          const cls = part.added ? 'diff-add' : part.removed ? 'diff-remove' : 'diff-ctx';
          const marker = part.added ? '+' : part.removed ? '-' : ' ';

          return lines.map((line, j) => (
            <div key={`${i}-${j}`} className={`diff-line ${cls}`}>
              <span className="diff-marker">{marker}</span>
              <span className="diff-text">{line || ' '}</span>
            </div>
          ));
        })}
      </code>
    </pre>
  );
}
