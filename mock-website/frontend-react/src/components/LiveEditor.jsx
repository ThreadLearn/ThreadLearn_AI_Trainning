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

export function buildHlMap(issues) {
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

export function CodeDisplay({ code, hlMap }) {
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

export default function LiveEditor({ code, onChange }) {
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
