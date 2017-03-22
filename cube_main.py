import argparse

from cube_params import *
from cube_sql import *
from math import sqrt
import os
import time

db_conn = None;

def main():
    global db_conn
    try:
        # Run the various graph algorithm below
        db_conn = cube_db_initialize()
    except:
        print "Unexpected error:", sys.exc_info()[0]    
        raise 

if __name__ == '__main__':
    main()