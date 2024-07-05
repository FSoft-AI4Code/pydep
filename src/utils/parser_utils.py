from typing import List
import tree_sitter
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from .utils import fix_white_space
import sys
sys.setrecursionlimit(200)

PY_LANGUAGE = Language(tspython.language())
language_parser = Parser(PY_LANGUAGE)

def traverse_type(node, results, kind, ignore_kind, avoid_nested= False) -> None:    
    if kind is None:
        results.append(node)
    elif node.type in kind:
        results.append(node)
        # avoid nested node (e.g. function, class) by not stop traveling if node type is found
        if avoid_nested:
            return 
    if not node.children:
        return
    for n in node.children:
        if n.type in ignore_kind:
            continue
        traverse_type(n, results, kind, ignore_kind, avoid_nested= avoid_nested)

def get_node_by_kind(root: tree_sitter.Node, kind: List[str], ignore_kind: List[str]=[], avoid_nested: bool= False) -> List:
    """
    Get all nodes with specific type
    
    Args:
        root (tree_sitter.Node): Tree sitter root node
        kind (List[str]): (node's) type that want to get
        ignore_kind (List[str]): (node's) type that DON'T want to get
        avoid_nested (bool): whether to avoid travel nested node with same type
    
    Return:
        List[tree_sitter.Node]: List of all 
    """

    node_list = []
    traverse_type(root, node_list, kind=kind, ignore_kind= ignore_kind, avoid_nested= avoid_nested)
    return node_list

def get_root_node(content: str) -> tree_sitter.Node:
    """
    Get the root node of the parsed content
    
    Args:
        content: input text content
    """
    root = language_parser.parse(bytes(content, "utf8"))
    return root.root_node

def get_import_list(content: str) -> List[tree_sitter.Node]:
    """
    Obtain all import statments in a code file
    
    Args:
        content: input text content
    
    Return:
        List of tree-sitter nodes that are import statement
    """
    root_node = get_root_node(content)
    import_nodes = get_node_by_kind(root_node, kind = ["import_statement", "import_from_statement", "future_import_statement"])
    return import_nodes

def parse_import(import_node: tree_sitter.Node):
    
    # import_text = import_node.text.decode()
    # import_line = remove_comment(import_text)
    # import_line = fix_white_space(import_line.replace("\n", " ").replace("\\", " ").replace("(", " ").replace(")", " "))
    # if import_line.endswith(","):
    #     import_line = import_line[:-1]

    # if " as " in import_line:
    #     module_name = import_line.split(" as ")[-1].strip()
    #     original_import_info = import_line.split(" as ")[0].strip()
    # else:
    #     module_name = None
    #     original_import_info = import_line

    # if import_node.type == "import_statement":
    #     package = None
    #     import_modules = [x.strip() for x in original_import_info[7:].strip().split(",")] # ignore 7 characters of "import "         
    # else:
    #     module_name = None
    #     import_modules = [x.strip() for x in original_import_info.split(" import ")[-1].strip().split(",")]
    #     package = import_line[5:].strip().split()[0] # ignore 5 character of "from "  
    
    import_module_nodes = []
    package = None

    package_start = False
    module_start = False
    for children in import_node.children:
        if children.type == "from":
            package_start= True
            module_start = False
        elif package_start:
            assert children.type in ["dotted_name", "__future__", "relative_import"]
            package = children.text.decode()
            package_start = False
        elif children.type == "import":
            module_start = True
        elif module_start and children.type in ["dotted_name", "aliased_import"]:
            import_module_nodes.append(children)

    import_details = []
    for import_module_node in import_module_nodes:
        module_name = None
        import_module = import_module_node.text.decode()
        if import_module_node.type == "aliased_import":
            import_module, module_name = [x.strip() for x in import_module.split(" as ")]

        if package is not None:    
            import_text = "from {} import {}".format(package, import_module)
        else:
            import_text = "import {}".format(import_module)

        if module_name is not None:
            import_text += " as {}".format(module_name)

        import_details.append({"package": package, 
                                "module": import_module, 
                                "name": module_name if module_name else import_module, 
                                "import_text": import_text})
    return import_details

#### Code file cleaning
def decorated_clean(content: str) -> str:
    """
    Clean line decoration mark '@' (e.g. @staticmethod)

    Args:
        content: content of code file
    """
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if not line.strip().startswith("@"):
            new_lines.append(line)
    return "\n".join(new_lines)

def map_line_to_id(content):
    line2id = {}
    tmp = []
    for lid, line in enumerate(content.splitlines()):
        if lid == 0:
            line2id[lid] = 0
        else:
            line2id[lid] = len(bytes("\n".join([x.decode("utf8") for x in tmp]), "utf8")) + 1 # plus 1 extra new lines
        tmp.append(line)
    return line2id

def remove_content(content: str, rm_position: List):
    content = bytes(content, "utf8")
    line2id = map_line_to_id(content)
    new_rm_position = [0]
    for pos in rm_position:
        new_rm_position.extend([line2id[pos[0][0]]+ pos[0][1], line2id[pos[1][0]]+ pos[1][1]]) 
    new_rm_position.append(len(content))

    new_content= ''
    for pos_id in range(0, len(new_rm_position), 2):
        new_content += content[new_rm_position[pos_id]:new_rm_position[pos_id+1]].decode("utf8")
    return new_content

def remove_comment(content):
    root_node = get_root_node(content)

    positions = []
    for node in get_node_by_kind(root_node, kind= ["comment"]):
        positions.append((node.start_point, node.end_point))

    if positions:
        cleaned_content = remove_content(content, positions)
    else:
        cleaned_content = content
    return cleaned_content.strip()

def code_basic_clean(file_content):
    """
    1. clean highlevel comment
    2. clean decorated line (line startswith @ )
    3. clean main program - if __name__ == "__main__"
    """
    root_node = get_root_node(file_content)

    positions = []
    for node in root_node.children:
        if node.type == "comment" or (node.type == 'expression_statement' and node.children[0].type == 'string'):
            positions.append((node.start_point, node.end_point))

    if positions:
        cleaned_content = remove_content(bytes(file_content, "utf8"), positions)
    else:
        cleaned_content = file_content

    if "if __name__ == \"__main__\"" in cleaned_content:
        new_lines = cleaned_content.splitlines()
        for lid, line in enumerate(new_lines):
            if line.strip().startswith("if __name__ == \"__main__\""):
                break
        cleaned_content = "\n".join(new_lines[:lid])
    
    return decorated_clean(cleaned_content)
