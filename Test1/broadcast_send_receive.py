#!/usr/bin/env python3

########################################################################

import socket
import argparse
import sys
import time

import os
import threading

########################################################################
# Broadcast Server class
########################################################################

class Sender:

    # Send the broadcast packet periodically. Set the period
    # (seconds).
    BROADCAST_PERIOD = 2

    # Define the message to broadcast.
    MSG_ENCODING = "utf-8"
    MESSAGE =  "SERVICE DISCOVERY"
    MESSAGE_ENCODED = MESSAGE.encode('utf-8')

    # Use the broadcast-to-everyone IP address or a directed broadcast
    # address. Define a broadcast port.
    BROADCAST_ADDRESS = "255.255.255.255" # or e.g., "192.168.1.255"
    BROADCAST_PORT = 30000 # Service Discovery
    ADDRESS_PORT = (BROADCAST_ADDRESS, BROADCAST_PORT)
	
    PORT = 30001 # File Sharing 

    HOSTNAME = socket.gethostname()
    HOST = socket.gethostbyname(socket.gethostname())
    RECV_SIZE = 1024
    BACKLOG = 10

    def __init__(self):
        self.server_directory()
        print("Shared directory files:", self.listDir)
        print("-" * 72)
        self.create_sender_socket()
        self.send_broadcasts()

    ###############################################################################
    # UDP Methods
    ###############################################################################
    
    def create_sender_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Set up a UDP socket.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Set the option for broadcasting.
            self.socket.bind((Sender.HOST, Sender.BROADCAST_PORT)) # To get the response from Receiver?

            
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def send_broadcasts(self):
        try:
            while True:
                ##################### DO NOT TOUCH THESE OR YOU'LL FUCK IT UP AGAIN #################################
                print("Listening for service discovery messages on {} ...".format(Sender.ADDRESS_PORT))
                self.socket.sendto(Sender.MESSAGE_ENCODED, Sender.ADDRESS_PORT)
                self.socket.sendto("Jastine's File Sharing Service".encode(Sender.MSG_ENCODING), Sender.ADDRESS_PORT)

                ############## RECEIVE RESPONSE FROM RECEIVER/CLIENT ##############
