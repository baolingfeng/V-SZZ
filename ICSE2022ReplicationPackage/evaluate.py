import os
import sys
import json
import statistics

from setting import WORK_DIR, DATA_FOLDER
from data_loader import JAVA_CVE_FIX_COMMITS, C_CVE_FIX_COMMITS, read_cve_commits, REPOS_DIR, JAVA_PROJECTS, C_PROJECTS
from log_generation import GitLog
from extract_tag import generate_vulnerable_versions


def eval_vulnerable_version(lang='C', szz_method='b'):
    with open(os.path.join(DATA_FOLDER, f'verified_cve_with_versions_{lang}.json')) as fin:
        labeled_items = json.load(fin)
    
    print(szz_method)
    version_recalls = []
    version_precisions = []
    
    correct_c = set()
    idetified_c = set()

    n_correct_commit = 0
    n_correct_version = 0
    n_szz_fail = 0
    for item in labeled_items:
        project = item['project']
        cve_id = item['cve_id']
        cve_version_consistent = item['cve_version_consistent']
        # print(project, cve_id)
        try:
            with open(os.path.join(WORK_DIR, f"results/{szz_method}-{project}.json")) as fin:
                szz_results = json.load(fin)
        except:
            continue
        
        SZZ_fail = False
        commit_version_map = {}
        fixing_inducing_map = {}
        inducing_commits = set()
        szz_commits = set()
        for fd in item['fixing_details']:
            fixing_commit = fd['fixing_commit']
            if fixing_commit not in szz_results:
                print('SZZ not work', cve_id, project)
                SZZ_fail = True
                continue

            szz_vic = szz_results[fixing_commit]
            # V-SZZ considers the last commit as the inducing commit
            if szz_method == 'my':
                szz_vic = []
                for record in szz_results[fixing_commit]:
                    szz_vic.append(record[-1][0])
            
            for sc in szz_vic:
                fixing_inducing_map[sc] = fixing_commit

            szz_commits |= set(szz_vic)
            
            for ic in fd['inducing_commits']:
                if ic['is_true_inducing'] == 'True':
                    inducing_commits.add(ic['commit_id'])

                # commit_version_map[ic['commit_id']] = ic
                if ic['affected_version_tags'] is None:
                    commit_version_map[ic['commit_id']] = set()
                else:
                    commit_version_map[ic['commit_id']] = set(ic['affected_version_tags'].split(','))
            
        sorted_szz_vic = sorted(list(szz_commits), key=lambda k: GitLog().get_commit_time(os.path.join(REPOS_DIR, project), k))
        if len(sorted_szz_vic) > 0:
            szz_vic =  sorted_szz_vic[0]
        else:
            szz_vic = None

        if SZZ_fail:
            n_szz_fail += 1
            continue

        sorted_inducing_commits = sorted(list(inducing_commits), key=lambda k: GitLog().get_commit_time(os.path.join(REPOS_DIR, project), k))
        if len(sorted_inducing_commits) <= 0:
            continue

        true_vic = sorted_inducing_commits[0]
        correct_c.add(true_vic)

        correct_versions = commit_version_map[true_vic]
        if szz_vic not in commit_version_map and szz_vic is not None:
            # print('szz commit id not found', cve_id, project, szz_vic)
            idetified_versions = generate_vulnerable_versions(project, fixing_inducing_map[szz_vic], szz_vic)
            # print(idetified_versions)
        elif szz_vic is None:
            idetified_versions = set()
        else:
            idetified_versions = commit_version_map[szz_vic]
        
        idetified_c = idetified_c | set(sorted_szz_vic)

        intersection = set([true_vic]).intersection(sorted_szz_vic)
        if len(intersection) > 0:
            n_correct_commit += 1

        intersection = set(correct_versions).intersection(idetified_versions)
        version_recalls.append(len(intersection) * 1.0 / len(correct_versions) if len(correct_versions) > 0 else 0)
        version_precisions.append(len(intersection) * 1.0 / len(idetified_versions) if len(idetified_versions) > 0 else 0)
        if correct_versions == idetified_versions:
            n_correct_version += 1

    intersection = correct_c.intersection(idetified_c)
    recall_c = len(intersection) * 1.0 / len(correct_c)
    precision_c = len(intersection) * 1.0 / len(idetified_c) 

    print(recall_c, precision_c)

    return n_correct_commit, n_correct_version, n_szz_fail, recall_c, precision_c, statistics.mean(version_recalls), statistics.mean(version_precisions)


if __name__ == "__main__":
    fout = open('eval_results.txt', 'w')
    for lang in ['C', 'Java']:
    # for lang in ['C']:
        for szz_method in ['b', 'ag', 'ma', 'ra', 'my']:
            if lang == 'C' and szz_method == 'ra':
                continue

            results = eval_vulnerable_version(lang, szz_method)
            fout.write(szz_method + '\n')
            fout.write('{0}, {1}, {2}\n'.format(results[0], results[1], results[2]))
            fout.write('{0}, {1}\n'.format(results[3], results[4]))
            fout.write('{0}, {1}\n'.format(results[5], results[6]))

    fout.close()

