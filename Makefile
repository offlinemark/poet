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

bin:
	mkdir -p $@

bin/poet-client: client.pyo $(COMMON)
# main file needs to be named __main__.py(c/o) for zip file packaging to work
	cp $< common/__main__.pyo

# zip everything up. -r : zip file destination
	cd common && $(ZIP) -r ../$@ *.pyo modules/*.pyo

# get rid of auto-appended .zip extension
	mv $@.zip $@

# make executable
	mv $@ .tmp
	echo "#!/usr/bin/env python2.7" > $@
	cat .tmp >> $@
	rm .tmp
	chmod +x $@


bin/poet-server: server.pyo $(COMMON)
	cp $< common/__main__.pyo
	cd common && $(ZIP) -r ../$@ *.pyo modules/*.pyo
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
	rm -f common/__main__.py
	rm -f common/*.pyo common/*.pyc
	rm -f common/modules/*.pyo common/modules/*.pyc

squeaky:
	$(MAKE) clean
	rm -rf archive

# testing helpers
include Testing.mk
