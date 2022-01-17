from flask import Flask, request, jsonify, render_template, make_response, redirect, url_for
from flask import g
from flask_wtf.csrf import CSRFProtect
import random
import sys
import os
import json
import shutil
import git 
from unidiff import PatchSet
from io import StringIO
import subprocess
import re

from cve import CVEItem

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app = Flask(__name__, static_folder=ASSETS_DIR)
app.config['TEMPLATES_AUTO_RELOAD'] = True
csrf = CSRFProtect(app)

app.secret_key = os.urandom(24)

# TODO: replace your working directory
work_dir = '/data1/xxx'

replication_dir = os.path.join(work_dir, 'ICSE2020ReplicationPackage')

# TODO: project repositries, please modify it according to your repo directory
repo_dir = os.path.join(work_dir, 'repos')

# the datasets containing CVE vulnerabilities and their fixing commits
java_vul_fixing_file = os.path.join(replication_dir, 'data', 'java_cve_fix_detail.json')
c_vul_fixing_file = os.path.join(replication_dir, 'data', 'c_cve_fix_detail.json')

# This file is a file that stores the annotated results
labeled_file = os.path.join(replication_dir, 'data', 'label.json')

def get_cve_data(project_type="java"):
    cve_data = None
    if project_type == "java":
        cve_data = getattr(g, '_java_cve_data', None)
        if cve_data is None:
            with open(java_vul_fixing_file) as fin:
                cve_data = g._java_cve_data = json.load(fin)
    elif project_type == "c":
        cve_data = getattr(g, '_c_cve_data', None)
        if cve_data is None:
            with open(c_vul_fixing_file) as fin:
                cve_data = g._c_cve_data = json.load(fin)

    return cve_data


def transform_table_data(cve_data):
    with open(labeled_file) as fin:
        annotation = json.load(fin) 

    rows = []
    for project in cve_data:
        project_url = cve_data[project]['url']
        for cve_id in cve_data[project]['cves']:
            if 'fix_details' not in cve_data[project]['cves'][cve_id]:
                continue
            
            cwe = cve_data[project]['cves'][cve_id]['cwe']

            for fix in cve_data[project]['cves'][cve_id]['fix_details']:
                fixing_commit_id = fix['commit_id']  
                num_src_file = fix['num_src_file']
                num_del_line = fix['num_del_line']
                num_add_line = fix['num_add_line']

                has_annotated = False
                if project in annotation and cve_id in annotation[project] and fixing_commit_id in annotation[project][cve_id]['fixing_commits']:
                    has_annotated = True

                row = {'project': project, 'project_url':project_url, 'cve_id': cve_id, 'cwe': cwe, 'fixing_commit_id': fixing_commit_id, 'num_src_file':num_src_file, 'num_del_line':num_del_line, 'num_add_line':num_add_line, 'has_annotated': has_annotated}
                rows.append(row)
    
    return rows

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

def git_diff(project, commit_id):
    target_path = os.path.join(repo_dir, project)
    repository = git.Repo(target_path)
    try:
        commit = repository.commit(commit_id)
        uni_diff_text = repository.git.diff(commit_id+ '~1', commit_id,
                                        ignore_blank_lines=True, 
                                        ignore_space_at_eol=True)
        
        patch_set = PatchSet(StringIO(uni_diff_text))
    except Exception as e:
        return None, None 

    deleted_lines = {}  
    for patched_file in patch_set:
        file_path = patched_file.path  # file name
        # ad_line_no = [(line.target_line_no, line.value) for hunk in patched_file for line in hunk if line.is_added and not is_nosise(line.value.strip())]  
        
        del_line_no = [line.source_line_no for hunk in patched_file for line in hunk if line.is_removed and not is_nosise(line.value.strip())]  
        if len(del_line_no) > 0:
            deleted_lines[file_path] = del_line_no

        # deleted_lines.append((file_path, del_line_no, ad_line_no))

    return uni_diff_text, deleted_lines   

@csrf.exempt
@app.route("/cve_data", methods=["GET", "POST"])
def submit_survey():
    # print request.json
    if 'project_type' in request.args:
        project_type = request.args['project_type'] 
    else:
        project_type = "java"
    
    cve_data = get_cve_data(project_type)
    table_data = transform_table_data(cve_data)

    return jsonify({'table_data': table_data})
   

@app.route('/vulfixingcommit')
def vulfixingcommit():
    cve_id = request.args['cve_id'] 
    project = request.args['project']
    commit_id = request.args['commit']
    print(cve_id+"/"+project+"/"+commit_id)
    
    if 'project_type' in request.args:
        project_type = request.args['project_type'] 
    else:
        project_type = "java"

    cve_item = CVEItem.initiliaze(cve_id)
    if cve_item is None:
        cve_desc = ""
        cwe = ""
        cwe_desc = ""
    else:
        cve_desc = cve_item.description
        cwe = cve_item.cwe
        cwe_desc = cve_item.cwe_desc

    cve_data = get_cve_data(project_type)
    project_url = cve_data[project]['url']

    uni_diff_text, deleted_lines = git_diff(project, commit_id)
    print(re.split('\n|\r|\r\n', uni_diff_text))
    # uni_diff_text = uni_diff_text.replace('\n', '\\\n\n')
    diff_text_arr = []
    for line in re.split('\n|\r|\r\n', uni_diff_text):
        line = line.replace('\\', '\\\\')
        diff_text_arr.append(line)
    print(diff_text_arr)


    fix_detail = None
    for fix in cve_data[project]['cves'][cve_id]['fix_details']:
        if fix['commit_id'] == commit_id:
            fix_detail = fix
            break

    record = {'cve_id': cve_id, 'project': project, 'project_url':project_url, 'commit_id': commit_id, 'cve_desc': cve_desc, 'cwe': cwe, 'cwe_desc':cwe_desc, 'uni_diff_text': diff_text_arr, 'fix_detail': fix_detail, 'deleted_lines': deleted_lines}
    
    return render_template('vulfixingcommit.html', record=record)

