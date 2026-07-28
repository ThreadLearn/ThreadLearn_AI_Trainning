import { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Toaster, toast } from 'sonner';
import { Send, Terminal, Brain, Cpu, Target, BookOpen, Sparkles, Code2, Undo2, Redo2, Play, Languages, Sun, Moon, HelpCircle } from 'lucide-react';

import { LIVE_SAMPLES } from './mockCases';
import { MOCK_RESULTS } from './mockAnalysisResults';
import { MOCK_HISTORY } from './mockHistory';
import { useI18n } from './i18n.jsx';
import { useTheme } from './theme.jsx';
import './App.css';

import CodeEditor from './components/CodeEditor';
import IssueCard from './components/IssueCard';
import { PipelineSummary } from './components/PipelineProgress';
import AnalysisResult from './components/AnalysisResult';
import HistoryList from './components/HistoryList';
import HistoryTrendChart from './components/HistoryTrendChart';
import RunOutput from './components/RunOutput';
import ResearchSection from './components/ResearchSection';
import SpotlightTour from './components/SpotlightTour';
import { useRunCode } from './hooks/useRunCode';
import { useCodeHistory } from './hooks/useCodeHistory';

// Delay (ms) between each pipeline stage reveal — mimics real inference latency
const STAGE_DELAYS = [350, 550, 700, 300, 1400];
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

const TOUR_STEPS = ['sample', 'run', 'analyze', 'editor', 'about', 'result', 'trend', 'history', 'research'];
const TOUR_SEEN_KEY = 'threadlearn-tour-seen';

