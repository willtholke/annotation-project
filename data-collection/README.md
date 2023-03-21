# Data Collection

This subdirectory contains the logic for collecting and formatting Python code snippets from popular GitHub repositories 
that contain Python projects.

## Scripts

### `adjudicated.py`

The main script to run is `adjudicated.py`, which makes GitHub API requests and cleans the data so that it only includes
repositories that have Python files with version 3.6.0 or greater (as determined by searching through the `setup.py` 
file for each repository). It takes in user input for the minimum number of stars and forks per repository, the maximum
number of files to consider across all repositories, the max number of files to consider in each repository, and the max number of snippets to be considered from each file.

The collected snippets are categorized as either a "Class" or a "Function" and are exported to a .tsv file named 'adjudicated.tsv' with the following format: 

- UID: unique identifier for each snippet 
- Category: class or function 
- Snippet: the code snippet

Cleaned data will be saved to `/cleaned-data` with a unique filename. Repository data for each API request is 
saved to `/raw-data`.

### `conversions.py`

With `conversions.py`, you can revert the .txt adjudicated data to .tsv. You can also revert the .tsv adjudicated data
to .txt, but this is more of a manual process. This is exceptionally useful if you want to edit the data in .tsv 
format and convert back to .txt.

## Acknowledgments

Although the program is intended to gather a significant amount of data of high quality, it is important to keep in 
mind that some misclassifications may still occur.

Note that the GitHub API has rate limits that restrict the number of requests that can be made within a certain time period.

## Usage

Make sure you have the required packages installed, which are handled by pipenv. To install the required packages, run the following command:

1. ```
   pipenv install
    ```

2. Before running `adjudicated.py`, create a classic GitHub personal access token with the "repo" scope.
Then, create a file named `.env` in the root directory with the following:
    ```
    GITHUB_API_TOKEN=your_access_token
    ```
