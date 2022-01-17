import os
import sys
import json

from setting import *

def load_java_cve_commits():
    java_cve_fix_commit_file = os.path.join(DATA_FOLDER, 'java_cve_fix_detail.json')
    with open(java_cve_fix_commit_file) as fin:
        java_cve_fix_commits = json.load(fin)
        return java_cve_fix_commits

def load_c_cve_commits():
    c_cve_fix_commit_file = os.path.join(DATA_FOLDER, 'c_cve_fix_detail.json')
    with open(c_cve_fix_commit_file) as fin:
        c_cve_fix_commits = json.load(fin)
        return c_cve_fix_commits

def load_annotated_cves():
    with open(os.path.join(DATA_FOLDER, 'label.json')) as fin:
        return json.load(fin)

def load_annotated_commits(target_projects=None):
    with open(os.path.join(DATA_FOLDER, 'label.json')) as fin:
        annotation = json.load(fin)

        project_commits = {}
        for project in annotation:
            if target_projects is not None and project not in target_projects:
                continue

            project_commits[project] = []
            for cve_id in annotation[project]:
                cwe = annotation[project][cve_id]['cwe']
                for fixing_commit in annotation[project][cve_id]['fixing_commits']:
                    project_commits[project].append(fixing_commit)

        return project_commits  

JAVA_CVE_FIX_COMMITS = load_java_cve_commits()
C_CVE_FIX_COMMITS = load_c_cve_commits()
JAVA_PROJECTS = [project for project in JAVA_CVE_FIX_COMMITS]
C_PROJECTS = [project for project in C_CVE_FIX_COMMITS]
ANNOTATED_COMMITS = load_annotated_commits()
ANNOTATED_CVES = load_annotated_cves()

def read_cve_commits(project, cve_fix_commits):
    cve_commits = cve_fix_commits[project]['cves']
    
    all_valid_commits = []
    for cve_id in cve_commits:
        if 'fix_details' not in cve_commits[cve_id]:
            print(project, ' invalid')
            break

        fixes = cve_commits[cve_id]['fixes']
        fixes_detail = cve_commits[cve_id]['fix_details']

        valid_fixes = [fix['commit_id'] for fix in fixes_detail]

        all_valid_commits.extend(valid_fixes)
    
    return list(set(all_valid_commits))