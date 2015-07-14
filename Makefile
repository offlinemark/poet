COMMON = $(wildcard common/*.py common/modules/*.py)
COMMON := $(subst py,pyo,$(COMMON))
OUT = bin/ bin/poet-client bin/poet-server

ZIP = /usr/bin/zip
PYCC = python2.7 -OO -m py_compile

#
# default: produces output client and server executables in bin/
#

default: $(OUT)

# for debugging, just place the main files into the common/ directory, then
# cd into that directory and execute the client and server. can't debug
# "production" builds because debug info is stripped from them
dbg:
	cp client.py common
	cp server.py common
	ls -1 common/modules |grep -v pyo |grep -v __init__ > common/modindex.txt

bin:
	mkdir -p $@

bin/poet-client: client.pyo $(COMMON)
# main file needs to be named __main__.py(c/o) for zip file packaging to work
	cp $< common/__main__.pyo

# create module index file, so client/server know what to load at runtime
	ls -1 common/modules |grep -v pyo |grep -v __init__ > common/modindex.txt

# zip everything up. -r : zip file destination
	cd common && $(ZIP) -r ../$@ *.pyo modindex.txt modules/*.pyo

# get rid of auto-appended .zip extension
	mv $@.zip $@

# make executable
	mv $@ .tmp
	echo "#!/usr/bin/env python2.7" > $@
	cat .tmp >> $@
	rm .tmp
	chmod +x $@


bin/poet-server: server.pyo $(COMMON)
# exact same stuff as above
	cp $< common/__main__.pyo
	ls -1 common/modules |grep -v pyo |grep -v __init__ > common/modindex.txt
	cd common && $(ZIP) -r ../$@ *.pyo modindex.txt modules/*.pyo
	mv $@.zip $@
	mv $@ .tmp
	echo "#!/usr/bin/env python2.7" > $@
	cat .tmp >> $@
	rm .tmp
	chmod +x $@

%.pyo: %.py
	$(PYCC) $<

clean:
	rm -rf bin
	rm -f *.pyo
	rm -f common/__main__.py common/modindex.txt
	rm -f common/client.py common/server.py
	rm -f common/*.pyo common/*.pyc
	rm -f common/modules/*.pyo common/modules/*.pyc

squeaky:
	$(MAKE) clean
	rm -rf archive

# testing helpers
include Testing.mk
