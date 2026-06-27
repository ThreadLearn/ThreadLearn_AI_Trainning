#!/usr/bin/env python3
"""
AI1-01b | Edge Cases Generator
Sinh ra 250 mẫu dữ liệu đặc trị (Zalgo, Double CB, File Append, Leak, Singleton Race).
Mục đích: Chữa bệnh Overfitting của AI, ép AI sử dụng Chain-of-Thought cho các lỗi luồng.
"""

import json
import os

DOMAINS = [
    ("User", "user", "userId", "users"),
    ("Product", "prod", "productId", "products"),
    ("Order", "ord", "orderId", "orders"),
    ("Invoice", "inv", "invoiceId", "invoices"),
    ("Payment", "pay", "paymentId", "payments"),
    ("Comment", "cmt", "commentId", "comments"),
    ("Article", "art", "articleId", "articles"),
    ("Settings", "set", "settingsId", "settings"),
    ("Config", "cfg", "configId", "configs"),
    ("Session", "sess", "sessionId", "sessions")
]

# Random words to augment
VERBS = ["load", "fetch", "get", "retrieve", "pull"]

def generate_zalgo_pairs():
    pairs = []
    for d in DOMAINS:
        for v in VERBS:
            entity, prefix, _, _ = d
            func_name = f"{v}{entity}Data"
            cache_var = f"global.{prefix}Cache"
            
            inp = f"""function {func_name}(cb) {{
  if ({cache_var}) {{
    cb(null, {cache_var});
    return;
  }}
  db.query('SELECT * FROM {prefix}', (err, data) => {{
    {cache_var} = data;
    cb(err, data);
  }});
}}"""
            
            out = f"""// THOUGHT PROCESS:
// 1. Phân tích: Hàm {func_name} gọi callback đồng bộ (synchronous) khi có cache, nhưng lại gọi dị bộ (asynchronous) khi truy vấn DB. Đây là lỗi Zalgo kinh điển, gây rủi ro Race Condition không lường trước cho luồng gọi.
// 2. Giải pháp: Cần chuẩn hóa luồng thực thi bằng cách đưa nhánh đồng bộ vào Event Loop thông qua `process.nextTick` hoặc `setImmediate`.

function {func_name}(cb) {{
  if ({cache_var}) {{
    process.nextTick(() => cb(null, {cache_var}));
    return;
  }}
  db.query('SELECT * FROM {prefix}', (err, data) => {{
    {cache_var} = data;
    cb(err, data);
  }});
}}"""
            pairs.append({"input": inp, "output": out, "category": "Zalgo"})
    return pairs

def generate_leak_pairs():
    pairs = []
    for d in DOMAINS:
        for v in VERBS:
            entity, prefix, _, _ = d
            route = f"/stream/{prefix}"
            target_url = f"http://internal-service/{prefix}.dat"
            
            inp = f"""app.get('{route}', (req, res) => {{
  const {prefix}Stream = http.request('{target_url}');
  {prefix}Stream.pipe(res);
  {prefix}Stream.on('error', (e) => res.status(500).end());
}});"""
            
            out = f"""// THOUGHT PROCESS:
// 1. Phân tích: Đoạn code pipe stream `{prefix}Stream` thẳng vào `res`. Tuy nhiên, nếu phía client (người dùng) đột ngột ngắt kết nối (đóng tab, rớt mạng), stream nguồn vẫn tiếp tục tải dữ liệu vào bộ nhớ, gây ra lỗi Buffer Leak (Rò rỉ RAM).
// 2. Giải pháp: Phải lắng nghe sự kiện `close` trên request (req) để chủ động tiêu hủy (destroy) stream nguồn khi client ngắt mạng.

app.get('{route}', (req, res) => {{
  const {prefix}Stream = http.request('{target_url}');
  {prefix}Stream.pipe(res);
  
  {prefix}Stream.on('error', (e) => res.status(500).end());
  
  // Dọn dẹp rác, chống rò rỉ bộ nhớ
  req.on('close', () => {{
    {prefix}Stream.destroy();
  }});
}});"""
            pairs.append({"input": inp, "output": out, "category": "Buffer Leak"})
    return pairs

