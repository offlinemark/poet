#
# testing helpers
#
# For development instead of having to type all the arguments, it's convenient
# to use these shortcuts.
#

# arguments
IP = 127.0.0.1
DELAY = 1
PORT = -p 8081
PYTHON = python2.7

CL = client.py
SV = server.py
BIN_CL = $(OUT)/poet-$(basename $(CL))
BIN_SV = $(OUT)/poet-$(basename $(SV))

#
# shortcuts for running debug build scripts that are in the project root
# directory
#

# run client at localhost:8081, delay 1s
cl: dbg
	$(PYTHON) $(CL) $(IP) $(DELAY) $(PORT) --no-selfdestruct

# run client at localhost:8081, delay 1s, verbosely
clv: dbg
	$(PYTHON) $(CL) $(IP) $(DELAY) $(PORT) --debug --no-selfdestruct --no-daemon

# run server on localhost:8081
sv: dbg
	$(PYTHON) $(SV) $(PORT)

#
# shortcuts for running the real build in bin/
#

# run client at localhost:8081, delay 1s
bcl: default
	$(PYTHON) $(BIN_CL) $(IP) $(DELAY) $(PORT) --no-selfdestruct

# run client at localhost:8081, delay 1s, verbosely
bclv: default
	$(PYTHON) $(BIN_CL) $(IP) $(DELAY) $(PORT) --debug --no-selfdestruct --no-daemon

# run server on localhost:8081
bsv: default
	$(PYTHON) $(BIN_SV) $(PORT)
