client = {}


def client_handler(cmd):
    def decorate(func):
        client[cmd] = func
    return decorate


def server(argv, conn):
    print argv
    resp = conn.exchange('example')
    print resp


@client_handler('example')
def example():
    return 'example from client'
