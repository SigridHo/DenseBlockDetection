import sys
import csv
from cube_params import *
from cube_sql import *
import matplotlib.pyplot as plt  

def readBlocks(block_index):
    num_benign = 0   # number of benign connection in the dense block
    num_attack = 0
    benignLabels = ["-", "normal."]

    table_name = BLOCK_TABLE + str(block_index)
    denseBlock = cube_sql_fetchRows(db_conn, table_name)

    for row in denseBlock:
        trueLabel = labels[row]
        if trueLabel in benignLabels:
            num_benign += 1
        else:
            num_attack += 1

    print "dense blocks #%d: benign=%d, attack=%d" % (block_index, num_benign, num_attack)
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


''' plot the ROC curve '''
def plotROC(X, Y, fileName):
    plt.figure(1)
    plt.title('ROC Curve - %s' % fileName)  
    plt.xlabel('False Positive Rate')  
    plt.ylabel('True Positive Rate')  
    # plt.axis([0.0, 0.1, 0.0, 0.1])
    # plt.xticks([i * 0.1 for i in range(0, 11)])
    # plt.yticks([i * 0.1 for i in range(0, 11)])
    plt.plot(X, Y, 'r')  
    plt.grid()  
    plt.show() 
    plt.savefig('./ROC_Curve_%s.pdf' % fileName)

def computeStat(num_benign, num_attack, total_num_benign, total_num_attack):
    falsePostive_rate = num_benign * 1.0 / total_num_benign
    truePositive_rate = num_attack * 1.0 / total_num_attack

    # print "num_blocks, fp_rate, tp_rate" 
    # print "%.12f, %.12f" % (falsePostive_rate, truePositive_rate)
    return falsePostive_rate, truePositive_rate

def main():
    global labels     # a dictionary to store the records and their label 
    labels = {} 
    file = sys.argv[1] 
    fileName = 'DARPA TCP Dump'
    maxNumBlocks = int(sys.argv[2])
    # read the true labels of each record from dataset
    total_num_benign, total_num_attack = readLabels(file)
    num_records_left = total_num_attack + total_num_benign
    try:
        ''' initialize the database connection '''
        global db_conn
        db_conn = cube_db_initialize()

        ''' interating through blocks to compute AUC '''
        accum_benign_inBlock = 0   # accumulated number of benign connections
        accum_attack_inBlock = 0
        falsePostive_rate = []
        truePositive_rate = []

        truePositive = []
        trueNegative = [] 
        Accuracy = []

        for i in range(maxNumBlocks):
            num_benign, num_attack = readBlocks(i)
            num_records_inBlock = num_benign + num_attack
            num_records_left -= num_records_inBlock

            accum_benign_inBlock += num_benign  # FP
            accum_attack_inBlock += num_attack  # TP

            falseNegative = total_num_attack - accum_attack_inBlock # FN
            truePositive.append(accum_attack_inBlock)
            trueNegative.append(num_records_left - falseNegative)   # TN

            fp, tp = computeStat(accum_benign_inBlock, accum_attack_inBlock, total_num_benign, total_num_attack)
            falsePostive_rate.append(fp)
            truePositive_rate.append(tp)

        print "falsePostive_rate: \n", falsePostive_rate
        print "truePositive_rate: \n", truePositive_rate
        plotROC(falsePostive_rate, truePositive_rate, fileName)

        # compute accuracy using linear interpolation 
        AUC = []
        for i in range(maxNumBlocks - 1):
            TP = truePositive[i] + truePositive[i + 1]
            TN = trueNegative[i] + trueNegative[i + 1]
            accuracy = (TP + TN) * 0.5 / (total_num_benign + total_num_attack)
            AUC.append(accuracy)
        X = [((2 * i + 1.0) / 2) for i in range(maxNumBlocks - 1)]
        plt.figure(1)
        plt.title('Accuracy - %s' % fileName)  
        plt.xlabel('Number of blocks (k)')  
        plt.ylabel('Accuracy')  
        plt.xticks([i for i in range(1, maxNumBlocks + 1)])
        plt.plot(X, AUC, 'r')  
        plt.grid()  
        # plt.show() 
        plt.savefig('./Acuuracy_%s.pdf' % fileName)

    except:
        print "Unexpected error:", sys.exc_info()[0]    
        raise 


if __name__ == '__main__':
    """
    console input format: 

    python cube_ROC.py dataset_with_labels number_of_dense_blocks 

    """
    main()

