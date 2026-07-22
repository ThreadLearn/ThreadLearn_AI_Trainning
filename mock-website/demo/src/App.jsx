import { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Toaster, toast } from 'sonner';
import { Send, Terminal, Brain, Cpu, Target, BookOpen, Sparkles, Code2, Undo2, Redo2, Play } from 'lucide-react';

import { LIVE_SAMPLES } from './mockCases';
import { MOCK_RESULTS } from './mockAnalysisResults';
import { MOCK_HISTORY } from './mockHistory';
import './App.css';

import CodeEditor from './components/CodeEditor';
import IssueCard from './components/IssueCard';
import { PipelineSummary } from './components/PipelineProgress';
import AnalysisResult from './components/AnalysisResult';
import HistoryList from './components/HistoryList';
import HistoryTrendChart from './components/HistoryTrendChart';
import RunOutput from './components/RunOutput';
import ResearchSection from './components/ResearchSection';
import { useRunCode } from './hooks/useRunCode';
import { useCodeHistory } from './hooks/useCodeHistory';

// Delay (ms) between each pipeline stage reveal — mimics real inference latency
const STAGE_DELAYS = [350, 550, 700, 300, 1400];
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

export default function App() {
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
    toast.success('Fix applied to editor');
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
      setError('Code is empty. Paste some JavaScript to analyze.');
      setLoading(false);
      return;
    }

    if (sampleIdx < 0 || !MOCK_RESULTS[sampleIdx]) {
      setError('Demo mode only supports the built-in samples above.\nSelect one from "Sample code" to see ThreadLearn analyze it.');
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
        ? `ThreadLearn detected <strong>${issueList.length} issue${issueList.length > 1 ? 's' : ''}</strong> using RAG retrieval from ${docs.length} knowledge-base document${docs.length !== 1 ? 's' : ''}. Review each issue card for details and fixes.`
        : 'No concurrency issues detected in this code.'
    );

    setLoading(false);
    toast.success('Code analyzed!');
  }

  return (
    <div className="app-page">
      <Toaster position="top-right" richColors />

      {/* ── HERO ─────────────────────────────────────────────── */}
      <motion.header initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="hero">
        <div className="hero-inner">
          <span className="hero-pill">AI Coach</span>
          <h1 className="hero-title">Analyze concurrency bugs before they ship.</h1>
          <p className="hero-sub">
            Fine-tuned Qwen2.5-Coder-1.5B + BM25 retrieval pipeline, detecting real JavaScript race conditions.
            This is a standalone demo replaying pre-computed results — see the <a href="https://github.com/ThreadLearn/ThreadLearn_AI_Trainning" target="_blank" rel="noreferrer">research repo</a> for the live system.
          </p>
        </div>
      </motion.header>

      <div className="page-body">
        <div className="ai-grid">
          {/* ── LEFT: editor + run + analyze ─────────────────── */}
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.05 }} className="panel-white editor-panel">
            <div className="editor-controls">
              <label className="sample-label">
                <span className="sample-label-text">Sample code</span>
                <select className="case-select" value={sampleIdx} onChange={(e) => handleSampleChange(Number(e.target.value))}>
                  {liveSamples.map((c, i) => <option key={i} value={i}>{c.title}</option>)}
                </select>
              </label>
              <div className="editor-buttons">
                <button type="button" className="btn-outline" disabled={!code.trim() || isRunning} onClick={handleRun}>
                  <Terminal size={15} /> Run
                </button>
                <button type="button" className="btn-primary" disabled={!code.trim() || loading} onClick={runAnalysis}>
                  <Send size={15} /> {loading ? 'Analyzing…' : 'Analyze code'}
                </button>
              </div>
            </div>

            <div className={`code-block ${hasRunOutput ? '' : 'grow'}`}>
              <div className="code-block-header">
                <div className="code-block-title">
                  <Code2 size={16} className="lime-icon" />
                  <div>
                    <p className="code-block-kicker">ThreadLearn analyzer</p>
                    <p className="code-block-filename">javascript.snippet</p>
                  </div>
                </div>
                <div className="code-block-actions">
                  <button type="button" className="icon-btn" disabled={!canUndo} title="Undo" onClick={undo}><Undo2 size={14} /></button>
                  <button type="button" className="icon-btn" disabled={!canRedo} title="Redo" onClick={redo}><Redo2 size={14} /></button>
                  <span className="live-api-pill"><Play size={13} /> Demo mode</span>
                </div>
              </div>
              <CodeEditor value={code} onChange={handleCodeChange} placeholder="Paste your code here..." className={hasRunOutput ? 'h-fixed' : 'h-grow'} />
            </div>

            <RunOutput logs={runLogs} isRunning={isRunning} runError={runError} hasRun={hasRun} />
          </motion.section>

          {/* ── RIGHT: About + Result ─────────────────────────── */}
          <aside className="ai-sidebar">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.1 }} className="about-card">
              <Brain size={24} />
              <h2>About this AI</h2>
              <div className="about-list">
                <div className="about-item">
                  <Cpu size={15} />
                  <p><strong>Model:</strong> Qwen2.5-Coder-1.5B, fine-tuned with QLoRA (r=16, α=32) on race-condition patterns.</p>
                </div>
                <div className="about-item">
                  <Target size={15} />
                  <p><strong>Training data:</strong> 892 labeled (buggy → fixed) pairs — 332 handcrafted + 560 template-generated. 73.3% score on a 30-case real-world benchmark.</p>
                </div>
                <div className="about-item">
                  <BookOpen size={15} />
                  <p><strong>Knowledge base:</strong> 2,050 reference docs retrieved via BM25 (RAG) to ground every fix in real concurrency patterns.</p>
                </div>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.15 }} className="result-card">
              <div className="result-card-header">
                <Sparkles size={18} />
                <h2>{loading ? 'Analyzing…' : 'Latest result'}</h2>
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
                  <p className="result-placeholder-kicker">Mock AI review</p>
                  <p className="result-placeholder-text">Select a sample above and click <strong>Analyze code</strong> to see ThreadLearn detect and fix a real JavaScript concurrency bug.</p>
                </div>
              )}
            </motion.div>
          </aside>
        </div>

        {MOCK_HISTORY.length > 1 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.2 }}>
            <HistoryTrendChart history={MOCK_HISTORY} />
          </motion.div>
        )}

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.25 }} className="panel-white history-panel">
          <div className="history-panel-header">
            <div>
              <p className="history-panel-kicker">History</p>
              <h2 className="history-panel-title">Analysis history</h2>
            </div>
            <span className="history-count-pill">{MOCK_HISTORY.length} records</span>
          </div>
          <HistoryList history={MOCK_HISTORY} />
        </motion.div>

        <ResearchSection />
      </div>
    </div>
  );
}
