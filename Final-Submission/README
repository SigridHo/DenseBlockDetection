—- Author: Haoming Chen, Xinrui He
—- Date: April 25, 2017
—- 15826 Project: Dense block detection with D-Cube

** FILES DESCRIPTION **

1. The directory “DOC” contains the related tex files to generate the final writeup.

2. Python files “cube_*.py” are the implementation of D-Cube Algorithm. Other python files are auxiliary functions to modify the format of the dataset before applying D-Cube.

3. “darpa_toy.csv” is a toy dataset for demonstration and quick validation. 

4. Directory “Marker_method” contains the modified Python scripts using the “marker” method mentioned in the project description. 

5. Directory “Indexing” contains the modified Python scripts using indexing of database to try to accelerate. 


** INSTRUCTIONS **

1. IMPORTANT: Please change the corresponding initialization parameters in “cube_params.py” (i.e.: Username, Password, Port, etc.) before running cube_main.py.

2. Type “make” to run the demo on a sample input file “darpa_toy.csv”.

3. Type “make paper.pdf” to generate the PDF version of the project writeup. {Note that you must install corresponding version of Tex compiler to run this command.)

4. Type “make clean” to eliminate all the derived and temporary files.

5. Type “make all.tar” to create a tar file for distribution.


6. For Task 3:

   6.1. To run the Marker Method, change your current directory to “Marker_method”. Type "make" to run the demo on a sample input file “darpa_toy.csv” with Marker Method.

   6.2. To run the different indexing options, change your current directory to “Indexing”. Type "make" to run the demo on a sample input file “darpa_toy.csv” with indexing. The default indexing option is btree. If you want to change the indexing method to gist or gin, set the "method" variable to "gist" or "gin" in function "cube_sql_index" of "indexing/cube_sql.py". 
   
   Note: To run with gist or gin options, you may need to create extension on your dataset to support multicolumn indexing. Use command "CREATE EXTENSION btree_gin;" or "CREATE EXTENSION btree_gist;" in your database. You can only use these commands once on your database.
