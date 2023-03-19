import requests
import random
import os
import re
import pandas as pd
import csv
import ast
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv(override=True)
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

headers = {
    "Authorization": f"token {GITHUB_API_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def find_repositories():
    url = "https://api.github.com/search/repositories"
    query = "language:python stars:>100"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 200}
    response = requests.get(url, headers=headers, params=params)
    return response.json()["items"]


def get_min_python_version(file_content):
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return None

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value,
                                                     ast.Call) and getattr(
                node.value.func, 'id', None) == 'setup':
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


def get_repo_files(repo):
    url = f"https://api.github.com/repos/{repo['full_name']}/contents"
    response = requests.get(url, headers=headers)
    files = response.json()
    return files


def get_repo_py_version(repo):
    files = get_repo_files(repo)

    setup_version = None
    for file in files:
        if file["name"] == "setup.py":
            file_content = requests.get(file["download_url"]).text
            setup_version = get_min_python_version(file_content)
            break
    return repo["name"], setup_version


def filter_python_files(repo, min_version="3.6.0"):
    repo_version = get_repo_py_version(repo)

    python_files = []
    files = get_repo_files(repo)
    if repo_version[1] and repo_version[1] > min_version:
        print("repository", repo_version[0], "has compatible version",
              repo_version[1])
        for file in files:
            if file["name"].endswith(".py"):
                if file["name"] == "setup.py":
                    break
                print("adding", file['name'], "to be scraped for snippets!")
                file["version"] = repo_version
                python_files.append(file)
        print()
    return python_files


def collect_data(repositories):
    data = []
    processed_repos = set()
    for r in repositories:
        if r["full_name"] in processed_repos:
            continue
        files = filter_python_files(r)
        if files:
            processed_repos.add(r["full_name"])
            data.append({"username": r["owner"]["login"], "repo_name": r["name"], "files": files})
            print({"username": r["owner"]["login"], "repo_name": r["name"], "files": files})
    return [d for d in data if d is not None]


def separate_contents(file_content):
    categories = {
        "Class": [],
        "Function": [],
    }

    # Regex patterns for each category
    class_pattern = r'\bclass\s+[A-Za-z_]\w*\b'
    function_pattern = r'\bdef\s+[A-Za-z_]\w*\b'

    # Split the file content into lines
    lines = file_content.splitlines()

    # Function to capture the body of a class or function
    def capture_body(start_line_idx, lines):
        body = lines[start_line_idx] + "\n"
        indent = re.match(r'^(\s*)', lines[start_line_idx]).group(1)
        for line in lines[start_line_idx + 1:]:
            if line.startswith(indent) and not re.match(r'^\s*$', line):
                body += line + "\n"
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


def select_and_store_snippets(data, max_snippets=None):
    snippets = []
    counter = defaultdict(int)

    snippet_count = 0
    for repo_data in data:
        repo_name = repo_data['repo_name']
        print(repo_name)
        for file_idx, file in enumerate(repo_data["files"]):
            file_name = file['name']
            file_content = requests.get(file["download_url"]).text
            categories = separate_contents(file_content)
            for cat, code_snippets in categories.items():
                if code_snippets:
                    for snippet in code_snippets:
                        uid_counter = str(counter[f'{repo_name}|{file_name}']).zfill(3)
                        uid = f"{repo_data['username']}|{repo_name}|{file_name}|{uid_counter}"
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
                            return snippets
    return snippets


def export_to_tsv(snippets):
    df = pd.DataFrame(snippets, columns=["UID", "Category", "Snippet"])
    df.to_csv("adjudicated.tsv", sep="\t", index=False)


def main():
    repositories = find_repositories()
    data = collect_data(repositories)
    snippets = select_and_store_snippets(data)
    export_to_tsv(snippets)
    # Convert .tsv to .txt
    # os.rename("adjudicated.tsv", "adjudicated.txt")


if __name__ == "__main__" :
    main()


# somethinng is wrong with how they're being added to the table