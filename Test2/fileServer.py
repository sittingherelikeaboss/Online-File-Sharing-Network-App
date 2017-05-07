# THIS IS THE SERVER

import socket
import threading
import os

def RetrFile(name, socket):
    filename = socket.recv(1024)
    if os.path.isfile(filename):
        socket.send("EXISTS " + str(os.path.getsize(filename)))
        userResponse = socket.recv(1024)
        if userResponse[:2] == 'OK':
            with open(filename, 'rb') as f:
                bytesToSend = f.read(1024)
                socket.send(bytesToSend)
                while bytesToSend != "":
                    bytesToSend = f.read(1024)
                    socket.send(bytesToSend)
    else:
        socket.send("ERR")

    socket.close()

def Main():
    host = "255.255.255.255"
    port = 5000

    s = socket.socket()
    s.bind((host, port))

    s.listen(5)

    print("Server started")

    while True:
        c, addr = s.accept()
        print("Client connected ip:<", addr, ">")
        t = threading.Thread(target = RetrFile, args = ("retrThread", c))
        t.start()

    s.close()

if __name__ == '__main__':
    Main()
