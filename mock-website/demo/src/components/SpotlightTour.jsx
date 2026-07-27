import { useEffect, useState, useCallback } from 'react';
import { X, ArrowRight, ArrowLeft } from 'lucide-react';
import { useI18n } from '../i18n.jsx';

const PAD = 8;

function getRect(selector) {
  const el = document.querySelector(`[data-tour="${selector}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { top: r.top - PAD, left: r.left - PAD, width: r.width + PAD * 2, height: r.height + PAD * 2 };
}

export default function SpotlightTour({ steps, active, onClose }) {
  const { t } = useI18n();
  const [i, setI] = useState(0);
  const [rect, setRect] = useState(null);

  const recalc = useCallback(() => {
    if (!active) return;
    const r = getRect(steps[i]);
    if (r) {
      setRect(r);
      const el = document.querySelector(`[data-tour="${steps[i]}"]`);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      setRect(null);
    }
  }, [active, i, steps]);

  useEffect(() => {
    if (!active) return;
    const id = setTimeout(recalc, 260); // wait for smooth-scroll settle on step change
    window.addEventListener('resize', recalc);
    window.addEventListener('scroll', recalc, true); // track hole during smooth-scroll animation
    return () => {
      clearTimeout(id);
      window.removeEventListener('resize', recalc);
      window.removeEventListener('scroll', recalc, true);
    };
  }, [active, i, recalc]);

  useEffect(() => {
    if (active) setI(0);
  }, [active]);

  const isLast = i === steps.length - 1;

  useEffect(() => {
    if (!active) return;
    function onKey(e) {
      if (e.key === 'Enter' || e.key === 'ArrowRight') {
        e.preventDefault();
        if (isLast) onClose();
        else setI((v) => v + 1);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        setI((v) => Math.max(0, v - 1));
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [active, isLast, onClose]);

  if (!active) return null;

  const step = t.tourSteps[i];

  // Tooltip position: below target if room, else above.
  const tooltipTop = rect ? Math.min(rect.top + rect.height + 14, window.innerHeight - 220) : window.innerHeight / 2 - 80;
  const tooltipLeft = rect ? Math.min(Math.max(rect.left, 16), window.innerWidth - 380) : window.innerWidth / 2 - 180;

  return (
    <div className="tour-overlay" onClick={onClose}>
      {rect && (
        <div
          className="tour-hole"
          style={{ top: rect.top, left: rect.left, width: rect.width, height: rect.height }}
          onClick={(e) => e.stopPropagation()}
        />
      )}
      <div className="tour-tooltip" style={{ top: tooltipTop, left: tooltipLeft }} onClick={(e) => e.stopPropagation()}>
        <button type="button" className="tour-close" onClick={onClose}><X size={14} /></button>
        <p className="tour-step-count">{t.tourStepOf(i + 1, steps.length)}</p>
        <p className="tour-title">{step.title}</p>
        <p className="tour-body">{step.body}</p>
        <div className="tour-actions">
          {i > 0 && (
            <button type="button" className="tour-btn tour-btn-ghost" onClick={() => setI((v) => v - 1)}>
              <ArrowLeft size={13} /> {t.tourPrev}
            </button>
          )}
          <button type="button" className="tour-btn tour-btn-skip" onClick={onClose}>{t.tourSkip}</button>
          {!isLast ? (
            <button type="button" className="tour-btn tour-btn-primary" onClick={() => setI((v) => v + 1)}>
              {t.tourNext} <ArrowRight size={13} />
            </button>
          ) : (
            <button type="button" className="tour-btn tour-btn-primary" onClick={onClose}>{t.tourDone}</button>
          )}
        </div>
        <p className="tour-hint"><kbd>Enter</kbd>/<kbd>→</kbd> {t.tourEnterHint} · <kbd>←</kbd> {t.tourPrev.toLowerCase()} · <kbd>Esc</kbd> {t.tourSkip.toLowerCase()}</p>
      </div>
    </div>
  );
}
