import csv
import sys

def main(infile, outfile):
    out = csv.writer(open(outfile, 'w'))

    f = open(infile, 'r')
    lines = f.readlines()

    for line in lines:
        line = line.strip().split(',')
        line.append('1')
        out.writerow(line)


if __name__ == '__main__':
	# sys.argv[1] is the original csv file for reading 
	# sys.argv[2] is the output modified csv file after removing the last column of 1
    main(sys.argv[1], sys.argv[2])