@csrf.exempt
@app.route("/gitblame", methods=["GET", "POST"])
def gitblame():
    project = request.json['project'] 
    commit = request.json['commit'] 
    file = request.json['file']
    line = request.json['line']

    blame_cmd = "git blame -L {line},+1 -f -n {commit_id}~ -l -- {file}".format(line=line, file=file, commit_id=commit)
    project_dir = os.path.join(repo_dir, project)

    try:
        blame_raw = subprocess.check_output(blame_cmd, shell=True, cwd=project_dir).decode('utf-8',errors='ignore')

        blame_commit = {}
        blame_commit['commit_id'] = blame_raw.split()[0]
        blame_commit['file'] = blame_raw.split()[1]
        blame_commit['line'] = blame_raw.split()[2]
        blame_commit['project'] = project

        if blame_commit['commit_id'].startswith('^'):
            print('the init repo commit', blame_commit['commit_id'])
            blame_commit['commit_id'] = blame_commit['commit_id'][1:]
            blame_commit['is_init'] = True

        # print(blameresult)

        return jsonify({'msg': 'success', 'blame_result': blame_commit})
    except Exception as e:
        return jsonify({'msg': 'fail'})

@csrf.exempt
@app.route("/savepc", methods=["GET", "POST"])
def savepc():
    project = request.json['project'] 
    commit = request.json['commit'] 
    file = request.json['file']
    line = request.json['line']
    cve = request.json['cve']
    cwe = request.json['cwe']
    pcCommits = request.json['pcCommits']
    pcDel = request.json['pcDel']
    pcAdd = request.json['pcAdd']
    vic = request.json['vic']
    vulType = request.json['vulType']

    with open(labeled_file, 'r') as fin:
        data = json.load(fin)
    
    record = {'project': project, 'commit': commit, 'file': file, 'line': line, 'cve': cve, 'cwe': cwe, 'Previous Commits': pcCommits, 'Deleted Lines': pcDel, 'Added Lines': pcAdd, 'Vulnerability Introducing Commit': vic, 'Vulnerability Type': vulType}
    
    if project not in data:
        data[project] = {}
    
    if cve not in data[project]:
        data[project][cve] = {'cwe': cwe, 'Vulnerability Type': vulType, 'fixing_commits': {}}
    
    if commit not in data[project][cve]['fixing_commits']:
        data[project][cve]['fixing_commits'][commit] = {}

    if file not in data[project][cve]['fixing_commits'][commit]:
        data[project][cve]['fixing_commits'][commit][file] = {}

    data[project][cve]['fixing_commits'][commit][file][line] = {'Previous Commits': pcCommits, 'Deleted Lines': pcDel, 'Added Lines': pcAdd, 'Vulnerability Introducing Commit': vic}
    
    with open(labeled_file, 'w') as fout:
        json.dump(data, fout, indent=4)

    return jsonify({'msg': 'success'})

@app.route('/blameresult', methods=["GET", "POST"])
def blameresult():
    # print(request.args)
    project = request.args.get('project')
    blame_commit = request.args.get('blame_commit') 
    origin_commit = request.args.get('origin_commit') 
    file = request.args.get('file')
    line = request.args.get('line')
    is_init = request.args.get('is_init')

    result = {}
    result['project'] = project
    result['blame_commit'] = blame_commit
    result['origin_commit'] = origin_commit
    result['file'] = file
    result['line'] = line

    if is_init == 'true':
        result['is_init'] = True
        result['diff_text'] = ""
        result['deleted_lines'] = []
    else:
        uni_diff_text, deleted_lines = git_diff(project, blame_commit)
        # print('file: ' + file)
        diff_text = []
        flag = False
        for line in re.split('\n|\r|\r\n', uni_diff_text):
            if line.startswith('diff --git '):
                # print(line)
                if line.find(file) >= 0:
                    diff_text.append(line)
                    flag = True
                else:
                    flag = False
                continue

            if flag:
                line = line.replace('\\', '\\\\')
                diff_text.append(line)

        # print(diff_text)
        result['diff_text'] = diff_text
        result['deleted_lines'] = deleted_lines[file] if file in deleted_lines else []
    return render_template('blameresult.html', result=result)


@app.route('/')
def index():
    project_type = request.args.get('project_type')
    if project_type is None:
        project_type = 'java'

    return render_template('index.html', project_type=project_type)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    # connect to ip adress
    app.run(host='0.0.0.0', port=8080)
