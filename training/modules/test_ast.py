from ast_preprocessor import extractFunctions, stripComments, extract_keywords

code = """
// this is a comment
const a = 1;
async function hello() { 
    console.log("hi"); 
} 
const arrow = () => { return 1; };
"""

print("--- FUNCTIONS ---")
print(extractFunctions(code, 'js'))
print("--- COMMENTS STRIPPED ---")
print(stripComments(code, 'js'))
print("--- KEYWORDS ---")
print(extract_keywords(code, 'js'))
