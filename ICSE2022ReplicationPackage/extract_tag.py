import os
import sys
import json
import subprocess
import re
import hashlib
from log_generation import GitLog

from setting import *

from data_loader import JAVA_CVE_FIX_COMMITS, C_CVE_FIX_COMMITS, read_cve_commits, REPOS_DIR, JAVA_PROJECTS, C_PROJECTS, ANNOTATED_CVES
from git_analysis.analyze_git_logs import retrieve_git_logs, retrieve_git_logs_dict, get_ancestors, get_parent_tags, get_son_tags

repos_dir = REPOS_DIR
log_dir = LOG_DIR

def get_tags(repo_dir):
    output = GitLog().git_tag(repo_dir)
    tags = output.split('\n')

    commit_tag_map = {}
    for tag in tags:
        if tag.strip() == "":
            continue

        try:
            output = GitLog().git_show(repo_dir, tag)
        except Exception as e:
            print(tag, e)
            continue

        commit = None
        timestamp = None
        for line in output.split('\n'):
            if line.startswith('commit:'):
                commit = line[8:].strip()
            
            if line.startswith('timestamp:'):
                timestamp = line[11:].strip()
                break
        
        if commit is not None:
            commit_tag_map[commit] = tag

    return commit_tag_map

def generate_logs(repo_dir, output):
    log_str = GitLog().git_log(repo_dir)
    with open(output, 'w') as fout:
        fout.write(log_str)


def get_duplicate_commits(commit_id, commit_patch_map, patch_commit_map):
    if commit_id not in commit_patch_map:
        return []
    
    duplicated_commits = set()
    for h in commit_patch_map[commit_id]:
        for c in patch_commit_map[h]:
            if c == commit_id:
                continue

            s1 = set(commit_patch_map[commit_id])
            s2 = set(commit_patch_map[c])
            if s1 == s2 or s1.issubset(s2):
                duplicated_commits.add(c)

    return list(duplicated_commits)

def generate_vulnerable_versions(project, fixing_commit, inducing_commit):
    git_logs = retrieve_git_logs(os.path.join(log_dir, project+"-meta.log"), project)
    git_log_dict = retrieve_git_logs_dict(git_logs, project)
    
    commit_tag_map = get_tags(os.path.join(repos_dir, project))
    for commit_id in git_log_dict:
        if commit_id in commit_tag_map:
            git_log_dict[commit_id].set_tag(commit_tag_map[commit_id])
        
        if len(git_log_dict[commit_id].parent) == 0:
            git_log_dict[commit_id].set_tag("Initial Commit")
    
    with open(os.path.join(WORK_DIR, f'data_commit_patch_map/{project}-commit-patch.json')) as fin1, \
            open(os.path.join(WORK_DIR, f'data_commit_patch_map/{project}-patch-commit.json')) as fin2:
        commit_patch_map = json.load(fin1)
        patch_commit_map = json.load(fin2)

    try:
        fc_sons_tag = get_son_tags(git_log_dict, fixing_commit)

        duplicated_commits = get_duplicate_commits(fixing_commit, commit_patch_map, patch_commit_map)
        if len(duplicated_commits) > 0:
            for c in duplicated_commits:
                fc_sons_tag |= get_son_tags(git_log_dict, c)

        ic_sons_tag = get_son_tags(git_log_dict, inducing_commit)

        duplicated_commits = get_duplicate_commits(inducing_commit, commit_patch_map, patch_commit_map)
        for c in duplicated_commits:
            ic_sons_tag |= get_son_tags(git_log_dict, c)

        ic_sons_tag = set([t.tag for t in ic_sons_tag])
        fc_sons_tag = set([t.tag for t in fc_sons_tag])

        return ic_sons_tag - fc_sons_tag

    except Exception as e:
        print(e)
        return None




    