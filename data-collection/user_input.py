import requests
import json


def get_user_input():
    min_stars = int(input("Enter the minimum number of stars you want to "
                          "consider: "))
    min_forks = int(input("Enter the minimum number of forks you want to "
                          "consider: "))
    return min_stars, min_forks


def save_data_to_file(data, filename):
    with open(filename, "w") as outfile:
        json.dump(data, outfile)


def load_data_from_file(filename):
    with open(filename, "r") as infile:
        data = json.load(infile)
    return data


def fetch_repositories(min_stars, min_forks, headers):
    url = "https://api.github.com/search/repositories"
    query = f"language:python stars:>={min_stars} forks:>={min_forks}"

    # Makes requests for REPOS_PER_PAGE * MAX_PAGES repositories
    repos_per_page = 100
    max_pages = 3
    all_items = []

    for page in range(1, max_pages + 1):
        params = {"q": query, "sort": "stars", "order": "desc",
                  "per_page": repos_per_page, "page": page}
        response = requests.get(url, headers=headers, params=params)
        items = response.json()["items"]
        all_items.extend(items)

    return all_items


def get_max_snippets():
    max_snippets = int(input("Enter the maximum number of snippets you want "
                             "to grab (in total): "))
    return max_snippets


def get_max_file_snippets():
    max_snippets = int(input("Enter the maximum number of snippets you want "
                             "to grab (from each file in a repo): "))
    return max_snippets


def get_max_files():
    max_files = int(input("Enter the maximum number of files you want to "
                          "consider to be parsed for snippets (or -1 for no "
                          "limit): "))
    return max_files


def get_max_repo_files():
    max_files = int(input("Enter the maximum number of files you want to "
                          "consider from each individual repo (or -1 for no "
                          "limit [not recommended]): "))
    return max_files
