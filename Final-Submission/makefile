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
	@echo "Running demo using darpa_toy.csv"
	\python cube_main.py --file $(PATH_Data)/darpa_toy.csv --N 3 --k 5 --density ari --selection density

clean:
	\rm -f *.pyc *.tar
	\cd DOC; make -s spotless

paper.pdf:
	@echo ""
	\cd DOC; make -s

all.tar: 
	@echo ""
	tar cvf all.tar *


