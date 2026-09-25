"""
AI2 — bo sung doc cho 4 pattern_id dang 0 doc trong KB (concurrent_write_array,
context_loss_this, resource_exhaustion, missing_join) va cac pattern qua mong
(<10 doc: buffer_leak, promise_no_await, double_callback, zalgo).

Nguon: GitHub Issues/PR that (B2) cho 4 pattern trang, viet tay dua tren
tai lieu chinh thuc MDN/Node.js docs (B3) cho pattern mong. Moi doc gan san
category + pattern_ids khop schema hien co.

Chay: python add_gap_docs.py
"""
import json
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base.json"

NEW_DOCS = [
    # ---- B2: nguon that tu GitHub Issues (4 pattern dang 0 doc) ----
    {
        "id": "js-gap-001",
        "title": "Race Condition: Concurrent Array Mutation Without Sync (Node.js)",
        "content": (
            "Nhieu async task cung push/splice vao 1 mang shared co the gay mat du lieu "
            "hoac thu tu sai, vi moi thao tac khong atomic khi xen ke voi await. "
            "Vi du thuc te: nhieu request handler cung ghi vao 1 mang cache/queue "
            "shared, dan den item bi ghi de hoac idempotency key trung nhau khi 2 "
            "call chay song song cung du lieu (xem MemWal issue #932: 2 call remember() "
            "song song chia se cung idempotency key, request thu 2 bi am tham mat, "
            "khong loi, khong log). Fix: dung mutex/lock (async-mutex), hoac gom "
            "write vao 1 hang doi tuan tu (serialize qua 1 Promise chain), hoac dung "
            "cau truc immutable + reduce thay vi mutate truc tiep mang shared."
        ),
        "language": "javascript",
        "category": "race-conditions",
        "source": "GitHub Issues (MemWal #932, node-js-race-conditions)",
        "url": "https://github.com/MystenLabs/MemWal/issues/932",
        "pattern_ids": ["concurrent_write_array"],
    },
    {
        "id": "js-gap-002",
        "title": "Context Loss: 'this' Undefined Inside Callback Without Bind",
        "content": (
            "Khi truyen method cua object lam callback (vi du obj.method truyen thang "
            "vao setTimeout, array.map, hoac event listener) ma khong bind/arrow "
            "function, 'this' ben trong callback khong con tro ve object goc — thuong "
            "la undefined (strict mode) hoac global object. Van de tuong tu xay ra voi "
            "AsyncLocalStorage/continuation-local-storage: context bi mat qua cac "
            "boundary bat dong bo nhu callback waterfall, middleware session, hoac khi "
            "convert callback sang Promise bang util.promisify (xem Node.js issue "
            "#20127 va #41285). Fix: dung arrow function de ke thua 'this' tu scope "
            "ngoai, hoac .bind(this) truoc khi truyen callback, hoac AsyncLocalStorage "
            "voi enterWith/run duoc goi dung cho o moi async boundary."
        ),
        "language": "javascript",
        "category": "race-conditions",
        "source": "GitHub Issues (nodejs/node #20127, #41285)",
        "url": "https://github.com/nodejs/node/issues/20127",
        "pattern_ids": ["context_loss_this"],
    },
    {
        "id": "js-gap-003",
        "title": "Resource Exhaustion: EMFILE Too Many Open Files (Node.js)",
        "content": (
            "Mo qua nhieu file/socket/connection dong thoi ma khong dong lai vuot gioi "
            "han file descriptor cua he dieu hanh, gay loi EMFILE: too many open files. "
            "Thuong xay ra khi vong lap doc N file bang fs.readFile/createReadStream ma "
            "khong gioi han concurrency, hoac connection pool khong co max size (xem "
            "nodejs/node issue #4386, #25856). He qua: request moi bi tu choi, process "
            "co the crash. Fix: gioi han so file/connection mo dong thoi bang queue "
            "(p-limit, hoac tu viet semaphore), luon dong file/socket trong "
            "try/finally ke ca khi loi, dung thu vien graceful-fs de tu dong retry "
            "khi cham nguong FD, hoac tang ulimit -n neu do la gioi han he thong that "
            "su can thiet."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "GitHub Issues (nodejs/node #4386, #25856)",
        "url": "https://github.com/nodejs/node/issues/4386",
        "pattern_ids": ["resource_exhaustion"],
    },
    {
        "id": "js-gap-004",
        "title": "Missing Join: Worker Thread Not Awaited Before Continuing (Node.js)",
        "content": (
            "Tao worker_threads.Worker nhung khong doi worker hoan tat (khong lang "
            "nghe event 'exit'/'message' hoac khong await mot Promise wrap quanh "
            "worker) truoc khi code tiep tuc chay hoac process thoat — du lieu worker "
            "tra ve co the bi mat, hoac process.exit() bi hang vo han khi co "
            "background job dang cho worker join (xem nodejs/node PR #66171: hang khi "
            "join worker luc process.exit; PR #56191: crash khi worker join sau khi "
            "da exit). Fix: wrap Worker trong Promise, resolve o event 'exit' hoac "
            "'message' cuoi cung, dung Promise.all() de doi tat ca worker truoc khi "
            "tiep tuc logic phu thuoc ket qua cua chung; khong goi process.exit() thu "
            "cong khi con worker chua join."
        ),
        "language": "javascript",
        "category": "race-conditions",
        "source": "GitHub Issues/PR (nodejs/node #66171, #56191)",
        "url": "https://github.com/nodejs/node/pull/66171",
        "pattern_ids": ["missing_join"],
    },
    # ---- B3: viet tay dua tren tai lieu chinh thuc (pattern qua mong) ----
    {
        "id": "js-gap-005",
        "title": "Zalgo: Ham Vua Sync Vua Async Tuy Dieu Kien",
        "content": (
            "'Releasing Zalgo' — mot ham nhan callback nhung doi khi goi callback dong "
            "bo (ngay lap tuc, vi du khi doc tu cache) va doi khi goi bat dong bo (vi "
            "du khi phai doc file/goi network), tuy vao nhanh code nao duoc chay. Dieu "
            "nay pha vo gia dinh cua caller ve thu tu thuc thi: code goi ham co the "
            "chay truoc hoac sau cac dong lenh tiep theo tuy tinh huong, gay bug rat "
            "kho tai hien vi phu thuoc timing/du lieu cu the. Vi du kinh dien: ham "
            "getData(cb) neu co cache thi goi cb(data) ngay, neu khong co cache thi "
            "fetch roi goi cb trong .then() — 2 nhanh nay co do tre khac han nhau. Fix: "
            "luon dam bao callback duoc goi bat dong bo bang cach wrap trong "
            "process.nextTick()/queueMicrotask() du la nhanh sync hay async, hoac dung "
            "async/await + Promise thay callback de trinh dien engine tu dong dam bao "
            "tinh nhat quan."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "Node.js Design Patterns (isaacs, 'Designing APIs for Async')",
        "url": "https://blog.izs.me/2013/08/designing-apis-for-asynchrony/",
        "pattern_ids": ["zalgo"],
    },
    {
        "id": "js-gap-006",
        "title": "Double Callback: Callback Bi Goi Nhieu Hon Mot Lan",
        "content": (
            "Mot callback duoc goi nhieu hon 1 lan do code khong return sau khi goi "
            "callback trong 1 nhanh dieu kien, khien nhanh con lai cung goi callback "
            "do — hoac do vua goi callback vua throw/reject cho cung 1 loi. Hau qua: "
            "caller nhan ket qua/loi lap lai, co the ghi database 2 lan, gui email 2 "
            "lan, hoac crash do handler khong ky vong duoc goi lan 2. Vi du: function "
            "readFile(path, cb) { fs.stat(path, (err, stat) => { if (err) cb(err); "
            "if (stat.size > MAX) cb(new Error('too big')); ... cb(null, data) }) } — "
            "thieu return sau moi lan goi cb khien ca 2 nhanh loi va nhanh thanh cong "
            "co the cung chay. Fix: luon 'return cb(...)' de dam bao ham dung ngay sau "
            "khi goi callback lan dau, hoac dung 1 flag 'called' de guard, tot nhat la "
            "chuyen sang Promise (Promise chi resolve/reject 1 lan duy nhat, cac lan "
            "sau tu dong bi bo qua)."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "Node.js callback conventions (Node.js API docs)",
        "url": "https://nodejs.org/api/errors.html#error-first-callbacks",
        "pattern_ids": ["double_callback"],
    },
    {
        "id": "js-gap-007",
        "title": "Missing Await: Goi Ham Async Nhung Quen Await Ket Qua",
        "content": (
            "Goi 1 ham async/Promise-returning nhung khong await hoac .then() ket "
            "qua — code tiep tuc chay ngay ma khong doi operation hoan tat. Neu "
            "operation la ghi database/file, code phia sau co the doc du lieu chua "
            "duoc ghi xong (stale read). Neu la trong vong lap, cac call se chay song "
            "song ngoai y muon thay vi tuan tu, co the vuot rate limit hoac gay race "
            "condition tren tai nguyen chung. Loi con nguy hiem hon khi Promise bi "
            "reject ma khong ai bat — tro thanh unhandled rejection. Vi du: "
            "async function save(data) { db.insert(data); return 'ok' } — thieu await "
            "truoc db.insert khien ham tra ve 'ok' truoc khi biet insert co thanh cong "
            "khong. Fix: luon await hoac return truc tiep Promise (return db.insert(data)), "
            "bat eslint rule no-floating-promises de phat hien tu dong luc build."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "MDN Web Docs — async/await",
        "url": "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous/Promises",
        "pattern_ids": ["promise_no_await"],
    },
    {
        "id": "js-gap-008",
        "title": "Buffer/Stream Leak: Khong Dong Stream Sau Khi Dung/Loi",
        "content": (
            "Mo Readable/Writable stream (doc file, HTTP response, database cursor) "
            "nhung khong goi .destroy()/.close() khi loi xay ra giua chung hoac khi "
            "consumer dung doc som (vi du pipe bi huy). Stream con lai o trang thai mo "
            "tiep tuc giu file descriptor va buffer trong memory, tich luy qua nhieu "
            "request se gay memory leak va cuoi cung EMFILE (lien quan resource_exhaustion). "
            "Vi du: const rs = fs.createReadStream(path); rs.pipe(res); — neu res bi "
            "client dong som (client huy request), 'rs' khong tu dong destroy tru khi "
            "dung pipeline() thay pipe() truc tiep. Fix: dung stream.pipeline() (Node.js "
            "core, tu dong cleanup ca 2 dau khi 1 ben loi/dong), hoac tu bat event "
            "'close'/'error' cua ca 2 stream de goi destroy() thu cong cho ben con lai."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "Node.js Stream API docs",
        "url": "https://nodejs.org/api/stream.html#streampipelinesource-transforms-destination-callback",
        "pattern_ids": ["buffer_leak"],
    },
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
