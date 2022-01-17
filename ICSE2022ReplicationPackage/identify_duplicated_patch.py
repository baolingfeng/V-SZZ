import os
import sys
import json
import subprocess
import re
import hashlib
import git # get diff patch on Windows 
from unidiff import PatchSet
from io import StringIO
from log_generation import GitLog

from setting import *

from git_analysis.analyze_git_logs import retrieve_git_logs, retrieve_git_logs_dict, get_ancestors, get_parent_tags, get_son_tags, traverse_affected_versions
from data_loader import JAVA_CVE_FIX_COMMITS, C_CVE_FIX_COMMITS, read_cve_commits, REPOS_DIR, JAVA_PROJECTS, C_PROJECTS, ANNOTATED_CVES

repos_dir = REPOS_DIR
log_dir = LOG_DIR

def clear_patched_file(patched_file):
    results = []
    for line in patched_file.split('\n'):
        if line.startswith('index '):
            continue
        
        # ignore the line with line information since some cherry picked patches have different line number
        if line.startswith('@@'):
            continue
        
        results.append(line)
    
    return '\n'.join(results)

def is_target_file(file_path):
    splitted_path_tokens = file_path.lower().split('/')

    file_name = splitted_path_tokens[-1]
    idx = file_name.find('.')
    if idx <= 0:
        return False
    
    suffix = file_name[idx+1:]
    if suffix not in ['java', 'c', 'cpp', 'h', 'hpp']:
        return False
    
    if 'test' in splitted_path_tokens:
        return False
    
    if file_name.startswith('test') or file_name.endswith('test'):
        return False
    
    return True
    
def genereate_hashes_for_patch(repository, commit_id):
    try:
        uni_diff_text = repository.git.diff(commit_id+ '~1', commit_id,
                                        ignore_blank_lines=True, 
                                        ignore_space_at_eol=True)
        
        patch_set = PatchSet(StringIO(uni_diff_text))
    except Exception as e:
        print(e)
        return None
    
    hashes = []
    for patched_file in patch_set:
        file_path = patched_file.path
        if not is_target_file(file_path):
            continue

        content = clear_patched_file(str(patched_file))
        # print(content)
        h = hashlib.sha1(content.encode('utf-8', 'ignore')).hexdigest()

        hashes.append(h)
    
    return hashes

def identify_duplicate_patch(project):
    git_logs = retrieve_git_logs(os.path.join(log_dir, project+"-meta.log"), project)
    
    project_path = os.path.join(repos_dir, project)
    repository = git.Repo(project_path)

    commit_patch_map = {}
    for gl in git_logs:
        print(gl.commit_id)
        hashes = genereate_hashes_for_patch(repository, gl.commit_id)
        if hashes is not None:
            commit_patch_map[gl.commit_id] = hashes
    
    patch_commit_map = {}
    for commit_id in commit_patch_map:
        for h in commit_patch_map[commit_id]:
            if h in patch_commit_map:
                patch_commit_map[h].append(commit_id)
            else:
                patch_commit_map[h] = [commit_id]
    
    return commit_patch_map, patch_commit_map

def batch_duplicate_detection(projects):
    # for project in C_PROJECTS:
    for project in projects:
        try:
            commit_patch_map, patch_commit_map = identify_duplicate_patch(project)
            with open(f'data_commit_patch_map/{project}-commit-patch.json', 'w') as fout1, \
                open(f'data_commit_patch_map/{project}-patch-commit.json', 'w') as fout2:
                json.dump(commit_patch_map, fout1, indent=4)
                json.dump(patch_commit_map, fout2, indent=4)
        except Exception as e:
            print(project, e)
        else:
            pass
        
        break
   
if __name__ == '__main__':
    # Generate hashes for hunks in commits
    batch_duplicate_detection()
   
