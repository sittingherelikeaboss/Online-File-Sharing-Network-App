#!/usr/bin/env python3

########################################################################

import socket
import argparse
import sys

# Lab 3 Additional Libraries
import os
import time

########################################################################
# Echo-Server class
########################################################################

# We will not be using this, use the Server class with threading in
# EchoClientServer_Thread.py
class Server:

    HOSTNAME = socket.gethostname()
    PORT = 30001

    RECV_SIZE = 1024
    BACKLOG = 10
    
    MSG_ENCODING = "utf-8"

    def __init__(self):
        self.create_listen_socket()
        self.process_connections_forever()

    def create_listen_socket(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Get socket layer socket options.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to socket address, i.e., IP address and port.
            self.socket.bind( (Server.HOSTNAME, Server.PORT) )

            # Set socket to listen state.
            self.socket.listen(Server.BACKLOG)
            print("Listening on port {} ...".format(Server.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def process_connections_forever(self):
        try:
            while True:
                # Block while waiting for incoming connections. When
                # one is accepted, pass the new socket reference to
                # the connection handler.
                self.connection_handler(self.socket.accept())
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            self.socket.close()
            sys.exit(1)

    def connection_handler(self, client):
        connection, address_port = client
        print("-" * 72)
        print("Connection received from {}.".format(address_port))

        while True:

            try:

                # Receive bytes over the TCP connection. This will block
                # until "at least 1 byte or more" is available.
                recvd_bytes = connection.recv(Server.RECV_SIZE)
            
                # If recv returns with zero bytes, the other end of the
                # TCP connection has closed (The other end is probably in
                # FIN WAIT 2 and we are in CLOSE WAIT.). If so, close the
                # server end of the connection and get the next client
                # connection.
                if len(recvd_bytes) == 0:
                    print("Closing client connection ... ")
                    connection.close()
                    break
                
                # Decode the received bytes back into strings. Then output
                # them.
                recvd_str = recvd_bytes.decode(Server.MSG_ENCODING)
                print("Received: ", recvd_str)
                
                # Send the received bytes back to the client.
                connection.sendall(recvd_bytes)
                print("Sent: ", recvd_str)

            except KeyboardInterrupt:
                print()
                print("Closing client connection ... ")
                connection.close()
                break

########################################################################
# Echo-Client class
########################################################################

# We will be using this for for Lab 3
class Client: # Sender

    SERVER_HOSTNAME = socket.gethostname()
    RECV_SIZE = 1024

    ########################### MODIFICATIONS ##########################

    HOST = socket.gethostbyname(socket.gethostname())

    # Send the broadcast packet periodically. Set the period (seconds)
    BROADCAST_PERIOD = 1

    # Define the message to broadcast.
    MSG_ENCODING = "utf-8"
    MESSAGE = "SERVICE DISCOVERY"
    MESSAGE_ENCODED = MESSAGE.encode(MSG_ENCODING)

    # Use the broadcast-to-everyone IP address or a directed broadcast
    # address. Define a broadcast port.
    BROADCAST_ADDRESS = "255.255.255.255"
    BROADCAST_PORT = 30000 # Service Discovery Port (SDP)
    ADDRESS_PORT = (BROADCAST_ADDRESS, BROADCAST_PORT)

    ACCEPT_TIMEOUT = 5 # (seconds)
    RECV_SIZE = 1024
    NUM_BROADCAST_PACKETS = 3 # Send 3 "SERVICE DISCOVERY" packets

    ####################################################################

    def __init__(self):
        self.get_socket()
        self.send_console_input_forever()

    def get_console_input(self):
        # In this version we keep prompting the user until a non-blank
        # line is entered.
        while True:
            self.input_text = input("Enter command: ")
            if self.input_text != '':
                break

    def console_commands(self):
        if self.input_text == "scan": # THIS WORKS!!!
            self.send_broadcasts()
        elif self.input_text[:7] == "connect": # THIS WORKS!!!
            # This is to establish a TCP connection to the server
            IP_addr = ''
            port = ''
            firstWord = True
            for i in self.input_text[8:]:
                if i == ' ':
                    firstWord = False
                    continue
                if firstWord:
                    IP_addr += i
                else:
                    port += i
            self.connect_to_server(IP_addr, int(port))
        elif self.input_text == "llist": # THIS WORKS!!!
            self.client_directory()
            print("Local File Sharing Directory", self.listDir)
        elif self.input_text == "rlist": # THIS WORKS!!!
            self.input_text = "list"
            self.connection_send() # Send "list" command to Server
            self.connection_receive()
        elif self.input_text[:3] == "put":
            self.connection_send()
            print("fileName:", self.input_text[4:])
            self.send_file(self.input_text[4:])
        elif self.input_text[:3] == "get": # THIS WORKS!!!
            self.connection_send()
            self.receive_file(self.input_text[4:])
        elif self.input_text[:3] == "bye": # THIS WORKS!!!
            self.connection_send() # Send "bye" command to Server
            print("Closing server connection ...")
            self.socket[0].close()
            sys.exit(1)
        else:
            print("Invalid command")
    
    def send_console_input_forever(self):
        while True:
            try:
                self.get_console_input()
                self.console_commands()
                #print("Did it even come back here?")
            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing server connection ...")
                self.socket[0].close()
                sys.exit(1)

    def client_directory(self):
        os.chdir("clientDirectory")
        self.listDir = os.listdir(os.getcwd())
        os.chdir("..")

    def get_socket(self):
        try:   
            # Create an IPv4 TCP socket [0] and set up a UDP socket [1].
            self.socket = [socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                           socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]

            # Set the option for broadcasting.
            self.socket[1].setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # To get the response from SERVER / RECEIVER?
            self.socket[1].bind((Client.HOST, Client.BROADCAST_PORT)) 
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def send_file(self, fileName): # For "put" command to server
        os.chdir("clientDirectory") # Server file directory
        with open(fileName, 'rb') as f:
            while True:
                bytesToSend = f.read(256)
                currSize = sys.getsizeof(bytesToSend)
                self.socket[0].send(bytesToSend)
                if currSize < 256:
                    break
        print(fileName, "succesfully sent!")
        f.close()
        os.chdir("..") # Move out of directory

    def receive_file(self, fileName): # For "get" command to server
        os.chdir("clientDirectory") # Client files directory
##        print("Current working directory:", os.getcwd())
        with open('new_' + fileName, 'wb') as f:
            while True:
                data = self.socket[0].recv(256)
                currSize = sys.getsizeof(data)
                print(currSize)
                f.write(data)
                if currSize < 256:
                    break
        f.close()
        print(fileName, "succesfully received!")
        os.chdir("..") # Move out of directory


    ############################################################################
    # TCP/IP Methods
    ############################################################################

    def connect_to_server(self, IP_addr, port):
        try:
            # Connect to the server using its socket address tuple.
            #self.socket.connect((Client.SERVER_HOSTNAME, Server.PORT))
            #print("It tried to connect to the server tho?????")
            self.socket[0].connect((IP_addr, port))
        except Exception as msg:
            print(msg)
            sys.exit(1)
                
    def connection_send(self):
        try:
            # Send string objects over the connection. The string must
            # be encoded into bytes objects first.
            self.socket[0].sendall(self.input_text.encode(Server.MSG_ENCODING))
            print("Sent: ", self.input_text)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connection_receive(self):
        try:
            # Receive and print out text. The received bytes objects
            # must be decoded into string objects.
            recvd_bytes = self.socket[0].recv(Client.RECV_SIZE)

            # recv will block if nothing is available. If we receive
            # zero bytes, the connection has been closed from the
            # other end. In that case, close the connection on this
            # end and exit.
            if len(recvd_bytes) == 0:
                print("Closing server connection ... ")
                self.socket[0].close()
                sys.exit(1)

            print("Received: ", recvd_bytes.decode(Server.MSG_ENCODING))

        except Exception as msg:
            print(msg)
            sys.exit(1)

    ############################################################################
    # UDP Methods
    ############################################################################

##    def create_sender_socket(self):
##        try:
##            # Set up a UDP socket. Index 0.
##            self.socket.append(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
##
##            # Set the option for broadcasting.
##            self.socket[0].setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
##
##            # To get the response from SERVER / RECEIVER?
##            self.socket[0].bind((Client.HOST, Client.BROADCAST_PORT)) 
##        except Exception as msg:
##            print(msg)
##            sys.exit(1)

    def send_broadcasts(self):
        try:
            self.socket[1].settimeout(Client.ACCEPT_TIMEOUT)
            for i in range(Client.NUM_BROADCAST_PACKETS):
                print("Broadcasting to {} ...".format(Client.ADDRESS_PORT))
                self.socket[1].sendto(Client.MESSAGE_ENCODED, Client.ADDRESS_PORT)
                
                # Response from SERVER / RECEIVER
                data, address = self.socket[1].recvfrom(Client.RECV_SIZE)
                time.sleep(Client.BROADCAST_PERIOD)
                #print(data.decode(Client.MSG_ENCODING) == "Jastine's File Sharing Service")
                if data.decode(Client.MSG_ENCODING) == "Jastine's File Sharing Service":
                    print(data.decode(Client.MSG_ENCODING), "found at", "{}".format((Client.HOST, "30001")))
        except socket.timeout:
            print("No service found")
        except KeyboardInterrupt:
            print()
            print("Closing CLIENT / SENDER connection ...")
        except Exception as msg:
            print(msg)
##        finally:
##            #print("Just wondering if it did this")
            self.socket[1].close()
##            #sys.exit(1)

########################################################################
# Process command line arguments if run directly.
########################################################################

if __name__ == '__main__':
    roles = {'client': Client,'server': Server}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles, 
                        help='server or client role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()

########################################################################





