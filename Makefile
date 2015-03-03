LIB = lib/poetsocket.py
SRC = $(wildcard src/*.py) $(LIB)
BUILD = build

#
# build: produces client.zip
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
CL = client.zip
SV = server.zip


cl: $(BUILD)
	$(PYTHON) $</$(CL) $(IP) $(DELAY) $(PORT)

clv: $(BUILD)
	$(PYTHON) $</$(CL) $(IP) $(DELAY) $(PORT) -v

clvd: $(BUILD)
	$(PYTHON) $</$(CL) $(IP) $(DELAY) $(PORT) -v -d

sv: $(BUILD)
	$(PYTHON) $</$(SV) $(PORT)
