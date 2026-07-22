import { useRef } from 'react';

export default function CodeEditor({ value, onChange, className = '', placeholder }) {
  const textareaRef = useRef(null);
  const gutterRef = useRef(null);
  const lineCount = value.split('\n').length;

  function syncScroll() {
    if (gutterRef.current && textareaRef.current) {
      gutterRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  }

  return (
    <div className={`code-editor ${className}`}>
      <div ref={gutterRef} className="code-editor-gutter" aria-hidden="true">
        {Array.from({ length: lineCount }, (_, i) => <div key={i}>{i + 1}</div>)}
      </div>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onScroll={syncScroll}
        spellCheck={false}
        placeholder={placeholder}
        className="code-editor-textarea"
      />
    </div>
  );
}
