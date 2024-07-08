from pydepcall import Extractor
from pydepcall.Node import FunctionNode, ImportNode

src = "/home/namlh31aic/Project/AI4Code/pydepcall/tests/simple_repo"
module = "/home/namlh31aic/Project/AI4Code/pydepcall/tests/simple_repo/folder1/file2.py"

extractor = Extractor(src, None)
modules = extractor.extract()
module = modules[module]
print(len(module.import_list))

id = 1
function = module.function_list[id]

print(function.content)
print("="*100)
for child in function.children:
    print(child.content)
    if type(child) in [FunctionNode, ImportNode] and child.children:
        for x in child.children:
            print(x.content)
    print("-"*100)