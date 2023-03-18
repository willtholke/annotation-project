import requests
import random
import os
import re
from dotenv import load_dotenv
from collections import defaultdict
from uuid import uuid4

load_dotenv(override=True)
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

headers = {
    "Authorization": f"token {GITHUB_API_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def find_repositories():
    url = "https://api.github.com/search/repositories"
    query = "language:python stars:>1000"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 100}
    response = requests.get(url, headers=headers, params=params)
    return response.json()["items"]


def categorize_repositories(repositories):
    category_count = defaultdict(int)
    categorized_repos = defaultdict(list)

    for repo in repositories:
        for topic in repo["topics"]:
            category_count[topic] += 1
            categorized_repos[topic].append(repo)

    top_categories = sorted(category_count, key=category_count.get, reverse=True)[:10]
    return {cat: categorized_repos[cat] for cat in top_categories}


def filter_python_files(repo, min_version="3.6.0"):
    url = f"https://api.github.com/repos/{repo['full_name']}/contents"
    response = requests.get(url, headers=headers)
    files = response.json()
    python_files = []
    for file in files:
        if file["name"].endswith(".py"):
            file_content = requests.get(file["download_url"]).text
            version_match = re.search(r"python_requires\s*=\s*[\"']>=\s*("
                                      r"\d+\.\d+\.\d+)", file_content)
            if version_match and version_match.group(1) >= min_version:
                file["version"] = version_match.group(1)
                python_files.append(file)
    # only return the
    return python_files


def collect_data(categorized_repositories):
    data = []
    counter = 1
    for category, repos in categorized_repositories.items():
        for r in repos:
            files = filter_python_files(r)
            if files:
                data.append({"username": r["owner"]["login"], "repo_name": r[
                    "name"], "files": files})
            counter += 1
            # FIXME: remove the counter; it's just here for dev
            if counter == 10: break
        return data
    return data


def separate_contents(file_content):
    categories = {
        "ENUM": [],
        "Class and Class Definition": [],
        "Function and Function Definition": [],
        "Global Variable": [],
    }
    # Add your regex patterns and extraction logic here for each category
    return categories


def select_and_store_snippets(data):
    snippets = []
    random.shuffle(data)

    while len(snippets) < 625:
        for repo_data in data:
            for file in repo_data["files"]:
                file_content = requests.get(file["download_url"]).text
                categories = separate_contents(file_content)
                for cat, code_snippets in categories.items():
                    if code_snippets:
                        selected_snippet = random.choice(code_snippets)
                        snippets.append({
                            "UID": f"{repo_data['username']}_{repo_data['repo_name']}_{file['name']}_{cat}_{str(uuid4())}",
                            "Python Snippet": selected_snippet,
                        })
                        if len(snippets) >= 625:
                            break
    return snippets


def export_to_tsv(snippets):
    with open("adjudicated.tsv", "w") as f:
        f.write("UID\tPython Snippet\n")
        for snippet in snippets:
            f.write(f"{snippet['UID']}\t{snippet['Python Snippet']}\n")


def main():
    repositories = find_repositories()
    categorized_repositories = categorize_repositories(repositories)
    data = collect_data(categorized_repositories)
    print(data)
    # snippets = select_and_store_snippets(data)
    # export_to_tsv(snippets)
    #
    # # Convert .tsv to .txt
    # os.rename("adjudicated.tsv", "adjudicated.txt")


if __name__ == "__main__" :
    main()

