import os
from typing import List, Dict
from codetext.parser import PythonParser

from .build_repo_graph import get_repo_graph
from .utils import language_parser, get_root_node, get_node_by_kind, code_basic_clean, remove_comment
from .Node import FunctionNode, ClassNode, BlockNode, ImportNode, ModuleNode
from .constant import PY_EXTENSIONS, EXCLUDED_TYPING_IDENTIFIERS

class Extractor:
    def __init__(self, repo_src: str, module: str=None):
        self.repo_src = repo_src
        self.module = module
        self.repo_graph = get_repo_graph(repo_src)

    def extract(self):
        if self.module is None:
            return self.repo_extract()
        else:
            return self.file_extract()

    def file_extract(self):
        functions = get_functions_from_module_file(self.module)
        module_function_dict = {"function": {}, "import": {}}
        module_node = ModuleNode(path= self.module, repo_src= self.repo_src, repo_graph= self.repo_graph)
        
        for function in functions:
            get_dependencies(function, module_function_dict, self.repo_src, self.repo_graph)
        
        if self.module in [module_function_dict["function"]]: # check no extracted functions
            module_node.function_list.extend(sorted([module_function_dict["function"][self.module][x] for x in module_function_dict["function"][self.module]], key= lambda x: x.position_in_file[0][0]))
        if self.module in module_function_dict["import"]: # check no extracted import
            module_node.import_list.extend(sorted([module_function_dict["import"][self.module][x] for x in module_function_dict["import"][self.module]], key= lambda x: x.position_in_file[0][0]))
        
        return module_node
        

    def repo_extract(self):
        all_modules = []
        get_modules_from_repo(self.repo_src, all_modules)
        module_function_dict = {"function": {}, "import": {}}
        module_dict = {}

        for module in all_modules:
            functions = get_functions_from_module_file(module)
            module_dict[module] = ModuleNode(path= module, repo_src= self.repo_src, repo_graph= self.repo_graph)

            for function in functions:
                get_dependencies(function, module_function_dict, self.repo_src, self.repo_graph)

            if module in module_function_dict["function"]:
                module_dict[module].function_list.extend(sorted([module_function_dict["function"][module][x] for x in module_function_dict["function"][module]], key= lambda x: x.position_in_file[0][0]))
            if module in module_function_dict["import"]:
                module_dict[module].import_list.extend(sorted([module_function_dict["import"][module][x] for x in module_function_dict["import"][module]], key= lambda x: x.position_in_file[0][0]))
        return module_dict

def get_modules_from_repo(repo_src: str, modules: List=[]) -> List[str]:
    """
    Get all module files from a repository

    Args:
        repo_src: local path of the repository
        modules: list of extracted modules
    """
    
    IGNORE_MODULES = (".git", "__pycache__")
    for sub_f in os.listdir(repo_src):
        if sub_f.startswith(IGNORE_MODULES):
            continue
        if os.path.isdir(os.path.join(repo_src, sub_f)):
            get_modules_from_repo(os.path.join(repo_src, sub_f), modules)
        
        for py_ext in PY_EXTENSIONS:
            if sub_f.endswith(py_ext) and not sub_f.startswith("__init__"):
                modules.append(os.path.join(repo_src, sub_f))
                break

def get_functions_from_module_file(module_path: str) -> List:
    extracted_functions = []

    # Read module file
    try:
        with open(module_path, "r", encoding="utf-8") as f:
            file_content = f.read()
    except:
        return []

    root_node = get_root_node(file_content)

    function_nodes = get_node_by_kind(root_node, kind= ["function_definition"], ignore_kind=["class_definition"], avoid_nested= True)
    if len(function_nodes) == 0:
        return []

    for function_node in function_nodes:
        extracted_functions.append(FunctionNode(module_path, function_node.text.decode(), function_node))

    return extracted_functions


