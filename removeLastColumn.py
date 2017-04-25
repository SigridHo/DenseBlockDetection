import csv

def main(infile, outfile):
    mapping = {}
    out = csv.writer(open(outfile, 'w'))

    f = open(infile, 'r')
    lines = f.readlines()

    total_num_benign = 0
    total_num_attack = 0
    benignLabels = ["-", "normal."]

    for line in lines:
        line = line.strip().split(',')
        label = line[-1]
        key = tuple(line[:-1])

        if key in labels:
            # conflict labels - mark as type "conflict" and treat it as an attack type 
            if labels[key] != label:
                labels[key] = "conflict"
                total_num_attack += 1
            else:
                if labels[key] in benignLabels:
                    total_num_benign += 1
                else:
                    total_num_attack += 1
        else: 
            labels[key] = label
            if label in benignLabels:
                total_num_benign += 1
            else:
                total_num_attack += 1

    # print total_num_benign, total_num_attack, len(lines)
    return total_num_benign, total_num_attack


if __name__ == '__main__':
    main()