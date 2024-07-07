import json
from codetext.parser import PythonParser
from tree_sitter import Language, Parser
import tree_sitter
import os
from typing import Dict

from .utils import get_node_by_kind, get_root_node, decorated_clean
from .utils import language_parser as parser
from .constant import PY_EXTENSIONS

def get_identifier_in_file(filepath: str) -> Dict:
    """
    Get identifiers of a file

    Args:
        filepath: the file path to get identifiers
    """
    try:
        with open(filepath, "r") as f:
            filecontent = f.read()
        
        # Clean decorated line so easier to detect node type by 1st level
        filecontent = decorated_clean(filecontent)
    except Exception as e:
        # print(e)
        return {"path": filepath, "childrens": []}
        
    root_node = get_root_node(filecontent)

    all_modules = set()
    for children in root_node.children:
    
        if "import" in children.type:
            # Only consider the actual imported module
            # 1. import abc => abc
            # 2. from abc import xyz => xyz
            # 3. import abc as xyz => xyz

            import_as_identifiers = get_node_by_kind(children, kind=["aliased_import"])
            if import_as_identifiers:
                # import ... as ... or from .. import ... as ...
                all_modules.update([x.text.decode().split(" as ")[-1].strip() for x in import_as_identifiers])
            
            """
            Some cases could be:
            E.g.
                - from a import b, c as d
                - import a, b as c, d as e
            """
            start = False
            for subchild in children.children:
                if subchild.type == "import":
                    start = True
                elif start and subchild.type == "dotted_name":
                    all_modules.add(subchild.text.decode())
                
        else:
            child_identifiers = [x.text.decode() for x in get_node_by_kind(children, kind= ["identifier"])]
            # Obtain only the first occurrent identifier
            if child_identifiers:
                all_modules.add(child_identifiers[0])

    return {"path": filepath, "childrens": list(all_modules)}

    
def get_children(folder: str) -> Dict:
    graph_child = {"path": folder, "childrens": {}}
    for children in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, children)):
            graph_child["childrens"][children] = get_children(os.path.join(folder, children))
        elif children.endswith(PY_EXTENSIONS):
            graph_child["childrens"][children] = get_identifier_in_file(os.path.join(folder, children))
        
    return graph_child        


def get_repo_graph(repo_src: str, save_graph_to: str= None) -> Dict:
    """
    Construct module graph for a repository

    Args:
        repo_src: the local path of the repository
        save_graph_to: directory to save the created graph
    """
    graph = get_children(repo_src)
    if save_graph_to:

        if not os.path.exists(save_graph_to):
            os.makedirs(save_graph_to)

        reponame = repo_src.split("/")[-1]
        with open(os.path.join(save_graph_to, f"{reponame}.json"), "w") as f:
            json.dump(graph, f, indent=4)
    return graph