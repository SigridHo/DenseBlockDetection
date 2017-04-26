##################
# Authors: Haoming Chen and Xinrui He
# Date: April 25, 2017
##################

null      :=
SPACE     := $(null) $(null)
ABS_PATH  := $(shell pwd)
PATH_Data := $(subst $(SPACE),\ ,$(ABS_PATH))
PREFIX 	  := python cube_main.py --file $(PATH)/darpa_toy.csv --N 3


all: demo clean

demo:
	@echo ""
	@echo "Running demo using darpa_toy.csv"
	@echo ""
	@echo "IMPORTANT!!! Please change Username, Password, Port, etc. in cube_params.py and start the Postgres Database before running cube_main.py."
	@echo ""
	\python cube_main.py --file $(PATH_Data)/darpa_toy.csv --N 3 --k 5 --density ari --selection density


clean:
	\rm -f *.pyc *.tar *.pdf
	\cd DOC; make -s spotless

paper.pdf: clean
	\cd DOC; make -s
	\mv DOC/paper.pdf ./15826_final_report.pdf

all.tar: 
	@echo ""
	tar cvf all.tar *


