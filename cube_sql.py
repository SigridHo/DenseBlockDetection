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
        #if index > 20:   # print the top lines to avoid exhausted table-printing 
        #    break 
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


def cube_sql_block_create_insert(db_conn, block_table, ori_table, block_tables, att_names, dimension_num, cols_description):
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, block_table, cols_description)
    insert_cols = ", ".join(att_names)
    query = "INSERT INTO %s(%s)" % (block_table, insert_cols) + " SELECT "
    for i in range(dimension_num):
        if i != dimension_num - 1:
            query += ori_table + "." + att_names[i] + ", "
        else:
            query += ori_table + "." + att_names[i] + " FROM " + ori_table
    for i in range(dimension_num):
            query += ", " + block_tables[i]
    query += " WHERE "
    for i in range(dimension_num):
        if i != dimension_num - 1:
            query += ori_table + "." + att_names[i] + " = " + block_tables[i] + "." + att_names[i] + " AND "
        else:
            query += ori_table + "." + att_names[i] + " = " + block_tables[i] + "." + att_names[i]
    query += " ORDER BY " + ",".join(attr for attr in att_names)
    cur.execute(query)
    db_conn.commit()                            
    cur.close() 
    print "Created and inserted block table %s." % block_table


def cube_sql_insert_attrVal_mass(db_conn, b_table, block_table, attval_masses_table, dim, attrName):
    cur = db_conn.cursor()
    query = "INSERT INTO %s" % attval_masses_table \
        + " SELECT %d, B.%s, COUNT(*) AS attrVal_mass" % (dim, attrName) \
        + " FROM %s AS A, %s AS B WHERE A.%s = B.%s " % (block_table, b_table, attrName, attrName) \
        + " GROUP BY B.%s" % attrName
    cur.execute(query)
    db_conn.commit()     
    cur.close() 
    print "Inserted AttrVal Masses of dimension-%d (%s) into %s." % (dim, attrName, attval_masses_table)

def cube_select_values_to_remove(db_conn, d_cube_table, attval_masses_table, threshold, dim):
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, d_cube_table, "a_value text, attrVal_mass numeric")
    query = "INSERT INTO %s SELECT a_value, attrVal_mass FROM %s" % (d_cube_table, attval_masses_table) \
        + " WHERE dimension_index = %d AND attrVal_mass <= %f ORDER BY attrVal_mass" % (dim, threshold)
    cur.execute(query)
    db_conn.commit()                         
    cur.close() 
    print "Created %s for dimension %d in increasing order of attrVal_mass." % (d_cube_table, dim)


def cube_sql_dCube_sum(db_conn, d_cube_table):
    cur = db_conn.cursor()
    query = "SELECT SUM(attrval_mass) FROM %s"  % d_cube_table 
    cur.execute(query)
    delta = cur.fetchone()[0]
    db_conn.commit()                     
    cur.close() 
    # print "Computed attribute-vale masses for %s." % d_cube_table
    return delta


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
    query = "DELETE FROM %s AS A USING %s AS B" % (B_table, D_table) \
        + " WHERE A.%s = B.a_value" % attrName
    cur.execute(query)
    db_conn.commit()                            
    cur.close()
    print "Updated %s by removing tuples in %s." % (B_table, D_table)


def cube_sql_reconstruct_block(db_conn, b_table, r_table, order_table, att_name, col_fmt, r_tilde, dim):
    cur = db_conn.cursor()
    cube_sql_table_drop_create(db_conn, b_table, col_fmt) 
    query = "INSERT INTO %s" % b_table \
        + " SELECT A.%s FROM %s AS A, %s AS B" % (att_name, r_table, order_table) \
        + " WHERE A.%s = B.a_value AND B.order_a_i >= %d" % (att_name, r_tilde) \
        + " AND B.dimension_index = %d" % dim
    cur.execute(query)
    db_conn.commit()                            
    cur.close() 
    print "Reconstruct %s by %s and %s" % (b_table, r_table, order_table)    

