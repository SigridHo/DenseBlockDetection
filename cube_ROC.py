import sys
import csv
from cube_params import *
from cube_sql import *
import math
import time

def readBlocks(numBlocks):
    print "Reading detected dense blocks from database..."
    num_benign = 0   # number of benign connection in the dense block
    num_attack = 0
    benignLabels = ["-", "normal."]

    for i in range(numBlocks):
        table_name = BLOCK_TABLE + str(i)
        denseBlock = cube_sql_fetchRows(db_conn, table_name)

        for row in denseBlock:
            print row
            trueLabel = labels[row]
            # print trueLabel
            if trueLabel in benignLabels:
                num_benign += 1
            else:
                num_attack += 1

    return num_benign, num_attack

def readLabels(file):
    print "Loading labels..."
    f = open(file, 'r')
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



# def plotROC():
#     # plot the ROC curve 


def computeStat(num_benign, num_attack, total_num_benign, total_num_attack):
    falsePostive_rate = num_benign * 1.0 / total_num_benign
    truePositive_rate = num_attack * 1.0 / total_num_attack

    print "num_blocks, fp_rate, tp_rate" 
    print "%s, %.12f, %.12f" % (sys.argv[2], falsePostive_rate, truePositive_rate)
    

def main():
    global labels     # a dictionary to store the records and their label 
    labels = {} 
    file = sys.argv[1] 
    numBlocks = int(sys.argv[2])
    # read the true labels of each record from dataset
    total_num_benign, total_num_attack = readLabels(file)  
    try:
        ''' initialize the database connection '''
        global db_conn
        db_conn = cube_db_initialize()
        num_benign, num_attack = readBlocks(numBlocks)
        computeStat(num_benign, num_attack, total_num_benign, total_num_attack)
        # plotROC(num_benign, num_attack)

    except:
        print "Unexpected error:", sys.exc_info()[0]    
        raise 


if __name__ == '__main__':
    """
    console input format: 

    python cube_ROC.py dataset_with_labels number_of_dense_blocks 

    """
    main()