##                data, address = self.socket.recvfrom(Sender.RECV_SIZE)
##                print(data.decode(Sender.MSG_ENCODING))
##                if data == Sender.MESSAGE_ENCODED:
##                    print("It went full retard")
##                    break
                
                #####################################################################################################
                time.sleep(Sender.BROADCAST_PERIOD)
                
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
            print("Closing sender connection ...")
        finally:
            self.socket.close()
            sys.exit(1)

    ###############################################################################
    # TCP/IP Methods
    ###############################################################################

    def create_listen_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((Sender.HOSTNAME, Sender.PORT))
            self.socket.listen(Sender.BACKLOG)
            print("Listening for file sharing connections on {} ...".format(Sender.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def process_connections(self):
        try:
            self.connection_handler(self.socket.accept())
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
            print("Closing sender connection ...")
        finally:
            self.socket.close()
            sys.exit(1)

    def connection_handler(self, client):
        connection, address_port = client
        print("-" * 72)
        print("Listening for file sharing connections on port {}.".format(address_port))
        while True:
            try:
                recvd_bytes = connection.recv(Server.RECV_SIZE)
                if len(recvd_bytes) == 0:
                    print("Closing sender connection ... ")
                    connection.close()
                    break
                recvd_str = recvd_bytes.decode(Server.MSG_ENCODING)
                print("Received: ", recvd_str)

                
                self.client_to_server_cmds(recvd_str, client)

                
                connection.sendall(self.str_to_send.encode(MSG_ENCODING))
                print("Sent: ", self.str_to_send)
            except KeyboardInterrupt:
                print()
                print("Closing sender connection ... ")
                connection.close()
                break

    def client_to_server_cmds(self, recvd_str, client):
        if recvd_str == "list":
            self.server_directory()
            self.str_to_send = ''
            for filename in self.listDir:
                self.str_to_send += filename + ' '
        elif recvd_str[:3] == "put":
            self.put_file(client, recvd_str[4:])
        elif recvd_str[:3] == "get":
            self.send_file(recvd_str[4:])
        elif recvd_str == "bye":
            print()
            print("Closing sender connection ...")
            self.socket.close()
            sys.exit(1)

    def server_directory(self):
        os.chdir("serverDirectory")
        self.listDir = os.listdir(os.getcwd())
        os.chdir("..")

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
# Echo Receiver class
########################################################################

class Receiver:

    RECV_SIZE = 256

    HOST = "0.0.0.0"
    ADDRESS_PORT = (HOST, Sender.BROADCAST_PORT)

    ACCEPT_TIMEOUT = 5

    SERVER_HOSTNAME = socket.gethostname()
    RECV_SIZE2 = 1024

    def __init__(self):
        self.get_console_input_forever()

    def get_console_input_forever(self):
        while True:
            try:
                self.get_console_input()
                self.console_commands()
            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing receiver connection ...")
                self.socket.close()
                sys.exit(1)

    def get_console_input(self):
        while True:
            self.input_text = input("Enter command: ")
            if self.input_text != '':
                break

    def client_directory(self):
        os.chdir("clientDirectory")
        self.listDir = os.listdir(os.getcwd())
        os.chdir("..")

    ###############################################################################
    # UDP Methods
    ###############################################################################

    def get_socket(self):
        try:
            # Create an IPv4 UDP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Bind to all interfaces and the agreed on broadcast port.
            self.socket.bind(Receiver.ADDRESS_PORT)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def receive_SD_message(self):
        try:
            #while True: # Infinite loop for debugging purposes
            ##################### DO NOT TOUCH THESE OR YOU'LL FUCK IT UP AGAIN ##################
            self.socket.settimeout(Receiver.ACCEPT_TIMEOUT)
            data, address = self.socket.recvfrom(Receiver.RECV_SIZE)
            serverName, address = self.socket.recvfrom(Receiver.RECV_SIZE)
            if data.decode(Sender.MSG_ENCODING) == "SERVICE DISCOVERY":
                self.socket.sendto(data, address) # Echo back the data
                print(serverName.decode(Sender.MSG_ENCODING), "found at {} ...".format(address))
            ######################################################################################
        except KeyboardInterrupt:
            print(); exit()
        except socket.timeout:
            print("No service found")
            sys.exit(1)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def console_commands(self):
        if self.input_text == "scan":
            self.get_socket()
            self.receive_SD_message()
            self.socket.close()
        elif self.input_text[:7] == "connect":
            print("Connection received from {} ...".format("IP address/Port"))
        elif self.input_text == "llist":
            self.client_directory()
            print("Local File Sharing Directory", self.listDir)
        elif self.input_text == "rlist":
            self.get_socket2()
            self.connect_to_sender()
            self.connection_send("list") # Issue a "list" command
            self.connection_receive()
        elif self.input_text[:3] == "put":
            pass
        elif self.input_text[:3] == "get":
            pass
        elif self.input_text[:3] == "bye":
            print()
            print("Closing receiver connection ...")
            self.socket.close()
            sys.exit(1)
        else:
            print("Invalid command")

    ###############################################################################
    # TCP/IP Methods
    ###############################################################################

    def get_socket2(self):
        try:
            # Create an IPv4 TCP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connect_to_sender(self):
        try:
            # Connect to the server using its socket address tuple.
            self.socket.connect((Receiver.SERVER_HOSTNAME, Sender.PORT))
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connection_send(self, str_to_send):
        try:
            self.socket.sendall(str_to_send.encode(Sender.MSG_ENCODING))
            print("Sent:", str_to_send)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def connection_receive(self):
        try:
            recvd_bytes = self.socket.recv(Receiver.RECV_SIZE2)
            if len(recvd_bytes) == 0:
                print("Closing server connection ... ")
                self.socket.close()
                sys.exit(1)
            print("Received: ", recvd_bytes.decode(Server.MSG_ENCODING))
        except Exception as msg:
            print(msg)
            sys.exit(1)
    
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
    roles = {'receiver': Receiver,'sender': Sender}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles, 
                        help='sender or receiver role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()

########################################################################





