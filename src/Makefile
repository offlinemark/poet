LIB = $(wildcard ../lib/*.py)
SRC = $(wildcard *.py)
MAIN = __main__.pyc
BUILD = ../build

# lol
ZIP = zip
PYCC = python2.7 -m py_compile

default: $(SRC:.py=.zip)

%.zip: %.pyc $(LIB:.py=.pyc)
# the file with main() needs to be named __main__.py for this to work
	ln -s $< $(MAIN)

# zip everything up. -j: ignore paths, only use file names. -r : zip file
# destination
	$(ZIP) -j -r $(BUILD)/poet-$@ $(MAIN) $(LIB:.py=.pyc)

# clean up, we don't need it anymore
	rm $(MAIN)

%.pyc: %.py
	$(PYCC) $<
