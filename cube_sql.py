# -*- coding: utf-8 -*-
import psycopg2
import sys
from cube_params import *

def cube_db_initialize():
    db_conn = psycopg2.connect("host='localhost' dbname=%s user=%s password=%s port=%d" % (CUBE_DB, CUBE_DB_USER, CUBE_DB_PASS, CUBE_DB_PORT))
    print "Connected To Database"
    return db_conn

# Drop and recreate table    
def cube_sql_table_drop_create(db_conn, table_name, create_sql_cols, drop=True):
    cur = db_conn.cursor()
    if (drop):
        try:
            cur.execute("DROP TABLE %s" % table_name)
        except psycopg2.Error:
            # Ignore the error
            db_conn.commit()
        
    cur.execute("CREATE TABLE %s (%s)" % (table_name, create_sql_cols))
    db_conn.commit()
    cur.close()

# Load table from file 
def cube_sql_load_table_from_file(db_conn, table_name, col_fmt, file_name, delim):
    cur = db_conn.cursor()
    cur.execute("COPY %s(%s) FROM '%s' DELIMITER AS '%s' CSV" % (table_name, col_fmt, file_name, delim))   
    db_conn.commit()
    cur.close()
    print "Loaded data from %s" % (file_name)

# Copy table completely
def cube_sql_copy_table(db_conn, dest_table, src_table):
    cur = db_conn.cursor()
    cur.execute("DROP TABLE %s" % dest_table)
    db_conn.commit()
    cur.execute("CREATE TABLE %s AS TABLE %s" % (dest_table, src_table))
    db_conn.commit()
    cur.close()
    print "Copied table %s to %s" % (src_table, dest_table)

def cube_sql_print_table(db_conn, table_name):
    cur = db_conn.cursor();
    cur.execute("SELECT * from %s" % table_name);
    for x in cur:
        print x
    cur.close();

def cube_sql_create_and_insert(db_conn, dest_table, src_table, col_fmt, insert_cols, select_cols):
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, dest_table, col_fmt)    
    cur.execute ("INSERT INTO %s(%s)" % (dest_table, insert_cols) + " SELECT %s FROM %s" % (select_cols,src_table))
    db_conn.commit()                            
    cur.close() 

def cube_sql_distinct_attribute_value(db_conn, dest_table, src_table, att_name, col_fmt):
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, dest_table, col_fmt)    
    cur.execute ("INSERT INTO %s(%s)" % (dest_table, att_name) + " SELECT DISTINCT ON (%s) %s FROM %s" % (att_name, att_name, src_table))
    db_conn.commit()                            
    cur.close() 