#!/usr/bin/env python3

########################################################################

import socket
import argparse
import sys
import time

import os
import threading

########################################################################
# Broadcast Server class -- CLIENT
########################################################################

class Sender: # CLIENT

    HOSTNAME = socket.gethostname()
    HOST = socket.gethostbyname(socket.gethostname())

    # Send the broadcast packet periodically. Set the period
    # (seconds).
    BROADCAST_PERIOD = 1

    # Define the message to broadcast.
    MSG_ENCODING = "utf-8"
    MESSAGE =  "SERVICE DISCOVERY"
    MESSAGE_ENCODED = MESSAGE.encode('utf-8')

    # Use the broadcast-to-everyone IP address or a directed broadcast
    # address. Define a broadcast port.
    BROADCAST_ADDRESS = "255.255.255.255" # or e.g., "192.168.1.255"
    BROADCAST_PORT = 30000 # Service Discovery Port (SDP)
    ADDRESS_PORT = (BROADCAST_ADDRESS, BROADCAST_PORT)

    ACCEPT_TIMEOUT = 5 # (seconds)
    RECV_SIZE = 1024
    NUM_BROADCAST_PACKETS = 3 # Send 3 "SERVICE DISCOVERY" packets

    def __init__(self):
        self.get_console_input_forever()

    def get_console_input_forever(self):
        while True:
            try:
                self.get_console_input()
                self.console_commands()
            except (KeyboardInterrupt, EOFError):
                print()
                print("Closing CLIENT / SENDER connection ...")
                self.socket.close()
                sys.exit(1)

    def get_console_input(self):
        while True:
            self.input_text = input("Enter command: ")
            if self.input_text != '':
                break

    def console_commands(self):
        if self.input_text == "scan":
            self.create_sender_socket()
            self.send_broadcasts()
            self.get_console_input_forever()
        elif self.input_text[:7] == "connect":
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
            print("Connection received from {} ...".format((IP_addr, port)))
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
            print("Closing CLIENT / SENDER connection ...")
            self.socket.close()
            sys.exit(1)
        else:
            print("Invalid command")

    def client_directory(self):
        os.chdir("clientDirectory")
        self.listDir = os.listdir(os.getcwd())
        os.chdir("..")
        
    ###############################################################################
    # UDP Methods
    ###############################################################################

    def create_sender_socket(self):
        try:
            # Set up a UDP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Set the option for broadcasting.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # To get the response from SERVER / RECEIVER?
            self.socket.bind((Sender.HOST, Sender.BROADCAST_PORT)) 
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def send_broadcasts(self):
        try:
            self.socket.settimeout(Sender.ACCEPT_TIMEOUT)
            for i in range(Sender.NUM_BROADCAST_PACKETS):
                print("Sending to {} ...".format(Sender.ADDRESS_PORT), self.socket.gettimeout())
                self.socket.sendto(Sender.MESSAGE_ENCODED, Sender.ADDRESS_PORT)
                # Response from SERVER / RECEIVER
                data, address = self.socket.recvfrom(Sender.RECV_SIZE)
                time.sleep(Sender.BROADCAST_PERIOD)
                if data.decode(Sender.MSG_ENCODING) == "ACK":
                    print("Response from Server: {}".format(data.decode(Sender.MSG_ENCODING)))
                    break
        except socket.timeout:
            print("No service found")
        except KeyboardInterrupt:
            print()
            print("Closing CLIENT / SENDER connection ...")
        except Exception as msg:
            print(msg)
        finally:
            self.socket.close()
            sys.exit(1)

    ###############################################################################
    # TCP/IP Methods
    ###############################################################################

########################################################################
# Echo Receiver class -- SERVER
########################################################################

class Receiver: # SERVER

    RECV_SIZE = 256

    HOST = "0.0.0.0"
    ADDRESS_PORT = (HOST, Sender.BROADCAST_PORT)

    def __init__(self):
        self.get_socket()
        self.receive_SDP()

    def get_socket(self):
        try:
            # Create an IPv4 UDP socket.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Bind to all interfaces and the agreed on broadcast port.
            self.socket.bind(Receiver.ADDRESS_PORT)
        except Exception as msg:
            print(msg)
            sys.exit(1)

    def receive_SDP(self):
        print("Listening for service discovery messages on SDP {} ...".format(Receiver.ADDRESS_PORT))
        while True:
            try:
                data, address = self.socket.recvfrom(Receiver.RECV_SIZE)
                if data.decode(Sender.MSG_ENCODING) == "SERVICE DISCOVERY":
                    self.socket.sendto("ACK".encode(Sender.MSG_ENCODING), address) # Echo back the data

                #print("Broadcast received: ", data.decode(Sender.MSG_ENCODING), address)
            except KeyboardInterrupt:
                print()
            except Exception as msg:
                print(msg)
                sys.exit(1)

    ###############################################################################
    # TCP/IP Methods
    ###############################################################################

##    def create_listen_socket(self):
##        print("-" * 72)
##        try:
##            # Create an IPv4 TCP socket.
##            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##
##            # Get socket layer socket options.
##            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
##
##            # Bind socket to socket address, i.e., IP address and port.
##            self.socket.bind( (Server.HOSTNAME, Server.PORT) )
##
##            # Set socket to listen state.
##            self.socket.listen(Server.BACKLOG)
##            print("Listening for file sharing connections on {} ...".format(Server.PORT))
##        except Exception as msg:
##            print(msg)
##            sys.exit(1)
##
##    def process_connections(self):
##        try:
##            self.connection_handler(self.socket.accept())
##        except Exception as msg:
##            print(msg)
##        except KeyboardInterrupt:
##            print()
##            print("Closing sender connection ...")
##        finally:
##            self.socket.close()
##            sys.exit(1)
##
##    def connection_handler(self, client):
##        connection, address_port = client
##        print("-" * 72)
##        print("Listening for file sharing connections on port {}.".format(address_port))
##        while True:
##            try:
##                recvd_bytes = connection.recv(Server.RECV_SIZE)
##                if len(recvd_bytes) == 0:
##                    print("Closing sender connection ... ")
##                    connection.close()
##                    break
##                recvd_str = recvd_bytes.decode(Server.MSG_ENCODING)
##                print("Received: ", recvd_str)
##
##                
##                self.client_to_server_cmds(recvd_str, client)
##
##                
##                connection.sendall(self.str_to_send.encode(MSG_ENCODING))
##                print("Sent: ", self.str_to_send)
##            except KeyboardInterrupt:
##                print()
##                print("Closing sender connection ... ")
##                connection.close()
##                break

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





