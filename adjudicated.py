import ast
import os
import re
from collections import defaultdict
import random

import pandas as pd
import requests
from dotenv import load_dotenv

from user_input import get_user_input, save_data_to_file, \
    load_data_from_file, fetch_repositories, get_max_snippets, \
    get_max_files, get_max_repo_files, get_max_file_snippets

load_dotenv(override=True)
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

headers = {
    "Authorization": f"token {GITHUB_API_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def find_repositories():
    min_stars, min_forks = get_user_input()

    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    data_filename = os.path.join(data_dir,
                                 f"repos_min_stars_{min_stars}_min_forks_"
                                 f"{min_forks}.txt")

    if os.path.exists(data_filename):
        print(
            f"Data file for minimum stars {min_stars} and minimum forks "
            f"{min_forks} already exists.")
        use_existing_data = input(
            "Do you want to use the stored data? (yes/no): ").lower()

        if use_existing_data == 'yes':
            all_items = load_data_from_file(data_filename)
        else:
            print("Making new API request...")
            all_items = fetch_repositories(min_stars, min_forks,
                                           headers=headers)
            save_data_to_file(all_items, data_filename)
    else:
        all_items = fetch_repositories(min_stars, min_forks, headers=headers)
        save_data_to_file(all_items, data_filename)

    repo_count = len(all_items)
    avg_stars = sum(item["stargazers_count"] for item in all_items) / repo_count
    avg_forks = sum(item["forks_count"] for item in all_items) / repo_count

    print(f"Found {repo_count} repositories!")
    print(f"Average stars: {avg_stars:.2f}")
    print(f"Average forks: {avg_forks:.2f}\n")

    return all_items


def get_min_python_version(file_content):
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return None

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and \
                getattr(node.value.func, 'id', None) == 'setup':
            for keyword in node.value.keywords:
                if keyword.arg == 'python_requires':
                    if isinstance(keyword.value, ast.Str):
                        version_string = keyword.value.s
                        version_match = re.search(r">=\s*([0-9.]+)",
                                                  version_string)
                        if version_match:
                            return version_match.group(1)
                    break
            break
    return None


def get_repo_files(repo, max_files_per_repo, path="", current_count=0):
    url = f"https://api.github.com/repos/{repo['full_name']}/contents/{path}"
    response = requests.get(url, headers=headers)
    files = response.json()
    python_files = []

    # In case of a rate limit error or another issue
    if not isinstance(files, list):
        return []

    # Look for setup.py in the root directory
    for file in files:
        if file["type"] == "file" and file["name"] == "setup.py":
            python_files.append(file)
            print(f"Found {repo['name']}/setup.py in the root directory")
            break

    # Otherwise, continue searching for .py files recursively
    for file in files:
        if 0 < max_files_per_repo <= current_count + len(python_files):
            break
        if file["type"] == "file" and file["name"].endswith(".py"):
            python_files.append(file)
        elif file["type"] == "dir":
            python_files.extend(
                get_repo_files(repo, max_files_per_repo, file["path"],
                               current_count + len(python_files)))

    return python_files


def get_repo_py_version(repo, files):
    setup_version = None
    for file in files:
        if file["name"] == "setup.py":
            file_content = requests.get(file["download_url"]).text
            setup_version = get_min_python_version(file_content)
            break

    return repo["name"], setup_version


def filter_python_files(repo, max_files_per_repo, min_version="3.6.0"):
    python_files = []
    files = get_repo_files(repo, max_files_per_repo)  # works
    repo_version = get_repo_py_version(repo, files)
    considered_repo = False
    if repo_version[1] and repo_version[1] > min_version:
        considered_repo = True

        for file in files:
            if file["name"].endswith(".py"):
                print(f"Adding "
                      f"{repo_version[0]}/{file['name']} to be scraped for "
                      f"snippets!")
                file["version"] = repo_version
                python_files.append(file)
        if not python_files:
            considered_repo = False
            print(
                f"No compatible files found in repository "
                f"'{repo_version[0]}' other than setup.py\n")

    return python_files, considered_repo


def collect_data(repositories):
    max_files, max_files_per_repo = get_max_files(), get_max_repo_files()
    data, processed_repos = [], set()
    files_count, considered_repos_count = 0, 0

    for r in repositories:
        if r["full_name"] in processed_repos:
            continue
        files, considered_repo = filter_python_files(r, max_files_per_repo)
        if files:
            processed_repos.add(r["full_name"])
            data.append(
                {"username": r["owner"]["login"], "repo_name": r["name"],
                 "files": files})
            files_count += len(files)

            if 0 < max_files <= files_count:
                print(
                    f"Successfully collected {max_files} "
                    f"files to be scraped for snippets!")
                break
        if considered_repo:
            considered_repos_count += 1
        if files and considered_repo:
            print([f"Adding {r['name']}/{file['name']} for consideration"
                   for file in files])
            print(f"Total repositories considered: {considered_repos_count}")
            print(f"Total files considered: {files_count}\n")
        else:
            print(
                f"Repository '{r['name']}' "
                f"was not considered due to no compatible files or version\n")

    return [d for d in data if d is not None]


def separate_contents(file_content):
    categories = {
        "Class": [],
        "Function": [],
    }

    class_pattern = r'\bclass\s+[A-Za-z_]\w*\b'
    function_pattern = r'\bdef\s+[A-Za-z_]\w*\b'
    lines = file_content.splitlines()

    def capture_body(start_line_idx, capture_lines):
        """ Capture the body of a class/function. """
        body = capture_lines[start_line_idx] + "\n"
        indent = re.match(r'^(\s*)', capture_lines[start_line_idx]).group(1)
        for lin in capture_lines[start_line_idx + 1:]:
            if line.startswith(indent) and not re.match(r'^\s*$', lin):
                body += lin + "\n"
            else:
                break
        return body

    # Locate classes and functions
    for i, line in enumerate(lines):
        class_match = re.search(class_pattern, line)
        function_match = re.search(function_pattern, line)

        if class_match:
            categories["Class"].append(capture_body(i, lines))
        elif function_match:
            categories["Function"].append(capture_body(i, lines))

    return categories


def select_and_store_snippets(data):
    snippets, snippet_count = [], 0
    counter = defaultdict(int)
    max_snippets = get_max_snippets()
    max_snippets_per_file = get_max_file_snippets()

    random.shuffle(data)
    # Get all the snippets, shuffle them, then select num max_snippets_per_file
    for repo_data in data:
        repo_name = repo_data['repo_name']
        for file_idx, file in enumerate(repo_data["files"]):
            file_name = file['name']
            file_content = requests.get(file["download_url"]).text
            categories = separate_contents(file_content)
            for cat, code_snippets in categories.items():
                if code_snippets:
                    for snippet in code_snippets:
                        uid_counter = str(
                            counter[f'{repo_name}|{file_name}']).zfill(3)
                        uid = f"{repo_data['username']}|{repo_name}|" \
                              f"{file_name}|{uid_counter}"
                        counter[f'{repo_name}|{file_name}'] += 1
                        snippets.append({
                            "UID": uid,
                            "Category": cat,
                            "Snippet": snippet
                        })
                        snippet_count += 1
                        print("Added a snippet! Total snippet count:",
                              snippet_count)
                        if max_snippets and snippet_count >= max_snippets:
                            random.shuffle(snippets)
                            # FIXME // TODO: After shuffling the snippets,
                            # then assign the UIDs
                            return snippets[:max_snippets_per_file-1]
    return snippets


def export_to_tsv(snippets):
    df = pd.DataFrame(snippets, columns=["UID", "Category", "Snippet"])
    df.to_csv("adjudicated.tsv", sep="\t", index=False)


def main():
    repositories = find_repositories()
    data = collect_data(repositories)
    snippets = select_and_store_snippets(data)
    export_to_tsv(snippets)

    # TODO: Finalize conversion of .tsv to .txt
    # os.rename("adjudicated.tsv", "adjudicated.txt")


if __name__ == "__main__":
    main()
