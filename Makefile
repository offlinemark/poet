SRC = __main__.py poetsocket.py
OUT = client.zip
CC = /usr/bin/zip
PYTHON = /usr/local/bin/python

IP = 127.0.0.1
DELAY = 1
PORT = -p 8081

#
# build
#

default: $(OUT)

$(OUT): $(SRC)
	$(CC) $(OUT) $(SRC)

clean:
	rm -rf archive $(OUT) *.pyc

#
# testing helpers
#

cl: $(OUT)
	$(PYTHON) $< $(IP) $(DELAY) $(PORT)

clv: $(OUT)
	$(PYTHON) $< $(IP) $(DELAY) $(PORT) -v 

clvd: $(OUT)
	$(PYTHON) $< $(IP) $(DELAY) $(PORT) -v -d

sv:
	./server.py $(PORT)
