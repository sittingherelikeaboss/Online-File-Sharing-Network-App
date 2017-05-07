#CoE 4DN4 - Lab 3

import EchoClientServer_Thread

# Create a SERVER / RECEIVER Object
# Server continually listens for broadcast packets on SDP 30000
# Also listens for incoming TCP client connections on FSP 30001
EchoClientServer_Thread.Server()
