import csv
import sys

def main(infile, outfile, N):
    out = csv.writer(open(outfile, 'w'))

    f = open(infile, 'r')
    lines = f.readlines()
    N = int(N)
    dicArray = [{} for k in range(N)]
    countArray = [0 for k in range(N)]
    for line in lines:
        line = line.strip().split(',')
        for i in range(N):
            if line[i] in dicArray[i]:
                line[i] = dicArray[i][line[i]]
            else:
                dicArray[i][line[i]] = str(countArray[i])
                line[i] = str(countArray[i])
                countArray[i] += 1
        out.writerow(line)


if __name__ == '__main__':
    # sys.argv[1] is the original csv file for reading 
    # sys.argv[2] is the output modified csv file after removing the last column of 1
    main(sys.argv[1], sys.argv[2], sys.argv[3])