LIB = $(wildcard ../lib/*.py)
SRC = $(wildcard *.py)
MAIN = __main__.py
BUILD = ../build

# lol
CC = zip

default: $(SRC:.py=.zip)

%.zip: %.py $(LIB)

# the file with main() needs to be named __main__.py for this to work
	ln -s $< $(MAIN)

# zip everything up. -j: ignore paths, only use file names. -r : zip file
# destination
	$(CC) -j -r $(BUILD)/$@ $(MAIN) $(LIB)

# clean up, we don't need it anymore
	rm $(MAIN)
