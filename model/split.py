import random

input_file = "../data-collection/batches/AP2/adjudicated.tsv"
output_file = "shuffled.tsv"
header = None
data = []

# Read input file into a list of rows
with open(input_file, "r") as f:
    for line in f:
        parts = line.strip().split('\t')
        for i in range(len(parts)):
            if '<newline>' in parts[i]:
                parts[i] = parts[i].replace('<newline>', '\n')
        data.append(parts)

# Shuffle the rows
random.shuffle(data)

# Write shuffled data to output file
with open(output_file, "w") as f:
    for row in data:
        for i in range(len(row)):
            if '\n' in row[i]:
                row[i] = row[i].replace('\n', '<newline>')
        f.write('\t'.join(row) + "\n")

# Split shuffled file into three files
with open(output_file, "r") as f:
    lines = f.readlines()
    n = len(lines)
    n1 = 300
    n2 = 100
    n3 = n - n1 - n2
    dev = lines[:n1]
    test = lines[n1:n1+n2]
    train = lines[n1+n2:]
    with open("splits/dev.txt", "w") as f1, open("splits/test.txt", "w") as \
            f2, \
            open("splits/train.txt", "w") as f3:
        f1.writelines(dev)  # exclude last line
        f2.writelines(test)  # exclude last line
        f3.writelines(train)  # exclude last line

