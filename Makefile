SRC = $(wildcard **/*.py)
OUT = bin

#
# default: produces output client and server executables in bin/
#

default: $(OUT)

# a debug build just brings the client, server, and library files all
# together into the same directory because the regular build disables
# debugging source context
dbg:
	@echo Copying source files into current directory.
	@echo
	for file in $(SRC) ; do \
		cp $$file . ; \
	done
	@echo
	@echo Done.

$(OUT): $(SRC)
	@echo Beginning build.
	@echo
	mkdir -p $(OUT)
	cd src && $(MAKE)
	@echo
	@echo Build Succeeded!

clean:
	rm -rf $(OUT) *.py*

squeaky:
	$(MAKE) clean
	rm -rf archive

# testing helpers
include Testing.mk
