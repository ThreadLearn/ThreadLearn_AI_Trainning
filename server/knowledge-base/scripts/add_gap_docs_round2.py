"""
AI2 — round 2 bo sung doc cho 4 pattern_id van con mong nhat sau round 1
(concurrent_write_array, context_loss_this, resource_exhaustion, missing_join —
moi pattern dang chi co 1 doc). Moi doc round nay khai thac 1 khia canh KHAC
han doc round 1 cung pattern (khong lap lai vi du/noi dung), de tang tinh da
dang khi BM25 retrieve.

Doi chieu voi round 1 (js-gap-001..004) de dam bao khong trung:
- concurrent_write_array: round1 noi ve idempotency key / mutex chung -> round2
  noi ve Promise.all + push khong dedupe (OAuth token duplicate, khac co che).
- context_loss_this: round1 noi ve AsyncLocalStorage/promisify -> round2 noi ve
  setTimeout/class method mat 'this' co ban (khac hoan toan co che).
- resource_exhaustion: round1 noi ve EMFILE file descriptor -> round2 noi ve
  database connection pool exhausted (loai tai nguyen khac: network conn, khong
  phai file).
- missing_join: round1 noi ve worker_threads.join() -> round2 noi ve forEach
  khong doi async callback (khac co che: khong lien quan worker thread).

Nguon: GitHub Issues that. Chay: python add_gap_docs_round2.py
"""
import json
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base.json"

NEW_DOCS = [
    {
        "id": "js-gap2-001",
        "title": "Concurrent Array Push Without Dedup: Duplicate Entries from Promise.all",
        "content": (
            "Nhieu request dong thoi cung push item vao 1 mang/token-list shared "
            "(vi du OAuth token store) ma khong kiem tra trung lap truoc khi ghi — "
            "moi call chay Promise.all doc gia tri hien tai, roi push ban rieng cua "
            "no, dan den nhieu ban ghi trung nhau thay vi 1 ban duy nhat. Khac voi "
            "loi mat du lieu do idempotency key trung (xem js-gap-001), day la loi "
            "NGUOC LAI: du lieu khong bi mat ma bi NHAN BAN — tung tab/request tao "
            "token rieng, token cu tro thanh stale nhung van con trong mang, khien "
            "API call sau nay dung nham token da het han (xem GitHub issue "
            "AARVAK-VSET/launchpad-node #14: xac thuc dong thoi qua nhieu tab tao "
            "nhieu entry token trung trong mang luu tru). Fix: doc-sua-ghi (check "
            "trung + push) phai la 1 thao tac atomic — dung Map/Set thay Array de "
            "tu loai trung theo key, hoac lock quanh toan bo chu ky doc-ghi thay vi "
            "chi lock luc ghi."
        ),
        "language": "javascript",
        "category": "race-conditions",
        "source": "GitHub Issues (AARVAK-VSET/launchpad-node #14)",
        "url": "https://github.com/AARVAK-VSET/launchpad-node/issues/14",
        "pattern_ids": ["concurrent_write_array"],
    },
    {
        "id": "js-gap2-002",
        "title": "setTimeout Truyen Method Truc Tiep Lam Mat 'this' (Class Instance)",
        "content": (
            "Truyen thang method cua 1 class instance vao setTimeout/setInterval "
            "(vi du setTimeout(user.sayHi, 1000)) khien callback chay voi 'this' tro "
            "ve global object hoac undefined (strict mode), khong phai instance goc "
            "— vi setTimeout goi ham nhu 1 function doc lap, khong con giu lien ket "
            "voi object ma method do thuoc ve. Ket qua: truy cap this.propertyName "
            "ben trong callback nem TypeError hoac tra ve undefined thay vi gia tri "
            "mong doi. Day la truong hop CO BAN nhat cua mat context — khac voi loi "
            "AsyncLocalStorage bi mat qua boundary bat dong bo phuc tap (xem "
            "js-gap-002), o day chi don gian la JavaScript function khong tu dong "
            "'nho' object goc khi duoc truyen di noi khac. Fix: setTimeout(() => "
            "user.sayHi(), 1000) (arrow function wrap), hoac "
            "setTimeout(user.sayHi.bind(user), 1000), hoac khai bao method bang "
            "class field arrow function (sayHi = () => {...}) de tu dong bind luc "
            "khoi tao instance."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "javascript.info — Function binding",
        "url": "https://javascript.info/bind",
        "pattern_ids": ["context_loss_this"],
    },
    {
        "id": "js-gap2-003",
        "title": "Database Connection Pool Exhausted: 'Too Many Clients Already'",
        "content": (
            "Goi nhieu query dong thoi (vi du qua Promise.all) ma khong release "
            "connection ve pool sau khi dung, hoac pool size mac dinh (thuong max: "
            "10) qua nho so voi tai thuc te, dan den loi 'sorry, too many clients "
            "already' (Postgres) hoac 'too many connections' (MySQL) — cac call sau "
            "bi timeout hoac hang vo han neu connectionTimeoutMillis khong duoc cau "
            "hinh. Day la tai nguyen mang (network connection) can kiet, KHAC voi "
            "EMFILE la file descriptor can kiet o cap OS (xem js-gap-003) — 2 loai "
            "tai nguyen khac nhau du trieu chung tuong tu (bi tu choi khi mo qua "
            "nhieu). Nguyen nhan pho bien nhat: quen goi client.release() sau khi "
            "dung xong connection tu pool.connect() (xem node-postgres issue #1289, "
            "#557). Fix: luon release() trong try/finally, cau hinh max pool size "
            "hop ly voi tai thuc te (vi du 20), dat idleTimeoutMillis de dong bot "
            "connection nhan roi, va connectionTimeoutMillis > 0 de fail nhanh thay "
            "vi hang mai."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "GitHub Issues (brianc/node-postgres #1289, #557)",
        "url": "https://github.com/brianc/node-postgres/issues/1289",
        "pattern_ids": ["resource_exhaustion"],
    },
    {
        "id": "js-gap2-004",
        "title": "forEach Khong Doi Async Callback: Vong Lap Ket Thuc Truoc Khi Xong Viec",
        "content": (
            "Dung Array.prototype.forEach voi callback async (items.forEach(async "
            "item => { await doSomething(item) })) — forEach KHONG await Promise "
            "callback tra ve, no goi callback lien tuc cho tung item roi thoat ngay, "
            "khong doi bat ky Promise nao hoan tat. Code phia sau vong lap chay "
            "truoc khi cac tac vu ben trong forEach xong — day chinh la 1 dang "
            "'missing join' o cap vong lap: cac tac vu song song dang chay bi bo "
            "roi, khong ai cho chung ket thuc, khac voi worker_threads khong duoc "
            "join() (xem js-gap-004) nhung cung chung ban chat 'khoi tao roi khong "
            "doi xong'. Vi du: items.forEach(async i => await save(i)); "
            "console.log('done') — 'done' in ra truoc khi save() nao thuc su xong "
            "(xem microsoft/vscode issue #117205: nhieu forEach + async trong "
            "codebase khong duoc await dung cach). Fix: dung "
            "for (const item of items) { await doSomething(item) } de chay tuan tu "
            "va cho dung, hoac await Promise.all(items.map(item => doSomething(item))) "
            "de chay song song nhung van doi tat ca hoan tat truoc khi tiep tuc."
        ),
        "language": "javascript",
        "category": "anti-patterns",
        "source": "GitHub Issues (microsoft/vscode #117205)",
        "url": "https://github.com/microsoft/vscode/issues/117205",
        "pattern_ids": ["missing_join"],
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
