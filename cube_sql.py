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
    print "Mass: " + str(mass)
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

def cube_select_values_to_remove(db_conn, valueToDel_TABLE, attVal_Masses_TABLE, threshold, i_dim):
    cols_description = "dimension_index integer, a_value integer, attribute-value_mass numeric"
    cols_name = ["dimension_index", "a_value", "attribute-value_mass"] 
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, valueToDel_TABLE, cols_description)
    insert_cols = ", ".join(cols_name)
    query = "INSERT INTO %s(%s)" % (valueToDel_TABLE, insert_cols) 
        + " SELECT * FROM %s WHERE %s == %d AND %f <= %f" % (attVal_Masses_TABLE, cols_name[0], i_dim, cols_name[1], threshold)
        + " ORDER BY %s" % cols_name[1]
    cur.execute(query)
    db_conn.commit()   
    cur.execute("SELECT %s FROM %s" % (cols_name[1], attVal_Masses_TABLE))
    valuesToDel = map(lambda x: x[0], cur.fetchall())
    db_conn.commit()                         
    cur.close() 
    print "Created %s for dimension %d in increasing order." % (valueToDel_TABLE, i_dim)
    return valuesToDel




