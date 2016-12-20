#! /usr/bin/env python

import socket
import threading
import random
import sys

task_no = 1
if len(sys.argv) > 1:
    task_no = sys.argv[1]

RAND_RANGE = 10

DEFAULT_SERVER_PORT = 4500
DEFAULT_CLIENT_PORT = 4501
LEADER_IP = "10.0.1.216"

def process(message):
    rand_var = random.randrange(RAND_RANGE)
    if (rand_var == 1):
        message = message + '1'
    return message + ':' + str(task_no)

def start_listener():
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener_socket.bind(('', DEFAULT_CLIENT_PORT))

    listener_socket.listen(5)

    #Listen for the leader's message and then respond when a request arrives.
    while(True):
        (leader_socket, address) = listener_socket.accept()
        message = leader_socket.recv(20)
        print message
        response = process(message)
        leader_socket.send(response)


def contact_leader():
    #Contact the leader
    #open up a socket that listens for the servers welcome message, and then contact the server once that's done
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((LEADER_IP, DEFAULT_SERVER_PORT))

    x = clientsocket.send("HELLO THERE:" + task_no) 
    print x
    y = clientsocket.recv(20)
    print y

    if 'OK' not in y:
        print "Something wrong"

#When the machine first wakes up, start the listener, then contact the leader
listener_thread = threading.Thread(target = start_listener)
listener_thread.start()

contact_leader()
