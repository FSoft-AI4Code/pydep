from pydepcall import Extractor
from pydepcall.Node import FunctionNode, ImportNode

reposrc = "simple_repo"
extractor = Extractor(reposrc)
output = extractor.extract()

module = "simple_repo/folder1/file2.py"
function = output[module].function_list[1]

print(function.content)
print("="*100)
for child in function.children:
    print(child.content)
    if type(child) in [FunctionNode, ImportNode] and child.children:
        for x in child.children:
            print(x.content)
    print("-"*100)