def generate_double_cb_pairs():
    pairs = []
    for d in DOMAINS:
        for v in VERBS:
            entity, prefix, _, _ = d
            func_name = f"{v}Cached{entity}"
            key = f"{prefix}_key"
            
            inp = f"""function {func_name}({key}, callback) {{
  redis.get({key}, (err, result) => {{
    if (err) callback(err);
    if (!result) callback(new Error('Miss'));
    callback(null, JSON.parse(result));
  }});
}}"""
            
            out = f"""// THOUGHT PROCESS:
// 1. Phân tích: Trong hàm `{func_name}`, khi có lỗi `err` hoặc không có `result`, hàm gọi `callback()` nhưng KHÔNG dùng lệnh `return`. Hệ quả là code sẽ tiếp tục chạy xuống dưới và gọi `callback` thêm lần nữa. Đây là lỗi Double Callback (Gửi Response 2 lần) gây sập server.
// 2. Giải pháp: Thêm từ khóa `return` trước các callback lỗi để ngắt ngay luồng thực thi.

function {func_name}({key}, callback) {{
  redis.get({key}, (err, result) => {{
    if (err) return callback(err);
    if (!result) return callback(new Error('Miss'));
    return callback(null, JSON.parse(result));
  }});
}}"""
            pairs.append({"input": inp, "output": out, "category": "Double Callback"})
    return pairs

def generate_singleton_race_pairs():
    pairs = []
    for d in DOMAINS:
        for v in VERBS:
            entity, prefix, _, _ = d
            class_name = f"{entity}Manager"
            
            inp = f"""class {class_name} {{
  constructor() {{ this.data = null; }}
  {v}() {{
    if (!this.data) {{
      fetch('/api/{prefix}').then(res => res.json()).then(d => {{
        this.data = d;
      }});
    }}
    return this.data;
  }}
}}"""
            
            out = f"""// THOUGHT PROCESS:
// 1. Phân tích: Class `{class_name}` cố gắng lưu cache vào `this.data`. Nhưng quá trình `fetch` là bất đồng bộ. Nếu có nhiều requests gọi hàm `{v}()` cùng lúc khi chưa có cache, hàm fetch sẽ bị gọi đi gọi lại nhiều lần (Race Condition). Ngoài ra nó trả về data bị `undefined` ở lần đầu tiên.
// 2. Giải pháp: Thay vì lưu kết quả cuối cùng, hãy lưu chính cái `Promise` đang gọi. Các request sau sẽ chờ chung cái Promise đó.

class {class_name} {{
  constructor() {{ 
    this.promise = null; 
  }}
  
  {v}() {{
    if (!this.promise) {{
      this.promise = fetch('/api/{prefix}')
        .then(res => res.json())
        .catch(err => {{
           this.promise = null; // Xóa cache nếu lỗi
           throw err;
        }});
    }}
    return this.promise;
  }}
}}"""
            pairs.append({"input": inp, "output": out, "category": "Singleton Race"})
    return pairs

def generate_file_append_pairs():
    pairs = []
    for d in DOMAINS:
        for v in VERBS:
            entity, prefix, _, _ = d
            func_name = f"log{entity}Action"
            file_name = f"{prefix}_audit.log"
            
            inp = f"""function {func_name}(action) {{
  fs.readFile('{file_name}', 'utf8', (err, log) => {{
    const entry = log + `[LOG]: ${{action}}\\n`;
    fs.writeFile('{file_name}', entry, (err) => {{}});
  }});
}}"""
            
            out = f"""// THOUGHT PROCESS:
// 1. Phân tích: Hàm `{func_name}` thực hiện đọc file rồi ghi đè lên file. Trong Node.js, I/O là bất đồng bộ. Nếu có nhiều tiến trình gọi hàm này cùng lúc, chúng sẽ đọc cùng một file cũ và ghi đè lẫn nhau, làm mất toàn bộ log mới (Race Condition kinh điển).
// 2. Giải pháp: Phải sử dụng hàm `fs.appendFile` để OS tự động khóa file ở tầng hệ điều hành (Atomic operation) khi ghi chèn thêm vào cuối file.

function {func_name}(action) {{
  const entry = `[LOG]: ${{action}}\\n`;
  fs.appendFile('{file_name}', entry, 'utf8', (err) => {{
    if (err) console.error("Failed to append log", err);
  }});
}}"""
            pairs.append({"input": inp, "output": out, "category": "File Append Race"})
    return pairs

def main():
    print("-> Bat dau sinh du lieu dac tri...")
    all_pairs = []
    all_pairs.extend(generate_zalgo_pairs())
    all_pairs.extend(generate_leak_pairs())
    all_pairs.extend(generate_double_cb_pairs())
    all_pairs.extend(generate_singleton_race_pairs())
    all_pairs.extend(generate_file_append_pairs())
    
    output_file = "edge_cases.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_pairs, f, ensure_ascii=False, indent=2)
        
    print(f"-> Da sinh thanh cong {len(all_pairs)} mau du lieu dac tri vao {output_file}")

if __name__ == "__main__":
    main()
