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
    # Command Line processing
    parser = argparse.ArgumentParser(description="Dense Block Detection")
    parser.add_argument ('--file', dest='input_file', type=str, required=True,
                         help='Full path to the file to load from.')
    parser.add_argument ('--delim', dest='delimiter', type=str, default=',',
                         help='Delimiter that separate the columns in the input file. default ","')
    args = parser.parse_args()
    try:
        # Run the various graph algorithm below
        db_conn = cube_db_initialize()
        cube_sql_table_drop_create(db_conn, CUBE_TABLE, "src_ip text, dst_ip text, time_stamp text")
        col_fmt = "src_ip, dst_ip, time_stamp"
        cube_sql_load_table_from_file(db_conn, CUBE_TABLE, col_fmt, args.input_file, args.delimiter)
        
    except:
        print "Unexpected error:", sys.exc_info()[0]    
        raise 

if __name__ == '__main__':
    main()