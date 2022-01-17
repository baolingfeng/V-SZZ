import json
import os
import shutil
import subprocess
import sys
from shutil import copytree


def move_results(project: str) -> None:
    try:
        filename = project.replace('/', '_') + ".txt"
        os.rename(filename, "results/" + filename)
        filename = project.replace('/', '_') + "_BugFixingCommit.csv"
        os.rename(filename, "results/" + filename)
        filename = project.replace('/', '_') + "_BugInducingCommits.csv"
        os.rename(filename, "results/" + filename)
        dir_name = project.split('/')[1]
        shutil.rmtree(dir_name)
        os.remove(dir_name + ".txt")
    except:
        pass


def copy_git(sources: str, base_path: str, repo_full_name: str) -> None:
    repo_dir = os.path.join(sources, repo_full_name)
    if os.path.isdir(repo_dir):
        repo_clone_name = repo_full_name.split('/')[1]
        copytree(repo_dir, base_path + repo_clone_name, symlinks=True)


def exec_open_szz(sources: str, base_path: str, project: str, list_proj: [str]) -> None:
    filename = project.replace('/', '_') + ".txt"
    with open(filename, 'w') as fout:
        for line in list_proj:
            fout.write(line)
            fout.write("\n")
        fout.close()
        print("Executing " + project)
        copy_git(sources, base_path, project)
        git_link = "https://github.com/" + project + ".git"
        subprocess.run(["java", "-jar", "openszz.jar", "-all", git_link, "https://issues.apache.org/jira/projects/BCEL", project, filename])
        move_results(project)


def main(argv):
    sources = argv[1]
    input_file = argv[2]
    base_path = argv[3]
    print("Cloned projects: " + sources)
    print(input_file)

    if not os.path.exists("results"):
        os.mkdir("results")

    with open(input_file) as json_file:
        file_json = json.load(json_file)
        # print(file_json)
        set_repos = set()
        for obj in file_json:
            repo_name = obj['repo_name']
            list_fix = []
            for block in file_json:
                if repo_name == block['repo_name']:
                    value_name = block['fix_commit_hash']
                    list_fix.append(value_name)
            if len(list_fix) > 0:
                exec_open_szz(sources, base_path, repo_name, list_fix)


if __name__ == "__main__":
    # execute only if run as a script
    main(sys.argv)
