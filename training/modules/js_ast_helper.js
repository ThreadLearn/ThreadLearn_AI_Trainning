/**
 * Helper sử dụng Babel AST để phân tích cú pháp JavaScript thực thụ.
 * Chạy bằng: node js_ast_helper.js <action>
 * Đầu vào: Mã nguồn JS qua stdin.
 * Đầu ra: Kết quả dạng JSON.
 */

const fs = require('fs');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;

const action = process.argv[2];

// Đọc toàn bộ code từ stdin
let code = fs.readFileSync(0, 'utf-8');

try {
    const ast = parser.parse(code, {
        sourceType: "module",
        plugins: ["jsx", "typescript", "asyncGenerators", "classProperties", "decorators-legacy"]
    });

    if (action === "strip_comments" || action === "normalize_whitespace") {
        // Xóa comment
        traverse(ast, {
            enter(path) {
                if (path.node.leadingComments) path.node.leadingComments = null;
                if (path.node.innerComments) path.node.innerComments = null;
                if (path.node.trailingComments) path.node.trailingComments = null;
            }
        });
        // Generate lại code (Babel tự động normalize whitespace)
        const output = generate(ast, { comments: false }, code);
        console.log(JSON.stringify({ result: output.code }));

    } else if (action === "extract_functions") {
        const functions = [];
        traverse(ast, {
            FunctionDeclaration(path) {
                functions.push({
                    name: path.node.id ? path.node.id.name : "anonymous",
                    type: path.node.async ? "async_function" : "function",
                    code: generate(path.node).code
                });
            },
            ArrowFunctionExpression(path) {
                // Tên hàm thường lấy từ VariableDeclarator cha
                let name = "anonymous";
                if (path.parent.type === "VariableDeclarator" && path.parent.id.name) {
                    name = path.parent.id.name;
                }
                functions.push({
                    name: name,
                    type: path.node.async ? "async_arrow_function" : "arrow_function",
                    code: generate(path.node).code
                });
            },
            ClassMethod(path) {
                functions.push({
                    name: path.node.key.name || "anonymous",
                    type: "class_method",
                    code: generate(path.node).code
                });
            }
        });
        console.log(JSON.stringify({ result: functions }));

    } else if (action === "extract_keywords") {
        const keywords = new Set();
        // Một số JS keywords cơ bản để loại trừ
        const jsReserved = new Set(["function", "const", "let", "var", "return", "if", "else", "for", "while", "class", "import", "export", "async", "await", "try", "catch", "new", "this", "console", "log"]);
        
        traverse(ast, {
            Identifier(path) {
                if (!jsReserved.has(path.node.name)) {
                    keywords.add(path.node.name);
                }
            }
        });
        
        const kwArray = Array.from(keywords).slice(0, 20).join(" ");
        console.log(JSON.stringify({ result: kwArray }));
    }

} catch (error) {
    // Nếu lỗi parse (VD: code lỗi syntax), trả về lỗi qua JSON
    console.log(JSON.stringify({ error: error.message }));
}
