import os

from .utils import parse_import, get_root_node, get_node_by_kind
from .constant import PY_EXTENSIONS

def search_path(key: str, graph, tracks= []):
    """
    Search the path from root of repo to the 'key' module. 
    
    Args:
        key (str): key module (starting point of a path) to be searched
        graph (Dict): graph of the repository
        tracks (List): tracking list of all searched path
    """
    if key is None:
        tracks.append(graph)
    else:
        for child in graph["childrens"]:
            if child == key or child in [key + x for x in PY_EXTENSIONS]:
                if type(graph["childrens"]) is not list:
                    tracks.append(graph["childrens"][child])
            else:
                if type(graph["childrens"]) is not list:
                    search_path(key, graph["childrens"][child], tracks= tracks)

def verify_track(separated_path, module, track):
    if len(separated_path) == 0:
        if type(track["childrens"]) is list:
            module_childrens = set(track["childrens"]).intersection(set([module + py_ext for py_ext in PY_EXTENSIONS]))
        else:
            module_childrens = set(track["childrens"].keys()).intersection(set([module + py_ext for py_ext in PY_EXTENSIONS]))
        module_childrens = list(module_childrens)
        assert len(module_childrens) <= 1, module_childrens

        if module not in track["childrens"] and \
        len(module_childrens) == 0:
            if "__init__.py" in track["childrens"]: # from folder(.__init__) import module
                if module not in track["childrens"]["__init__.py"]["childrens"]:
                    return False, False
                else:
                    return track["childrens"]["__init__.py"]["path"], False
            else:
                return False, False
        elif module in track["childrens"]:
            if type(track["childrens"]) is list:
                return track["path"], False
            # import folder
            return track["childrens"][module]["path"], True
        elif len(module_childrens) > 0:
            # import file
            if module + ".py" in module_childrens:
                return track["childrens"][module + ".py"]["path"], True
            return track["childrens"][module_childrens[0]]["path"], True
    else:
        if type(track["childrens"]) is list:
            module_childrens = set(track["childrens"]).intersection(set([separated_path[0] + py_ext for py_ext in PY_EXTENSIONS]))
        else:
            module_childrens = set(track["childrens"].keys()).intersection(set([separated_path[0] + py_ext for py_ext in PY_EXTENSIONS]))
        module_childrens = list(module_childrens)
        assert len(module_childrens) <= 1, module_childrens

        if separated_path[0] not in track["childrens"] and len(module_childrens) == 0:
            return False, False
        else:
            if separated_path[0] in track["childrens"]:
                if type(track["childrens"]) is list:
                    return False, False
                return verify_track(separated_path[1:], module, track["childrens"][separated_path[0]])
            else:
                if type(track["childrens"]) is list:
                    return False, False
                return verify_track(separated_path[1:], module, track["childrens"][module_childrens[0]])

def search_by_repo_graph(import_detail, repo_graph, current_path):
    def search_chain(separated_path, module, repo_graph, current_path):
        # Find all track
        all_tracks = []

        if len(separated_path) == 0: # import module
            # start_point = os.path.dirname(current_path).split("/")[-1]
            start_point = None
            separated_path= [start_point]
        else:
            start_point =  separated_path[0]
        search_path(start_point, repo_graph, all_tracks)

        for track in all_tracks:
            # start_point is always covered, skip 0 position
            track_verified, import_file_or_folder = verify_track(separated_path[1:], module, track)
            if track_verified:
                # if os.path.isdir(track_verified):
                #     print(separated_path, module, track_verified)
                return track_verified, import_file_or_folder
        return None, None
          
    if import_detail["package"] is not None:
        # import could be from fol1.fol2.file1 import 
        separated_path = import_detail["package"].split(".")
        track = search_chain(separated_path, import_detail["module"], repo_graph, current_path)

        if track is not None:
            return track
    else:
        separated_path = import_detail["module"].split(".")
        track = search_chain(separated_path[:-1], import_detail["module"].split(".")[-1], repo_graph, current_path)
        if track is not None:
            return track
    return None, None


def import_analyze(import_nodes, filepath, repo_graph):
    import_details = []
    for import_node in import_nodes:
        import_details.extend(parse_import(import_node))

    RELATIVE_IMPORT_PREFIXS = ["...", "..", "."]
    for import_detail in import_details:
        import_path = None
        import_file_or_folder = False

        for import_prefix in RELATIVE_IMPORT_PREFIXS:
            if import_detail["package"] is not None and import_detail["package"].startswith(import_prefix):
                start_dir = filepath
                for _ in range(len(import_prefix)):
                    start_dir = os.path.dirname(start_dir)
                
                if import_detail["package"] != import_prefix:
                    for py_ext in PY_EXTENSIONS:
                        if os.path.exists(os.path.join(start_dir, import_detail["package"][len(import_prefix):].replace(".", "/") + py_ext)): # from file import module 
                            import_path = os.path.join(start_dir, import_detail["package"][len(import_prefix):].replace(".", "/") + py_ext)
                            import_file_or_folder = False
                        elif os.path.exists(os.path.join(start_dir, import_detail["package"][len(import_prefix):].replace(".", "/"), import_detail["module"] + py_ext)): # from folder import file
                            import_path = os.path.join(start_dir, import_detail["package"][len(import_prefix):].replace(".", "/"), import_detail["module"] + py_ext)
                            import_file_or_folder = True
                        if import_path:
                            break
                    # Some functions might be imported from __init__ file
                    if not import_path:
                        init_path = os.path.join(start_dir, import_detail["package"][len(import_prefix):].replace(".", "/"), "__init__.py")
                        import_dir = os.path.join(start_dir, import_detail["package"][len(import_prefix):].replace(".", "/"), import_detail["module"])
                        if os.path.exists(init_path): # from folder import module in init file
                            with open(init_path, "r") as f:
                                init_content = f.read()
                            file_root_node= get_root_node(init_content)

                            if import_detail["module"] in [x.text.decode() for x in get_node_by_kind(file_root_node, kind=["identifier"])]:
                                import_path = init_path
                                import_file_or_folder = False
                        elif os.path.isdir(import_dir): # from folder import folder
                            # if os.path.exists(os.path.join(import_dir, "__init__.py")):
                            #     import_path = os.path.join(import_dir, "__init__.py")
                            import_path = import_dir
                            import_file_or_folder = True
                else:
                    for py_ext in PY_EXTENSIONS:
                        if os.path.exists(os.path.join(start_dir, import_detail["module"] + py_ext)):
                            import_path = os.path.join(start_dir, import_detail["module"] + py_ext) # from folder import file
                            import_file_or_folder = True
                        if import_path:
                            break
                        
                    if not import_path:
                        if os.path.isdir(os.path.join(start_dir, import_detail["module"])): # from folder import folder 
                            import_path = os.path.join(start_dir, import_detail["module"])
                            import_file_or_folder = True
                        elif os.path.exists(os.path.join(start_dir, "__init__.py")): # from folder import module in init file
                            with open(os.path.join(start_dir, "__init__.py"), "r") as f:
                                init_content = f.read()
                            file_root_node= get_root_node(init_content)

                            if import_detail["module"] in [x.text.decode() for x in get_node_by_kind(file_root_node, kind=["identifier"])]:
                                import_path = os.path.join(start_dir, "__init__.py")
                                import_file_or_folder = False
            if import_path:
                break
        
        if not import_path:
            import_path, import_file_or_folder = search_by_repo_graph(import_detail, repo_graph, filepath)


        import_detail["import_path"] = import_path
        import_detail["import_file_or_folder"] = import_file_or_folder
    return import_details