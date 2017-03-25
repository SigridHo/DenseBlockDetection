import argparse

from cube_params import *
from cube_sql import *
import math
import os
import time

db_conn = None;

def find_single_block_test(db_conn, CUBE_TABLE, att_tables, dimension_num, m_r, density, att_names, col_fmts):
    block_tables = [None] * dimension_num
    # For algorithm 1 testing
    for n in range(dimension_num):
        block_tables[n] = 'B' + str(n)
        att_name = att_names[n]
        col_fmt = col_fmts[n]
        cube_sql_distinct_attribute_value(db_conn, block_tables[n], CUBE_TABLE, att_name, col_fmt)
    return block_tables

def measure_density(db_conn, m_b, block_tables, m_r, att_tables, args):
    method = args.density
    if method.startswith('a'):  # Arithmetic Average Mass
        sum_size = 0.0  # sum of |B_n|
        for block_table in block_tables:
            sum_size += cube_sql_mass(db_conn, block_table)
        sum_size /= args.dimension_num
        density = m_b / sum_size

    elif method.startswith('g'): # Geometric Average Mass
        product_size = 1.0  # product of |B_n|
        for block_table in block_tables:
            product_size *= cube_sql_mass(db_conn, block_table)
        product_size = pow(product_size, 1.0/args.dimension_num)
        density = m_b / product_size

    elif method.startswith('s'): # Suspicousness
        ratio = float(m_b) / m_r
        density = m_b * (math.log(ratio) - 1)
        product_ratio = 1.0   # product of |B_n| / |R_n|
        for n in range(args.dimension_num):
            b_size = cube_sql_mass(db_conn, block_tables[n])
            r_size = cube_sql_mass(db_conn, att_tables[n])
            product_ratio *= float(b_size) / r_size
        density += m_r * product_ratio
        density -= m_b * math.log(product_ratio)

    else:
        print 'Unknown density measurement.'
        return 0

    print 'Density of Block: ' + str(density)
    return density

def CUBE_not_empty(db_conn, block_tables):
    for block_table in block_tables:
        if cube_sql_mass(db_conn, block_table) > 0:
            return True
    return False

def table_not_empty(db_conn, dest_table):
	return cube_sql_mass(db_conn, dest_table) > 0

def select_dimension(db_conn, block_tables, metric = "cardinality"):
	if metric == "density":
		return select_dimension_by_density(db_conn, block_tables)
	else:
		return select_dimension_by_cardinality(db_conn, block_tables)

def select_dimension_by_density(db_conn, block_tables):

	return 1


def select_dimension_by_cardinality(db_conn, block_tables):
	dim = -1 		
	maxMass = -1
	for block_table in block_tables:
		currMass = cube_sql_mass(db_conn, block_table)
        if currMass > maxMass:
        	maxMass = currMass
        	dim = int(block_table[1:])
	return dim, maxMass


def compute_attribute_value_masses(db_conn, B_TABLE, block_tables, attVal_Masses_TABLE, att_names):
	for block_table in block_tables:
		dim = int(block_table[1:])   # fetch the dimension index 
		print "Dimension = %d, Attribute = %s" % (dim, att_names[dim])
		cube_sql_insert_attrVal_mass(db_conn, B_TABLE, block_table, attVal_Masses_TABLE, dim, att_names[dim])


