import logging as log
import traceback
from typing import List, Set

from git import Commit
from pydriller import RepositoryMining, GitRepository

from szz.core.abstract_szz import AbstractSZZ, ImpactedFile


def match_files(file: str, impacted_files: List['ImpactedFile']) -> bool:
    for entry in impacted_files:
        if entry.file_path == file:
            return True
    return False


class PyDrillerSZZ(AbstractSZZ):
    """
    PyDriller SZZ implementation.

    Supported **kwargs:

    * ignore_revs_file_path

    """

    def __init__(self, repo_full_name: str, repo_url: str, repos_dir: str = None):
        super().__init__(repo_full_name, repo_url, repos_dir)

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
        self._set_working_tree_to_commit(fix_commit_hash)

        bug_introd_commits = set()

        gr = GitRepository(self.repository_path)
        pydriller_fix_commit = gr.get_commit(fix_commit_hash)
        for mod in pydriller_fix_commit.modifications:
            if match_files(mod.new_path, impacted_files) or match_files(mod.old_path, impacted_files):
                bics_per_mod = gr.get_commits_last_modified_lines(pydriller_fix_commit, mod)
                for bic_path, bic_commit_hashes in bics_per_mod.items():
                    for bic_commit_hash in bic_commit_hashes:
                        commit_introducing = self.get_commit(bic_commit_hash)
                        bug_introd_commits.add(commit_introducing)

        return bug_introd_commits
