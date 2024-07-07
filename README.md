# Dependency call extraction tool for Python modules

## What does this package do?
This package can use to extract functions, import statements (TODO: class) in a module file, and its call dependencies in a source repository.

Example:
Consider a simple repository structure:
```
simple_repo
  |
  |_ file1.py
  |_ folder1.py
        |_ file2.py     
```

The content in each file is
```
# file1.py
def print_function(str):
  print(str)

# folder1/file2.py
from file1 import print_function
def print_hello():
  print_function("hello")
```

The tool can use to find the dependency of `print_hello()` function in file2.py which is the `print_function()` function imported from file1.py

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

If you want to extract all module files in the repository
```
reposrc = YOUR_LOCAL_PATH_OF_REPO
extractor = Extractor(reposrc)
output = extractor.extract()
```

If you want to extract a specific module file in the repository
```
reposrc = YOUR_LOCAL_PATH_OF_REPO
module_file = YOUR_LOCAL_PATH_OF_FILE_IN_REPO
extractor = Extractor(reposrc, module_file)
output = extractor.extract()
```

### Output format
For extracting a specific module, the output will be a ModuleNode of the input file.

For extracting the whole repository, the output will be the dictionary of ModuleNode with the keys are all module files in the repository. 