def find_single_block(db_conn, CUBE_TABLE, att_tables, mass_r, att_names, col_fmts, args):

	# initialization of tables and attributes sets
    B_TABLE = "B_TABLE"
    cube_sql_copy_table(db_conn, B_TABLE, CUBE_TABLE)
    mass_b = mass_r
    block_tables = [None] * args.dimension_num
    for n in range(args.dimension_num):
        block_tables[n] = 'B' + str(n)
        cube_sql_copy_table(db_conn, block_tables[n], att_tables[n])
    density_tilde = measure_density(db_conn, mass_b, block_tables, mass_r, att_tables, args)
    r = 1
    r_tilde = 1

    # iteratation begins 
    while CUBE_not_empty(db_conn, block_tables):
        # compute all possible attribute_value masses
        print "\n# Calculating attribute-vale masses..."
        cols_description = "dimension_index integer, a_value text, attrVal_mass numeric"
        attVal_Masses_TABLE = "AttributeValue_Masses_TABLE"
        cube_sql_table_drop_create(db_conn, attVal_Masses_TABLE, cols_description)
        compute_attribute_value_masses(db_conn, B_TABLE, block_tables, attVal_Masses_TABLE, att_names)

        # select dimension with specified metric (default: by cardinality)
        print "\n# Selecting dimension..." 
        dim_i, mass_b_i = select_dimension(db_conn, block_tables, "cardinality")  # methods: density, cardinality(default)

        # find set which satisfies constraint to be removed 
        print "\n# Forming set to be removed (dim-%d)..." % dim_i
        threshold = mass_b * 1.0 / mass_b_i
        print "threshold = %f" % threshold
        D_CUBE_TABLE = "D_CUBE_TABLE"
        cube_select_values_to_remove(db_conn, D_CUBE_TABLE, attVal_Masses_TABLE, threshold, dim_i)
        D_CUBE_Static_TABLE = "D_CUBE_TABLE_static"   # duplicate a static copy for later operations
        cube_sql_copy_table(db_conn, D_CUBE_Static_TABLE, D_CUBE_TABLE)

        # iteratively delete rows of the specific dimsension and attribute value in Block
        print "\n# Iterating removal values..."
        cols_description = "a_value text, dimension_index integer, order_a_i integer"
        cube_sql_table_drop_create(db_conn, ORDER_TABLE, cols_description) 		# create order table

        while table_not_empty(db_conn, D_CUBE_TABLE):
        	a_value, attrVal_Mass = cube_sql_fetch_firstRow(db_conn, D_CUBE_TABLE)
        	conditions = ["a_value = '%s'" % a_value, "attrVal_Mass = %s" % attrVal_Mass]  # a list of conditions 
        	cube_sql_delete_rows(db_conn, D_CUBE_TABLE, conditions)
        	
        	# update block_i and mass_b
        	conditions = ["%s = '%s'" % (att_names[dim_i], a_value)]
        	cube_sql_delete_rows(db_conn, block_tables[dim_i], conditions)
        	mass_b -= long(attrVal_Mass)

        	# update order and density measure
        	density_prime = measure_density(db_conn, mass_b, block_tables, mass_r, att_tables, args)
        	newEntry = ["'%s'" % a_value, str(dim_i), str(r)]
        	cube_sql_insert_row(db_conn, ORDER_TABLE, newEntry)
        	r += 1
        	if density_prime > density_tilde:
        		density_tilde = density_prime
        		r_tilde = r

        # remove tuples from block (and update block_tables)
        print "\n# Removing tuples from block..."
        attrName = att_names[dim_i]
        cube_sql_update_block(db_conn, B_TABLE, D_CUBE_Static_TABLE, attrName)
    	block_tables = [None] * args.dimension_num
        for n in range(args.dimension_num):
        	block_tables[n] = 'B' + str(n)
        	att_name = att_names[n]
        	col_fmt = col_fmts[n]	
        	cube_sql_distinct_attribute_value(db_conn, block_tables[n], B_TABLE, att_name, col_fmt)

    # reconstruct target block
	print "\n# Reconstructing distinct value sets of block dimensions..."
    block_tables_ret = [None] * args.dimension_num
    for n in range(args.dimension_num):
		block_tables_ret[n] = 'B' + str(n)
		att_name = att_names[n]
		col_fmt = col_fmts[n]
		block_table_ret = block_tables_ret[n]
		att_table = att_tables[n]
		cube_sql_reconstruct_block(db_conn, block_table_ret, att_table, ORDER_TABLE, att_name, col_fmt, r_tilde, dim_i)


    # return block_tables
    return block_tables_ret

def main():
    global db_conn
    global CUBE_TABLE  # R
    global ORI_TABLE   # R_ori
    global BLOCK_TABLE # B_ori
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
        ''' initialize the database connection '''
        db_conn = cube_db_initialize()

        ''' initialize tables and copy original relations '''
        cols_description = "src_ip text, dest_ip text, time_stamp text"
        cube_sql_table_drop_create(db_conn, CUBE_TABLE, cols_description)
        cols_name = "src_ip, dest_ip, time_stamp"
        cube_sql_load_table_from_file(db_conn, CUBE_TABLE, cols_name, args.input_file, args.delimiter)

        cube_sql_copy_table(db_conn, ORI_TABLE, CUBE_TABLE)
        # cube_sql_print_table(db_conn, CUBE_TABLE)

        ''' create tables for N dimension attributes to store the distinct values '''
        att_tables = [None] * args.dimension_num    # R_n
        att_names = cols_name.split(", ")    
        col_fmts = cols_description.split(", ")   		# modified for better generalization
        for n in range(args.dimension_num):
            att_tables[n] = 'R' + str(n)
            att_name = att_names[n]
            col_fmt = col_fmts[n]
            cube_sql_distinct_attribute_value(db_conn, att_tables[n], CUBE_TABLE, att_name, col_fmt)
        # cube_sql_print_table(db_conn, "R1")

        ''' find single blocks and retrieve blocks from origianl data '''
        results = [None] * args.block_num
        for i in range(args.block_num):
            m_r = cube_sql_mass(db_conn, CUBE_TABLE)
            # print m_r
            block_tables = [None] * args.dimension_num # B_n

            block_tables = find_single_block(db_conn, CUBE_TABLE, att_tables, m_r, att_names, col_fmts, args)

            # cube_sql_delete_from_block(db_conn, CUBE_TABLE, block_tables, att_names, args.dimension_num)
            # results[i] = BLOCK_TABLE + str(i)
            # cube_sql_block_create_insert(db_conn, results[i], ORI_TABLE, block_tables, att_names, args.dimension_num, cols_description)
            # #m_r = cube_sql_mass(db_conn, results[i])
            # #print m_r

    except:
        print "Unexpected error:", sys.exc_info()[0]    
        raise 
    #return results

if __name__ == '__main__':
    main()