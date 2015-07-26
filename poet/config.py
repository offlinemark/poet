#
# Poet Configurations
#

# default client authentication token. change this to whatever you want!
AUTH = 'b9c39a336bb97a9c9bda2b82bdaacff3'

# directory to save output files to
ARCHIVE_DIR = 'archive'

#
# The below configs let you bake in the server IP and beacon interval
# into the final executable so it can simply be executed without supplying
# command line arguments.
#

# server IP
#
# if this is None, it *must* be specified as a command line argument
# when client is executed
#
# SERVER_IP = '1.2.3.4'  # example
SERVER_IP = None

# client beacon interval
#
# if this is None, it *may* be specified as a command line argument,
# otherwise, it will take the default value
#
# BEACON_INTERVAL = 300  # example
BEACON_INTERVAL = None
