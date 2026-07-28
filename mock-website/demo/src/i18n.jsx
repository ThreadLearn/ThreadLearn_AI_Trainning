import { createContext, useContext, useState } from 'react';

const STRINGS = {
  en: {
    heroPill: 'AI Coach',
    heroTitle: 'Analyze concurrency bugs before they ship.',
    heroSubPrefix: 'Fine-tuned Qwen2.5-Coder-1.5B + BM25 retrieval pipeline, detecting real JavaScript race conditions. This is a standalone demo replaying pre-computed results — see the',
    heroSubLink: 'research repo',
    heroSubSuffix: 'for the live system.',

    sampleCode: 'Sample code',
    run: 'Run',
    analyzeCode: 'Analyze code',
    analyzing: 'Analyzing…',
    threadlearnAnalyzer: 'ThreadLearn analyzer',
    demoMode: 'Demo mode',
    codeEditorPlaceholder: 'Paste your code here...',
    undo: 'Undo',
    redo: 'Redo',

    aboutTitle: 'About this AI',
    aboutModel: 'Model:',
    aboutModelText: 'Qwen2.5-Coder-1.5B, fine-tuned with QLoRA (r=16, α=32) on race-condition patterns.',
    aboutData: 'Training data:',
    aboutDataText: '892 labeled (buggy → fixed) pairs — 332 handcrafted + 560 template-generated. 73.3% score on a 30-case real-world benchmark.',
    aboutKb: 'Knowledge base:',
    aboutKbText: '2,050 reference docs retrieved via BM25 (RAG) to ground every fix in real concurrency patterns.',

    latestResult: 'Latest result',
    mockAiReview: 'Mock AI review',
    resultPlaceholder: 'Select a sample above and click',
    resultPlaceholderSuffix: 'to see ThreadLearn detect and fix a real JavaScript concurrency bug.',

    codeEmpty: 'Code is empty. Paste some JavaScript to analyze.',
    demoOnlySamples: 'Demo mode only supports the built-in samples above.\nSelect one from "Sample code" to see ThreadLearn analyze it.',
    toastResolved: 'Fix applied to editor',
    toastAnalyzed: 'Code analyzed!',
    explanationFound: (n, d) => `ThreadLearn detected <strong>${n} issue${n > 1 ? 's' : ''}</strong> using RAG retrieval from ${d} knowledge-base document${d !== 1 ? 's' : ''}. Review each issue card for details and fixes.`,
    explanationClean: 'No concurrency issues detected in this code.',

    historyKicker: 'History',
    historyTitle: 'Analysis history',
    historyRecords: 'records',

    researchKicker: 'Research',
    researchTitle: 'The paper behind this demo',
    researchAccepted: 'Accepted — ICTA 2026',
    researchPaperTitle: 'ThreadLearn: A RAG-Augmented Fine-Tuned Language Model for JavaScript Concurrency Bug Detection and Remediation',
    researchAbstract: 'Concurrency bugs in asynchronous JavaScript (Node.js) are a leading cause of serious production failures. Existing tools either detect bugs without fixing them, or reason about code with LLMs that miss the exact buggy line and need 7B–32B parameters. ThreadLearn combines a 5-pattern static race detector with Qwen2.5-Coder-1.5B fine-tuned via QLoRA on 892 hindsight Chain-of-Thought examples, augmented at inference time by a BM25 retrieval pipeline over a 2,050-document knowledge base. On a 30-case real-world benchmark drawn entirely from production npm packages, ThreadLearn achieves 22.0/30 (73.3%) — beating GPT-3.5-turbo with the same pipeline (65.0%) despite ~125× fewer parameters.',
    researchSubmission: 'Submission #259 · Artificial Intelligence and Intelligent Data Systems and Bioinformatics track',
    researchAuthorsCount: '3 authors · FPT University, Da Nang, Vietnam',

    pipelineTitle: 'How it works — the pipeline',
    pipelineSteps: [
      { name: 'Static Detection', detail: 'race_detector scans the source in O(n) time — 5 core JS patterns (14 total in production): closure_loop_var, shared_var_settimeout, promise_no_await, concurrent_write_array, counter_no_atomic. Emits {pattern_id, line_range, description} per match.' },
      { name: 'AST Keyword Extraction', detail: 'esprima parses the code into an AST and walks Identifier tokens — keeping CamelCase API names like setTimeout or Promise.all intact, unlike a regex tokenizer which would split them into "set timeout" or "promise all".' },
      { name: 'BM25 Retrieval', detail: 'The extracted keywords query a BM25 index (k1=1.5, b=0.75) over a 2,050-document knowledge base, returning the top-3 most relevant reference docs — no embeddings, no GPU, <500ms to build the index.' },
      { name: 'Prompt Construction', detail: 'The detector report, retrieved docs, and buggy code are assembled into a single prompt — matched exactly to the format used during fine-tuning, so the model recognizes the task.' },
      { name: 'Fix Generation', detail: 'Qwen2.5-Coder-1.5B, fine-tuned via QLoRA on 892 hindsight Chain-of-Thought examples, generates the corrected code with reasoning — one LLM call per issue (capped at 5) so multiple bugs in one file aren\'t missed.' },
    ],

    decisionsTitle: 'Design decisions',
    decisions: [
      { q: 'Why a static detector instead of LLM-only?', a: 'Rule-based detectors (ESLint, ThreadSanitizer) find bugs but can\'t fix them. LLM-only approaches (GPT-3.5-turbo, PCWMs) can reason about code but miss the exact buggy line and need 7B–32B parameters for competitive accuracy. The static detector narrows what the LLM must infer — its structured {pattern_id, line_range} output is injected as grounding context, so a 1.5B model doesn\'t need to re-derive what the detector already knows.' },
      { q: 'Why BM25 instead of vector search?', a: 'JavaScript code uses precise technical terms — setTimeout, Promise.all, async/await — where exact keyword match matters more than semantic paraphrase similarity. BM25 needs zero GPU/VRAM, builds its index in under 500ms for 2,050 docs, and runs fully offline with a ~50KB library, versus embedding models needing 500MB+ and a GPU to embed every document.' },
      { q: 'Why AST parsing instead of regex tokenizing?', a: 'A naive tokenizer splits "setTimeout" into "set timeout", weakening the BM25 match against a knowledge-base doc that contains the literal API name. esprima distinguishes Identifier tokens (developer-chosen names) from Keyword tokens (async, for, await) — something regex can\'t do — keeping API names intact and improving retrieval precision.' },
    ],

    authors: [
      { name: 'Le Tri Trung', role: 'AI2 — RAG Pipeline, FastAPI Server, Race Detector' },
      { name: 'Ha Van An', role: 'AI1 — Dataset Collection, QLoRA Fine-tuning' },
      { name: 'Nguyen Thi Thuy Hoai', role: 'Evaluation & Research Writing' },
    ],

    charts: [
      { title: 'Main Results', caption: 'ThreadLearn + pipeline scores 73.3% on the 30-case real-world benchmark, vs. 65.0% for GPT-3.5-turbo with the same pipeline.' },
      { title: 'Pipeline Amplifies Fine-Tuning', caption: 'The retrieval pipeline only helps models that already have domain knowledge — +10pp for the fine-tuned model, +0pp for the base model.' },
      { title: 'Per-Category Performance', caption: 'ThreadLearn leads on 5 of 10 bug categories with direct detector support; weakest on categories needing cross-boundary reasoning.' },
      { title: 'PASS / PARTIAL / FAIL Breakdown', caption: 'Detailed scoring across all 6 evaluated configurations, out of 30 real production bugs.' },
      { title: 'Dataset Composition', caption: '892 fine-tuning examples (332 handcrafted + 560 template-generated) and a 2,050-document knowledge base.' },
    ],

    runOutputTitle: 'Console output',
    runOutputEmpty: 'Code ran with no console output (nothing logged, no errors).',
    runOutputRunning: 'Running…',

    issueFound: (n) => `${n} Issue${n > 1 ? 's' : ''} Found`,
    noIssuesFound: 'No concurrency issues detected.',
    codeStats: 'Code Stats',
    lines: 'lines',
    chars: 'chars',
    issuesLbl: 'issues',
    totalTime: 'total time',
    patternsScanned: 'patterns scanned',
    cached: 'cached',
    aiExplanation: 'AI Explanation',
    kbReferences: 'Knowledge Base References',
    suggestedRewrite: 'Suggested rewrite',
    fix: 'Fix',
    noChangesSuggested: 'no changes suggested',
    resolve: 'Resolve',
    applied: 'Applied',
    noIssues: 'No issues',

    tourStart: 'Take the tour',
    tourNext: 'Next',
    tourPrev: 'Back',
    tourSkip: 'Skip',
    tourDone: 'Got it',
    tourEnterHint: 'to continue',
    tourStepOf: (i, n) => `${i} of ${n}`,
    tourSteps: [
      { title: 'Pick a sample bug', body: 'Choose one of 12 real JavaScript concurrency bugs from this dropdown — each has a pre-computed AI analysis, ready to replay.' },
      { title: 'Run the code', body: 'Executes your code in a sandboxed iframe and shows real console output — see the bug happen before ThreadLearn explains it.' },
      { title: 'Analyze code', body: 'Replays ThreadLearn\'s full 5-step pipeline: static detection → AST parsing → BM25 retrieval → prompt building → LLM fix generation.' },
      { title: 'The code editor', body: 'Your JavaScript snippet. Edit freely, or use Undo/Redo to step through changes — including fixes applied by the AI.' },
      { title: 'About this AI', body: 'The model, training data, and knowledge base behind ThreadLearn — the real numbers from the research paper (73.3% benchmark score, 892 training pairs, 2,050-doc KB).' },
      { title: 'Latest result', body: 'After analyzing, this card fills with the pipeline steps, detected issues, suggested fixes (with diff view), and the AI\'s explanation.' },
      { title: 'Issues found over time', body: 'A trend chart of a simulated analysis history — click any point to jump to that record below.' },
      { title: 'Analysis history', body: 'Past analyses, expandable to see the full report for each — mirrors what a real user account would accumulate over time.' },
      { title: 'The research behind this demo', body: 'The full paper abstract, authors, evaluation charts, and a plain-language breakdown of why each technical choice (BM25, AST, static detector) was made.' },
    ],
  },

  vi: {
    heroPill: 'Trợ lý AI',
    heroTitle: 'Phát hiện lỗi concurrency trước khi code lên production.',
    heroSubPrefix: 'Mô hình Qwen2.5-Coder-1.5B đã fine-tune + pipeline truy xuất BM25, phát hiện race condition thật trong JavaScript. Đây là bản demo độc lập phát lại kết quả đã tính sẵn — xem',
    heroSubLink: 'repo nghiên cứu',
    heroSubSuffix: 'để biết về hệ thống thật.',

    sampleCode: 'Code mẫu',
    run: 'Chạy',
    analyzeCode: 'Phân tích code',
    analyzing: 'Đang phân tích…',
    threadlearnAnalyzer: 'ThreadLearn analyzer',
    demoMode: 'Chế độ demo',
    codeEditorPlaceholder: 'Dán code vào đây...',
    undo: 'Hoàn tác',
    redo: 'Làm lại',

    aboutTitle: 'Về AI này',
    aboutModel: 'Model:',
    aboutModelText: 'Qwen2.5-Coder-1.5B, fine-tune bằng QLoRA (r=16, α=32) trên các pattern race-condition.',
    aboutData: 'Dữ liệu huấn luyện:',
    aboutDataText: '892 cặp (code lỗi → đã sửa) — 332 mẫu viết tay + 560 mẫu sinh tự động. Đạt 73.3% trên benchmark 30-case thực tế.',
    aboutKb: 'Kho tri thức:',
    aboutKbText: '2.050 tài liệu tham khảo, truy xuất bằng BM25 (RAG) để mỗi fix đều bám sát các pattern concurrency thật.',

    latestResult: 'Kết quả gần nhất',
    mockAiReview: 'Đánh giá AI mẫu',
    resultPlaceholder: 'Chọn 1 mẫu ở trên rồi bấm',
    resultPlaceholderSuffix: 'để xem ThreadLearn phát hiện và sửa lỗi concurrency JavaScript thật.',

    codeEmpty: 'Code đang trống. Dán đoạn JavaScript vào để phân tích.',
    demoOnlySamples: 'Chế độ demo chỉ hỗ trợ các mẫu có sẵn ở trên.\nChọn 1 mẫu trong "Code mẫu" để xem ThreadLearn phân tích.',
    toastResolved: 'Đã áp dụng fix vào editor',
    toastAnalyzed: 'Đã phân tích xong!',
    explanationFound: (n, d) => `ThreadLearn phát hiện <strong>${n} lỗi</strong>, dùng RAG truy xuất từ ${d} tài liệu tri thức. Xem từng issue để biết chi tiết và cách sửa.`,
    explanationClean: 'Không phát hiện lỗi concurrency nào trong code này.',

    historyKicker: 'Lịch sử',
    historyTitle: 'Lịch sử phân tích',
    historyRecords: 'bản ghi',

    researchKicker: 'Nghiên cứu',
    researchTitle: 'Bài báo đứng sau demo này',
    researchAccepted: 'Đã được chấp nhận — ICTA 2026',
    researchPaperTitle: 'ThreadLearn: Mô hình ngôn ngữ Fine-tune kết hợp RAG cho Phát hiện và Sửa lỗi Concurrency JavaScript',
    researchAbstract: 'Lỗi concurrency trong JavaScript bất đồng bộ (Node.js) là nguyên nhân hàng đầu gây sự cố nghiêm trọng trên production. Các công cụ hiện có hoặc chỉ phát hiện lỗi mà không sửa được, hoặc dùng LLM suy luận code nhưng bỏ sót đúng dòng lỗi và cần model 7B–32B tham số. ThreadLearn kết hợp bộ phát hiện race condition tĩnh 5-pattern với Qwen2.5-Coder-1.5B fine-tune bằng QLoRA trên 892 mẫu Chain-of-Thought hindsight, bổ sung lúc suy luận bằng pipeline truy xuất BM25 trên kho tri thức 2.050 tài liệu. Trên benchmark 30-case lấy hoàn toàn từ package npm production thật, ThreadLearn đạt 22.0/30 (73.3%) — vượt GPT-3.5-turbo dùng cùng pipeline (65.0%) dù có ít hơn ~125 lần tham số.',
    researchSubmission: 'Submission #259 · Track Artificial Intelligence and Intelligent Data Systems and Bioinformatics',
    researchAuthorsCount: '3 tác giả · Đại học FPT, Đà Nẵng, Việt Nam',

    pipelineTitle: 'Cơ chế hoạt động — pipeline xử lý',
    pipelineSteps: [
      { name: 'Phát hiện tĩnh', detail: 'race_detector quét source code trong O(n) — 5 pattern JS chính (14 pattern trong bản production): closure_loop_var, shared_var_settimeout, promise_no_await, concurrent_write_array, counter_no_atomic. Trả về {pattern_id, line_range, description} cho mỗi lần khớp.' },
      { name: 'Trích xuất từ khóa bằng AST', detail: 'esprima parse code thành cây AST rồi duyệt các Identifier token — giữ nguyên tên API dạng CamelCase như setTimeout hay Promise.all, khác với tokenizer regex sẽ tách thành "set timeout" hay "promise all".' },
      { name: 'Truy xuất BM25', detail: 'Từ khóa trích xuất được dùng để query index BM25 (k1=1.5, b=0.75) trên kho 2.050 tài liệu, trả về top-3 tài liệu liên quan nhất — không cần embedding, không cần GPU, dựng index dưới 500ms.' },
      { name: 'Xây dựng prompt', detail: 'Báo cáo từ detector, tài liệu truy xuất được, và code lỗi được ghép thành 1 prompt duy nhất — khớp chính xác định dạng dùng lúc fine-tune, để model nhận diện đúng nhiệm vụ.' },
      { name: 'Sinh code fix', detail: 'Qwen2.5-Coder-1.5B, fine-tune bằng QLoRA trên 892 mẫu Chain-of-Thought hindsight, sinh code đã sửa kèm lý giải — mỗi issue gọi LLM riêng (tối đa 5 issue) để không bỏ sót lỗi nào trong file có nhiều bug.' },
    ],

    decisionsTitle: 'Quyết định thiết kế',
    decisions: [
      { q: 'Vì sao dùng detector tĩnh thay vì chỉ dùng LLM?', a: 'Công cụ rule-based (ESLint, ThreadSanitizer) tìm ra lỗi nhưng không sửa được. Cách chỉ dùng LLM (GPT-3.5-turbo, PCWMs) suy luận được code nhưng bỏ sót đúng dòng lỗi và cần model 7B–32B tham số mới đạt độ chính xác cạnh tranh. Detector tĩnh thu hẹp phạm vi LLM cần suy luận — output có cấu trúc {pattern_id, line_range} được đưa vào prompt làm ngữ cảnh, nên model 1.5B không cần tự suy ra lại những gì detector đã biết.' },
      { q: 'Vì sao dùng BM25 thay vì vector search?', a: 'Code JavaScript dùng các từ kỹ thuật chính xác — setTimeout, Promise.all, async/await — nơi khớp từ khóa chính xác quan trọng hơn độ tương đồng ngữ nghĩa. BM25 không cần GPU/VRAM, dựng index dưới 500ms cho 2.050 tài liệu, chạy hoàn toàn offline với thư viện ~50KB, so với model embedding cần 500MB+ và GPU để embed từng tài liệu.' },
      { q: 'Vì sao dùng AST thay vì tokenize bằng regex?', a: 'Tokenizer thông thường tách "setTimeout" thành "set timeout", làm yếu điểm khớp BM25 với tài liệu chứa nguyên tên API. esprima phân biệt được token Identifier (tên do dev đặt) với token Keyword (async, for, await) — điều regex không làm được — giữ nguyên tên API và tăng độ chính xác truy xuất.' },
    ],

    authors: [
      { name: 'Lê Trí Trung', role: 'AI2 — RAG Pipeline, FastAPI Server, Race Detector' },
      { name: 'Hà Văn Ân', role: 'AI1 — Thu thập dữ liệu, Fine-tune QLoRA' },
      { name: 'Nguyễn Thị Thúy Hoài', role: 'Đánh giá & Viết báo cáo nghiên cứu' },
    ],

    charts: [
      { title: 'Kết quả chính', caption: 'ThreadLearn + pipeline đạt 73.3% trên benchmark 30-case thực tế, so với 65.0% của GPT-3.5-turbo dùng cùng pipeline.' },
      { title: 'Pipeline khuếch đại Fine-tuning', caption: 'Pipeline truy xuất chỉ giúp ích cho model đã có kiến thức domain sẵn — +10pp cho model đã fine-tune, +0pp cho model gốc.' },
      { title: 'Hiệu năng theo từng category', caption: 'ThreadLearn dẫn đầu 5/10 category bug có detector hỗ trợ trực tiếp; yếu nhất ở các category cần suy luận xuyên ranh giới bất đồng bộ.' },
      { title: 'Phân bổ PASS / PARTIAL / FAIL', caption: 'Điểm chi tiết trên cả 6 cấu hình đánh giá, trong tổng 30 bug thật từ production.' },
      { title: 'Thành phần dataset', caption: '892 mẫu fine-tuning (332 viết tay + 560 sinh tự động) và kho tri thức 2.050 tài liệu.' },
    ],

    runOutputTitle: 'Console output',
    runOutputEmpty: 'Code chạy xong không có output console (không log gì, không lỗi).',
    runOutputRunning: 'Đang chạy…',

    issueFound: (n) => `Tìm thấy ${n} issue`,
    noIssuesFound: 'Không phát hiện lỗi concurrency nào.',
    codeStats: 'Thống kê code',
    lines: 'dòng',
    chars: 'ký tự',
    issuesLbl: 'issue',
    totalTime: 'tổng thời gian',
    patternsScanned: 'pattern đã quét',
    cached: 'đã cache',
    aiExplanation: 'Giải thích của AI',
    kbReferences: 'Tài liệu tham khảo',
    suggestedRewrite: 'Đề xuất sửa',
    fix: 'Fix',
    noChangesSuggested: 'không có đề xuất thay đổi',
    resolve: 'Áp dụng',
    applied: 'Đã áp dụng',
    noIssues: 'Không có issue',

    tourStart: 'Xem hướng dẫn',
    tourNext: 'Tiếp',
    tourPrev: 'Quay lại',
    tourSkip: 'Bỏ qua',
    tourDone: 'Đã hiểu',
    tourEnterHint: 'để tiếp tục',
    tourStepOf: (i, n) => `${i}/${n}`,
    tourSteps: [
      { title: 'Chọn 1 mẫu bug', body: 'Chọn 1 trong 12 lỗi concurrency JavaScript thật từ dropdown này — mỗi mẫu đã có sẵn kết quả phân tích AI, sẵn sàng phát lại.' },
      { title: 'Chạy thử code', body: 'Chạy code trong iframe sandbox an toàn, hiện console output thật — xem lỗi xảy ra trước khi ThreadLearn giải thích.' },
      { title: 'Phân tích code', body: 'Phát lại đầy đủ pipeline 5 bước của ThreadLearn: phát hiện tĩnh → parse AST → truy xuất BM25 → xây prompt → sinh fix bằng LLM.' },
      { title: 'Ô soạn code', body: 'Đoạn JavaScript của bạn. Sửa tự do, hoặc dùng Undo/Redo để lùi/tiến qua các thay đổi — kể cả fix do AI áp dụng.' },
      { title: 'Về AI này', body: 'Model, dữ liệu huấn luyện, và kho tri thức đứng sau ThreadLearn — số liệu thật từ bài báo nghiên cứu (73.3% điểm benchmark, 892 cặp huấn luyện, kho 2.050 tài liệu).' },
      { title: 'Kết quả gần nhất', body: 'Sau khi phân tích, card này hiện các bước pipeline, issue phát hiện được, đề xuất fix (kèm diff view), và giải thích của AI.' },
      { title: 'Biểu đồ lịch sử', body: 'Biểu đồ xu hướng số issue theo thời gian (dữ liệu mô phỏng) — bấm vào 1 điểm để nhảy tới bản ghi tương ứng bên dưới.' },
      { title: 'Lịch sử phân tích', body: 'Các lần phân tích trước, có thể mở rộng xem báo cáo đầy đủ — mô phỏng dữ liệu tích lũy của 1 tài khoản thật theo thời gian.' },
      { title: 'Nghiên cứu đứng sau demo', body: 'Toàn bộ abstract, tác giả, biểu đồ đánh giá, và giải thích dễ hiểu vì sao chọn từng công nghệ (BM25, AST, detector tĩnh).' },
    ],
  },
};

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState('vi');
  const t = STRINGS[lang];
  const toggleLang = () => setLang((l) => (l === 'en' ? 'vi' : 'en'));
  return <I18nContext.Provider value={{ lang, t, toggleLang }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used inside I18nProvider');
  return ctx;
}
