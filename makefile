##################
# Authors: Haoming Chen and Xinrui He
# Date: March 25, 2017
##################

null      :=
SPACE     := $(null) $(null)
ABS_PATH  := $(shell pwd)
PATH 	  := $(subst $(SPACE),\ ,$(ABS_PATH))
PREFIX 	  := python cube_main.py --file $(PATH)/datasets/darpa.csv --N 3

run:
	$(PREFIX) --k 5 --density geometric --selection cardinality

k=5.density=g.selection=c: $(PREFIX) --k 5 --density geometric --selection cardinality

k=5.density=a.selection=c: $(PREFIX) --k 5 --density arithmetic --selection cardinality

k=5.density=s.selection=c: $(PREFIX) --k 5 --density suspiciousness --selection cardinality

k=5.density=g.selection=d: $(PREFIX) --k 5 --density geometric --selection density

k=5.density=a.selection=d: $(PREFIX) --k 5 --density arithmetic --selection density

k=5.density=s.selection=d: $(PREFIX) --k 5 --density suspiciousness --selection density

