from codetext.parser import PythonParser
import tree_sitter
from typing import List, Dict

from .travel_graph import import_analyze
from .utils import get_root_node, get_node_by_kind, get_import_list, remove_content, find_all_substring
from .build_repo_graph import get_repo_graph 


class ModuleNode:
    """
    Module node object

    Attributes:
        path (str): the local path of file containing the function
        repo_src (str): the local path of the repository containing the module
    """
    def __init__(self, path: str, repo_src: str, repo_graph: Dict):
        self.path = path
        self.function_list = []
        self.import_list = []
        


class FunctionNode:
    """
    Function node object

    Attributes:
        path (str): the local path of file containing the function
        content (str): the function content in text
        name (str): function's name
        params (dict): function's parameters
        return_type (str): function's return type
        docstrings (str): function's docstring
        called_identifiers (list): called dependencies inside function
        position_in_file (tuple): start, end position of function in module file
        tree_sitter_node (tree_sitter.Node): Node parsed from file using tree-sitter
        children (list): List of called dependencies
    """
    def __init__(self, path: str, content: str, tree_sitter_node: tree_sitter.Node):
        self.path = path
        self.content = content
        self.tree_sitter_node = tree_sitter_node

        self.position_in_file = (tree_sitter_node.start_point, tree_sitter_node.end_point)
        self.name, self.params, self.return_type, self.docstring = self.get_metadata()
        self.called_identifiers = self.get_called_identifiers()

        self.children = []

    def get_metadata(self):
        function_metadata = PythonParser.get_function_metadata(self.tree_sitter_node)
        docstring = PythonParser.get_docstring(self.tree_sitter_node)
        return function_metadata["identifier"], function_metadata["parameters"], function_metadata["return_type"], docstring

    def get_called_identifiers(self):
        # Do not consider parameter identifier and typing types identifier. Do not forget to exclude self identifier
        identifiers = [x for x in get_dependencies(self.tree_sitter_node) if x not in list(self.params.keys()) + [self.name]]
        return identifiers
    

class ClassNode:
    """
    Class node object

    Attributes:
        path (str): the local path of file containing the function
        content (str): the function content in text
        name (str): function's name
        position_in_file (tuple): start, end position of class in module file
        tree_sitter_node (tree_sitter.Node): Node parsed from file using tree-sitter
    """
    def __init__(self, path: str, content: str, tree_sitter_node: tree_sitter.Node):
        self.path = path
        self.content = content    
        self.tree_sitter_node = tree_sitter_node

        self.position_in_file = (tree_sitter_node.start_point, tree_sitter_node.end_point)
        self.name = self.get_name()


    def get_name(self):
        return PythonParser.get_class_metadata(self.tree_sitter_node)["identifier"]

class BlockNode:
    """
    Block node object

    Attributes:
        path (str): the local path of file containing the function
        content (str): the function content in text
        name(str): first identifier's name
        position_in_file (tuple): start, end position of block in module file
        tree_sitter_node (tree_sitter.Node): Node parsed from file using tree-sitter
    """
    def __init__(self, path: str, content: str, tree_sitter_node: tree_sitter.Node):
        self.path = path
        self.content = content
        self.tree_sitter_node = tree_sitter_node
        self.name = self.get_name()
        self.position_in_file = (tree_sitter_node.start_point, tree_sitter_node.end_point)

    def get_name(self):
        return get_node_by_kind(self.tree_sitter_node, kind=["identifier"])[0].text.decode()

class ImportNode:
    """
    Import node object

    Attributes:
        path (str): the local path of file containing the function
        content (str): the function content in text
        position_in_file (tuple): start, end position of import statement in module file
        tree_sitter_node (tree_sitter.Node): Node parsed from file using tree-sitter
    """
    def __init__(self, path: str, content: str, tree_sitter_node: tree_sitter.Node, repo_graph: Dict):
        self.path = path
        self.content = content
        self.tree_sitter_node = tree_sitter_node
        self.repo_graph = repo_graph

        self.position_in_file = (tree_sitter_node.start_point, tree_sitter_node.end_point)
        self.import_dict = self.parse_import()
        self.children = []

    def parse_import(self):
        import_dict = import_analyze([self.tree_sitter_node], self.path, self.repo_graph)
        return import_dict



def remove_parentheses(input_string):
    # Remove string so that we can avoid parentheses in string
    root_node = get_root_node(input_string)
    rm_positions = []
    for node in get_node_by_kind(root_node, kind=["string"], avoid_nested=True):
        rm_positions.append((node.start_point, node.end_point)) 
    string = remove_content(input_string, rm_positions)


    open_indexes = find_all_substring("\(", string)
    close_indexes = find_all_substring("\)", string)
    assert len(open_indexes) == len(close_indexes), input_string
    modified_string = string[0:open_indexes[0]]
    for cid, close_index in enumerate(close_indexes):
        if cid == len(close_indexes) - 1:
            modified_string += string[close_index+1:]
        else:
            modified_string += string[close_index+1:open_indexes[cid+1]]
    return modified_string

def get_dependencies(function_node):
    """
    
    """

    must_contain_identifiers = set()
    exclude_identifiers = set()

    for call_node in get_node_by_kind(function_node, kind=["call"]):
        call_content = remove_parentheses(call_node.text.decode())
        identifiers = call_content.split(".")

        if len(identifiers) == 1:
            must_contain_identifiers.add(identifiers[0])
        else:
            exclude_identifiers.update(identifiers[1:])
    
    included_identifiers = set()
    for identifier_node in get_node_by_kind(function_node, kind=["identifier"]):
        identifier_text = identifier_node.text.decode()
        if identifier_text in must_contain_identifiers or identifier_text not in exclude_identifiers:
            included_identifiers.add(identifier_text)
    return included_identifiers

    
    



