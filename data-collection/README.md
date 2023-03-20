# Data Collection README

## Features

- Search for repositories with a minimum number of stars and forks
- Filter repositories based on the minimum Python version required
- Scrape Python files for code snippets (classes and functions)
- Export the collected snippets to a TSV file

## Usage

1. Set up your GitHub API token by creating a `.env` file in the root of the project directory and adding the following line:

```
GITHUB_API_TOKEN=your_token_here
```