def get_function_dependencies(target_function: FunctionNode, module_function_dict: Dict, repo_src: str, repo_graph: Dict):
    
    local_path = target_function.path
    # Read module file
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            file_content = f.read()
    except:
        return []

    root_node = get_root_node(file_content)

    # Obtain blocks that are function 
    for node in get_node_by_kind(root_node, kind= ["function_definition"], ignore_kind=["class_definition"], avoid_nested= True):
        iden_name = PythonParser.get_function_metadata(node, file_content)["identifier"]
        if iden_name in target_function.called_identifiers:
            if iden_name not in module_function_dict["function"][local_path]:
                dep_function = FunctionNode(local_path, node.text.decode(), node)
                get_dependencies(dep_function, module_function_dict, repo_src, repo_graph)
            target_function.children.append(module_function_dict["function"][local_path][iden_name])
    
    # Obtain blocks that are class 
    for node in get_node_by_kind(root_node, kind= ["class_definition"], ignore_kind=["function_definition"], avoid_nested= True):
        iden_name = PythonParser.get_function_metadata(node, file_content)["identifier"]
        if iden_name in target_function.called_identifiers:
            """
            TODO: update dependencies for class object
            # if iden_name not in module_function_dict[local_path]:
            #     dep_class = ClassNode(local_path, node.text.decode(), node)
            #     module_function_dict[local_path][iden_name] = get_dependencies(dep_function, module_function_dict)
            """
            target_function.children.append(ClassNode(local_path, node.text.decode(), node))

    # Obtain blocks that are variables, import, ...
    # Do we need to consider decorated_definition @ ?
    for node in root_node.children:
        if node.type in ["function_definition", "class_definition", "decorated_definition"]: # already consider function and class definition
            continue
        if "import" in node.type:
            node_identifiers = [x.text.decode() for x in get_node_by_kind(node, kind=["dotted_name"])]
            if "*" in node_identifiers or len(set(node_identifiers).intersection(set(target_function.called_identifiers))) > 0:
                if local_path not in module_function_dict["import"]:
                    module_function_dict["import"][local_path] = {}
                
                if node.text.decode() not in module_function_dict["import"][local_path]:
                    dep_import = ImportNode(local_path, node.text.decode(), node, repo_graph)
                    get_dependencies(dep_import, module_function_dict, repo_src, repo_graph)
                target_function.children.append(module_function_dict["import"][local_path][node.text.decode()])
        # only consider the first identifier
        # only consider "expression_statement" ?
        elif node.type in ["expression_statement"]:
            node_identifiers = [x.text.decode() for x in get_node_by_kind(node, kind=["identifier"])]
            if node_identifiers and node_identifiers[0] in target_function.called_identifiers and node_identifiers[0] not in EXCLUDED_TYPING_IDENTIFIERS: # avoid achieving redundant context with typing identifiers
                target_function.children.append(BlockNode(local_path, node.text.decode(), node))

    return target_function    

