"""
AI2 — batch 5 mo rong KB: viet tay 15 doc/pattern cho 2 pattern cuoi con o muc
24 doc (sync_io_blocking, global_var_thread). Moi doc la 1 tinh huong code CU
THE khac nhau that su, khong dung khuon cau lap lai.

Chay: python add_batch5_docs.py
"""
import json
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base.json"

NEW_DOCS = [
    # ============= SYNC_IO_BLOCKING (15 doc) =============
    {"id": "js-b5-sio-001", "title": "Sync IO Blocking: Doc File Config Bang readFileSync Trong Moi Request Handler",
     "content": "app.get('/settings', (req, res) => { const config = fs.readFileSync('./config.json', 'utf8'); res.json(JSON.parse(config)) }) — readFileSync() chan toan bo event loop cho den khi doc xong file (du chi vai ms voi file nho, nhung tich luy voi luu luong request cao), moi request khac dang cho xu ly (bao gom request healthcheck) deu bi tre — voi 1000 request/giay, tong thoi gian chan cong don co the gay tang do tre dang ke tren toan bo server.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-002", "title": "Sync IO Blocking: Ghi Log Bang appendFileSync Trong Middleware Xu Ly Moi Request",
     "content": "app.use((req, res, next) => { fs.appendFileSync('access.log', `${req.method} ${req.path}\\n`); next() }) — moi request deu chan event loop de ghi 1 dong log vao file — trong giai doan tai cao (vi du bi DDoS hoac traffic spike hop phap), disk I/O co the cham lai (disk dang bi tai nang), moi lan ghi cham se chan TOAN BO cac request khac dang cho xu ly, tao hieu ung day chuyen lam server tre theo cap so nhan.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-003", "title": "Sync IO Blocking: Kiem Tra Ton Tai File Upload Bang existsSync Truoc Moi Lan Ghi",
     "content": "function saveUpload(filename, data) { while (fs.existsSync(getUniquePath(filename))) { filename = generateNewName(filename) } fs.writeFileSync(getUniquePath(filename), data) } — vong lap while ket hop existsSync() VA writeFileSync() deu la sync I/O, chay hoan toan dong bo — neu co xung dot ten file lien tuc (vi du nhieu user upload file trung ten cung luc), vong lap while co the chay nhieu vong, moi vong chan event loop 1 lan, lam do tre request tich luy khong the du doan truoc.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-004", "title": "Sync IO Blocking: Doc Toan Bo Thu Muc Va Danh Sach File Bang readdirSync Trong Cron Job Thuong Xuyen",
     "content": "cron.schedule('*/10 * * * * *', () => { const files = fs.readdirSync('./uploads'); processFileList(files) }) — cron job nay chay MOI 10 giay va dung readdirSync() de liet ke file trong thu muc uploads — neu thu muc co hang chuc nghin file (tich luy qua thoi gian), readdirSync() co the mat vai chuc den vai tram ms de tra ve, chan event loop dinh ky moi 10 giay, gay giat cuc (latency spike) dinh ky rat de nhan biet trong monitoring.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-005", "title": "Sync IO Blocking: Doc Va Ghi File Session Bang readFileSync/writeFileSync Trong Middleware Auth Custom",
     "content": "function customSessionMiddleware(req, res, next) { const sessionData = fs.readFileSync(`./sessions/${req.cookies.sid}.json`, 'utf8'); req.session = JSON.parse(sessionData); res.on('finish', () => { fs.writeFileSync(`./sessions/${req.cookies.sid}.json`, JSON.stringify(req.session)) }); next() } — middleware nay chay cho MOI request co session (gan nhu tat ca request), doc VA ghi file dong bo — thay vi dung session store chuyen dung (Redis/memory), viec dung filesystem sync nhu 1 'database' tho so nay chan event loop 2 lan cho moi request, la 1 trong nhung nguon gay cham he thong pho bien nhat khi 'tu che' session storage.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-006", "title": "Sync IO Blocking: Parse File Excel Lon Bang Thu Vien Dong Bo Trong Route Xu Ly Upload",
     "content": "app.post('/import', upload.single('file'), (req, res) => { const workbook = xlsx.readFile(req.file.path); const data = xlsx.utils.sheet_to_json(workbook.Sheets['Sheet1']); processImportData(data); res.json({ imported: data.length }) }) — xlsx.readFile() la thao tac dong bo hoan toan, voi file Excel lon (hang chuc nghin dong) co the mat vai giay de parse — trong luc do, event loop bi chan hoan toan, MOI request khac toi server (ke ca cac request khong lien quan gi den import) deu phai cho den khi file Excel nay parse xong.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-007", "title": "Sync IO Blocking: Sao Chep File Backup Bang copyFileSync Trong Endpoint Trigger Backup Thu Cong",
     "content": "app.post('/admin/backup', (req, res) => { fs.copyFileSync('./database.db', `./backups/backup-${Date.now()}.db`); res.json({ status: 'backed up' }) }) — voi file database lon (vai GB), copyFileSync() co the mat hang chuc giay de hoan tat — trong suot khoang thoi gian nay, TOAN BO server ngung phan hoi bat ky request nao khac, gay downtime thuc te tren production chi vi 1 admin bam nut backup thu cong, du chuc nang nay it khi duoc goi.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-008", "title": "Sync IO Blocking: Load Danh Sach Blacklist IP Tu File Bang readFileSync Trong Middleware Chan Truy Cap",
     "content": "app.use((req, res, next) => { const blacklist = fs.readFileSync('./blacklist.txt', 'utf8').split('\\n'); if (blacklist.includes(req.ip)) return res.status(403).end(); next() }) — middleware nay CHAY LAI tu dau, doc lai TOAN BO file blacklist.txt tu disk cho MOI request (khong cache trong memory) — day la sai lam kep: vua khong can thiet phai doc lai file moi lan (noi dung it thay doi), vua dung sync I/O chan event loop lien tuc, ca 2 van de cong don lam giam throughput server dang ke.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-009", "title": "Sync IO Blocking: Doc Certificate SSL Tu File Trong Ham Khoi Tao HTTPS Server Duoc Goi Lap Nhieu Lan Khi Reload Config",
     "content": "function createHttpsServer() { const options = { key: fs.readFileSync('./cert/key.pem'), cert: fs.readFileSync('./cert/cert.pem') }; return https.createServer(options, app) } setInterval(() => { server = createHttpsServer() }, 3600000) — ham nay duoc thiet ke de reload certificate moi gio (dung cho auto-renewal), dung readFileSync() moi lan — trong 1 ung dung don gian goi 1 lan luc khoi dong thi khong sao, nhung neu duoc goi lai dinh ky nhu trong vi du nay tren server dang phuc vu traffic, moi lan reload deu chan event loop trong khoang thoi gian doc 2 file certificate.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-010", "title": "Sync IO Blocking: Tinh Hash MD5 Cua File Lon Bang crypto Dong Bo Trong Route Kiem Tra Tinh Toan Ven",
     "content": "app.post('/verify-checksum', (req, res) => { const fileBuffer = fs.readFileSync(req.body.filePath); const hash = crypto.createHash('md5').update(fileBuffer).digest('hex'); res.json({ hash, valid: hash === req.body.expectedHash }) }) — ca readFileSync() (doc file, co the lon vai chuc/tram MB) VA thao tac hash (CPU-bound, khong phai I/O nhung cung dong bo, chan event loop) deu chan hoan toan — voi file lon, thoi gian chan co the len den vai giay, khien server hoan toan khong phan hoi duoc request nao khac trong luc do.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-011", "title": "Sync IO Blocking: Xoa Nhieu File Tam Bang unlinkSync Trong Vong Lap Cleanup Cron",
     "content": "cron.schedule('0 * * * *', () => { const oldFiles = getExpiredFiles(); oldFiles.forEach(f => fs.unlinkSync(f.path)) }) — cron job chay moi gio, xoa tung file het han bang unlinkSync() trong vong lap forEach — neu co hang nghin file can xoa (tich luy sau 1 gio), moi lan xoa deu chan event loop, tong thoi gian chan cong don co the len den vai giay moi gio, gay giat dinh ky khien monitoring bao dong nham ve 'server cham' theo chu ky.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-012", "title": "Sync IO Blocking: Load Model Machine Learning Tu File Bang readFileSync Trong Ham Predict Duoc Goi Moi Request",
     "content": "app.post('/predict', (req, res) => { const modelData = fs.readFileSync('./model/weights.bin'); const model = loadModelFromBuffer(modelData); const result = model.predict(req.body.input); res.json({ result }) }) — day la sai lam ro rang: model KHONG can load lai tu file cho moi request (chi can load 1 lan luc khoi dong va giu trong memory), nhung code nay lam vay — moi request predict deu chan event loop de doc lai file weights (co the vai chuc MB), vua lang phi vua lam server rat cham duoi tai.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-013", "title": "Sync IO Blocking: Ghi File Audit Log JSON Bang writeFileSync Ghi De Toan Bo File Moi Lan Them Entry",
     "content": "function logAuditEvent(event) { const logs = JSON.parse(fs.readFileSync('./audit.json', 'utf8')); logs.push(event); fs.writeFileSync('./audit.json', JSON.stringify(logs)) } — moi lan ghi 1 audit event, ham nay doc TOAN BO file JSON cu (co the da co hang chuc nghin entry tich luy qua thoi gian), parse, them 1 entry, roi ghi lai TOAN BO file — ca thoi gian doc lan ghi deu tang tuyen tinh theo kich thuoc file, sau vai thang van hanh file audit log co the lam moi lan ghi event mat vai giay, chan event loop moi lan.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-014", "title": "Sync IO Blocking: Doc File Ngon Ngu I18n Bang readFileSync Trong Ham Dich Duoc Goi O Moi Component Render",
     "content": "function translate(key, locale) { const translations = JSON.parse(fs.readFileSync(`./locales/${locale}.json`, 'utf8')); return translations[key] || key } — ham dich nay duoc goi rat nhieu lan trong 1 request (moi label tren trang can dich rieng, co the hang chuc lan goi translate() cho 1 trang), moi lan goi deu doc lai TOAN BO file locale tu disk — mac du noi dung file khong doi giua cac lan goi trong cung 1 request, khong co cache nao duoc dung, gay lang phi I/O dong bo lap di lap lai.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},
    {"id": "js-b5-sio-015", "title": "Sync IO Blocking: Kiem Tra Quyen Truy Cap File Bang statSync Truoc Moi Lan Serve Static File Custom",
     "content": "app.get('/files/:name', (req, res) => { const filePath = path.join(STATIC_DIR, req.params.name); const stats = fs.statSync(filePath); if (stats.isFile()) { res.sendFile(filePath) } else { res.status(404).end() } }) — moi request tai file tinh deu goi statSync() dong bo truoc khi phuc vu — voi luong truy cap cao (endpoint serve anh/asset la endpoint thuong bi goi nhieu nhat), viec chan event loop lap di lap lai chi de kiem tra 1 dieu kien don gian (file co ton tai khong) tao ra chi phi khong can thiet, nen dung fs.promises.stat() bat dong bo thay the.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch5, dua tren mo ta sync_io_blocking)", "url": "", "pattern_ids": ["sync_io_blocking"]},

    # ============= GLOBAL_VAR_THREAD (15 doc) =============
    {"id": "js-b5-gvt-001", "title": "Global Var Thread: Bien Dem Global Duoc Ky Vong Chia Se Giua Cac Worker Xu Ly Anh Song Song",
     "content": "let totalProcessed = 0; function processImageInWorker(imagePath) { const worker = new Worker('./imageWorker.js', { workerData: { imagePath } }); worker.on('message', () => { totalProcessed++ }) } — bien totalProcessed duoc khai bao o module scope, nhung MOI worker_threads.Worker co bo nho JavaScript rieng biet hoan toan (khong chia se heap voi main thread) — bien totalProcessed trong worker script (neu co khai bao tuong tu) la 1 bien HOAN TOAN KHAC voi bien cung ten trong main thread, viec tang no ben trong worker khong he anh huong gi den bien o main thread.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-002", "title": "Global Var Thread: Cache In-Memory Gia Dinh Dung Chung Giua Cac Worker Xu Ly Request Trong Cluster Module",
     "content": "let requestCache = {}; app.get('/data/:id', (req, res) => { if (requestCache[req.params.id]) return res.json(requestCache[req.params.id]); const data = expensiveComputation(req.params.id); requestCache[req.params.id] = data; res.json(data) }) cluster.fork() // tao nhieu worker process — khi dung Node.js cluster module de scale server qua nhieu CPU core, moi worker process co bo nho HOAN TOAN rieng (khong phai thread chia se memory, ma la process con rieng biet) — bien requestCache khong duoc chia se giua cac worker, cache hit rate thuc te thap hon nhieu so voi ky vong vi moi request co the roi vao worker khac nhau voi cache rieng.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-003", "title": "Global Var Thread: Flag Trang Thai 'Dang Xu Ly' Duoc Kiem Tra Tu Main Thread Nhung Set Tu Worker Thread",
     "content": "let isProcessing = false; function startBackgroundJob() { isProcessing = true; const worker = new Worker('./job.js'); worker.on('message', (msg) => { if (msg === 'done') isProcessing = false }) } // worker.js noi bo: postMessage('done') khi xong — bien isProcessing chi thuc su duoc cap nhat qua co che message-passing (worker.on('message')), KHONG phai do worker truc tiep thay doi bien global cua main thread (dieu nay khong the xay ra giua cac thread trong Node.js) — code de gay hieu lam neu ai do nham tuong bien global tu dong dong bo giua cac thread nhu trong ngon ngu co shared-memory threading truyen thong (Java, C++).",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-004", "title": "Global Var Thread: Config Object Duoc Sua Doi O Main Thread Ky Vong Worker Thread Thay Doi Theo",
     "content": "let appConfig = { debugMode: false }; const worker = new Worker('./task.js', { workerData: { config: appConfig } }); function enableDebug() { appConfig.debugMode = true } // worker khong biet gi ve thay doi nay — workerData duoc SAO CHEP (khong phai tham chieu) sang worker luc khoi tao Worker — sau khi worker da chay, bat ky thay doi nao tren appConfig o main thread (nhu enableDebug()) hoan toan khong anh huong gi den ban sao appConfig ben trong worker, gay hieu lam nghiem trong ve kha nang cau hinh dong (dynamic config) giua cac thread.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-005", "title": "Global Var Thread: Logger Singleton Ky Vong Ghi Chung 1 File Tu Nhieu Worker_threads Dong Thoi",
     "content": "// logger.js: const logStream = fs.createWriteStream('app.log', { flags: 'a' }); module.exports = { log: (msg) => logStream.write(msg + '\\n') } // worker1.js va worker2.js deu require('./logger.js') — moi worker_threads require module nay se chay LAI toan bo code module (bao gom ca fs.createWriteStream), tao ra file stream RIENG cho tung worker — neu 2 worker ghi vao 'app.log' gan nhu dong thoi qua 2 stream object khac nhau (du cung 1 duong dan file), co the gay xen ke/ghi de noi dung log tren he thong file thuc te vi 2 file descriptor doc lap dang cung ghi.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-006", "title": "Global Var Thread: Bien Dem Rate Limit Toan Cuc Khong Chia Se Giua Cac Worker Xu Ly API Song Song",
     "content": "let apiCallsThisMinute = 0; function callExternalApi() { if (apiCallsThisMinute >= 100) throw new Error('rate limit'); apiCallsThisMinute++; return fetch(externalUrl) } // ham nay duoc goi tu code chay trong worker_threads pool de xu ly nhieu task song song — moi worker co bien apiCallsThisMinute RIENG (bat dau tu 0), rate limit thuc te ap dung TREN TUNG WORKER thay vi toan cuc — voi 5 worker, tong so request thuc te co the len toi 500/phut thay vi 100/phut nhu du dinh, co nguy co vuot qua rate limit that su cua external API va bi chan.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-007", "title": "Global Var Thread: Bien Global Luu Trang Thai Ket Noi Database Duoc Khoi Tao Rieng O Moi Worker Process PM2 Cluster Mode",
     "content": "let dbConnected = false; async function initDb() { await mongoose.connect(MONGO_URI); dbConnected = true } app.get('/status', (req, res) => res.json({ dbConnected })) // chay voi pm2 start app.js -i 4 (4 instance cluster) — moi instance PM2 la 1 Node.js process rieng biet hoan toan (giong cluster module), bien dbConnected chi phan anh trang thai KET NOI CUA RIENG PROCESS DO — endpoint /status co the tra ve ket qua khac nhau tuy load balancer route request toi instance nao, gay hieu lam nghiem trong khi debug 'tai sao status luc true luc false'.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-008", "title": "Global Var Thread: Mang Global Luu Danh Sach Task Dang Cho Ky Vong Worker_threads Them Vao Truc Tiep",
     "content": "let pendingTasks = []; function dispatchToWorker(task) { const worker = new Worker('./taskWorker.js', { workerData: task }); worker.on('exit', () => { pendingTasks = pendingTasks.filter(t => t.id !== task.id) }) } // taskWorker.js co bien pendingTasks CUNG TEN nhung la bien HOAN TOAN KHAC (bo nho rieng cua worker), moi thay doi ben trong worker khong anh huong gi den mang pendingTasks o main thread — code nham lan viet nham logic push task vao 'pendingTasks' BEN TRONG worker script se khong bao gio thay phan anh o main thread, gay bug logic kho phat hien vi khong co loi ro rang nao xuat hien.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-009", "title": "Global Var Thread: Bien Dem So Loi Toan He Thong Khong Chinh Xac Khi App Chay Duoi Nhieu Docker Container",
     "content": "let totalErrors = 0; process.on('uncaughtException', (err) => { totalErrors++; logError(err) }) app.get('/metrics', (req, res) => res.json({ totalErrors })) // app chay trong Kubernetes voi 3 replica (3 container/pod rieng biet) — moi container la 1 Node.js process HOAN TOAN doc lap (khong chi la thread, ma la ca 1 OS process rieng trong container rieng), bien totalErrors chi dem loi CUA RIENG POD DO — dashboard giam sat goi /metrics tren 1 pod cu the se cho ket qua sai lech neu muc dich la theo doi tong so loi CUA TOAN CLUSTER, can dung Prometheus/metrics aggregator thay vi bien in-memory.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-010", "title": "Global Var Thread: Bien Global Cache Ket Qua Tinh Toan Nang Duoc Tinh Lai O Moi Worker_threads Thay Vi Dung Chung",
     "content": "let cachedFibonacci = {}; function computeFib(n) { if (cachedFibonacci[n]) return cachedFibonacci[n]; const result = slowFibonacci(n); cachedFibonacci[n] = result; return result } // ham nay duoc goi tu code chay trong worker pool de xu ly nhieu request tinh toan song song — moi worker co cachedFibonacci RIENG, cung 1 gia tri n duoc tinh toan LAI TU DAU o moi worker thay vi dung chung 1 lan tinh — mat toan bo loi ich cua cache neu du dinh la chia se giua tat ca cac phep tinh song song, gay lang phi CPU dang ke voi phep tinh nang.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-011", "title": "Global Var Thread: SharedArrayBuffer Duoc Dung Dung Nhung Bien Wrapper Thuong (Khong Phai Typed Array View) Bi Nham La Chia Se",
     "content": "const sab = new SharedArrayBuffer(4); const sharedView = new Int32Array(sab); let localCopy = sharedView[0]; function incrementInWorker() { Atomics.add(sharedView, 0, 1) } function checkValue() { return localCopy } // localCopy chi la 1 SO NGUYEN THUONG duoc doc 1 lan tu sharedView, KHONG phai 1 view lien tuc toi vung nho chia se — sau khi worker tang gia tri trong sharedView qua Atomics.add(), bien localCopy o noi khac (da doc truoc do) van giu gia tri CU, khong tu dong cap nhat — chi truy cap TRUC TIEP qua sharedView[0] moi phan anh dung gia tri hien tai duoc chia se giua cac thread.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-012", "title": "Global Var Thread: Bien Toggle Feature Flag Global Duoc Cap Nhat O 1 Worker Nhung Cac Worker Khac Khong Thay",
     "content": "let featureEnabled = false; app.post('/admin/toggle-feature', (req, res) => { featureEnabled = !featureEnabled; res.json({ featureEnabled }) }) app.get('/feature-check', (req, res) => { res.json({ enabled: featureEnabled }) }) // chay voi Node.js cluster (nhieu worker process xu ly request) — admin bam toggle tren 1 request, request do duoc route toi worker A, featureEnabled cua worker A thay doi — nhung cac request /feature-check tiep theo co the duoc route toi worker B, C (van co featureEnabled cu) — hanh vi feature flag KHONG NHAT QUAN tuy request roi vao worker nao, can dung Redis/shared store thay vi bien in-memory cho feature flag trong moi truong multi-process.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-013", "title": "Global Var Thread: Bien Dem Job Queue Length Global Bi Sai Lech Khi Chay Nhieu Instance Worker Server Rieng Biet",
     "content": "let queueLength = 0; function enqueueJob(job) { queueLength++; jobQueue.push(job) } function dequeueJob() { queueLength--; return jobQueue.shift() } // he thong duoc scale bang cach chay 3 instance cua CUNG server nay (moi instance 1 process Node.js rieng, khong chia se memory) — moi instance co jobQueue va queueLength RIENG, dashboard hien thi 'queueLength' tu 1 instance cu the khong phan anh dung tong so job that su dang cho tren toan he thong, gay hieu lam khi giam sat/scale he thong dua tren metric sai.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-014", "title": "Global Var Thread: Bien Global Chua Instance Model AI Duoc Load Rieng O Moi Worker_threads Xu Ly Inference",
     "content": "let loadedModel = null; async function initModelInWorker() { loadedModel = await tf.loadLayersModel('file://./model.json') } // moi worker_threads trong pool goi initModelInWorker() rieng khi khoi tao — voi model AI nang (vai tram MB), moi worker phai load model VAO BO NHO RIENG CUA NO (khong chia se voi cac worker khac) — voi pool 8 worker, tong bo nho tieu thu la 8 lan kich thuoc model thay vi 1 lan, co the gay het bo nho tren may co RAM han che, du muc dich ban dau la dung nhieu worker de tang throughput.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
    {"id": "js-b5-gvt-015", "title": "Global Var Thread: Bien Toan Cuc Luu Session Token Refresh Trong Progress Ky Vong Ngan Duplicate Request Giua Cac Tab Nhung Khong Hoat Dong Qua Service Worker",
     "content": "let isRefreshing = false; async function refreshTokenIfNeeded() { if (isRefreshing) return; isRefreshing = true; await refreshAccessToken(); isRefreshing = false } // code nay chay trong main thread cua tab trinh duyet, DUOC KY VONG ngan 2 request refresh token trung lap — NHUNG neu app co Service Worker RIENG xu ly network request (pattern pho bien trong PWA), Service Worker chay trong 1 thread hoan toan tach biet voi main thread cua trang, bien isRefreshing trong Service Worker (neu co) la bien HOAN TOAN KHAC, khong ngan duoc duplicate request thuc su xay ra qua Service Worker.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch5, dua tren mo ta global_var_thread)", "url": "", "pattern_ids": ["global_var_thread"]},
]


def main() -> None:
    docs = json.loads(KB_PATH.read_text(encoding="utf-8"))
    existing_ids = {d["id"] for d in docs}
    added = 0
    for nd in NEW_DOCS:
        if nd["id"] in existing_ids:
            print(f"SKIP (id da ton tai): {nd['id']}")
            continue
        docs.append(nd)
        added += 1
    KB_PATH.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Added {added} doc moi. Tong KB: {len(docs)} doc.")


if __name__ == "__main__":
    main()
