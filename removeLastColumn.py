import csv
import sys

def main(infile, outfile):
    out = csv.writer(open(outfile, 'w'))

    f = open(infile, 'r')
    lines = f.readlines()

    for line in lines:
        line = line.strip().split(',')
        line = line[:-1]
        out.writerow(line)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])