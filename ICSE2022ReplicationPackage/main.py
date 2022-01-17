import os
import sys
import json
import logging as log

from setting import *

sys.path.append(os.path.join(SZZ_FOLDER, 'tools/pyszz/'))

from szz.ag_szz import AGSZZ
from szz.b_szz import BaseSZZ
from szz.l_szz import LSZZ
from szz.ma_szz import MASZZ, DetectLineMoved
from szz.r_szz import RSZZ
from szz.ra_szz import RASZZ
from szz.pd_szz import PyDrillerSZZ
from szz.my_szz import MySZZ

from data_loader import JAVA_CVE_FIX_COMMITS, C_CVE_FIX_COMMITS, JAVA_PROJECTS, C_PROJECTS, read_cve_commits, load_annotated_commits

def run_szz(project, commits, method, repo_url=None, max_change_size=DEFAULT_MAX_CHANGE_SIZE):
    output_file = "results/{method}-{project}.json".format(method=method, project=project)

    if os.path.exists(output_file):
        return
    use_temp_dir = False

    output = {}
    if method == "b":
        b_szz = BaseSZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = b_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = b_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None)
            output[commit] = [commit.hexsha for commit in bug_introducing_commits]
    elif method == "ag":
        ag_szz = AGSZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = ag_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = ag_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None,
                                      max_change_size=max_change_size)
            output[commit] = [commit.hexsha for commit in bug_introducing_commits]
    elif method == "ma":
        ma_szz = MASZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = ma_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = ma_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None,
                                      max_change_size=max_change_size)

            output[commit] = [commit.hexsha for commit in bug_introducing_commits]
    elif method == "my":
        my_szz = MySZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir, ast_map_path=AST_MAP_PATH)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = my_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = my_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None)
            output[commit] = bug_introducing_commits
    elif method == "ra":
        ra_szz = RASZZ(repo_full_name=project, repo_url=repo_url, repos_dir=REPOS_DIR, use_temp_dir=use_temp_dir)
        for commit in commits:
            print('Fixing Commit:', commit)
            imp_files = ra_szz.get_impacted_files(fix_commit_hash=commit, file_ext_to_parse=['c', 'java', 'cpp', 'h', 'hpp'], only_deleted_lines=True)
            bug_introducing_commits = ra_szz.find_bic(fix_commit_hash=commit,
                                      impacted_files=imp_files,
                                      ignore_revs_file_path=None,
                                      max_change_size=max_change_size)
            output[commit] = [commit.hexsha for commit in bug_introducing_commits]

    with open(output_file, 'w') as fout:
        json.dump(output, fout, indent=4)

if __name__ == "__main__":
    use_temp_dir = False

    # fixing_commits = JAVA_CVE_FIX_COMMITS
    # fixing_commits = C_CVE_FIX_COMMITS

    project_commits = load_annotated_commits()
    for project in project_commits:
        print("Project:", project)
        run_szz(project, project_commits[project], 'ma')

        break


        
    