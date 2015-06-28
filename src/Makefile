SRC = $(wildcard *.py)
COMMON = $(wildcard ../common/*.py)
COMMON := $(subst py,pyo,$(COMMON))

MAIN = __main__.pyo
OUT = ../bin
ZIP = zip
PYCC = python2.7 -OO -m py_compile


default: $(SRC:.py=.zip)

BIN = $(OUT)/poet-$@
%.zip: %.pyo $(COMMON)
# the file with main() needs to be named __main__.py for this to work
	ln -s $< $(MAIN)

# zip everything up. -j: ignore paths, only use file names. -r : zip file
# destination
	$(ZIP) -j -r $(BIN) $(MAIN) $(COMMON)

# clean up, we don't need it anymore
	rm $(MAIN)

# make exectuable
	cp $(BIN) .tmp
	echo "#!/usr/bin/env python2.7" > $(BIN)
	cat .tmp >> $(BIN)
	rm .tmp
	chmod +x $(BIN)

# we don't need the zip ending
	mv $(BIN) $(basename $(BIN))

%.pyo: %.py
	$(PYCC) $<
