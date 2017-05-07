#!/usr/bin/env python3

########################################################################

import socket
import argparse
import sys
import time

# LAB 3 LIBRARIES
import os
import threading # Handling multiple clients

########################################################################
# Echo-Server class
########################################################################

class Server:

    MSG_ENCODING = "utf-8"
    
    # TCP/IP Socket
    HOSTNAME = socket.gethostname()
    FS_PORT = 30001 # File Sharing Port / Broadcast Port
    RECV_SIZE = 1024
    BACKLOG = 10

    # UDP Socket
    BROADCAST_PERIOD = 1
    MESSAGE = "SERVICE DISCOVERY"
    MESSAGE_ENCODED = MESSAGE.encode(MSG_ENCODING)
    BROADCAST_ADDRESS = "255.255.255.255"
    BROADCAST_PORT = 30000 # Service Discovery Port
    ADDRESS_PORT = (BROADCAST_ADDRESS, FS_PORT)
   
    def __init__(self):
        #self.available_for_sharing()

        # The server should print output indicating that it is listening
        # on the host laptop SDP for incoming service discovery
        # messages on the SDP
        self.create_sender_socket()
        self.send_broadcasts_forever()

    ################################################################
    # TCP/IP STUFF -- FILE SHARING PORT
    ################################################################
    
    def create_listen_socket(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set up a UDP socket.
            self.UDPsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Get socket layer socket options.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Set the option for broadcasting.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind socket to socket address, i.e., IP address and port.
            self.socket.bind((Server.HOSTNAME, Server.FS_PORT))

            # Set socket to listen state.
            self.socket.listen(Server.BACKLOG)
            print("-" * 72)
            print("Listening for service discovery messages on SDP port {} ...".format(Server.FS_PORT))
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
                
                if recvd_str == "bye":
                    print("Closing client connection ... ")
                    connection.close()
                    break
                elif recvd_str[:3] == "put":
                    recvd_bytes = self.client_to_server_commands(client, recvd_str)
                    connection.sendall(recvd_bytes)
                    self.put_file(client, recvd_str[4:])
                else: # Send back new byte object
                    recvd_bytes = self.client_to_server_commands(client, recvd_str)
                    connection.sendall(recvd_bytes)
                    
                # Send the received bytes back to the client.
                print("Sent: ", recvd_str)

            except KeyboardInterrupt:
                print()
                print("Closing client connection ... ")
                connection.close()
                break
            
    ################################################################
    # UDP STUFF -- SERVICE DISCOVERY PORT -- RECEIVER
    ################################################################
    
    def create_sender_socket(self): 
        try:
            # Set up a UDP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Set the option for broadcasting.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def send_broadcasts_forever(self):
        try:
            while True:
                print("Listening for service discovery messages on SDP port {} ...".format(Server.ADDRESS_PORT))
                self.socket.sendto(Server.MESSAGE_ENCODED, Server.ADDRESS_PORT)
                time.sleep(Server.BROADCAST_PERIOD)
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            self.socket.close()
            sys.exit(1)
            
    ################################################################
    # LAB 3 ADDED METHODS
    ################################################################

    def client_to_server_commands(self, client, command):
        if command == "list": # Remote list
            # Return directory listing of file sharing directory
            # Can list be converted into a byte object???????
            self.available_for_sharing()
            str_to_send = ""
            for x in self.listDir:
                str_to_send += x + " "
            return str_to_send.encode(Server.MSG_ENCODING)
        elif command[:3] == "put":
            return "ok".encode(Server.MSG_ENCODING)
        elif command[:3] == "get":
            # Implement File Transfer
            return "file sent to client".encode(Server.MSG_ENCODING)

    def available_for_sharing(self):
        print(os.getcwd())
        os.chdir("serverDirectory") # Server Files
        self.listDir = os.listdir(os.getcwd())
        os.chdir("..") # Move out of directory
        print("Remote File Sharing Directory /serverDirectory", self.listDir)

    def put_file(self, client, fileName): # For "put" command AKA receiving
        connection, address_port = client
        os.chdir("serverDirectory") # Server file directory
        print("Current working directory:", os.getcwd())
        
        fileInfo = os.stat(fileName) # Creates a tuple of file information
        fileSize = fileInfo[6] # Indexes file size information from tuple
        f = open('new_' + fileName, 'wb')
        print(f)
        data = connection.recv(Server.RECV_SIZE)
        totalRecv = len(data) # Keep track of how much has been sent
        f.write(data)
        
        while totalRecv < fileSize:
            data = connection.recv(Server.RECV_SIZE)
            totalRecv += len(data) # Keep track of how much has been sent
            f.write(data)

        os.chdir("..") # Move out of directory

    def send_file(self, fileName): # For "get" command
        os.chdir("serverDirectory") # Server file directory
        print("Current working directory:", os.getcwd())

        with open(fileName, 'rb') as f:
            bytesToSend = f.read(Client.RECV_SIZE)
            self.socket(bytesToSend)
            while bytesToSend != "":
                bytesToSend = f.read(Client.RECV_SIZE)
                self.socket.send(bytesToSend)
        os.chdir("..") # Move out of directory

########################################################################
# Echo-Client class
########################################################################

class Client:

    # TCP/IP 
    SERVER_HOSTNAME = socket.gethostname()
    RECV_SIZE = 1024

    # UDP
    RECV_SIZE_UDP = 256
    HOST = "0.0.0.0"
    ADDRESS_PORT = (HOST, Server.BROADCAST_PORT)

    def __init__(self):
        self.get_UDP_socket()
        self.receive_forever()

    ################################################################
    # TCP/IP STUFF -- FILE SHARING PORT
    ################################################################

    def get_socket(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connect_to_server(self):
        try:
            # Connect to the server using its socket address tuple.
            self.socket.connect((Client.SERVER_HOSTNAME, Server.FS_PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def get_console_input(self):
        # In this version we keep prompting the user until a non-blank
        # line is entered.
        while True:
            self.input_text = input("Enter command: ")
            if self.input_text != '':
                break

    def send_console_input_forever(self):
        while True:
            try:
                self.get_console_input()
                self.client_commands(self.input_text)
                #self.connection_send()
                #self.connection_receive()
            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing server connection ...")
                self.socket.close()
                sys.exit(1)

    def connection_send(self, string_to_send):
        try:
            # Send string objects over the connection. The string must
            # be encoded into bytes objects first.
            self.socket.sendall(string_to_send.encode(Server.MSG_ENCODING))
            print("Sent: ", string_to_send)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connection_receive(self, command):
        try:
            # Receive and print out text. The received bytes objects
            # must be decoded into string objects.
            recvd_bytes = self.socket.recv(Client.RECV_SIZE)
            recvd_str = recvd_bytes.decode(Server.MSG_ENCODING)
            
            # recv will block if nothing is available. If we receive
            # zero bytes, the connection has been closed from the
            # other end. In that case, close the connection on this
            # end and exit.
            if len(recvd_bytes) == 0 or recvd_str == "bye":
                print("Closing server connection ... ")
                self.socket.close()
                sys.exit(1)
            elif command == "put":
                if recvd_str == "ok":
                    fileName = self.input_text 
                    self.send_file(fileName[4:]) # Concatenate file name only
                    print(fileName[4:])
                    
            elif command == "list":
                print("Remote File Sharing Directory /serverDirectory", recvd_str)
                
            print("Received: ", recvd_str)

        except Exception as msg:
            print(msg)
            sys.exit(1)

    ################################################################
    # UDP STUFF -- SERVICE DISCOVERY PORT -- SENDER
    ################################################################

    def get_UDP_socket(self):
        try:
            # Create an IPv4 UDP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Bind to all interfaces and the agreed on broadcast port.
            self.socket.bind(Client.ADDRESS_PORT)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def receive_forever(self):
        while True:
            try:
                data, address = self.socket.recvfrom(Client.RECV_SIZE_UDP)
                print("Broadcast received: ", data.decode(Server.MSG_ENCODING), address)
            except KeyboardInterrupt:
                print()
                exit()
            except Exception as msg:
                print(msg)
                sys.exit(1)

    ################################################################
    # LAB 3 ADDED METHODS
    ################################################################

    def client_commands(self, command):
        if command == "bye":
            self.connection_send("bye")
            self.connection_receive(command)
        elif command == "scan":
            # Transmit one or more SERVICE DISCOVERY broadcasts
            # Listen for file sharing server response
            pass
        elif command == "llist": # Local list
            # Client gives directory listing of its local file sharing directory
            self.available_for_sharing()
        elif command == "rlist": # Remote list
            # Sends "list" command to server to obtain file sharing directoy listing
            self.connection_send("list")
            self.connection_receive("list")
        elif command[:3] == "put":
            self.connection_send(command) # Issue "put" command to the server
            self.connection_receive("put") # Server responds with "ok"
            print("It went here 3")
            
            # Client sends file over the connection
        elif command[:3] == "get":
            # Issue "get" command to the server
            self.connection_send(command)

            # Save file locally
        else:
            print("Please enter a valid command")

    def available_for_sharing(self):
        print(os.getcwd())
        os.chdir("clientDirectory") # Client files directory
        listDir = os.listdir(os.getcwd())
        os.chdir("..") # Exit directory
        print("Local File Sharing Directory /clientDirectory", listDir)

    def send_file(self, fileName): # For "put" command to server
        os.chdir("clientDirectory") # Client files directory
        print("Current working directory:", os.getcwd())
        with open(fileName, 'rb') as f:
            bytesToSend = f.read(Server.RECV_SIZE) # Read 1024 bytes from file
            self.socket.send(bytesToSend)
            while bytesToSend != "":
                bytesToSend = f.read(Server.RECV_SIZE) # Read 1024 bytes from file
                self.socket.send(bytesToSend)
        os.chdir("..") # Move out of directory

    def get_file(self): # For "get" command to server
        os.chdir("clientDirectory") # Client files directory
        print("Current working directory:", os.getcwd())
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





