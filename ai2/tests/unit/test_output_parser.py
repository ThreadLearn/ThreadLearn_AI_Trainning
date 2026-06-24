from output_parser import cleanOutput, clean_repetition

def run_tests():
    print("🚀 Bắt đầu chạy Unit Test cho Output Parser (Task AI1-08)...\n")

    # Case 1: Lặp code (Repetition)
    case1_input = """
let counter = 0;
function increment() {
  counter++;
}
let counter = 0;
function increment() {
  counter++;
}
"""
    parsed1 = cleanOutput(case1_input)
    assert "let counter = 0;\nfunction increment() {\n  counter++;\n}" == parsed1["code"], "Lỗi Case 1"
    print("✅ Case 1: Xóa Lặp code thành công.")

    # Case 2: Markdown block tiêu chuẩn
    case2_input = """
Đoạn code sau đã được tối ưu hóa:
```javascript
async function fetchAll() {
  return await Promise.all([f1(), f2()]);
}
```
Chúc bạn may mắn!
"""
    parsed2 = cleanOutput(case2_input)
    assert parsed2["code"] == "async function fetchAll() {\n  return await Promise.all([f1(), f2()]);\n}"
    assert "Đoạn code sau đã được tối ưu hóa:\n\nChúc bạn may mắn!" in parsed2["explanation"]
    print("✅ Case 2: Trích xuất Code và Explanation từ Markdown thành công.")

    # Case 3: Nhiều Markdown blocks (chỉ lấy block đầu tiên)
    case3_input = """
```js
const a = 1;
```
Và đây là rác:
```javascript
const b = 2;
```
"""
    parsed3 = cleanOutput(case3_input)
    assert parsed3["code"] == "const a = 1;"
    assert "Và đây là rác:" in parsed3["explanation"]
    print("✅ Case 3: Xử lý nhiều Markdown blocks thành công.")

    # Case 4: Không có Markdown block
    case4_input = """async function run() {
    await fs.readFile();
}"""
    parsed4 = cleanOutput(case4_input)
    assert parsed4["code"] == case4_input
    assert "No markdown" in parsed4["explanation"]
    print("✅ Case 4: Xử lý Raw text (Không có Markdown) thành công.")

    print("\n🎉 Mọi Unit Tests đều vượt qua!")

if __name__ == "__main__":
    run_tests()
