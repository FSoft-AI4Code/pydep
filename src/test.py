from pycall import Extractor
from pycall.Node import FunctionNode, ImportNode

src = "/home/namlh31aic/Project/AI4Code/py-dependency/tests/CodeText-parser"
module = "/home/namlh31aic/Project/AI4Code/py-dependency/tests/CodeText-parser/src/codetext/parser/c_sharp_parser.py"

extractor = Extractor(src, module)
module = extractor.extract()
print(extractor)

id = 0
function = module.function_list[id]

print(function.content)
print("="*100)
for child in function.children:
    print(child.content)
    if type(child) in [FunctionNode, ImportNode] and child.children:
        for x in child.children:
            print(x.content)
    print("-"*100)