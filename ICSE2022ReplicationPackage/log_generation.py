# -*- coding: utf-8 -*-
import sys

import os
import subprocess
import git # get diff patch on Windows 
from unidiff import PatchSet
from io import StringIO

def wrapper_change_path(func):
    cwd = os.getcwd()

    def inner(*args, **kwargs):
        return func(*args, **kwargs)


    os.chdir(cwd)
    return inner

def is_nosise(line):
    #
    line = line.strip('\t').strip('\r').strip()
    # ignore blank line
    if line == '':
        return True
    # ignore comment
    if line.startswith('//') or line.startswith('/**') or line.startswith('*') or \
            line.startswith('/*') or line.endswith('*/'):
        return True
    # ignore import line
    if line.startswith('import ') or line.startswith('package'):
        return True
    return False

class GitLog:
    commands = {
        'meta': 'meta_cmd',
        'numstat': 'numstat_cmd',
        'namestat': 'namestat_cmd',
        'merge_numstat': 'merge_numstat_cmd',
        'merge_namestat': 'merge_namestat_cmd'
    }

    def __init__(self):
        self.meta_cmd = 'git log --reverse --all --pretty=format:\"commit: %H%n' \
                        'parent: %P%n' \
                        'author: %an%n' \
                        'author email: %ae%n' \
                        'time stamp: %at%n' \
                        'committer: %cn%n' \
                        'committer email: %ce%n' \
                        '%B%n\"  '
        self.numstat_cmd = 'git log --pretty=format:\"commit: %H\" --numstat -M --all --reverse '
        self.namestat_cmd = 'git log  --pretty=format:\"commit: %H\" --name-status -M --all --reverse '
        self.merge_numstat_cmd = 'git log --pretty=oneline --numstat -m --merges -M --all --reverse '
        self.merge_namestat_cmd = 'git log --pretty=oneline  --name-status -m --merges -M  --all --reverse '

    @wrapper_change_path
    def git_log(self, project_path):
        os.chdir(project_path)

        cmd = getattr(self, GitLog.commands.get('meta'))
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        return out
    
    @wrapper_change_path
    def git_tag(self, project_path):
        os.chdir(project_path)

        cmd = 'git tag'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        return out
    
    @wrapper_change_path
    def git_show(self, project_path, tag):
        os.chdir(project_path)

        cmd = 'git show {tag} --pretty=format:"commit: %H%ntimestamp: %ct%n"'.format(tag=tag)
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        return out
    
    def git_diff(self, project_path, commit_id):
        repository = git.Repo(project_path)
        try:
            commit = repository.commit(commit_id)
            uni_diff_text = repository.git.diff(commit_id+ '~1', commit_id,
                                            ignore_blank_lines=True, 
                                            ignore_space_at_eol=True)
            
            patch_set = PatchSet(StringIO(uni_diff_text))
        except Exception as e:
            print(project_path, 'Error: ', e)
            return None

        change_list = []  
        for patched_file in patch_set:
            file_path = patched_file.path  # file name
            ad_line_no = [(line.target_line_no, line.value) for hunk in patched_file for line in hunk if line.is_added and not is_nosise(line.value.strip())]  
            
            del_line_no = [(line.source_line_no, line.value) for hunk in patched_file for line in hunk if line.is_removed and not is_nosise(line.value.strip())]  
            change_list.append((file_path, del_line_no, ad_line_no))

        return change_list


    
    def git_diff_2(self, project_path, commit_id):
        repository = git.Repo(project_path)
        try:
            commit = repository.commit(commit_id)
            uni_diff_text = repository.git.diff(commit_id+ '~1', commit_id,
                                            ignore_blank_lines=True, 
                                            ignore_space_at_eol=True)
            
            patch_set = PatchSet(StringIO(uni_diff_text))
        except Exception as e:
            print(project, 'Error: ', e)
            return None

        change_list = []  
        for patched_file in patch_set:
            file_path = patched_file.path  # file name
            ad_line_no = [(line.target_line_no, line.value) for hunk in patched_file for line in hunk if line.is_added and not is_nosise(line.value.strip())]  
            
            del_line_no = [(line.source_line_no, line.value) for hunk in patched_file for line in hunk if line.is_removed and not is_nosise(line.value.strip())]  
            change_list.append({"file_path": file_path, "del_line_no": del_line_no, "ad_line_no": ad_line_no, "is_added_file": patched_file.is_added_file})

        return change_list

    @wrapper_change_path
    def get_commit_time(self, project_path, commit_id):
        os.chdir(project_path)

        cmd = 'git show -s --format=%ci {commit}'.format(commit=commit_id)
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        return out
    
    @wrapper_change_path
    def fetch_tags(self, project_path):
        os.chdir(project_path)

        cmd = 'git fetch --all --tags'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')

    @wrapper_change_path
    def get_tags(self, project_path):
        os.chdir(project_path)

        cmd = 'git show-ref --tags'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        return out
    
    @wrapper_change_path
    def get_commits_range(self, project_path, commit1, commit2):
        os.chdir(project_path)

        cmd = f'git log --pretty=oneline {commit1}...{commit2}'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        commits = []
        for line in out.split('\n'):
            commits.append(line.split(' ')[0])

        return out
    
    @wrapper_change_path
    def get_commits_from(self, project_path, commit_id):
        os.chdir(project_path)

        cmd = f'git log --pretty=oneline {commit_id}'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        commits = []
        for line in out.split('\n'):
            commits.append(line.split(' ')[0])

        return commits

if __name__ == '__main__':
    pass


