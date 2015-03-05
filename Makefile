SRC = $(wildcard **/*.py)
BUILD = build

#
# build: produces client.zip and server.zip
#

default: $(BUILD)

$(BUILD): $(SRC)
	@echo Beginning build.
	@echo
	mkdir -p build
	cd src && $(MAKE)
	@echo
	@echo Build Succeeded!

clean:
	rm -rf $(BUILD)

squeaky:
	$(MAKE) clean
	rm -rf archive

#
# testing helpers
#

# arguments
IP = 127.0.0.1
DELAY = 1
PORT = -p 8081

PYTHON = python
CL = poet-client.zip
SV = poet-server.zip


# run client at localhost:8081, delay 1s
cl: $(BUILD)
	$(PYTHON) $</$(CL) $(IP) $(DELAY) $(PORT)

# run client at localhost:8081, delay 1s, verbosely
clv: $(BUILD)
	$(PYTHON) $</$(CL) $(IP) $(DELAY) $(PORT) -v

# run client at localhost:8081, delay 1s, verbosely, and delete on disk
# after launch
clvd: $(BUILD)
	$(PYTHON) $</$(CL) $(IP) $(DELAY) $(PORT) -v -d

# run server on localhost:8081
sv: $(BUILD)
	$(PYTHON) $</$(SV) $(PORT)
