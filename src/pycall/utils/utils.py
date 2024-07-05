import os
import git
from typing import List
import re

def clone_repo(src: str, save_dir: str="repos"):
    """
    Clone repository if it is not downloaded

    Args:
        src: repo directory or link
        save_dir: save directory if cloning
    Return:
        Local directory of repository
    """
    if not os.path.exists(src):
        repo_path = os.path.join(save_dir, src.split("/")[-1].split(".")[0])
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # Check if repository is already cloned
        if not os.path.exists(repo_path):
            git.Git(save_dir).clone(src)
        return repo_path
    else:
        return src

def fix_white_space(string: str):
    """Remove redundant white space"""
    return " ".join(string.split())

def remove_empty_line(string: str):
    """Remove empty line"""
    return "\n".join([x for x in string.splitlines() if x.strip()])

def find_all_substring(substring, string):
    return sorted([m.start() for m in re.finditer(substring, string)])