export default function App() {
  const { lang, t, toggleLang } = useI18n();
  const { theme, toggleTheme } = useTheme();
  const { code, setCode, undo, redo, resetCode, canUndo, canRedo } = useCodeHistory(LIVE_SAMPLES[0]?.code || '');
  const [sampleIdx, setSampleIdx] = useState(0);

  const [issues, setIssues] = useState(null);
  const [docsUsed, setDocsUsed] = useState([]);
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pipelineSteps, setPipelineSteps] = useState([]);
  const [promptInlineOpen, setPromptInlineOpen] = useState(false);
  const [analyzeTime, setAnalyzeTime] = useState(null);
  const [patternsChecked, setPatternsChecked] = useState(null);
  const analyzeStart = useRef(null);
  const runToken = useRef(0);

  const { logs: runLogs, isRunning, runError, hasRun, run: runCode, reset: resetRun } = useRunCode();
  const hasRunOutput = isRunning || hasRun || runLogs.length > 0 || !!runError;

  const liveSamples = LIVE_SAMPLES;

  const [tourActive, setTourActive] = useState(false);
  useEffect(() => {
    const seen = window.localStorage.getItem(TOUR_SEEN_KEY);
    if (!seen) {
      const id = setTimeout(() => setTourActive(true), 600);
      return () => clearTimeout(id);
    }
  }, []);
  function closeTour() {
    setTourActive(false);
    window.localStorage.setItem(TOUR_SEEN_KEY, '1');
  }

  function reset() {
    setIssues(null);
    setDocsUsed([]);
    setExplanation('');
    setError('');
    setPipelineSteps([]);
    setPromptInlineOpen(false);
    setAnalyzeTime(null);
    setPatternsChecked(null);
  }

  function handleSampleChange(idx) {
    setSampleIdx(idx);
    if (idx >= 0) resetCode(liveSamples[idx]?.code || '');
    reset();
    resetRun();
  }

  function handleCodeChange(value) {
    setCode(value);
    if (issues !== null) reset();
    resetRun();
  }

  function handleResolve(fixedCode) {
    setCode(fixedCode);
    toast.success(t.toastResolved);
  }

  function handleRun() {
    runCode(code);
  }

  async function runAnalysis() {
    const myToken = ++runToken.current;
    setLoading(true);
    setError('');
    setIssues(null);
    setPipelineSteps([]);

    const trimmed = code.trim();
    if (!trimmed) {
      setError(t.codeEmpty);
      setLoading(false);
      return;
    }

    if (sampleIdx < 0 || !MOCK_RESULTS[sampleIdx]) {
      setError(t.demoOnlySamples);
      setLoading(false);
      return;
    }

    const mock = MOCK_RESULTS[sampleIdx];
    analyzeStart.current = Date.now();

    const steps = [];
    for (let i = 0; i < mock.pipeline.length; i++) {
      await sleep(STAGE_DELAYS[i] ?? 400);
      if (runToken.current !== myToken) return;
      steps.push({ ...mock.pipeline[i], _startTime: Date.now() - 50, _endTime: Date.now() });
      setPipelineSteps([...steps]);
    }

    if (runToken.current !== myToken) return;

    const issueList = mock.issues;
    setIssues(issueList);
    setDocsUsed(mock.docsUsed || []);
    setPatternsChecked(mock.patternsChecked ?? null);
    setAnalyzeTime(Date.now() - analyzeStart.current);
    const docs = mock.docsUsed || [];
    setExplanation(
      issueList.length > 0
        ? t.explanationFound(issueList.length, docs.length)
        : t.explanationClean
    );

    setLoading(false);
    toast.success(t.toastAnalyzed);
  }

  return (
    <div className="app-page">
      <Toaster position="top-right" richColors />

      {/* ── HERO ─────────────────────────────────────────────── */}
      <motion.header initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="hero">
        <div className="hero-inner">
          <div className="hero-top-row">
            <span className="hero-pill">{t.heroPill}</span>
            <div className="hero-toggles">
              <button type="button" className="lang-toggle" onClick={() => setTourActive(true)}>
                <HelpCircle size={14} /> {t.tourStart}
              </button>
              <button type="button" className="lang-toggle icon-only" onClick={toggleTheme} title={theme === 'light' ? 'Dark mode' : 'Light mode'}>
                {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
              </button>
              <button type="button" className="lang-toggle" onClick={toggleLang}>
                <Languages size={14} /> {lang === 'en' ? 'Tiếng Việt' : 'English'}
              </button>
            </div>
          </div>
          <h1 className="hero-title">{t.heroTitle}</h1>
          <p className="hero-sub">
            {t.heroSubPrefix} <a href="https://github.com/ThreadLearn/ThreadLearn_AI_Trainning" target="_blank" rel="noreferrer">{t.heroSubLink}</a> {t.heroSubSuffix}
          </p>
        </div>
      </motion.header>

      <div className="page-body">
        <div className="ai-grid">
          {/* ── LEFT: editor + run + analyze ─────────────────── */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.05 }} className="panel-white editor-panel">
            <div className="editor-controls">
              <label className="sample-label" data-tour="sample">
                <span className="sample-label-text">{t.sampleCode}</span>
                <select className="case-select" value={sampleIdx} onChange={(e) => handleSampleChange(Number(e.target.value))}>
                  {liveSamples.map((c, i) => <option key={i} value={i}>{c.title}</option>)}
                </select>
              </label>
              <div className="editor-buttons">
                <button type="button" className="btn-outline" data-tour="run" disabled={!code.trim() || isRunning} onClick={handleRun}>
                  <Terminal size={15} /> {t.run}
                </button>
                <button type="button" className="btn-primary" data-tour="analyze" disabled={!code.trim() || loading} onClick={runAnalysis}>
                  <Send size={15} /> {loading ? t.analyzing : t.analyzeCode}
                </button>
              </div>
            </div>

            <div className={`code-block ${hasRunOutput ? '' : 'grow'}`} data-tour="editor">
              <div className="code-block-header">
                <div className="code-block-title">
                  <Code2 size={16} className="lime-icon" />
                  <div>
                    <p className="code-block-kicker">{t.threadlearnAnalyzer}</p>
                    <p className="code-block-filename">javascript.snippet</p>
                  </div>
                </div>
                <div className="code-block-actions">
                  <button type="button" className="icon-btn" disabled={!canUndo} title={t.undo} onClick={undo}><Undo2 size={14} /></button>
                  <button type="button" className="icon-btn" disabled={!canRedo} title={t.redo} onClick={redo}><Redo2 size={14} /></button>
                  <span className="live-api-pill"><Play size={13} /> {t.demoMode}</span>
                </div>
              </div>
              <CodeEditor value={code} onChange={handleCodeChange} placeholder={t.codeEditorPlaceholder} className={hasRunOutput ? 'h-fixed' : 'h-grow'} />
            </div>

            <RunOutput logs={runLogs} isRunning={isRunning} runError={runError} hasRun={hasRun} />
          </motion.section>

          {/* ── RIGHT: About + Result ─────────────────────────── */}
          <aside className="ai-sidebar">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.1 }} className="about-card" data-tour="about">
              <Brain size={24} />
              <h2>{t.aboutTitle}</h2>
              <div className="about-list">
                <div className="about-item">
                  <Cpu size={15} />
                  <p><strong>{t.aboutModel}</strong> {t.aboutModelText}</p>
                </div>
                <div className="about-item">
                  <Target size={15} />
                  <p><strong>{t.aboutData}</strong> {t.aboutDataText}</p>
                </div>
                <div className="about-item">
                  <BookOpen size={15} />
                  <p><strong>{t.aboutKb}</strong> {t.aboutKbText}</p>
                </div>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.15 }} className="result-card" data-tour="result">
              <div className="result-card-header">
                <Sparkles size={18} />
                <h2>{loading ? t.analyzing : t.latestResult}</h2>
              </div>

              {error && <div className="error-banner visible">{error}</div>}

              {loading || pipelineSteps.length > 0 ? (
                <div className="result-streaming">
                  <PipelineSummary pipelineSteps={pipelineSteps} promptInlineOpen={promptInlineOpen} setPromptInlineOpen={setPromptInlineOpen} />
                  {issues !== null && (
                    <AnalysisResult
                      view={{ issues, docsUsed, explanation, analyzeTimeMs: analyzeTime, patternsChecked, code }}
                      onResolve={handleResolve}
                    />
                  )}
                </div>
              ) : (
                <div className="result-placeholder">
                  <p className="result-placeholder-kicker">{t.mockAiReview}</p>
                  <p className="result-placeholder-text">{t.resultPlaceholder} <strong>{t.analyzeCode}</strong> {t.resultPlaceholderSuffix}</p>
                </div>
              )}
            </motion.div>
          </aside>
        </div>

        {MOCK_HISTORY.length > 1 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.2 }} data-tour="trend">
            <HistoryTrendChart history={MOCK_HISTORY} />
          </motion.div>
        )}

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.25 }} className="panel-white history-panel" data-tour="history">
          <div className="history-panel-header">
            <div>
              <p className="history-panel-kicker">{t.historyKicker}</p>
              <h2 className="history-panel-title">{t.historyTitle}</h2>
            </div>
            <span className="history-count-pill">{MOCK_HISTORY.length} {t.historyRecords}</span>
          </div>
          <HistoryList history={MOCK_HISTORY} />
        </motion.div>

        <div data-tour="research">
          <ResearchSection />
        </div>
      </div>

      <SpotlightTour steps={TOUR_STEPS} active={tourActive} onClose={closeTour} />
    </div>
  );
}