def get_import_dependencies(target_import: ImportNode, module_function_dict: Dict, repo_src: str, repo_graph: Dict):
    import_dict = [x for x in target_import.import_dict if x["import_path"] and x["import_path"].startswith(repo_src)]
    
    # third party import or import that are failed to obtain path
    if not import_dict:
        return target_import
    
    # Get related files
    selected_file = {}
    for import_info in import_dict:
        if import_info["import_path"] not in selected_file:
            selected_file[import_info["import_path"]] = []
        if import_info["name"] == "*" or import_info["import_file_or_folder"]:
            selected_file[import_info["import_path"]].append("*")
        else:
            selected_file[import_info["import_path"]].append(import_info["module"])
    
    for fid, import_file in enumerate(selected_file):
        try:
            # Sometime the import_file extracted is a directory. We ignore this case now :(
            with open(import_file, "r", encoding="utf-8") as f:
                cross_file_content = f.read()
        except:
            continue

        root_node = get_root_node(cross_file_content)

        # Obtain blocks that are function 
        for node in get_node_by_kind(root_node, kind= ["function_definition"], ignore_kind=["class_definition"], avoid_nested= True):
            iden_name = PythonParser.get_function_metadata(node)["identifier"]
            if "*" in selected_file[import_file] or iden_name in selected_file[import_file]:
                if import_file not in module_function_dict["function"]:
                    module_function_dict["function"][import_file] = {}

                if iden_name not in module_function_dict["function"][import_file]:
                    dep_function = FunctionNode(import_file, node.text.decode(), node)
                    get_dependencies(dep_function, module_function_dict, repo_src, repo_graph)
                target_import.children.append(module_function_dict["function"][import_file][iden_name])
        
        # Obtain blocks that are class 
        for node in get_node_by_kind(root_node, kind= ["class_definition"], ignore_kind=["function_definition"], avoid_nested= True):
            iden_name = PythonParser.get_function_metadata(node)["identifier"]
            if "*" in selected_file[import_file] or iden_name in selected_file[import_file]:
                """
                TODO: update dependencies for class object
                # if iden_name not in module_function_dict[local_path]:
                #     dep_class = ClassNode(local_path, node.text.decode(), node)
                #     module_function_dict[local_path][iden_name] = get_dependencies(dep_function, module_function_dict)
                """
                target_import.children.append(ClassNode(import_file, node.text.decode(), node))
            
        # Obtain blocks that are variables, ...
        # Do we need to consider decorated_definition @ ?
        for node in root_node.children:
            if node.type in ["function_definition", "class_definition", "decorated_definition"]:# or "import" in node.type: # already consider function and class definition
                continue
            
            if "import" in node.type:
                node_identifiers = [x.text.decode() for x in get_node_by_kind(node, kind=["dotted_name"])]
                if "*" in selected_file[import_file] or len(set(node_identifiers).intersection(set(selected_file[import_file]))) > 0:
                    if import_file not in module_function_dict["import"]:
                        module_function_dict["import"][import_file] = {}
                    
                    if node.text.decode() not in module_function_dict["import"][import_file]:
                        dep_import = ImportNode(import_file, node.text.decode(), node, repo_graph)
                        get_dependencies(dep_import, module_function_dict, repo_src, repo_graph)
                    target_import.children.append(module_function_dict["import"][import_file][node.text.decode()])
            elif node.type in ["expression_statement"]:
                node_identifiers = [x.text.decode() for x in get_node_by_kind(node, kind= ["identifier"])]
                if node_identifiers and node_identifiers[0] in selected_file[import_file]:
                    target_import.children.append(BlockNode(import_file, node.text.decode(), node))
    return target_import


def get_dependencies(target_node: FunctionNode | ImportNode, module_function_dict: Dict, repo_src: str, repo_graph: Dict):

    target_node_type = None
    if type(target_node) is FunctionNode:
        target_node_type = "function"
    elif type(target_node) is ImportNode:
        target_node_type = "import"
    else:
        raise ValueError("target_node type {} hasn't supported yet!".format(type(target_node)))
    

    if target_node.path not in module_function_dict[target_node_type]:
        module_function_dict[target_node_type][target_node.path] = {}

    if target_node_type == "function":
        if target_node.name in module_function_dict[target_node_type][target_node.path]:
            return
    elif target_node_type == "import":
        if target_node.content in module_function_dict[target_node_type][target_node.path]:
            return 
    
    try:
        # Some functions are recursive functions which can call forever
        # Break when reach max recursion => the tree could be very large
        if target_node_type == "function":
            target_node = get_function_dependencies(target_node, module_function_dict, repo_src, repo_graph)
        elif target_node_type == "import":
            target_node = get_import_dependencies(target_node, module_function_dict, repo_src, repo_graph)
    except Exception as e:
        # print(e)
        pass

    if target_node_type == "import":
        module_function_dict[target_node_type][target_node.path][target_node.content] = target_node
    elif target_node_type == "function":
        module_function_dict[target_node_type][target_node.path][target_node.name] = target_node