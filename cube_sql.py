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
def cube_sql_load_table_from_file(db_conn, table_name, col_fmt, file_name, delim, drop=True):
    cur = db_conn.cursor()
    cur.execute("COPY %s(%s) FROM '%s' DELIMITER AS '%s' CSV" % (table_name, col_fmt, file_name, delim))   
    db_conn.commit()
    cur.close()
    print "Loaded data from %s" % (file_name)

# Copy table completely
def cube_sql_copy_table(db_conn, dest_table, src_table, drop=True):
    cur = db_conn.cursor()
    if (drop):
        try:
            cur.execute("DROP TABLE %s" % dest_table)
        except psycopg2.Error:
            # Ignore the error
            db_conn.commit()
    cur.execute("CREATE TABLE %s AS TABLE %s" % (dest_table, src_table))
    db_conn.commit()
    cur.close()
    print "Copied table %s to %s" % (src_table, dest_table)

def cube_sql_print_table(db_conn, table_name):
    cur = db_conn.cursor();
    cur.execute("SELECT * from %s" % table_name);
    index = 1
    for x in cur:
        print x
        index += 1
        if index > 20:   # print the top lines to avoid exhausted table-printing 
            break 
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
    print "Get distinct attribute from table %s to %s" % (src_table, dest_table)

def cube_sql_mass(db_conn, table_name):
    cur = db_conn.cursor()
    cur.execute ("SELECT count(*) FROM %s" % table_name)
    mass = cur.fetchone()[0]
    db_conn.commit()                            
    cur.close() 
    # print "Mass of %s: " % table_name + str(mass)
    return mass

def cube_sql_delete_from_block(db_conn, table_name, block_tables, att_names, dimension_num):
    cur = db_conn.cursor()
    query = "DELETE FROM " + table_name + " USING "
    for i in range(dimension_num):
        if i != dimension_num - 1:
            query += block_tables[i] + ", "
        else:
            query += block_tables[i] + " WHERE "
    for i in range(dimension_num):
        if i != dimension_num - 1:
            query += table_name + "." + att_names[i] + " = " + block_tables[i] + "." + att_names[i] + " AND "
        else:
            query += table_name + "." + att_names[i] + " = " + block_tables[i] + "." + att_names[i]
    cur.execute(query)
    db_conn.commit()                            
    cur.close()
    print "Deleted from block." 

def cube_sql_block_create_insert(db_conn, block_table, cube_table, block_tables, att_names, dimension_num, cols_description):
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, block_table, cols_description)
    insert_cols = ", ".join(att_names)
    query = "INSERT INTO %s(%s)" % (block_table, insert_cols) + " SELECT "
    for i in range(dimension_num):
        if i != dimension_num - 1:
            query += cube_table + "." + att_names[i] + ", "
        else:
            query += cube_table + "." + att_names[i] + " FROM " + cube_table
    for i in range(dimension_num):
            query += ", " + block_tables[i]
    query += " WHERE "
    for i in range(dimension_num):
        if i != dimension_num - 1:
            query += cube_table + "." + att_names[i] + " = " + block_tables[i] + "." + att_names[i] + " AND "
        else:
            query += cube_table + "." + att_names[i] + " = " + block_tables[i] + "." + att_names[i]
    cur.execute(query)
    db_conn.commit()                            
    cur.close() 
    print "Created and inserted block table %s." % block_table


def cube_sql_insert_attrVal_mass(db_conn, B_TABLE, block_table, attVal_Masses_TABLE, dim, attrName):
    cur = db_conn.cursor()
    query = "INSERT INTO %s" % attVal_Masses_TABLE \
        + " SELECT %d, %s.%s, COUNT(*) AS attrVal_mass" % (dim, block_table, attrName) \
        + " FROM %s, %s WHERE %s.%s = %s.%s " % (block_table, B_TABLE, block_table, attrName, B_TABLE, attrName) \
        + " GROUP BY %s.%s" % (block_table, attrName)
    cur.execute(query)
    db_conn.commit()     
    cur.close() 
    print "Inserted AttrVal Masses of dimension-%d (%s) into %s." % (dim, attrName, attVal_Masses_TABLE)


def cube_select_values_to_remove(db_conn, D_CUBE_TABLE, attVal_Masses_TABLE, threshold, dim):
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, D_CUBE_TABLE, "a_value text, attrVal_mass numeric")
    query = "INSERT INTO %s SELECT a_value, attrVal_mass FROM %s" % (D_CUBE_TABLE, attVal_Masses_TABLE) \
        + " WHERE dimension_index = %d AND attrVal_mass <= %f ORDER BY attrVal_mass" % (dim, threshold)
    cur.execute(query)
    db_conn.commit()                         
    cur.close() 
    print "Created %s for dimension %d in increasing order of attrVal_mass." % (D_CUBE_TABLE, dim)


def cube_sql_fetch_firstRow(db_conn, dest_table):
    cur = db_conn.cursor()
    query = "SELECT a_value, attrVal_mass::text FROM %s LIMIT 1" % dest_table 
    cur.execute(query)
    (a_value, attrVal_mass) = cur.fetchone()  # fetch the corresponding a_value and attrVal mass
    db_conn.commit()                     
    cur.close() 
    # print "Fetched first row for %s." % dest_table
    return a_value, attrVal_mass


def cube_sql_delete_rows(db_conn, dest_table, conditions):
    cur = db_conn.cursor()
    conditions = " AND ".join(conditions)
    query = "DELETE FROM %s WHERE %s" % (dest_table, conditions)
    cur.execute(query)
    db_conn.commit()                       
    cur.close() 
    # print "Deleted rows given the conditions."

def cube_sql_insert_row(db_conn, dest_table, newEntry):
    cur = db_conn.cursor()
    newEntry = ", ".join(newEntry)
    query = "INSERT INTO %s VALUES (%s)" % (dest_table, newEntry) 
    cur.execute(query)
    db_conn.commit()                       
    cur.close() 
    # print "Inserted a row given the conditions."

def cube_sql_update_block(db_conn, B_table, D_table, attrName):
    cur = db_conn.cursor()
    query = "DELETE FROM %s USING %s" % (B_table, D_table) \
        + " WHERE %s.%s = %s.a_value" % (B_table, attrName, D_table)
    cur.execute(query)
    db_conn.commit()                            
    cur.close()
    print "Updated %s by removing tuples in %s." % (B_table, D_table)




