#!/usr/bin/env python3

########################################################################

import socket
import argparse
import sys
import threading

import os

# Use the standard echo client.
from EchoClientServer import Client

########################################################################
# Echo-Server class
########################################################################

class Server: # Receiver

    HOSTNAME = "0.0.0.0" # socket.gethostname()
    PORT = 30001 # For incoming TCP client connections on File Sharing Port

    # Service Discovery Port for broadcast packet received from Client
    ADDRESS_PORT = (HOSTNAME, Client.BROADCAST_PORT) 

    RECV_SIZE = 256
    BACKLOG = 10
    
    MSG_ENCODING = "utf-8"

    RESPONSE = "Jastine's File Sharing Service"
    RESPONSE_ENCODED = RESPONSE.encode(MSG_ENCODING)

    LISTEN_WAIT = 2

    def __init__(self):
        self.server_directory()
        print("Shared directory files available for sharing:", self.listDir)
        self.thread_list = []
        self.broadcast_thread = []
        self.create_listen_socket()
        # self.receive_forever() # Uncomment for UDP only
        self.process_connections_forever()

    def create_listen_socket(self):
        try:
            # Create an IPv4 TCP socket [0] and set up a UDP socket [1].
            self.socket = [socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                           socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]

            ############################### TCP / IP ###############################
            
            # Get socket layer socket options.
            self.socket[0].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to socket address, i.e., IP address and port.
            self.socket[0].bind((Server.HOSTNAME, Server.PORT))

            # Set socket to listen state.
            self.socket[0].listen(Server.BACKLOG)
            print("-" * 72)
            print("Listening for file sharing connections on port {} ..." \
                  .format(Server.PORT))

            ################################## UDP ##################################
            
            # Bind to all interfaces and the agreed on broadcat port.
            self.socket[1].bind(Server.ADDRESS_PORT)
            print("Listening for service discovery messages on port {} ...".format(Client.BROADCAST_PORT))
            
            #########################################################################

        except Exception as msg:
            print(msg)
            sys.exit(1)

    def receive_forever(self): # Only for UDP
        print("-" * 72)
        while True:
            try:
                # Continuously listening to service discovery broadcasts
                data, address = self.socket[1].recvfrom(Client.RECV_SIZE)
                print("Message from Client: {}".format(data.decode(Server.MSG_ENCODING)))
            
                if data.decode(Client.MSG_ENCODING) == "SERVICE DISCOVERY":
                    self.socket[1].sendto(Server.RESPONSE_ENCODED, address)
            except KeyboardInterrupt:
                print(); exit()
            except Exception as msg:
                print(msg)
                sys.exit(1)

    def response_handler(self, data, address):
        if data.decode(Client.MSG_ENCODING) == "SERVICE DISCOVERY":
            print("SERVICE DISCOVERY message from Client!")
            self.socket[1].sendto(Server.RESPONSE_ENCODED, address)
    
    def process_connections_forever(self):
        try:
            print("-" * 72)
            while True:
                #print("1")
                try:
                    # Wait 2 seconds for potential UDP broadcast packets from Client
                    self.socket[1].settimeout(Server.LISTEN_WAIT)
                    #self.socket[1].setblocking(False)
                    
                    data, address = self.socket[1].recvfrom(Client.RECV_SIZE)
                    new_broadcast_thread = threading.Thread(target=self.response_handler,
                                                      args=(data,address,))

                    # Record the new broadcast receive thread
                    self.broadcast_thread.append(new_broadcast_thread)

                    # Start the new broadcast receive thread running
                    #print("Starting broadcast receive thread:", new_broadcast_thread.name)
                    new_broadcast_thread.daemon = True
                    new_broadcast_thread.start()

                except socket.timeout:
                    pass
                #print("2")
                try:
                    # Wait 2 seconds for potential TCP connection from Client
                    self.socket[0].settimeout(Server.LISTEN_WAIT)
                    #self.socket[0].setblocking(False)
                    
                    new_client = self.socket[0].accept()
                    ########################################################
                    # A new client has connected. Create a new thread and
                    # have it process the client using the connection
                    # handler function.
                    new_thread = threading.Thread(target=self.connection_handler,
                                                  args=(new_client,))
                    
                    # Record the new thread.
                    self.thread_list.append(new_thread)

                    # Start the new thread running.
                    print("Starting serving thread:", new_thread.name)
                    new_thread.daemon = True
                    new_thread.start()

                except socket.timeout:
                    pass
                #print("3")
        except Exception as msg:
            print("Uh oh...")
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            print("Closing server socket ...")
            self.socket[0].close()
            sys.exit(1)

    def connection_handler(self, client):
        connection, address_port = client
        print("-" * 72)
        print("Connection received from {}.".format(address_port))

        while True:
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

            # Make decision based on received string from Client
            self.client_to_server_commands(client, recvd_str)
                
            # Send the received bytes back to the client.
            #connection.sendall(recvd_bytes)
            #print("Sent: ", recvd_str)

    def client_to_server_commands(self, client, command):
        connection, address_port = client
        if command == "list": # THIS WORKS!!!
            self.server_directory()
            stringToSend = ''
            for filename in self.listDir:
                stringToSend += filename + ' '
            connection.sendall(stringToSend.encode(Server.MSG_ENCODING))
            print("Sent:", stringToSend)
        elif command[:3] == "put":
            self.receive_file(client, command[4:])
        elif command[:3] == "get": # THIS WORKS!!!
            self.send_file(command[4:], client)
        elif command == "bye": # THIS WORKS!!!
            print("Closing client connection ...")
            self.socket[0].close()
            sys.exit(1)

    def server_directory(self):
        os.chdir("serverDirectory")
        self.listDir = os.listdir(os.getcwd())
        os.chdir("..") # Move out of directory

    def receive_file(self, client, fileName): # For "put" command AKA receiving
        try:
            connection, address_port = client
            os.chdir("serverDirectory") # Client files directory
            with open('new_' + fileName, 'wb') as f:
                while True:
                    data = connection.recv(256)
                    currSize = sys.getsizeof(data)
                    print(currSize)
                    f.write(data)
                    if currSize < 256:
                        break
            f.close()
            print(fileName, "successfully received!")
            os.chdir("..") # Move out of directory
        except KeyboardInterrupt:
            os.remove('new_' + fileName)
            sys.exit(1)
            

    def send_file(self, fileName, client): # For "get" command
        connection, address_port = client
        os.chdir("serverDirectory") # Server file directory
        with open(fileName, 'rb') as f:
            while True:
                bytesToSend = f.read(256)
                currSize = sys.getsizeof(bytesToSend)
                connection.send(bytesToSend)
                if currSize < 256:
                    break
                
        print(fileName, "succesfully sent!")
        f.close()
        os.chdir("..") # Move out of directory

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





