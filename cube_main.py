import argparse

from cube_params import *
from cube_sql import *
import math
import os
import time

db_conn = None;

''' Marker Method: constraint'''
# marker_cons = "MARKER IS NULL"

def find_single_block_test(db_conn, RELATION_TABLE, relation_tables, dimension_num, m_r, density, att_names, col_fmts):
    block_tables = [None] * dimension_num
    # For algorithm 1 testing
    for n in range(dimension_num):
        block_tables[n] = 'B' + str(n)
        att_name = att_names[n]
        col_fmt = col_fmts[n]
        cube_sql_distinct_attribute_value(db_conn, block_tables[n], RELATION_TABLE, att_name, col_fmt)
    return block_tables

# 0422
def measure_density(m_b, Bn_mass, m_r, Rn_mass, args):
    method = args.density
    density = 0.0
    #print m_b
    if method.startswith('a'):  # Arithmetic Average Mass
        if m_b == 0:
            return 0.0
        sum_size = 0.0  # sum of |B_n|
        for inc in Bn_mass:
            # if inc == 0:
            #     return 0;
            sum_size += inc 
        if sum_size == 0:
            return -1
        density = m_b * 1.0 * args.dimension_num / sum_size 

    elif method.startswith('g'): # Geometric Average Mass
        product_size = 1.0  # product of |B_n|
        if m_b == 0:
             return 0.0
        for inc in Bn_mass:
            product_size *= inc
        if product_size == 0:
            return -1
        denominator = pow(product_size, 1.0 / args.dimension_num)
        density = m_b * 1.0 / denominator

    elif method.startswith('s'): # Suspicousness
        if m_b == 0:
            return -1
        density = m_b * (math.log(float(m_b) / m_r) - 1)
        product_ratio = 1.0   # product of |B_n| / |R_n|
        for n in range(args.dimension_num):
            b_size = Bn_mass[n]
            r_size = Rn_mass[n]
            product_ratio *= float(b_size) / r_size
        if product_ratio != 0:
            density += m_r * product_ratio - m_b * math.log(product_ratio)
        else:
            return -1

    else:
        print 'Unknown density measurement.'
        return 0.0

    # print 'Density of Block: ' + str(density)
    return density

def Block_not_empty(db_conn, block_table):
    if cube_sql_mass(db_conn, block_table) > 0:
        return True
    else:
        return False


def table_not_empty(db_conn, dest_table):
    return cube_sql_mass(db_conn, dest_table) > 0


def select_dimension(db_conn, block_tables, relation_tables, att_names, ATTVAL_MASSES_TABLE, mass_b, mass_r, Bn_mass, Rn_mass, args):
    if args.selection == "density":
        return select_dimension_by_density(db_conn, block_tables, relation_tables, att_names, ATTVAL_MASSES_TABLE, mass_b, mass_r, Bn_mass, Rn_mass, args)
    else:
        return select_dimension_by_cardinality(Bn_mass)

def select_dimension_by_density(db_conn, block_tables, relation_tables, att_names, ATTVAL_MASSES_TABLE, mass_b, mass_r, Bn_mass, Rn_mass, args):
    # parameter initialization 
    density_tilde = float('-inf')
    dim = 0
    maxMass = cube_sql_mass(db_conn, block_tables[0])
    d_cube_table = "d_cube_dimSelection"

    for i in range(args.dimension_num):
        mass_b_i = Bn_mass[i]
        if mass_b_i > 0:
            # find set which satisfies constraint to be removed 
            threshold = mass_b * 1.0 / mass_b_i
            #print mass_b
            #print mass_b_i
            #print 'threshold: ' + str(threshold)
            cube_select_values_to_remove(db_conn, d_cube_table, ATTVAL_MASSES_TABLE, threshold, i)

            # update mass, distinct value set and density
            delta = cube_sql_dCube_sum(db_conn, d_cube_table)
            mass_b_prime = mass_b - delta
            # print mass_b, mass_b_prime

            block_table_i_prime = "B%d_prime" % i
            cube_sql_copy_table(db_conn, block_table_i_prime, block_tables[i])
            cube_sql_update_block(db_conn, block_table_i_prime, d_cube_table, att_names[i])
            Bn_mass_union = [j for j in Bn_mass]  
            Bn_mass_union[i] = cube_sql_mass(db_conn, block_table_i_prime)
            density_prime = measure_density(float(mass_b_prime), Bn_mass_union, mass_r, Rn_mass, args)

            # update max density and corresponding dimension index 
            if density_prime > density_tilde:
                density_tilde = density_prime
                dim = i
                maxMass = mass_b_i

    # drop auxilary tables which are no longer needed to save disk space
    cube_sql_table_drop(db_conn, d_cube_table)

    return dim, maxMass


