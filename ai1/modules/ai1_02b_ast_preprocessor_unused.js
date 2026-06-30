/**
 * AI1-02 | ThreadLearn — AST Preprocessor (with Data Flow Analysis)
 * Bóc tách AST, xóa comment dư thừa, và phân tích luồng dữ liệu (Use-Def) 
 * để chèn HINT (gợi ý song song hóa) cho mô hình LLM.
 */

const fs = require('fs');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;

const INPUT_FILE = 'raw_dataset.json';
const OUTPUT_FILE = 'ast_dataset.json';

function processCode(code) {
    try {
        const ast = parser.parse(code, {
            sourceType: "module",
            plugins: ["asyncGenerators", "classProperties", "classPrivateProperties", "classPrivateMethods", "topLevelAwait"]
        });

        // 1. Xóa toàn bộ comments nguyên thủy của user
        traverse(ast, {
            enter(path) {
                if (path.node.leadingComments) path.node.leadingComments = null;
                if (path.node.innerComments) path.node.innerComments = null;
                if (path.node.trailingComments) path.node.trailingComments = null;
            }
        });

        // 2. Data Flow Analysis (DFA) - Phân tích phụ thuộc biến
        traverse(ast, {
            BlockStatement(path) {
                const body = path.node.body;
                let asyncVars = [];
                let hasDependencies = false;

                // Tìm các lệnh khai báo biến có chứa 'await' liên tiếp
                for (let i = 0; i < body.length; i++) {
                    const stmt = body[i];
                    if (stmt.type === 'VariableDeclaration') {
                        for (const decl of stmt.declarations) {
                            if (decl.init && (decl.init.type === 'AwaitExpression' || hasAwait(decl.init))) {
                                const varName = decl.id.name;
                                
                                // Kiểm tra xem biểu thức này có dùng biến nào đã khai báo ở trên không
                                let dependsOnPrevious = false;
                                traverse(decl.init, {
                                    noScope: true,
                                    Identifier(idPath) {
                                        if (asyncVars.includes(idPath.node.name)) {
                                            dependsOnPrevious = true;
                                        }
                                    }
                                }, path.scope, path);

                                if (dependsOnPrevious) {
                                    hasDependencies = true;
                                }
                                if (varName) {
                                    asyncVars.push(varName);
                                }
                            }
                        }
                    }
                }

                // Nếu có >= 2 biến await mà KHÔNG phụ thuộc nhau -> Thêm HINT
                if (asyncVars.length >= 2 && !hasDependencies) {
                    const hintMessage = ` HINT: Variables [${asyncVars.join(', ')}] are data-independent. Safe to run in parallel. `;
                    
                    // Thêm comment vào node đầu tiên của block
                    if (!body[0].leadingComments) body[0].leadingComments = [];
                    body[0].leadingComments.push({
                        type: 'CommentLine',
                        value: hintMessage
                    });
                }
            }
        });

        // Hàm helper kiểm tra có chứa await ở trong không
        function hasAwait(node) {
            let found = false;
            traverse(node, {
                noScope: true,
                AwaitExpression() { found = true; }
            });
            return found;
        }

        // 3. Generate lại code (Giữ lại comment HINT vừa tạo)
        const output = generate(ast, {
            comments: true,
            retainLines: false,
            compact: false
        });

        return { success: true, code: output.code };
    } catch (err) {
        return { success: false, error: err.message };
    }
}

function main() {
    console.log(`🔍 Đang đọc file: ${INPUT_FILE}...`);
    const rawData = JSON.parse(fs.readFileSync(INPUT_FILE, 'utf-8'));
    
    let successCount = 0;
    let errorCount = 0;
    
    const astData = rawData.map((item, idx) => {
        // Chỉ cần phân tích và gắn hint ở code INPUT
        const inpRes = processCode(item.input);
        
        // Output thì chỉ cần clean syntax (ko gắn hint)
        let outRes;
        try {
            let outAst = parser.parse(item.output, {
                sourceType: "module",
                plugins: ["asyncGenerators", "classProperties", "classPrivateProperties", "classPrivateMethods", "topLevelAwait"]
            });
            traverse(outAst, {
                enter(p) { p.node.leadingComments = null; p.node.innerComments = null; p.node.trailingComments = null; }
            });
            outRes = { success: true, code: generate(outAst, {comments: false}).code };
        } catch (err) {
            outRes = { success: false, error: err.message };
        }
        
        if (!inpRes.success || !outRes.success) {
            errorCount++;
            return null;
        }
        
        successCount++;
        return {
            ...item,
            input: inpRes.code,
            output: outRes.code
        };
    }).filter(item => item !== null);
    
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(astData, null, 2), 'utf-8');
    
    console.log("━".repeat(50));
    console.log(`✅ AST PREPROCESSING (WITH DFA HINTS) HOÀN TẤT`);
    console.log(`  • Số mẫu thành công: ${successCount}`);
    console.log(`  • Đã lưu kết quả tại: ${OUTPUT_FILE}`);
}

main();
