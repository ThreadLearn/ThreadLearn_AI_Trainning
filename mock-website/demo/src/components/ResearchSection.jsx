import { motion } from 'framer-motion';
import { FileText, Users, CheckCircle2 } from 'lucide-react';

const AUTHORS = [
  { name: 'Le Tri Trung', role: 'AI2 — RAG Pipeline, FastAPI Server, Race Detector', email: 'letritrung2605@gmail.com', orcid: '0009-0007-0790-1388' },
  { name: 'Ha Van An', role: 'AI1 — Dataset Collection, QLoRA Fine-tuning', email: 'van.an.webdev@gmail.com', orcid: '0009-0000-8536-4396' },
  { name: 'Nguyen Thi Thuy Hoai', role: 'Evaluation & Research Writing', email: 'hoaintt40@fe.edu.vn', orcid: '0009-0007-6328-0715' },
];

const CHARTS = [
  { src: '/research/slide_main_results.png', title: 'Main Results', caption: 'ThreadLearn + pipeline scores 73.3% on the 30-case real-world benchmark, vs. 65.0% for GPT-3.5-turbo with the same pipeline.' },
  { src: '/research/slide_pipeline_gain.png', title: 'Pipeline Amplifies Fine-Tuning', caption: 'The retrieval pipeline only helps models that already have domain knowledge — +10pp for the fine-tuned model, +0pp for the base model.' },
  { src: '/research/slide_radar_categories.png', title: 'Per-Category Performance', caption: 'ThreadLearn leads on 5 of 10 bug categories with direct detector support; weakest on categories needing cross-boundary reasoning.' },
  { src: '/research/slide_pass_breakdown.png', title: 'PASS / PARTIAL / FAIL Breakdown', caption: 'Detailed scoring across all 6 evaluated configurations, out of 30 real production bugs.' },
  { src: '/research/slide_dataset_composition.png', title: 'Dataset Composition', caption: '892 fine-tuning examples (332 handcrafted + 560 template-generated) and a 2,050-document knowledge base.' },
];

export default function ResearchSection() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25, delay: 0.3 }} className="panel-white research-panel">
      <div className="research-header">
        <div>
          <p className="history-panel-kicker">Research</p>
          <h2 className="history-panel-title">The paper behind this demo</h2>
        </div>
        <span className="research-accepted-pill"><CheckCircle2 size={13} /> Accepted — ICTA 2026</span>
      </div>

      <div className="research-body">
        <div className="research-summary">
          <h3 className="research-paper-title">
            ThreadLearn: A RAG-Augmented Fine-Tuned Language Model for JavaScript Concurrency Bug Detection and Remediation
          </h3>
          <p className="research-abstract">
            Concurrency bugs in asynchronous JavaScript (Node.js) are a leading cause of serious production failures.
            Existing tools either detect bugs without fixing them, or reason about code with LLMs that miss the exact
            buggy line and need 7B–32B parameters. ThreadLearn combines a 5-pattern static race detector with
            Qwen2.5-Coder-1.5B fine-tuned via QLoRA on 892 hindsight Chain-of-Thought examples, augmented at inference
            time by a BM25 retrieval pipeline over a 2,050-document knowledge base. On a 30-case real-world benchmark
            drawn entirely from production npm packages, ThreadLearn achieves 22.0/30 (73.3%) — beating GPT-3.5-turbo
            with the same pipeline (65.0%) despite ~125× fewer parameters.
          </p>

          <div className="research-meta">
            <div className="research-meta-item">
              <FileText size={14} />
              <span>Submission #259 · Artificial Intelligence and Intelligent Data Systems and Bioinformatics track</span>
            </div>
            <div className="research-meta-item">
              <Users size={14} />
              <span>3 authors · FPT University, Da Nang, Vietnam</span>
            </div>
          </div>

          <div className="research-authors">
            {AUTHORS.map((a) => (
              <div key={a.email} className="research-author-card">
                <p className="research-author-name">{a.name}</p>
                <p className="research-author-role">{a.role}</p>
                <p className="research-author-orcid">ORCID {a.orcid}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="research-charts">
          {CHARTS.map((c) => (
            <figure key={c.src} className="research-chart-card">
              <img src={c.src} alt={c.title} loading="lazy" />
              <figcaption>
                <p className="research-chart-title">{c.title}</p>
                <p className="research-chart-caption">{c.caption}</p>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
