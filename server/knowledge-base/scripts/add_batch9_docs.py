"""
AI2 — batch 9 mo rong KB: viet tay 15 doc/pattern cho 3 pattern mong nhat con
lai (double_callback:25, zalgo:25, concurrent_write_array:32 — chon them 1
pattern de tron batch). Moi doc la 1 tinh huong code CU THE khac nhau that su,
khac cac doc round1/batch1/batch7 da co cung pattern.

Chay: python add_batch9_docs.py
"""
import json
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base.json"

NEW_DOCS = [
    # ============= DOUBLE_CALLBACK (15 doc) =============
    {"id": "js-b9-dc-001", "title": "Double Callback: Ham Xu Ly Payment Gateway Webhook Goi Callback O Ca Idempotency Check Va Xu Ly Chinh",
     "content": "function handleWebhook(event, cb) { if (isDuplicate(event.id)) cb(null, 'already processed'); processPayment(event, (err) => cb(err, 'processed')) } — thieu return sau lan cb dau tien khi phat hien duplicate, nen code van tiep tuc goi processPayment() du event da duoc xu ly truoc do, va cb duoc goi lan thu 2 voi ket qua khac — thanh toan co the bi xu ly 2 lan (tru tien khach hang 2 lan) du logic idempotency check tuong nhu da ngan chan dung.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-002", "title": "Double Callback: Ham Validate Va Upload Avatar Goi Callback O Nhanh Loi Kich Thuoc Va Nhanh Thanh Cong Sau Do",
     "content": "function processAvatarUpload(file, cb) { if (file.size > 5000000) cb(new Error('too large')); resizeImage(file, (err, resized) => { uploadToStorage(resized, (err2, url) => cb(err2, url)) }) } — thieu return sau cb loi kich thuoc, resizeImage() van chay tiep voi file qua lon (co the gay loi rieng hoac cham), sau do cb duoc goi lai lan 2 voi ket qua tu uploadToStorage — client nhan 2 response cho 1 request, response dau la loi, response sau co the la URL thanh cong gay UI hien thi mau thuan.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-003", "title": "Double Callback: Custom Promise Wrapper Quanh SDK Cu Goi Ca resolve Va Reject Cho Cung 1 Loi Mang",
     "content": "function callLegacyApi(params) { return new Promise((resolve, reject) => { legacySdk.request(params, (err, data) => { if (err) { reject(err); resolve(null) } else { resolve(data) } }) }) } — nhanh loi goi CA reject(err) VA resolve(null) lien tiep — Promise chi chap nhan lan settle DAU TIEN (reject), lan resolve(null) sau do bi bo qua am tham (khong throw loi), NHUNG doan code nay the hien y do sai lam ro rang trong tu duy cua nguoi viet, de gay nham lan khi debug vi tuong rang co the 'sua loi' bang cach resolve sau khi reject.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-004", "title": "Double Callback: Ham Xac Thuc 2 Factor Goi Callback O Timeout Va O Callback Xac Nhan Tu SMS Provider",
     "content": "function verifyOtp(phone, code, cb) { const timer = setTimeout(() => cb(new Error('verification timeout')), 30000); smsProvider.verify(phone, code, (err, valid) => { cb(err, valid) }) } — khong luu ket qua clearTimeout(timer) sau khi smsProvider.verify() tra ve — neu smsProvider phan hoi DUNG luc 30 giay (bien gioi timeout), ca timeout callback va verify callback co the cung goi cb() gan nhu dong thoi, gay 2 ket qua mau thuan (1 bao timeout that bai, 1 bao xac thuc thanh cong) cho cung 1 lan nhap OTP.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-005", "title": "Double Callback: Middleware Rate Limiting Custom Goi next() Ca Khi Vuot Gioi Han Va Khi Cho Phep Tiep Tuc",
     "content": "function rateLimiter(req, res, next) { const count = incrementCount(req.ip); if (count > 100) { res.status(429).end(); next() } } — thieu return sau res.status(429).end(), khien next() van duoc goi ngay sau do du da tra response 429 — Express tiep tuc chay middleware/route handler tiep theo trong chuoi, co the ghi de len response da gui (gay loi 'Cannot set headers after they are sent') hoac thuc thi logic business ma dung ra phai bi chan boi rate limit.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-006", "title": "Double Callback: Ham Doc Config Tu Cache Roi Fallback Sang File Goi Callback O Ca 2 Nhanh Khi Cache Loi",
     "content": "function loadConfig(cb) { cache.get('config', (err, cached) => { if (err) { fs.readFile('./config.json', 'utf8', (err2, data) => cb(err2, JSON.parse(data))) } cb(null, cached) }) } — thieu return trong nhanh if(err), khien du co loi cache VA da bat dau doc file fallback, dong 'cb(null, cached)' ben ngoai VAN duoc thuc thi ngay (voi cached la undefined vi cache loi) — cb duoc goi 2 lan: 1 lan ngay voi du lieu sai (undefined), 1 lan sau do voi du lieu tu file thuc su dung.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-007", "title": "Double Callback: Ham Xu Ly Job Trong BullMQ Goi done() Trong Catch Block Va Trong Finally Block",
     "content": "worker.process(async (job, done) => { try { const result = await handleJob(job); done(null, result) } catch (err) { done(err) } finally { done(null, 'cleanup done') } }) — finally LUON chay bat ke try/catch co loi hay khong, va no goi done() LAN THU 2 sau khi try hoac catch da goi done() lan dau — BullMQ nhan bao cao ket qua job 2 lan mau thuan nhau (1 lan tu try/catch that su, 1 lan 'cleanup done' tu finally), co the ghi de trang thai job that su bang thong bao sai.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-008", "title": "Double Callback: Ham Kiem Tra Domain Blacklist Qua DNS Lookup Voi Callback Cache Va Callback DNS That",
     "content": "function checkDomainSafe(domain, cb) { const cached = blacklistCache.get(domain); if (cached !== undefined) cb(null, cached); dns.resolve(domain, (err, addresses) => { const isBlacklisted = checkAgainstBlacklist(addresses); blacklistCache.set(domain, isBlacklisted); cb(err, isBlacklisted) }) } — thieu return sau lan cb dau tien khi co cache hit, khien code van tiep tuc goi dns.resolve() TON KEM (network call khong can thiet) VA goi cb lan 2 voi ket qua co the KHAC voi ket qua cache (neu blacklist thay doi giua 2 lan check) — caller nhan 2 ket qua mau thuan cho cung 1 domain trong cung 1 request.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-009", "title": "Double Callback: Custom Retry Wrapper Cho HTTP Request Goi Callback O Ca Response Loi Va Response Thanh Cong Sau Retry",
     "content": "function fetchWithSingleRetry(url, cb) { http.get(url, (res) => { if (res.statusCode >= 500) { cb(new Error('server error')); http.get(url, (res2) => cb(null, res2)) } else { cb(null, res) } }) } — thieu return truoc lan retry, khien code goi cb loi NGAY (lan 1), roi TIEP TUC retry va goi cb lan 2 voi ket qua retry (co the thanh cong) — caller nhan 2 callback mau thuan: 1 loi, 1 thanh cong, cho 1 lan goi fetchWithSingleRetry duy nhat, logic xu ly phia caller kho biet nen tin ket qua nao.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-010", "title": "Double Callback: Ham Xu Ly Voice Recognition Callback Streaming Goi Callback Ca Khi Nhan Partial Result Va Final Result",
     "content": "speechRecognizer.on('result', (result) => { if (result.isFinal) { onTranscriptReady(result.text) } onTranscriptReady(result.text) }) — thieu 'return' hoac 'else' sau nhanh if(result.isFinal), khien onTranscriptReady() duoc goi 2 LAN cho ket qua final: 1 lan trong nhanh if, 1 lan ngoai if — code goi ham xu ly transcript (co the la luu vao database hoac hien thi UI) chay 2 lan trung lap cho cung 1 doan noi, gay du lieu trung lap trong lich su hoi thoai hoac giao dien hien thi text lap lai.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-011", "title": "Double Callback: Ham Xu Ly File Watcher Debounce Tu Che Goi Callback O Ca Lan Dau Va Sau Debounce Timer",
     "content": "function watchWithDebounce(path, cb) { let timer; fs.watch(path, (event, filename) => { cb(event, filename); clearTimeout(timer); timer = setTimeout(() => cb('debounced-change', filename), 300) }) } — ham nay goi cb() NGAY LAP TUC cho MOI thay doi file (khong debounce that su o lan goi dau), ROI con dat 1 timer de goi cb() THEM 1 lan nua sau 300ms — voi 1 thay doi file don le, cb duoc goi 2 lan (1 ngay lap tuc, 1 sau debounce) thay vi chi 1 lan duy nhat sau khi debounce dung nghia, gay xu ly trung lap trong logic build tool/hot-reload dung ham nay.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-012", "title": "Double Callback: Ham Kiem Tra Suc Khoe Dependency Voi Ca Callback Tu Cache Stale-While-Revalidate Va Callback Fetch Moi",
     "content": "function checkHealthSWR(serviceUrl, cb) { const stale = healthCache.get(serviceUrl); if (stale) cb(null, stale.status); fetch(serviceUrl + '/health').then(res => { const fresh = res.ok; healthCache.set(serviceUrl, { status: fresh }); cb(null, fresh) }) } — pattern stale-while-revalidate can goi callback 2 LAN CO CHU DICH (1 lan voi du lieu cu ngay lap tuc, 1 lan voi du lieu moi sau do) — NHUNG neu caller khong duoc thiet ke de xu ly duoc goi 2 lan (vi du dung trong 1 Promise wrapper chi resolve() 1 lan), lan goi thu 2 bi mat am tham hoac gay loi 'Promise already resolved', can tach ro rang API nay thanh 2 callback (onStale, onFresh) rieng biet thay vi dung chung 1 cb.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-013", "title": "Double Callback: Ham Xu Ly Drag And Drop Upload Goi Callback Ca Khi Validate MIME Type That Bai Va Sau Khi Doc File Xong",
     "content": "function handleFileDrop(file, cb) { if (!ALLOWED_TYPES.includes(file.type)) cb(new Error('invalid type')); const reader = new FileReader(); reader.onload = (e) => cb(null, e.target.result); reader.readAsDataURL(file) } — thieu return sau cb loi MIME type — reader van tiep tuc doc file (lang phi tai nguyen voi file khong hop le), va khi doc xong (bat dong bo, luon xay ra sau) cb duoc goi lan 2 voi ket qua thanh cong — UI co the hien thi ca thong bao loi VA preview file cung luc, gay nham lan cho nguoi dung ve trang thai thuc su cua file vua keo tha.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-014", "title": "Double Callback: Ham Ket Noi Database Voi Fallback Sang Replica Goi Callback O Ca Loi Primary Va Thanh Cong Replica",
     "content": "function connectWithFallback(cb) { db.connect(primaryUrl, (err, conn) => { if (err) { cb(err); db.connect(replicaUrl, (err2, conn2) => cb(err2, conn2)) } else { cb(null, conn) } }) } — thieu return sau cb(err) khi ket noi primary that bai — code van tiep tuc thu ket noi replica VA goi cb lan 2 voi ket qua tu do — code goi ham nhan duoc thong bao loi TRUOC roi sau do lai nhan duoc ket noi thanh cong, neu logic phia caller da xu ly nhanh loi (vi du hien thi banner 'mat ket noi' cho user) thi banner do van con hien thi du he thong da that su ket noi thanh cong qua replica.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},
    {"id": "js-b9-dc-015", "title": "Double Callback: Ham Middleware Xac Thuc Chu Ky HMAC Webhook Goi next() O Nhanh Sai Chu Ky Va Nhanh Dung",
     "content": "function verifyHmacMiddleware(req, res, next) { const valid = verifySignature(req.headers['x-signature'], req.rawBody); if (!valid) { res.status(401).json({ error: 'invalid signature' }); next(new Error('unauthorized')) } next() } — 2 loi cong don: thieu return sau ca block if(!valid) LAN thieu else — voi chu ky SAI, code goi next(err) (bao loi cho Express error handler) VA VAN goi next() KHONG THAM SO ngay sau do (coi nhu request hop le tiep tuc) — Express co the xu ly ca 2 duong dan goi next() gay hanh vi khong xac dinh, tham chi co nguy co request voi chu ky SAI van duoc xu ly tiep nhu request hop le.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta double_callback)", "url": "", "pattern_ids": ["double_callback"]},

    # ============= ZALGO (15 doc) =============
    {"id": "js-b9-zalgo-001", "title": "Zalgo: Ham Format Currency Tra Ve Dong Bo Neu Co Locale Cache San, Bat Dong Bo Neu Phai Tai Locale Data Moi",
     "content": "function formatPrice(amount, locale, cb) { if (localeCache.has(locale)) { cb(formatWithLocale(amount, localeCache.get(locale))) } else { import(`./locales/${locale}.js`).then(mod => { localeCache.set(locale, mod.default); cb(formatWithLocale(amount, mod.default)) }) } } — nhanh cache hit goi cb() dong bo, nhanh cache miss goi cb() bat dong bo (dynamic import) — code goi formatPrice() nhieu lan lien tiep voi cac locale khac nhau se thay thu tu hien thi gia tien tren UI khong theo dung thu tu goi ham, gay UI hien thi lon xon khi render danh sach san pham voi nhieu locale khac nhau.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-002", "title": "Zalgo: Middleware Kiem Tra Feature Flag Tra Ve Dong Bo Tu Local Override Bat Dong Bo Tu Remote Config Service",
     "content": "function checkFeatureFlag(flagName, cb) { if (process.env[`FLAG_${flagName}`]) { cb(process.env[`FLAG_${flagName}`] === 'true') } else { flagService.get(flagName).then(cb) } } — trong moi truong dev (co env var override) callback chay dong bo, trong production (phai goi flagService that) callback chay bat dong bo — code test tich hop viet va chay pass o moi truong dev (do hanh vi dong bo lam test khong can doi async) nhung fail hoac flaky o production do hanh vi bat dong bo thuc su khac han.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-003", "title": "Zalgo: Ham Kiem Tra Quyen Truy Cap Goi Callback Dong Bo Cho Admin Bat Dong Bo Cho User Thuong Can Query DB",
     "content": "function checkPermission(user, resource, cb) { if (user.role === 'admin') { cb(true) } else { db.permissions.findOne({ userId: user.id, resourceId: resource.id }).then(perm => cb(!!perm)) } } — admin nhan callback DONG BO (khong I/O), user thuong nhan callback BAT DONG BO (query database) — code goi checkPermission() trong 1 vong lap kiem tra nhieu resource se co thu tu callback KHONG NHAT QUAN tuy user la admin hay khong, gay kho khan khi viet logic gom nhom ket qua permission theo dung thu tu resource ban dau.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-004", "title": "Zalgo: Ham Tinh Toan Thue Goi Callback Dong Bo Voi Cong Thuc Fixed-Rate Bat Dong Bo Khi Can Goi API Ty Gia Ngoai",
     "content": "function calculateTax(amount, currency, cb) { if (currency === 'USD') { cb(amount * 0.08) } else { exchangeRateApi.convert(amount, currency, 'USD').then(usdAmount => cb(usdAmount * 0.08)) } } — voi USD (truong hop pho bien nhat) callback chay dong bo, cac currency khac phai goi API ty gia bat dong bo — code tinh tong hoa don gom nhieu item o cac currency khac nhau se nhan ket qua tinh thue KHONG THEO DUNG THU TU item, gay kho khan khi hien thi bang chi tiet hoa don theo dung thu tu san pham.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-005", "title": "Zalgo: Thu Vien Parse Markdown Tra Ve Dong Bo Cho Text Thuan Bat Dong Bo Khi Co Code Block Can Highlight Syntax",
     "content": "function renderMarkdown(text, cb) { if (!text.includes('```')) { cb(simpleRender(text)) } else { import('./syntax-highlighter.js').then(highlighter => cb(fullRender(text, highlighter))) } } — text KHONG co code block render dong bo (nhanh), text CO code block phai dynamic import thu vien highlight bat dong bo — component render danh sach nhieu comment (1 so co code, 1 so khong) se nhan ket qua render khong theo dung thu tu comment goc, gay giao dien hien thi comment lon xon neu code phu thuoc vao thu tu callback de sap xep DOM.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-006", "title": "Zalgo: Ham Xac Thuc Input Form Tra Ve Dong Bo Cho Regex Check Bat Dong Bo Khi Can Kiem Tra Username Unique",
     "content": "function validateField(fieldName, value, cb) { if (fieldName !== 'username') { cb(REGEX_RULES[fieldName].test(value)) } else { checkUsernameAvailable(value).then(cb) } } — hau het field validate dong bo (regex nhanh), rieng field 'username' validate bat dong bo (query database check trung) — form co nhieu field duoc validate dong thoi qua vong lap goi validateField() se hien thi ket qua loi/hop le KHONG THEO DUNG THU TU field tren man hinh, gay UX kho hieu khi user thay thong bao loi 'nhay' khong theo thu tu ho nhap.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-007", "title": "Zalgo: Ham Lay Avatar User Tra Ve Dong Bo Neu Co Gravatar URL San Bat Dong Bo Neu Phai Generate Avatar Mac Dinh",
     "content": "function getAvatarUrl(user, cb) { if (user.gravatarHash) { cb(`https://gravatar.com/avatar/${user.gravatarHash}`) } else { generateDefaultAvatar(user.name).then(cb) } } — generateDefaultAvatar() la async (co the goi service tao anh SVG tu chu cai dau ten) — danh sach user hien thi avatar (co gravatar VA khong co) render qua vong lap goi getAvatarUrl() se nhan URL avatar theo thu tu KHONG NHAT QUAN, cac avatar 'generate' co the xuat hien tre hon dang ke so voi avatar gravatar trong cung 1 danh sach, gay hien tuong layout shift ngau nhien khi trang dang tai.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-008", "title": "Zalgo: Middleware Nen Response Tra Ve Dong Bo Neu Response Nho Bat Dong Bo Neu Phai Goi Worker Thread Nen Response Lon",
     "content": "function compressResponse(data, cb) { if (data.length < 1000) { cb(gzipSync(data)) } else { const worker = new Worker('./gzip-worker.js', { workerData: data }); worker.on('message', cb) } } — response nho nen dong bo (nhanh, sync), response lon offload sang worker_threads (bat dong bo) — server xu ly nhieu request dong thoi voi kich thuoc response da dang se co thu tu hoan tat request KHONG THEO DUNG THU TU nhan request, gay kho khan khi debug logging middleware dua vao gia dinh 'request nao goi truoc thi log truoc'.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-009", "title": "Zalgo: Ham Kiem Tra Spam Comment Tra Ve Dong Bo Voi Blacklist Tu Khoa Local Bat Dong Bo Khi Goi ML Model API Ngoai",
     "content": "function checkSpam(text, cb) { const hasBlacklistedWord = BLACKLIST.some(w => text.includes(w)); if (hasBlacklistedWord) { cb(true) } else { mlSpamDetector.predict(text).then(isSpam => cb(isSpam)) } } — text co tu khoa blacklist tra ket qua dong bo NGAY (khong can goi ML model), text khong co tu khoa phai goi ML API bat dong bo de kiem tra ky hon — he thong duyet nhieu comment cung luc se co ket qua kiem duyet tra ve KHONG THEO DUNG THU TU comment duoc gui, gay kho khan khi hien thi trang thai 'dang kiem duyet' dung thu tu cho nguoi dung theo doi comment cua ho.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-010", "title": "Zalgo: Ham Resolve Duong Dan Import Module Tra Ve Dong Bo Cho Module Built-in Bat Dong Bo Khi Phai Doc package.json De Resolve Alias",
     "content": "function resolveModulePath(moduleName, cb) { if (BUILTIN_MODULES.includes(moduleName)) { cb(moduleName) } else { fs.readFile('./package.json', 'utf8', (err, content) => { const aliases = JSON.parse(content).aliases || {}; cb(aliases[moduleName] || moduleName) }) } } — module built-in (fs, path, http...) resolve dong bo ngay, module custom can doc package.json de tim alias thi resolve bat dong bo — bundler tu che dung ham nay de resolve nhieu import trong 1 file se xu ly cac import THEO THU TU KHONG NHAT QUAN, co the gay loi thu tu khoi tao module sai (vi du module A can B da san sang nhung B bi resolve tre hon do phai doc file).",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-011", "title": "Zalgo: Ham Lay Gia San Pham Tra Ve Dong Bo Tu Cache Redis Local Bat Dong Bo Khi Phai Goi Pricing Engine Cho San Pham Dong Gia",
     "content": "function getProductPrice(productId, cb) { const cachedPrice = priceCache.get(productId); if (cachedPrice !== undefined) { cb(cachedPrice) } else { pricingEngine.calculate(productId).then(price => { priceCache.set(productId, price); cb(price) }) } } — san pham gia tinh cache san (dong bo), san pham chua co cache (dong gia, moi ra mat) phai tinh qua pricing engine (bat dong bo) — trang danh sach san pham render gia qua vong lap goi ham nay se hien thi gia THEO THU TU KHONG THEO DUNG THU TU san pham hien thi, gay UI 'nhay' gia san pham khong theo thu tu cot/hang du kien tren luoi san pham.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-012", "title": "Zalgo: Ham Xu Ly Su Kien Analytics Tra Ve Dong Bo Neu Batch Buffer Chua Day Bat Dong Bo Khi Buffer Day Phai Flush Ngay",
     "content": "function trackEvent(event, cb) { eventBuffer.push(event); if (eventBuffer.length < BATCH_SIZE) { cb() } else { flushEventsToServer(eventBuffer).then(() => { eventBuffer.length = 0; cb() }) } } — hau het lan goi callback dong bo (chi push vao buffer), nhung DINH KY (khi buffer day) callback chay bat dong bo (network call flush) — code goi trackEvent() nhieu lan lien tiep se thay hau het callback chay ngay nhung dinh ky co 1 lan bi cham dang ke, gay do tre khong deu rat kho phat hien qua profiling thong thuong, dac biet gay hai neu code goi tiep theo gia dinh trackEvent() luon nhanh.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-013", "title": "Zalgo: Ham Kiem Tra Vi Tri Dia Ly Nguoi Dung Tra Ve Dong Bo Tu GPS Cache Bat Dong Bo Khi Phai Xin Quyen Truy Cap Location Moi",
     "content": "function getUserLocation(cb) { if (lastKnownLocation && Date.now() - lastKnownLocation.time < 60000) { cb(lastKnownLocation.coords) } else { navigator.geolocation.getCurrentPosition(pos => cb(pos.coords)) } } — vi tri con 'moi' (duoi 1 phut) tra ve dong bo tu cache, vi tri het han/chua co phai xin GPS bat dong bo (co the yeu cau user cap quyen, mat vai giay) — component ban do goi ham nay lien tuc de cap nhat vi tri se nhan ket qua ve KHONG THEO DUNG THU TU thoi gian goi, co the ve sai thu tu duong di neu logic khong tu sap xep lai theo timestamp thuc te.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-014", "title": "Zalgo: Ham Load Plugin Cho He Thong Extension Tra Ve Dong Bo Voi Plugin Da Duoc Require San Bat Dong Bo Khi Phai Tai Tu NPM Registry",
     "content": "function loadPlugin(pluginName, cb) { if (require.cache[require.resolve(pluginName)]) { cb(require(pluginName)) } else { npmInstall(pluginName).then(() => cb(require(pluginName))) } } — plugin da co san trong module cache load dong bo, plugin CHUA CO phai npm install truoc (bat dong bo, co the mat hang chuc giay) — he thong khoi tao nhieu plugin cung luc qua vong lap se khoi tao chung THEO THU TU KHONG NHAT QUAN, gay loi neu 1 plugin phu thuoc plugin khac phai duoc khoi tao truoc no ma thu tu bi dao lon do zalgo.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},
    {"id": "js-b9-zalgo-015", "title": "Zalgo: Ham Kiem Tra Trang Thai Domain SSL Certificate Tra Ve Dong Bo Tu Cache Bat Dong Bo Khi Phai Query CA That Su",
     "content": "function checkSSLStatus(domain, cb) { const cached = sslStatusCache.get(domain); if (cached && Date.now() - cached.checkedAt < 3600000) { cb(cached.status) } else { checkCertificateAuthority(domain).then(status => { sslStatusCache.set(domain, { status, checkedAt: Date.now() }); cb(status) }) } } — domain vua duoc check trong 1 gio tra ve dong bo, domain chua check/het han cache phai query CA that su (bat dong bo, mat vai giay) — dashboard monitoring hien thi trang thai SSL cho nhieu domain cung luc se hien thi ket qua THEO THU TU KHONG NHAT QUAN voi thu tu domain tren man hinh, gay kho theo doi domain nao dang duoc kiem tra khi UI cap nhat lon xon.",
     "language": "javascript", "category": "anti-patterns",
     "source": "Generated (batch9, dua tren mo ta zalgo)", "url": "", "pattern_ids": ["zalgo"]},

    # ============= CONCURRENT_WRITE_ARRAY (15 doc) =============
    {"id": "js-b9-cwa-001", "title": "Concurrent Write: Nhieu Test Parallel Trong Cypress Cung Ghi Vao Mang Global Test Artifacts Log Chia Se Qua File",
     "content": "// support/e2e.js: let artifacts = JSON.parse(fs.readFileSync('artifacts.json', 'utf8')); afterEach(() => { artifacts.push({ test: Cypress.currentTest.title, screenshot: getScreenshotPath() }); fs.writeFileSync('artifacts.json', JSON.stringify(artifacts)) }) — Cypress chay nhieu spec file song song qua nhieu process (--parallel flag), moi process doc/ghi CUNG 1 file artifacts.json doc lap — cac process ghi de len nhau, file artifacts.json cuoi cung chi con danh sach cua process ghi sau cung, mat artifact cua cac spec file khac da chay xong truoc do.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch9, dua tren mo ta concurrent_write_array)", "url": "", "pattern_ids": ["concurrent_write_array"]},
    {"id": "js-b9-cwa-002", "title": "Concurrent Write: Nhieu Webhook Provider Khac Nhau Cung Ghi Vao Mang Notification Center Chung Cua User Qua Redis List",
     "content": "async function pushNotification(userId, notif) { const list = await redis.lrange(`notif:${userId}`, 0, -1); list.push(JSON.stringify(notif)); await redis.del(`notif:${userId}`); await redis.rpush(`notif:${userId}`, ...list) } — cach lam nay (doc toan bo list, sua trong JS, xoa roi ghi lai) khong tan dung Redis LPUSH/RPUSH atomic co san — 2 webhook (vi du Stripe va SendGrid) gui thong bao cho cung 1 user gan nhu dong thoi se doc list cu giong nhau, ca 2 cung xoa va ghi lai, 1 trong 2 notification bi mat do ghi de — dung truc tiep redis.rpush(key, notif) se atomic va an toan hon nhieu.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch9, dua tren mo ta concurrent_write_array)", "url": "", "pattern_ids": ["concurrent_write_array"]},
    {"id": "js-b9-cwa-003", "title": "Concurrent Write: Nhieu Thread Trong Deno Worker Cung Ghi Vao Mang Shared Qua postMessage Ma Khong Dong Bo Update UI State",
     "content": "let taskResults = []; for (let i = 0; i < 4; i++) { const worker = new Worker('./task.js', { type: 'module' }); worker.postMessage({ id: i }); worker.onmessage = (e) => { taskResults.push(e.data); updateProgressBar(taskResults.length / 4) } } — 4 worker hoan thanh gan nhu dong thoi, moi onmessage handler push vao taskResults va doc length de update progress bar — trong runtime don luong (main thread nhan message) day thuc te an toan tuan tu, NHUNG neu code duoc port sang moi truong co nhieu main thread nhan message song song (edge case cua mot so runtime khac), co the mat update tien do.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch9, dua tren mo ta concurrent_write_array)", "url": "", "pattern_ids": ["concurrent_write_array"]},
    {"id": "js-b9-cwa-004", "title": "Concurrent Write: Nhieu Serverless Function Cung Ghi Vao Mang Feature Usage Metrics Truoc Khi Flush Dinh Ky Ve CloudWatch",
     "content": "let metricsBuffer = []; exports.handler = async (event) => { metricsBuffer.push({ feature: event.feature, timestamp: Date.now() }); if (metricsBuffer.length >= 20) { await flushMetrics(metricsBuffer); metricsBuffer = [] } return handleRequest(event) } — moi Lambda 'warm' instance (duoc tai su dung giua cac invocation) giu bien metricsBuffer RIENG cua no (khong chia se giua cac instance khac nhau do auto-scaling) — voi nhieu instance chay song song duoi tai cao, moi instance flush metrics doc lap voi buffer nho hon 20 that su du dinh, gay so lan flush (va chi phi API call) nhieu hon can thiet thay vi gom du 20 item that su.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch9, dua tren mo ta concurrent_write_array)", "url": "", "pattern_ids": ["concurrent_write_array"]},
    {"id": "js-b9-cwa-005", "title": "Concurrent Write: Nhieu Nguoi Choi Trong Turn-Based Game Cung Ghi Vao Mang Move History Khi Client Gui Move Trung Thoi Diem Do Lag",
     "content": "let moveHistory = []; socket.on('move', async (data) => { const gameState = await loadGameState(data.gameId); if (isValidMove(gameState, data.move)) { moveHistory.push(data.move); await saveGameState(gameId, applyMove(gameState, data.move)) } }) — 2 client gui move gan nhu dong thoi (do lag mang, client A khong biet client B da di truoc) — ca 2 cung load gameState cu giong nhau, ca 2 cung qua kiem tra isValidMove() (vi ca 2 deu dua tren state cu), ca 2 cung push vao moveHistory va save — game state cuoi cung ghi de mat 1 nuoc di, du ca 2 client deu thay move cua ho da duoc chap nhan.",
     "language": "javascript", "category": "race-conditions",
     "source": "Generated (batch9, dua tren mo ta concurrent_write_array)", "url": "", "pattern_ids": ["concurrent_write_array"]},
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
