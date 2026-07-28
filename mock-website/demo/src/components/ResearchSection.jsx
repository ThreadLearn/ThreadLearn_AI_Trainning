import { motion } from 'framer-motion';
import { FileText, Users, CheckCircle2, Zap, GitBranch, Search, Brain, ShieldCheck } from 'lucide-react';
import { useI18n } from '../i18n.jsx';

const PIPELINE_ICONS = [Zap, GitBranch, Search, FileText, Brain];
const AUTHOR_META = [
  { email: 'letritrung2605@gmail.com', orcid: '0009-0007-0790-1388' },
  { email: 'van.an.webdev@gmail.com', orcid: '0009-0000-8536-4396' },
  { email: 'hoaintt40@fe.edu.vn', orcid: '0009-0007-6328-0715' },
];
const CHART_SRCS = [
  '/research/slide_main_results.png',
  '/research/slide_pipeline_gain.png',
  '/research/slide_radar_categories.png',
  '/research/slide_pass_breakdown.png',
  '/research/slide_dataset_composition.png',
];

export default function ResearchSection() {
  const { t } = useI18n();

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.3 }} className="panel-white research-panel">
      <div className="research-header">
        <div>
          <p className="history-panel-kicker">{t.researchKicker}</p>
          <h2 className="history-panel-title">{t.researchTitle}</h2>
        </div>
        <span className="research-accepted-pill"><CheckCircle2 size={13} /> {t.researchAccepted}</span>
      </div>

      <div className="research-body">
        <div className="research-summary">
          <h3 className="research-paper-title">{t.researchPaperTitle}</h3>
          <p className="research-abstract">{t.researchAbstract}</p>

          <div className="research-meta">
            <div className="research-meta-item">
              <FileText size={14} />
              <span>{t.researchSubmission}</span>
            </div>
            <div className="research-meta-item">
              <Users size={14} />
              <span>{t.researchAuthorsCount}</span>
            </div>
          </div>

          <div className="research-authors">
            {t.authors.map((a, i) => (
              <div key={AUTHOR_META[i].email} className="research-author-card">
                <p className="research-author-name">{a.name}</p>
                <p className="research-author-role">{a.role}</p>
                <p className="research-author-orcid">ORCID {AUTHOR_META[i].orcid}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="research-charts">
          {t.charts.map((c, i) => (
            <figure key={CHART_SRCS[i]} className="research-chart-card">
              <img src={CHART_SRCS[i]} alt={c.title} loading="lazy" />
              <figcaption>
                <p className="research-chart-title">{c.title}</p>
                <p className="research-chart-caption">{c.caption}</p>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>

      {/* ── How it works: pipeline ─────────────────────────── */}
      <div className="research-subsection">
        <h3 className="research-subsection-title">{t.pipelineTitle}</h3>
        <div className="pipeline-explain-list">
          {t.pipelineSteps.map((s, i) => {
            const Icon = PIPELINE_ICONS[i];
            return (
              <div key={s.name} className="pipeline-explain-row">
                <div className="pipeline-explain-num">{i + 1}</div>
                <div className="pipeline-explain-body">
                  <div className="pipeline-explain-head">
                    <Icon size={15} />
                    <span>{s.name}</span>
                  </div>
                  <p>{s.detail}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Design decisions Q&A ───────────────────────────── */}
      <div className="research-subsection">
        <h3 className="research-subsection-title"><ShieldCheck size={16} /> {t.decisionsTitle}</h3>
        <div className="design-qa-list">
          {t.decisions.map((d) => (
            <div key={d.q} className="design-qa-card">
              <p className="design-qa-q">{d.q}</p>
              <p className="design-qa-a">{d.a}</p>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