def select_dimension_by_cardinality(Bn_mass):
    # parameter initialization     
    dim = -1         
    maxMass = -1
    currDim = 0
    # find dimension with maximum mass
    for currMass in Bn_mass:
        if currMass >= maxMass:
            maxMass = currMass
            dim = currDim
        currDim += 1
    #print Bn_mass
    #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", dim, maxMass
    return dim, maxMass


def compute_attribute_value_masses(db_conn, B_TABLE, block_tables, ATTVAL_MASSES_TABLE, att_names):
    for block_table in block_tables:
        dim = int(block_table[1:])   # fetch the dimension index 
        # print "Dimension = %d, Attribute = %s" % (dim, att_names[dim])
        cube_sql_insert_attrVal_mass(db_conn, B_TABLE, block_table, ATTVAL_MASSES_TABLE, dim, att_names[dim])


def find_single_block(db_conn, RELATION_TABLE, relation_tables, mass_r, att_names, col_fmts, Rn_mass, args):

    # initialization of tables and attributes sets
    B_TABLE = "B_TABLE"

    ''' Marker Method: Copy With Marker'''
    # cube_sql_copy_table_marker(db_conn, B_TABLE, RELATION_TABLE, marker_cons)
    cube_sql_copy_table(db_conn,B_TABLE,RELATION_TABLE)
   
    mass_b = mass_r
    block_tables = [None] * args.dimension_num
    Bn_mass = [None] * args.dimension_num
    #Rn_mass = [None] * args.dimension_num
    
    for n in range(args.dimension_num):
        block_tables[n] = 'B' + str(n)
        cube_sql_copy_table(db_conn, block_tables[n], relation_tables[n])
        Bn_mass[n] = Rn_mass[n]
    
    density_tilde = measure_density(mass_b, Bn_mass, mass_r, Rn_mass, args)
    r = 1
    r_tilde = 1

    # initialize ORDER table 
    cols_description = "a_value text, dimension_index integer, order_a_i integer"
    cube_sql_table_drop_create(db_conn, ORDER_TABLE, cols_description)         # create order table

    while mass_b > 0:
        for n in range(args.dimension_num):
            block_tables[n] = 'B' + str(n)
            att_name = att_names[n]
            col_fmt = col_fmts[n]    
            cube_sql_distinct_attribute_value(db_conn, block_tables[n], B_TABLE, att_name, col_fmt)
            Bn_mass[n] = cube_sql_mass(db_conn, block_tables[n])
        # compute all possible attribute_value masses
        print "\n# Calculating attribute-vale masses..."
        cols_description = "dimension_index integer, a_value text, attrVal_mass numeric"
        cube_sql_table_drop_create(db_conn, ATTVAL_MASSES_TABLE, cols_description)
        compute_attribute_value_masses(db_conn, B_TABLE, block_tables, ATTVAL_MASSES_TABLE, att_names)
        # cube_sql_print_table(db_conn, ATTVAL_MASSES_TABLE)

        # select dimension with specified metric (default: by cardinality)
        print "\n# Selecting dimension..." 
        # metric methods: density, cardinality(default)
        dim_i, mass_b_i = select_dimension(db_conn, block_tables, relation_tables, att_names, ATTVAL_MASSES_TABLE, mass_b, mass_r, Bn_mass, Rn_mass, args)  

        # find set which satisfies constraint to be removed 
        print "\n# Forming set to be removed (dim-%d)..." % dim_i
        threshold = mass_b * 1.0 / mass_b_i
        # print "threshold = %f" % threshold
        cube_select_values_to_remove(db_conn, D_CUBE_TABLE, ATTVAL_MASSES_TABLE, threshold, dim_i)
        cube_sql_copy_table(db_conn, D_CUBE_STATIC_TABLE, D_CUBE_TABLE)

        # iteratively delete rows of the specific dimsension and attribute value in Block
        print "\n# Iterating removal values..."
        #cube_sql_print_table(db_conn, D_CUBE_TABLE)
        while table_not_empty(db_conn, D_CUBE_TABLE):
            a_value, attrVal_Mass = cube_sql_fetch_firstRow(db_conn, D_CUBE_TABLE)
            conditions = ["a_value = '%s'" % a_value, "attrVal_Mass = %s" % attrVal_Mass]  # a list of conditions 
            cube_sql_delete_rows(db_conn, D_CUBE_TABLE, conditions)
            
            # update block_i and mass_b
            conditions = ["%s = '%s'" % (att_names[dim_i], a_value)]
            cube_sql_delete_rows(db_conn, block_tables[dim_i], conditions)
            mass_b -= long(attrVal_Mass)
            #print 'mass_B: ' + str(mass_b)
            Bn_mass[dim_i] -= 1

            # update order and density measure
            density_prime = measure_density(mass_b, Bn_mass, mass_r, Rn_mass, args)
            newEntry = ["'%s'" % a_value, str(dim_i), str(r)]
            cube_sql_insert_row(db_conn, ORDER_TABLE, newEntry)
            r += 1
            if density_prime > density_tilde:
                density_tilde = density_prime
                r_tilde = r

        # remove tuples from block (and update block_tables)
        print "\n# Removing tuples from block..."
        attrName = att_names[dim_i]
        cube_sql_update_block(db_conn, B_TABLE, D_CUBE_STATIC_TABLE, attrName)
        mass_b = cube_sql_mass(db_conn, B_TABLE)
        #cube_sql_print_table(db_conn, B_TABLE)
        
        ##############################################
        # Move the B_n update to the beginning of the loop

    # reconstruct target block
    print "\n# Reconstructing distinct value sets of block dimensions..."
    block_tables_ret = [None] * args.dimension_num
    # print r_tilde, density_tilde
    # cube_sql_print_table(db_conn, ORDER_TABLE)

    for n in range(args.dimension_num):
        block_tables_ret[n] = 'B' + str(n)
        att_name = att_names[n]
        col_fmt = col_fmts[n]
        block_table_ret = block_tables_ret[n]
        relation_table = relation_tables[n]
        ##############################################
        # reconstsruction is modified in sql file
        cube_sql_reconstruct_block(db_conn, block_table_ret, relation_table, ORDER_TABLE, att_name, col_fmt, r_tilde, n)
        #print block_table_ret
        #cube_sql_print_table(db_conn, block_table_ret)


    # drop auxilary tables which are no longer needed to save disk space
    # cube_sql_table_drop(db_conn, ATTVAL_MASSES_TABLE)
    # cube_sql_table_drop(db_conn, D_CUBE_TABLE)   
    # cube_sql_table_drop(db_conn, D_CUBE_STATIC_TABLE)   
    # cube_sql_table_drop(db_conn, ORDER_TABLE)   

    return block_tables_ret     # return block_tables

