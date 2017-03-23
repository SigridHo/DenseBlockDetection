import argparse

from cube_params import *
from cube_sql import *
from math import sqrt
import os
import time

db_conn = None;

def main():
    global db_conn
    global CUBE_TABLE
    global ORI_TABLE
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
        # Run the various graph algorithm below
        db_conn = cube_db_initialize()
        cube_sql_table_drop_create(db_conn, CUBE_TABLE, "src_ip text, dest_ip text, time_stamp text")
        cols_name = "src_ip, dest_ip, time_stamp"
        cube_sql_load_table_from_file(db_conn, CUBE_TABLE, cols_name, args.input_file, args.delimiter)
        cube_sql_copy_table(db_conn, ORI_TABLE, CUBE_TABLE)
        att_tables = [None] * args.dimension_num
        att_names = ['src_ip', 'dest_ip', 'time_stamp']
        col_fmts = ['src_ip text', 'dest_ip text', 'time_stamp text']
        for n in range(args.dimension_num):
        	att_tables[n] = 'R' + str(n)
        	att_name = att_names[n]
        	col_fmt = col_fmts[n]
        	cube_sql_distinct_attribute_value(db_conn, att_tables[n], CUBE_TABLE, att_name, col_fmt)
        #cube_sql_print_table(db_conn, att_tables[2])
        results = [None] * args.block_num
        for i in range(args.block_num):
        	m_r = cube_sql_mass(db_conn, CUBE_TABLE)
        	print m_r

    except:
        print "Unexpected error:", sys.exc_info()[0]    
        raise 

if __name__ == '__main__':
    main()