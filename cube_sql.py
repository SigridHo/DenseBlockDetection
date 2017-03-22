# -*- coding: utf-8 -*-
import psycopg2
import sys
from cube_params import *

def cube_db_initialize():
    db_conn = psycopg2.connect("host='localhost' dbname=%s user=%s password=%s port=%d" % (CUBE_DB, CUBE_DB_USER, CUBE_DB_PASS, CUBE_DB_PORT))
    print "Connected To Database"
    return db_conn