def main():
    global db_conn
    global RELATION_TABLE  # R
    global ORI_TABLE   # R_ori
    global BLOCK_TABLE # B_ori
    global D_CUBE_TABLE
    global REPORT_TABLE
    global ATTVAL_MASSES_TABLE
    # Command Line processing
    parser = argparse.ArgumentParser(description="Dense Block Detection")
    parser.add_argument ('--file', dest='input_file', type=str, required=True,
                         help='Full path to the file to load from.')
    parser.add_argument ('--delim', dest='delimiter', type=str, default=',',
                         help='Delimiter that separate the columns in the input file. default ","')
    parser.add_argument ('--N', dest='dimension_num', type=int, required=True, 
                         help='number of dimension attributes.')
    parser.add_argument ('--k', dest='block_num', type=int, required=True,
                         help='number of dense blocks we aim to find.')
    parser.add_argument ('--density', dest='density', type=str, default='arithmetic',
                         help='density measure. Support arithmetic, geometric, suspiciousness.')
    parser.add_argument ('--selection', dest='selection', type=str, default='density',
                         help='dimension selection policy.Support density, cardinality.')
    args = parser.parse_args()
    try:
        # overall timer
        overall_start = time.time() 

        ''' initialize the database connection '''
        db_conn = cube_db_initialize()

        # table to store block statistics for report (density, elapsed time 
        report_description = "block_index integer, density float, entryCount integer, elapsed_time numeric" 
        cube_sql_table_drop_create(db_conn, REPORT_TABLE, report_description)

        ''' initialize tables and copy original relations '''
        cols_description = ""
        cols_name = ""
        for i in range(args.dimension_num):
            cols_description += "A" + str(i) + " text, "
            cols_name += "A" + str(i) + ", "
        cols_description = cols_description[:-2]
        cols_name = cols_name[:-2]
        #cols_description = "src_ip text, dest_ip text, time_stamp text"
        #cols_name = "src_ip, dest_ip, time_stamp"

        cube_sql_table_drop_create(db_conn, RELATION_TABLE, cols_description)
        cube_sql_load_table_from_file(db_conn, RELATION_TABLE, cols_name, args.input_file, args.delimiter)

        # RAW_RELATION_TABLE = "RAW_RELATION_TABLE"
        # cube_sql_table_drop_create(db_conn, RAW_RELATION_TABLE, cols_description)
        # cube_sql_load_table_from_file(db_conn, RAW_RELATION_TABLE, cols_name, args.input_file, args.delimiter)
        # cube_sql_distinct_entries(db_conn, RAW_RELATION_TABLE, RELATION_TABLE)
        
        #cube_sql_bucketize(db_conn, RELATION_TABLE)
        #cube_sql_print_table(db_conn, RELATION_TABLE)

        cube_sql_copy_table(db_conn, ORI_TABLE, RELATION_TABLE)

        ''' Marker Method: Add Marker column''' 
        # marker_description = "MARKER text"
        # cube_sql_add_column(db_conn, RELATION_TABLE, marker_description)
        
        mass_ori = cube_sql_mass(db_conn, ORI_TABLE)
        ori_tables = [None] * args.dimension_num
        # cube_sql_print_table(db_conn, RELATION_TABLE)

        ''' create tables for N dimension attributes to store the distinct values '''
        relation_tables = [None] * args.dimension_num    # R_n
        Rn_mass = [None] * args.dimension_num
        ORIn_mass = [None] * args.dimension_num
        att_names = cols_name.split(", ")  
        col_fmts = cols_description.split(", ")           # modified for better generalization
        for n in range(args.dimension_num):
            relation_tables[n] = 'R' + str(n)
            ori_tables[n] = 'ORI' + str(n)
            att_name = att_names[n]
            col_fmt = col_fmts[n]
            cube_sql_distinct_attribute_value(db_conn, relation_tables[n], RELATION_TABLE, att_name, col_fmt)
            cube_sql_copy_table(db_conn, ori_tables[n], relation_tables[n])
            Rn_mass[n] = cube_sql_mass(db_conn, relation_tables[n])
            ORIn_mass[n] = Rn_mass[n]

        ''' find single blocks and retrieve blocks from origianl data '''
        results = [None] * args.block_num
        for i in range(args.block_num):
            # timer for each block detection 
            block_start = time.time() 

            # 0422
            if i == 0:
                m_r = mass_ori
            else:
                ''' Marker Method'''
                # m_r = cube_sql_mass_marker(db_conn, RELATION_TABLE, marker_cons)
                m_r = cube_sql_mass(db_conn, RELATION_TABLE)
            
            block_tables = [None] * args.dimension_num # B_n
            block_tables = find_single_block(db_conn, RELATION_TABLE, relation_tables, m_r, att_names, col_fmts, Rn_mass, args)        

            #cube_sql_delete_from_block(db_conn, RELATION_TABLE, block_tables, att_names, args.dimension_num)
            
            ''' Marker Method: update marker'''
            # setting = "MARKER = '1' "
            # cube_sql_update_marker(db_conn, RELATION_TABLE, block_tables, att_names, args.dimension_num, setting)
            cube_sql_delete_from_block(db_conn, RELATION_TABLE, block_tables, att_names, args.dimension_num)
            
            for n in range(args.dimension_num):
                relation_tables[n] = 'R' + str(n)
                att_name = att_names[n]
                col_fmt = col_fmts[n]

                ''' Marker Method: get attribute'''
                # cube_sql_distinct_attribute_value_marker(db_conn, relation_tables[n], RELATION_TABLE, att_name, col_fmt, marker_cons)
                cube_sql_distinct_attribute_value(db_conn, relation_tables[n], RELATION_TABLE, att_name, col_fmt)
                Rn_mass[n] = cube_sql_mass(db_conn, relation_tables[n])


            results[i] = BLOCK_TABLE + str(i)
            cube_sql_block_create_insert(db_conn, results[i], ORI_TABLE, block_tables, att_names, args.dimension_num, cols_description)
            #cube_sql_print_table(db_conn, results[i])
            # print cube_sql_mass(db_conn, results[i])

            result_mass_b = cube_sql_mass(db_conn, results[i])
            result_block_tables = [None] * args.dimension_num
            resultn_mass = [None] * args.dimension_num
            for n in range(args.dimension_num):
                result_block_tables[n] = 'RESULT_B' + str(n)
                att_name = att_names[n]
                col_fmt = col_fmts[n]
                cube_sql_distinct_attribute_value(db_conn, result_block_tables[n], results[i], att_name, col_fmt)
                resultn_mass[n] = cube_sql_mass(db_conn, result_block_tables[n])
                #print cube_sql_mass(db_conn, result_block_tables[n])
            result_density = measure_density(result_mass_b, resultn_mass, mass_ori, ORIn_mass, args)
            #print 'Result: '
            #print 'Density: ' + str(result_density)

            # add block statistcs into table
            block_end = time.time()
            block_elapsed_time = block_end - block_start
            print "Block Elapsed Time: %fs" % block_elapsed_time
            newEntry = [str(i), str(result_density), str(result_mass_b), str(block_elapsed_time)]
            cube_sql_insert_row(db_conn, REPORT_TABLE, newEntry)
            cube_sql_print_table(db_conn, REPORT_TABLE)

        # overall timer
        overall_end = time.time()
        print "Total Elapsed Time: %fs" % (overall_end - overall_start) 

    except:
        print "Unexpected error:", sys.exc_info()[0]    
        raise 
    #return results

if __name__ == '__main__':
    main()