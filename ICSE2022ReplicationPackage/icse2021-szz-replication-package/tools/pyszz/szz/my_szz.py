import os
import sys
import logging as log
import traceback
from typing import List, Set
import subprocess
import json

from git import Commit

from szz.core.abstract_szz import AbstractSZZ, ImpactedFile

from pydriller import ModificationType, GitRepository as PyDrillerGitRepo
import Levenshtein


def remove_whitespace(line_str):
    return ''.join(line_str.strip().split())

def compute_line_ratio(line_str1, line_str2):
    l1 = remove_whitespace(line_str1)
    l2 = remove_whitespace(line_str2)
    return Levenshtein.ratio(l1, l2)

MAXSIZE = sys.maxsize

class MySZZ(AbstractSZZ):
    """
    My SZZ implementation.

    Supported **kwargs:

    * ignore_revs_file_path

    """

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None, use_temp_dir: bool = True, ast_map_path = None):
        super().__init__(repo_full_name, repo_url, repos_dir, use_temp_dir)
        self.ast_map_path = ast_map_path

    def find_bic(self, fix_commit_hash: str, impacted_files: List['ImpactedFile'], **kwargs) -> Set[Commit]:
        """
        Find bug introducing commits candidates.

        :param str fix_commit_hash: hash of fix commit to scan for buggy commits
        :param List[ImpactedFile] impacted_files: list of impacted files in fix commit
        :key ignore_revs_file_path (str): specify ignore revs file for git blame to ignore specific commits.
        :returns Set[Commit] a set of bug introducing commits candidates, represented by Commit object
        """

        log.info(f"find_bic() kwargs: {kwargs}")

        ignore_revs_file_path = kwargs.get('ignore_revs_file_path', None)
        # self._set_working_tree_to_commit(fix_commit_hash)

        bug_introd_commits = []
        for imp_file in impacted_files:
            # print('impacted file', imp_file.file_path)
            try:
                blame_data = self._blame(
                    # rev='HEAD^',
                    rev='{commit_id}^'.format(commit_id=fix_commit_hash),
                    file_path=imp_file.file_path,
                    modified_lines=imp_file.modified_lines,
                    ignore_revs_file_path=ignore_revs_file_path,
                    ignore_whitespaces=False,
                    skip_comments=True
                )

                for entry in blame_data:
                    print(entry.commit, entry.line_num, entry.line_str)
                    previous_commits = []
                    
                    blame_result = entry
                    while True:
                        if imp_file.file_path.endswith(".java"):
                            mapped_line_num, change_type = self.map_modified_line_java(blame_result, imp_file.file_path)
                            previous_commits.append((blame_result.commit.hexsha, blame_result.line_num, blame_result.line_str, change_type))
                        else:
                            mapped_line_num = self.map_modified_line(blame_result, imp_file.file_path)
                            previous_commits.append((blame_result.commit.hexsha, blame_result.line_num, blame_result.line_str))
                        
                        if mapped_line_num == -1:
                            break
                        
                        
                        blame_data2 = self._blame(
                                        rev='{commit_id}^'.format(commit_id=blame_result.commit.hexsha),
                                        file_path=imp_file.file_path,
                                        modified_lines=[mapped_line_num],
                                        ignore_revs_file_path=ignore_revs_file_path,
                                        ignore_whitespaces=False,
                                        skip_comments=True
                                    )
                        blame_result = list(blame_data2)[0]
                        # print(blame_result.commit.hexsha, blame_result.line_num)
                        # print(mapped_line_num, blame_result.commit.hexsha, blame_result.line_num, blame_result.line_str)
                        # previous_commits.append((blame_result.commit, blame_result.line_num, blame_result.line_str))

                    # bug_introd_commits[entry.line_num] = {'line_str': entry.line_str, 'file_path': entry.file_path, 'previous_commits': previous_commits}
                    bug_introd_commits.append({'line_num':entry.line_num, 'line_str': entry.line_str, 'file_path': entry.file_path, 'previous_commits': previous_commits})
                    # bug_introd_commits.append(previous_commits)
            except:
                print(traceback.format_exc())

        return bug_introd_commits

    def map_modified_line_java(self, blame_entry, blame_file_path):
        mapping_cmd = "java -jar ASTMapEval.jar -p {project} -c {commit_id} -o {output} -f {file_path}"
        ast_map_temp = os.path.join(self.ast_map_path, 'temp')

        commit_id = blame_entry.commit.hexsha
        file_path = blame_file_path.replace('\\', '/')
        
        line_num = blame_entry.line_num

        mapping_db = None
        mapping_db_file = os.path.join(ast_map_temp, "{project}.json".format(project=self.repo_full_name))
        if os.path.exists(mapping_db_file):
            mapping_db = json.load(open(mapping_db_file))
            if commit_id not in mapping_db:
                subprocess.check_output(mapping_cmd.format(project=self.repo_full_name, commit_id=commit_id, output=os.path.join(ast_map_temp, "tmp.json"), file_path=file_path), cwd=self.ast_map_path, shell=True).decode('utf-8', errors='ignore')

                mapping_results = json.load(open(os.path.join(ast_map_temp, "tmp.json")))
                mapping_db[commit_id] = {}
                mapping_db[commit_id][file_path] = mapping_results
            elif file_path not in mapping_db[commit_id]:
                subprocess.check_output(mapping_cmd.format(project=self.repo_full_name, commit_id=commit_id, output=os.path.join(ast_map_temp, "tmp.json"), file_path=file_path), cwd=self.ast_map_path, shell=True).decode('utf-8', errors='ignore')

                mapping_results = json.load(open(os.path.join(ast_map_temp, "tmp.json")))
                mapping_db[commit_id][file_path] = mapping_results
            else:
                mapping_results = mapping_db[commit_id][file_path]
        else:
            subprocess.check_output(mapping_cmd.format(project=self.repo_full_name, commit_id=commit_id, output=os.path.join(ast_map_temp, "tmp.json"), file_path=file_path), cwd=self.ast_map_path, shell=True).decode('utf-8', errors='ignore')

            mapping_results = json.load(open(os.path.join(ast_map_temp, "tmp.json")))
            mapping_db = {}
            mapping_db[commit_id] = {}
            mapping_db[commit_id][file_path] = mapping_results

        with open(mapping_db_file, 'w') as fout:
            json.dump(mapping_db, fout, indent=4)

        target_file = None
        target_stmt = None
        for result in mapping_results:
            if file_path == result['src']:
                target_file = result['dst']
                      
                for stmt in result['stmt']:
                    if 'dstStmtStartLine' in stmt and stmt['dstStmtStartLine'] == int(line_num):
                        target_stmt = stmt
                        break
                
                if target_stmt is not None:
                    break
        
        if target_stmt is None:
            # "New File"
            return -1, "New File"
        
        # results.append((buggy_commit, buggy_file, buggy_line, target_stmt['stmtChangeType']))
        if target_stmt['stmtChangeType'] == "Insert":
            return -1, target_stmt['stmtChangeType']
        
        return target_stmt['srcStmtStartLine'], target_stmt['stmtChangeType']
       

    def map_modified_line(self, blame_entry, blame_file_path):
        #TODO: rename type 
        blame_commit = PyDrillerGitRepo(self.repository_path).get_commit(blame_entry.commit.hexsha)
        # print('get blame commit', blame_commit, blame_entry.commit.hexsha)

        for mod in blame_commit.modifications:
            file_path = mod.new_path
            if mod.change_type == ModificationType.DELETE or mod.change_type == ModificationType.RENAME:
                file_path = mod.old_path

            if file_path != blame_file_path:
                continue

            if not mod.old_path:
                # "newly added"
                return -1

            lines_added = [added for added in mod.diff_parsed['added']]
            lines_deleted = [deleted for deleted in mod.diff_parsed['deleted']]

            if len(lines_deleted) == 0:
                return -1
            
            print('line added/deleted', len(lines_added), len(lines_deleted))

            if blame_entry.line_str:
                sorted_lines_deleted = [(line[0], line[1], 
                                            compute_line_ratio(blame_entry.line_str, line[1]), 
                                            abs(blame_entry.line_num - line[0])) 
                                        for line in lines_deleted]
                sorted_lines_deleted = sorted(sorted_lines_deleted, key=lambda x : (x[2], MAXSIZE-x[3]), reverse=True)
                # print(sorted_lines_deleted)
                
                # print(sorted_lines_deleted)
                if sorted_lines_deleted[0][2] > 0.75:
                    return sorted_lines_deleted[0][0]
                                             
        return -1        
                
                    