import csv
import pandas as pd
import os


def create_simple_tsv(df, output_tsv_file):
    # Create simplified TSV file
    df_simplified = df["Snippet"]
    df_simplified = df_simplified.to_frame()
    df_simplified.insert(0, "ID", range(len(df_simplified)))
    df_simplified.insert(1, "Adjudicated", "adjudicated")
    df_simplified.insert(2, "Label", "label-na")
    df_simplified.to_csv(output_tsv_file, sep="\t", index=False, header=False)
    return df_simplified


def revert_txt_to_tsv(input_txt_file):
    # Read the txt file
    with open(input_txt_file, "r", newline="", encoding="utf-8") as txt_file:
        tsv_reader = csv.reader(txt_file, delimiter="\t")
        data = [row for row in tsv_reader]

    # Replace <newline> with actual newline characters within code snippets
    for row in data:
        row[-1] = row[-1].replace("<newline>", "\n")

    # Convert the data back to a DataFrame
    df_reverted = pd.DataFrame(data, columns=["ID", "Adjudicated", "Label", "Snippet"])

    # Generate output file name by adding "reverted" before the file extension
    output_tsv_file = os.path.splitext(input_txt_file)[0] + "-reverted.tsv"

    # Save the DataFrame as a TSV file
    df_reverted.to_csv(output_tsv_file, sep="\t", index=False, header=False)

    # Print confirmation message
    print(f"Reverted {input_txt_file} back to its original TSV format as {output_tsv_file}")


def main():
    input_txt_file = input("Please enter the file name with its path (e.g., "
                           "cleaned-data/"
                           "adjudicated-xxxx.txt): ")
    revert_txt_to_tsv(input_txt_file)


if __name__ == "__main__":
    main()
