import datetime
import json

import mysql.connector as mysql


def get_connection():
    return mysql.connect(
        host="localhost",
        port=3307,
        user="commits",
        passwd="commits",
        database="bugfix_commits"
    )


def get_fix_commits_data(conn):
    cursor = conn.cursor(dictionary=True)
    query = f"""
           SELECT id, hash, repository, issue_opening_date
           FROM fix_commit
           """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    return data


def get_fix_commits_langs(conn, fix_commit_id):
    cursor = conn.cursor(dictionary=True)
    query = f"""
           SELECT distinct lang
           FROM fix_impacted_file
            WHERE fix_commit_id = %s
           """
    cursor.execute(query, (fix_commit_id,))
    data = cursor.fetchall()
    cursor.close()

    return data


def get_issues_link(conn, fix_commit_id):
    cursor = conn.cursor(dictionary=True)
    query = f"""
           SELECT url
           FROM issue
            WHERE fix_commit_id = %s
           """
    cursor.execute(query, (fix_commit_id,))
    data = cursor.fetchall()
    cursor.close()

    return data


def get_bug_commits_data(conn, fix_commit_id):
    cursor = conn.cursor(dictionary=True)
    query = f"""
           SELECT hash, created_at
           FROM bug_commit
            WHERE fix_commit_id = %s
           """
    cursor.execute(query, (fix_commit_id,))
    data = cursor.fetchall()
    cursor.close()

    return data


def extract_bugfix_commits_exp1():
    commits = list()

    conn = get_connection()
    fix_commits = get_fix_commits_data(conn)
    print(len(fix_commits))

    for fc in fix_commits:
        bug_commits = get_bug_commits_data(conn, fc["id"])
        langs = [ext["lang"] for ext in get_fix_commits_langs(conn, fc["id"])]

        if not fc["issue_opening_date"]:
            commits.append({
                "id": fc["id"],
                "repo_name": fc["repository"],
                "fix_commit_hash": fc["hash"],
                "bug_commit_hash": [bc["hash"] for bc in bug_commits],
                "language": langs
            })

    print(len(commits))
    return commits


def extract_bugfix_commits_exp2():
    commits = list()

    conn = get_connection()
    fix_commits = get_fix_commits_data(conn)
    print(len(fix_commits))

    for fc in fix_commits:
        bug_commits = get_bug_commits_data(conn, fc["id"])
        issue_links = [issue["url"] for issue in get_issues_link(conn, fc["id"])]
        langs = [ext["lang"] for ext in get_fix_commits_langs(conn, fc["id"])]

        if fc["issue_opening_date"]:
            issue_date = fc["issue_opening_date"].isoformat()

            commits.append({
                "id": fc["id"],
                "repo_name": fc["repository"],
                "fix_commit_hash": fc["hash"],
                "bug_commit_hash": [bc["hash"] for bc in bug_commits],
                "earliest_issue_date": issue_date,
                "issue_urls": issue_links,
                "language": langs
            })

    print(len(commits))
    return commits


def extract_bugfix_commits_exp3():
    commits = list()

    conn = get_connection()
    fix_commits = get_fix_commits_data(conn)
    print(len(fix_commits))

    for fc in fix_commits:
        bug_commits = get_bug_commits_data(conn, fc["id"])
        issue_links = [issue["url"] for issue in get_issues_link(conn, fc["id"])]
        langs = [ext["lang"] for ext in get_fix_commits_langs(conn, fc["id"])]

        if fc["issue_opening_date"]:
            issue_date = fc["issue_opening_date"].isoformat()

            commits.append({
                "id": fc["id"],
                "repo_name": fc["repository"],
                "fix_commit_hash": fc["hash"],
                "bug_commit_hash": [bc["hash"] for bc in bug_commits],
                "earliest_issue_date": issue_date,
                "issue_urls": issue_links,
                "language": langs
            })
        else:
            dates = [d["created_at"] for d in bug_commits]
            best_scenario_issue_date = (min(dates) + datetime.timedelta(seconds=60)).isoformat()

            commits.append({
                "id": fc["id"],
                "repo_name": fc["repository"],
                "fix_commit_hash": fc["hash"],
                "bug_commit_hash": [bc["hash"] for bc in bug_commits],
                "best_scenario_issue_date": best_scenario_issue_date,
                "language": langs
            })

    print(len(commits))
    return commits


def main():
    with open('bugfix_commits_no_issues.json', 'w') as out:
        json.dump(extract_bugfix_commits_exp1(), out)
    with open('bugfix_commits_issues_only.json', 'w') as out:
        json.dump(extract_bugfix_commits_exp2(), out)
    with open('bugfix_commits_all.json', 'w') as out:
        json.dump(extract_bugfix_commits_exp3(), out)


if __name__ == "__main__":
    main()
