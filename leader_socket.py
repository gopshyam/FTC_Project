#! /usr/bin/env python

import socket
import random
import threading
import time
import aws_interface
import sys

RANDOM_NUMBER_RANGE = 100
SEQUENCE_LIMIT = 100
SLEEP_TIME = 10

DEFAULT_LISTENER_PORT = 4500
DEFAULT_REPLICA_PORT = 4501
SERVER_IP = ""

F = 1
if len(sys.argv) > 1:
    F = sys.argv[1]

replica_ips = {}
sequence_number = 0

port_list = range(5500, 5600)

shared_data = list()
for i in range(SEQUENCE_LIMIT + 1):
    shared_data.append(dict())


def listen_for_replicas():
    '''When a new replica wakes up or is added,
    it pings the server on this known port.
    The server keeps track of this IP address
    and uses it for future communications'''

    #create an INET, STREAMing socket
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    #bind the socket to a public host,
    # and a well-known port
    serversocket.bind((SERVER_IP, DEFAULT_LISTENER_PORT))

    print serversocket.getsockname()[1]

    serversocket.listen(5)
    
    with open('outf', 'w+') as of:
        of.write("Listening")

    #become a server socket
    while(True):
        (clientsocket, address) = serversocket.accept()
        print "CONNECTION RECEIVED"
        with open('outf', 'w+') as of:
            of.write("Connected!")

        print clientsocket, address
        x = clientsocket.recv(20)
        print x
        task_no = int(x.split(':')[-1].strip())
        clientsocket.send("WHATTUP YO OK")
        print address
        if address[0] not in replica_ips.keys():
            replica_ips[address[0]] = (address[1], task_no)


def send_message(ip, message, port):
    '''Sends a message to the replica whose ip is specified,
    and stores the response in a common data structure
    TODO: Locks'''
    replica_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    replica_socket.connect((ip, port))
    replica_socket.send(message)

    response = replica_socket.recv(20)

    #Parse the response
    r_split = response.split(':')
    seq_no = int(r_split[0].strip())
    content = int(r_split[1].strip())
    task_no = int(r_split[2].strip())

    shared_data[seq_no][task_no] = content

def find_agreed_value(response):
    value_list = list()
    for addr in response.keys():
        value_list.append(response[addr])

    agreed_value = max(set(value_list), key=value_list.count)
    return agreed_value

def server_worker():
    '''The server worker thread generates a random number,
    sends it to all the replicas, and aggregates the result
    Also detects faulty replicas and uses the AWS interface
    to get rid of them
    TODO: AWS interface, kill self
    '''
    global sequence_number, shared_data
    while(True):
        time.sleep(SLEEP_TIME)
        if (len(replica_ips.keys()) < 2*F + 1):
            continue

        message_content = random.randrange(RANDOM_NUMBER_RANGE)
        sequence_number = sequence_number % SEQUENCE_LIMIT + 1
        message = str(sequence_number) + ": " + str(message_content)
        thread_list = list()
        for ip in replica_ips.keys():
            t = threading.Thread(target = send_message, args=(ip, message, replica_ips[ip]))
            thread_list.append(t)
            t.start()

        for t in thread_list:
            t.join()

        #Aggregate the responses
        response = shared_data[sequence_number]
        shared_data[sequence_number] = dict()
        if len(response) == 0:
            print "SOMETHING GOT LOST ALONG THE WAY"
            continue
        agreed_value = find_agreed_value(response)
        print sequence_number, agreed_value

        for addr in response.keys():
            if response[addr] != agreed_value:
                for replica in replica_ips.keys():
                    if replica_ips[replica] == addr:
                        replica_ips[replica] = []
                print str(addr) + " IS FAULTY. EXTERMINATING"
                aws_interface.handle_fault(str(addr))


replica_listener_thread = threading.Thread(target = listen_for_replicas)
server_worker_thread = threading.Thread(target = server_worker)

replica_listener_thread.start()
server_worker_thread.start()

