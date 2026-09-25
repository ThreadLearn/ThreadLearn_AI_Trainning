"""
AI2 — batch 6 mo rong KB: viet tay 15 doc/pattern cho 2 pattern mong nhat con
lai (resource_exhaustion:2, missing_join:2 — chi co doc tu round1/round2, chua
qua batch nao). Moi doc la 1 tinh huong code CU THE khac nhau that su.

Chay: python add_batch6_docs.py
"""
import json
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base.json"

NEW_DOCS = [
    # ============= RESOURCE_EXHAUSTION (15 doc) =============
    {"id": "js-b6-re-001", "title": "Resource Exhaustion: Mo Qua Nhieu Ket Noi Socket TCP Dong Thoi Trong Vong Lap Scan Port",
     "content": "for (const port of portsToScan) { const socket = net.createConnection(port, host); socket.on('error', () => {}) } — vong lap mo hang nghin ket noi TCP dong thoi ma khong gioi han concurrency va khong dong socket sau khi kiem tra xong — vuot qua gioi han file descriptor cua he dieu hanh (ulimit), gay loi EMFILE, dong thoi co the bi he thong bao mat coi la hanh vi port-scanning dang ngo.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-002", "title": "Resource Exhaustion: Tao Moi HTTP Agent Rieng Cho Moi Request Thay Vi Dung Chung Connection Pool",
     "content": "app.get('/proxy', async (req, res) => { const agent = new https.Agent({ keepAlive: true }); const response = await fetch(req.query.url, { agent }); res.send(await response.text()) }) — moi request toi endpoint proxy nay tao 1 HTTP Agent MOI (voi keepAlive giu ket noi mo lau hon), thay vi dung chung 1 agent duoc khoi tao 1 lan — moi agent giu rieng 1 tap connection pool, duoi tai cao (nhieu request/giay) so luong socket mo tich luy vuot qua gioi han he thong.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-003", "title": "Resource Exhaustion: Khong Gioi Han So Luong File Dang Duoc Xu Ly Dong Thoi Trong Batch Upload",
     "content": "async function processAllUploads(files) { return Promise.all(files.map(f => sharp(f.path).resize(800).toFile(f.outputPath))) } — Promise.all() khoi chay TAT CA thao tac xu ly anh dong thoi khong gioi han, moi thao tac sharp() mo 1 file handle rieng — voi batch upload hang nghin anh cung luc, so file descriptor mo dong thoi vuot qua gioi han he thong, gay loi EMFILE giua chung khi dang xu ly dot batch lon.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-004", "title": "Resource Exhaustion: Memory Leak Do Event Listener Tich Luy Khong Gioi Han Tren EventEmitter Dung Chung",
     "content": "function subscribeToUpdates(userId) { globalEmitter.on('update', (data) => notifyUser(userId, data)) } // ham nay duoc goi moi khi user mo 1 tab moi, khong bao gio unsubscribe — moi lan user mo tab moi them 1 listener vao globalEmitter ma khong bao gio remove, sau du 10 lan mo tab, Node.js phat canh bao 'MaxListenersExceededWarning', memory tang dan vi listener cu (tro toi user/tab da dong) van con ton tai va tiep tuc duoc goi.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-005", "title": "Resource Exhaustion: Database Query Khong Gioi Han LIMIT Tra Ve Hang Trieu Row Vao Memory",
     "content": "app.get('/export-all', async (req, res) => { const allRecords = await db.query('SELECT * FROM transactions'); res.json(allRecords) }) — query khong co LIMIT/pagination, voi bang co hang trieu dong, toan bo ket qua duoc load vao memory Node.js process cung 1 luc truoc khi gui response — co the gay 'JavaScript heap out of memory' crash toan bo server, dac biet nguy hiem tren endpoint export du lieu duoc goi boi nhieu client dong thoi.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-006", "title": "Resource Exhaustion: Tao Nhieu Child Process Song Song Ma Khong Gioi Han So Luong Dong Thoi",
     "content": "files.forEach(file => { const proc = spawn('convert', [file, file + '.png']) }) — vong lap spawn 1 child process rieng cho MOI file trong danh sach ma khong gioi han concurrency — voi hang tram file, he thong tao ra hang tram process ImageMagick chay dong thoi, moi process tieu ton CPU/memory rieng, co the lam qua tai toan bo he thong (dac biet tren container co gioi han tai nguyen chat che nhu Kubernetes pod).",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-007", "title": "Resource Exhaustion: WebSocket Server Khong Gioi Han So Luong Ket Noi Toi Da Tu 1 IP",
     "content": "wss.on('connection', (ws, req) => { activeConnections.set(ws, req.socket.remoteAddress) }) — server chap nhan so luong ket noi WebSocket khong gioi han tu bat ky IP nao — 1 client (vo tinh do bug retry loop, hoac co chu dich tan cong) co the mo hang nghin ket noi WebSocket lien tuc, moi ket noi giu 1 socket + buffer rieng, nhanh chong lam can kiet tai nguyen server cho cac client hop le khac.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-008", "title": "Resource Exhaustion: Cache In-Memory Khong Co Gioi Han Kich Thuoc (Unbounded Cache) Tich Luy Vo Han",
     "content": "const cache = new Map(); function getCachedResult(key, computeFn) { if (!cache.has(key)) cache.set(key, computeFn()) ; return cache.get(key) } — Map cache khong bao gio bi xoa entry cu, chi tang len theo thoi gian voi moi key moi duoc truy van — voi ung dung chay lien tuc nhieu ngay xu ly nhieu key khac nhau, cache Map nay tang khong gioi han, cuoi cung tieu thu het RAM cua process gay crash 'out of memory', can dung LRU cache co maxSize thay the.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-009", "title": "Resource Exhaustion: Recursive Function Khong Co Dieu Kien Dung Dung Gay Stack Overflow",
     "content": "function processLinkedList(node) { if (!node) return; handleNode(node); processLinkedList(node.next) } — voi linked list rat dai (hang chuc nghin node, vi du tu du lieu import khong duoc kiem soat), de quy khong duoc toi uu tail-call (V8 khong ho tro TCO) se lam ngap call stack, gay loi 'RangeError: Maximum call stack size exceeded' — can chuyen sang vong lap while thay vi de quy khi xu ly cau truc du lieu co the rat dai.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-010", "title": "Resource Exhaustion: Timer setInterval Tich Luy Khong Bao Gio Duoc Clear Khi Component/Session Ket Thuc",
     "content": "function startPolling(sessionId) { const timer = setInterval(() => checkSessionStatus(sessionId), 5000) } // khong luu timer id de clearInterval() sau nay — moi lan startPolling() duoc goi (vi du moi khi user mo trang), 1 interval moi duoc tao ma khong bao gio bi huy khi session ket thuc — sau nhieu gio van hanh, hang tram interval 'ma' van chay ngam, tieu ton CPU lien tuc va co the giu tham chieu toi cac object session da het han, ngan GC don dep bo nho.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-011", "title": "Resource Exhaustion: Batch Insert Database Khong Chia Nho Ma Gui Toan Bo Array Lon Trong 1 Query",
     "content": "async function bulkInsert(records) { await db.query('INSERT INTO logs VALUES ?', [records.map(r => [r.a, r.b, r.c])]) } — voi records co hang trieu phan tu, cau query duoc build voi TOAN BO du lieu trong 1 lan, kich thuoc query string/payload co the vuot qua gioi han max_allowed_packet cua MySQL hoac gay timeout do qua lon — can chia nho thanh nhieu batch nho hon (vi du 1000 record/batch) thay vi gui tat ca trong 1 lan.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-012", "title": "Resource Exhaustion: Redis Connection Duoc Tao Moi Cho Moi Lambda Invocation Khong Tai Su Dung",
     "content": "exports.handler = async (event) => { const client = redis.createClient({ url: REDIS_URL }); await client.connect(); const data = await client.get(event.key); await client.disconnect(); return data } — moi lan Lambda function duoc goi, 1 ket noi Redis MOI duoc tao va dong ngay sau do — duoi tai cao (hang tram invocation/giay do auto-scaling), so luong ket noi Redis duoc tao/dong lien tuc rat nhanh co the vuot qua gioi han connection cua Redis server, dac biet khi cac Lambda instance chay song song nhieu hon so du kien.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-013", "title": "Resource Exhaustion: Regex Backtracking Khong Kiem Soat Gay Treo CPU Voi Input Doc Hai (ReDoS)",
     "content": "function validateEmail(input) { return /^([a-zA-Z0-9_.-])+@(([a-zA-Z0-9-])+\\.)+([a-zA-Z0-9]{2,4})+$/.test(input) } — pattern regex nay co cau truc long nhau de bi catastrophic backtracking voi input duoc thiet ke co chu dich (vi du chuoi rat dai gom toan ky tu gan giong nhau nhung khong match) — voi input do, regex engine co the mat hang chuc giay den vo han de xu ly, chan hoan toan event loop, day la 1 dang tan cong tu choi dich vu (ReDoS) thuc su tren production.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-014", "title": "Resource Exhaustion: Retry Loop Khong Co Backoff Va Gioi Han Lan Thu Gay Ngap Request Toi Service Loi",
     "content": "async function callServiceForever(url) { while (true) { try { return await fetch(url) } catch (e) { /* retry ngay lap tuc */ } } } — vong lap while(true) retry ngay lap tuc khong co delay/backoff va khong co gioi han so lan thu — neu service dich that bai lien tuc (vi du dang down bao tri), vong lap nay gui request lien tuc voi toc do toi da co the, tieu ton CPU/network cua chinh app minh va co the lam nang them tinh trang qua tai cua service dich dang gap su co.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},
    {"id": "js-b6-re-015", "title": "Resource Exhaustion: Buffer.concat Lien Tuc Trong Vong Lap Xu Ly Stream Du Lieu Lon Gay O(n^2) Memory Copy",
     "content": "let result = Buffer.alloc(0); stream.on('data', (chunk) => { result = Buffer.concat([result, chunk]) }) — moi lan nhan 1 chunk du lieu tu stream, Buffer.concat() tao 1 buffer MOI va sao chep TOAN BO du lieu cu + chunk moi vao do — voi stream du lieu lon (video, file lon), thao tac nay co do phuc tap O(n^2) ve thoi gian VA lien tuc cap phat/giai phong buffer lon, gay ap luc nang len garbage collector va co the dan den 'out of memory' voi stream du du lieu lon.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta resource_exhaustion)", "url": "", "pattern_ids": ["resource_exhaustion"]},

    # ============= MISSING_JOIN (15 doc) =============
    {"id": "js-b6-mj-001", "title": "Missing Join: Khoi Tao Nhieu Worker Xu Ly File Song Song Nhung Khong Doi Tat Ca Truoc Khi Dong Ket Qua",
     "content": "function processAllFiles(files) { const results = []; files.forEach(f => { const worker = new Worker('./fileWorker.js', { workerData: f }); worker.on('message', r => results.push(r)) }); return results } — ham nay tra ve results NGAY LAP TUC (mang rong hoac chua day du), vi cac worker chay bat dong bo va chua kip gui message ve khi ham da return — code goi processAllFiles() nhan duoc mang rong thay vi ket qua thuc te, cac worker van tiep tuc chay ngam ma khong ai theo doi ket qua cua chung nua.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-002", "title": "Missing Join: Gui Nhieu Email Song Song Qua map() Nhung Khong Await Ket Qua Cua map()",
     "content": "function sendBulkEmails(recipients) { recipients.map(async (r) => await emailService.send(r.email, content)); console.log('All emails sent') } — .map() voi callback async tra ve mang cac Promise, nhung ket qua nay bi BO QUA hoan toan (khong gan vao bien, khong await) — dong console.log('All emails sent') chay NGAY LAP TUC, truoc khi bat ky email nao thuc su duoc gui xong, thong bao 'da gui xong' la sai hoan toan ve mat thoi diem.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-003", "title": "Missing Join: Test Suite Khoi Tao Nhieu Fixture Song Song Trong beforeAll Nhung Khong Doi Xong Het",
     "content": "let testDb, testCache; beforeAll(() => { setupTestDatabase().then(db => testDb = db); setupTestCache().then(cache => testCache = cache) }) — beforeAll() khong return Promise va khong await 2 lan setup — Jest coi beforeAll() da hoan tat ngay lap tuc (vi callback dong bo tra ve undefined), cac test case bat dau chay TRUOC KHI testDb/testCache thuc su duoc gan gia tri, gay loi 'Cannot read property of undefined' ngau nhien trong test dau tien.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-004", "title": "Missing Join: Khoi Dong Nhieu Microservice Con Song Song Trong Docker Compose Script Ma Khong Cho San Sang",
     "content": "async function startAllServices() { spawnService('auth-service'); spawnService('payment-service'); spawnService('notification-service'); console.log('All services started, ready to accept traffic') } — spawnService() khoi chay child process bat dong bo (khong await service thuc su san sang nhan request, chi biet no da duoc spawn) — thong bao 'ready to accept traffic' hien thi NGAY LAP TUC du cac service con co the can vai giay de khoi dong that su, gay request that bai neu load balancer tin vao thong bao nay va bat dau route traffic qua som.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-005", "title": "Missing Join: Chay Nhieu Migration Script Database Song Song Ma Khong Dam Bao Thu Tu Hoan Tat",
     "content": "['001_users.js', '002_orders.js', '003_indexes.js'].forEach(file => { runMigration(require('./migrations/' + file)) }) — cac migration co the phu thuoc thu tu (vi du 003_indexes.js can bang orders da duoc tao boi 002_orders.js), nhung forEach khoi chay TAT CA gan nhu dong thoi (khong doi migration truoc hoan tat) — migration tao index co the that bai vi bang orders chua duoc tao xong, gay loi khong nhat quan tuy vao toc do thuc thi cua tung migration.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-006", "title": "Missing Join: Dispatch Nhieu Action Redux Bat Dong Bo Song Song Nhung UI Render Truoc Khi Tat Ca Xong",
     "content": "function loadDashboardData(dispatch) { dispatch(fetchUserProfile()); dispatch(fetchOrderHistory()); dispatch(fetchNotifications()); setLoadingComplete(true) } — setLoadingComplete(true) duoc goi NGAY SAU KHI dispatch 3 action bat dong bo, khong doi ca 3 thunk hoan tat — UI hien thi trang thai 'da tai xong' va an loading spinner ngay lap tuc, trong khi du lieu thuc te van con dang tai, nguoi dung thay giao dien trong/thieu du lieu trong khoanh khac ngan truoc khi data thuc su ve.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-007", "title": "Missing Join: Ham Cleanup Xoa Nhieu Loai Tai Nguyen Song Song Nhung Khong Doi Xong De Bao Cao Ket Qua",
     "content": "function cleanupUserData(userId) { deleteUserFiles(userId); deleteUserSessions(userId); deleteUserCache(userId); return { status: 'cleaned' } } — ca 3 ham deleteXxx deu la async (thao tac I/O bat dong bo) nhung khong duoc await truoc khi return — ham cleanupUserData() bao cao 'cleaned' thanh cong NGAY LAP TUC, trong khi ca 3 thao tac xoa thuc te van dang chay ngam va co the that bai am tham (khong ai bat loi cua chung, tro thanh unhandled rejection rieng biet).",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-008", "title": "Missing Join: Chay Nhieu Health Check Song Song Cho Tung Dependency Nhung Tong Hop Ket Qua Qua Som",
     "content": "function checkAllDependencies() { const results = {}; checkDatabase().then(ok => results.db = ok); checkRedis().then(ok => results.redis = ok); checkS3().then(ok => results.s3 = ok); return results } — ham tra ve object results NGAY LAP TUC (object rong {}), truoc khi bat ky .then() nao trong 3 lan check kip gan gia tri — endpoint health check goi ham nay se luon bao cao 'tat ca deu undefined/unknown' thay vi trang thai that su cua tung dependency, khien he thong giam sat khong the phat hien duoc dependency nao dang gap su co.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-009", "title": "Missing Join: Upload Nhieu Phan Cua File Lon Song Song (Multipart) Nhung Hoan Tat Upload Qua Som",
     "content": "function uploadLargeFile(chunks) { chunks.forEach((chunk, i) => uploadPart(chunk, i)); completeMultipartUpload() } — completeMultipartUpload() (bao cho S3 biet 'da upload xong tat ca phan, ghep lai') duoc goi NGAY SAU forEach, khong doi TAT CA cac phan (chunk) thuc su upload xong (uploadPart la bat dong bo) — S3 nhan lenh hoan tat truoc khi du lieu day du, gay loi 'InvalidPart' hoac file cuoi cung bi thieu du lieu/hong.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-010", "title": "Missing Join: Chay Nhieu Test Case E2E Song Song Qua Trinh Duyet Headless Nhung Dong Browser Qua Som",
     "content": "async function runE2ETests(testCases) { const browser = await puppeteer.launch(); testCases.forEach(tc => runSingleTest(browser, tc)); await browser.close() } — forEach khong doi cac lan goi runSingleTest() (async) hoan tat truoc khi await browser.close() duoc thuc thi — browser bi dong NGAY LAP TUC trong khi cac test van dang chay ngam trong do, gay loi 'Target closed' hang loat cho hau het test case chua kip hoan thanh, ket qua test hoan toan khong dang tin cay.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-011", "title": "Missing Join: Ghi Nhieu Metric Song Song Vao Time-Series DB Nhung Tra Response HTTP Truoc Khi Ghi Xong",
     "content": "app.post('/batch-metrics', (req, res) => { req.body.metrics.forEach(m => influxClient.writePoint(m)); res.sendStatus(202) }) — writePoint() la bat dong bo (buffer va gui theo batch len InfluxDB), nhung forEach khong doi bat ky writePoint() nao hoan tat truoc khi res.sendStatus(202) duoc goi — client nhan HTTP 202 'Accepted' ngay lap tuc, nhung neu server crash ngay sau do (truoc khi buffer duoc flush), toan bo metric trong request nay bi mat vinh vien du client da nhan xac nhan thanh cong.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-012", "title": "Missing Join: Spawn Nhieu Child Process De Chay Test Song Song Nhung Tong Hop Ket Qua Truoc Khi Tat Ca Xong",
     "content": "function runParallelTests(testFiles) { const results = []; testFiles.forEach(f => { const proc = spawn('node', [f]); proc.on('exit', (code) => results.push({ file: f, passed: code === 0 })) }); printSummary(results) } — printSummary(results) chay NGAY LAP TUC voi mang results con rong (cac process con moi vua duoc spawn, chua co process nao kip 'exit') — bao cao tong ket test hien thi 0 test hoac danh sach khong day du, du tat ca test that su van dang chay ngam va se hoan tat sau do ma khong ai tong hop lai ket qua cua chung.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-013", "title": "Missing Join: Gui Nhieu Push Notification Song Song Qua FCM/APNs Nhung Ket Thuc Cron Job Truoc Khi Gui Xong",
     "content": "cron.schedule('0 9 * * *', () => { const users = getUsersForDailyReminder(); users.forEach(u => sendPushNotification(u.deviceToken, reminderMsg)); console.log('Daily reminders dispatched') }) — sendPushNotification() la bat dong bo (goi API FCM ngoai), forEach khong doi — console.log 'dispatched' in ra ngay lap tuc du cac notification van dang gui — trong moi truong serverless/Lambda voi cron trigger, function co the bi 'freeze' hoac terminate ngay sau log nay, huy bo cac notification con dang cho gui, khien nhieu user khong nhan duoc thong bao du log bao 'da gui'.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-014", "title": "Missing Join: Khoi Tao Nhieu Kafka Producer Song Song De Gui Batch Message Nhung Dong Ket Noi Qua Som",
     "content": "async function publishBatch(messages) { const producer = kafka.producer(); await producer.connect(); messages.forEach(m => producer.send({ topic: 'events', messages: [m] })); await producer.disconnect() } — producer.send() tra ve Promise (bat dong bo) nhung forEach khong doi — await producer.disconnect() duoc goi ngay sau forEach, co the dong ket noi truoc khi TAT CA message trong batch thuc su duoc gui len Kafka broker, gay mat message am tham trong batch lon ma khong co loi ro rang nao duoc bao cao.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
    {"id": "js-b6-mj-015", "title": "Missing Join: Chay Nhieu Script Seed Database Song Song Trong CI Pipeline Nhung Build Tiep Tuc Truoc Khi Xong",
     "content": "// CI script (bash goi node): node seed-users.js & node seed-products.js & node seed-orders.js & echo 'Seeding started, continuing pipeline...' — dau '&' chay 3 script Node.js o che do background (khong doi hoan tat), dong echo chay ngay lap tuc — CI pipeline tiep tuc sang buoc chay test TRUOC KHI du lieu seed thuc su co san trong database, cac test integration that bai ngau nhien do du lieu can thiet chua duoc seed xong, gay flaky CI kho tai hien tren local.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch6, dua tren mo ta missing_join)", "url": "", "pattern_ids": ["missing_join"]},
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
