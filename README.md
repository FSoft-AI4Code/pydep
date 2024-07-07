# Dependency call extraction tool for Python modules

# What does this package do?
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

# Quickstart Guide

## Install pydepcall
Using Anaconda env (feel free to use other env)
```
conda create -n YOUR_ENV_NAME python=3.10
conda activate YOUR_ENV_NAME
pip install pydepcall
```
