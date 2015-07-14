import module


def server(argv, conn):
    print argv
    resp = conn.exchange('example')
    print resp


@module.client_handler('example')
def example():
    return 'example from client'
