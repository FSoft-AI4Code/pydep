# Dependency call extraction tool for Python modules

## What does this package do?
This package can use to extract functions, import statements (TODO: class) in a module file, and their call dependencies in a source repository.

**Example:**

_Consider a simple repository structure_
```
simple_repo
  |
  |_ file1.py
  |_ folder1.py
        |_ file2.py     
```

_The content in each file is_
```
# file1.py
def print_function(str):
  print(str)

# folder1/file2.py
from file1 import print_function

def start_print():
  print_function("Author: Nam Le Hai")

def print_hello():
  print_function("hello")
```

The tool can use to find the dependency of `print_hello()` function in `file2.py` which is the `print_function()` function imported from `file1.py`.

## Quickstart Guide

Currently, our package only supports extracting dependency for functions and import statements in a module files.

### Requirement
Python >= 3.10

### Install pydepcall
Using [Anaconda](https://www.anaconda.com/) (feel free to use other env)
```
conda create -n YOUR_ENV_NAME python=3.10
conda activate YOUR_ENV_NAME
pip install pydepcall
```

### Usage:
```
from pydepcall import Extractor
```

_If you want to extract all module files in the repository_
```
reposrc = YOUR_LOCAL_PATH_OF_REPO
extractor = Extractor(reposrc)
output = extractor.extract()
```

_If you want to extract a specific module file in the repository_
```
reposrc = YOUR_LOCAL_PATH_OF_REPO
module_file = YOUR_LOCAL_PATH_OF_FILE_IN_REPO
extractor = Extractor(reposrc, module_file)
output = extractor.extract()
```

**Example**
```
>>> from pydepcall import Extractor
>>> reposrc = "simple_repo"
>>> extractor = Extractor(reposrc)
>>> output = extractor.extract()
>>> output
{'simple_repo/file1.py': <pydepcall.Node.ModuleNode object at 0x7faeb6d84580>, 'simple_repo/folder1/file2.py': <pydepcall.Node.ModuleNode object at 0x7faeb7822050>}

>>> output["simple_repo/folder1/file2.py"].function_list
[<pydepcall.Node.FunctionNode object at 0x7faeb6bc2740>, <pydepcall.Node.FunctionNode object at 0x7faeb6bc2530>]

>>> output["simple_repo/folder1/file2.py"].function_list[0].children
[<pydepcall.Node.ImportNode object at 0x7fc5fade6320>]

>>> output["simple_repo/folder1/file2.py"].function_list[0].children[0].children
[<pydepcall.Node.FunctionNode object at 0x7faeb6bc22c0>]

>>> output["simple_repo/folder1/file2.py"].function_list[0].children[0].children[0].content
'def print_function(str):\n  print(str)'
```

### Output format
For extracting a specific module, the output will be a `ModuleNode` of the input file.

For extracting the whole repository, the output will be the dictionary of `ModuleNode` with the keys are all module files in the repository. 

### Node objects
The package has 5 main nodes:
- `ModuleNode`: contains all FunctionNode and ImportNode in a module file
- `ImportNode`: a node represents an import statement
- `FunctionNode`: a node represents a python function
- `ClassNode`: a node represents a class
- `BlockNode`: a node represents a codeblock in the module file

Every node except `ModuleNode` has the following attributes:
- `path`: the module file's local path contain that node
- `content`: the text content of the node (function, import, class or codeblock)
- `position_in_file`: the position of the node in the module file

For `FunctionNode` and `ImportNode`, we can acquire their dependencies through their `children (node.children)` attribute.

Please see [Node.py](https://github.com/FSoft-AI4Code/pydepcall/blob/main/src/pydepcall/Node.py) for more details.

