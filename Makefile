CLIENT = client.py
ZIP = $(CLIENT:py=zip)
COMMON = poetsocket.py
SRC = $(CLIENT) $(COMMON)
MAIN = __main__.py

CC = /usr/bin/zip  # lol
PYTHON = /usr/local/bin/python

IP = 127.0.0.1
DELAY = 1
PORT = -p 8081

#
# build: produces client.zip
#

default: $(ZIP)

$(ZIP): $(SRC)
	# our main file needs to be named __main__.py when we zip it up
	ln -s $(CLIENT) $(MAIN)
	$(CC) $(ZIP) $(MAIN) $(COMMON)
	rm $(MAIN)

clean:
	rm -rf archive $(ZIP) *.pyc *.zip $(MAIN)

#
# testing helpers
#

cl: $(ZIP)
	$(PYTHON) $< $(IP) $(DELAY) $(PORT)

clv: $(ZIP)
	$(PYTHON) $< $(IP) $(DELAY) $(PORT) -v

clvd: $(ZIP)
	$(PYTHON) $< $(IP) $(DELAY) $(PORT) -v -d

sv:
	$(PYTHON) server.py $(PORT)
