# Socket Programming Assignment
# Server.py
# Author: Sameer Abdullah
# Email: abdu5039@mylaurier.ca
#
# Description:
# TCP server that supports up to 3 clients at once using multithreading.
# Handles client messages, tracks connections and disconnections,
# lists available files, and allows clients to download files.


# Imports
import socket
import threading
from datetime import datetime
import os


# Global Variables
num_clients_active = 0    # Track number of clients active at once (Max of 3)
num_clients_total = 0     # Tracks the total connections made to the server
client_lock = threading.Lock()   # Prevents multiple threads from changing shared client data at the same time

client_cache = {}               # Used to store each clients information

# Sends messages to the client with the message type and length
def SendMessage(client_socket, response, message_type = "MSG"):
    if isinstance(response, bytes) == True:
        encoded_response = response
    else:
        encoded_response = response.encode()

    encoded_response_len = len(encoded_response)
    header = message_type + " " + str(encoded_response_len) + "\n"
    header = header.encode()
    client_socket.sendall(header + encoded_response)


# Opens the requested file and prepares it to be sent to the client
def FileRequest(decoded_data):
    file = open(decoded_data, "rb")           # opens file
    file_contents = file.read()               # reads file
    file_name = decoded_data.encode()
    file_payload = file_name + b"\n" + file_contents
    file.close()
    return file_payload


# Handles client messages, commands, and disconnections
def HandleClient(client_socket, client_name):
    global num_clients_active
    
    client_reader = None


    try:
        SendMessage(client_socket, client_name)  
        client_reader = client_socket.makefile("rb")                      # Creates a file like reader for the client socket
        data = client_reader.readline()                                   # Reads the client's initial message
        print("Client Name:", data.decode().strip())
        SendMessage(client_socket, "Connected to Server!")


        file_selection = False


        while True:
            data = client_reader.readline()
            
            if not data:                                                # Breaks if the client disconnects
                break     
            decoded_data = data.decode().strip()                        # Converts received bytes into a string

            if decoded_data == "exit" or decoded_data == "Exit":     # checks if client wants to exit 
                response = "exit ACK"
                SendMessage(client_socket, response, message_type = "MSG")
                break 
            elif decoded_data == "status" or decoded_data == "Status":
                with client_lock:
                    response = str(client_cache)
            elif decoded_data == "list" or decoded_data == "List":
                response = str(os.listdir(".")) 
                file_selection = True
            elif (os.path.isfile(decoded_data) == True) and (file_selection == True):       # checks if the entered file exists
                file_payload = FileRequest(decoded_data)
                file_selection = False
                SendMessage(client_socket, file_payload, message_type = "FILE")
                continue
            elif file_selection == True:
                response = "File Not found"
                file_selection = False
                SendMessage(client_socket, response ,message_type = "ERR")
                continue
            else:
                response = decoded_data + " ACK"           

        

            print("Received: ", decoded_data)
            print(response)
            SendMessage(client_socket, response)  

    finally:
        with client_lock:
            num_clients_active -= 1         # keeps  track of exiting clients
            client_cache[client_name]["Disconnected"]= datetime.now() 
        if client_reader != None:
            client_reader.close()    
        client_socket.close()

        

# Starts the server, accepts clients, and uses threads to handle multiple clients
def main():
    global num_clients_total, num_clients_active
    
    # Creates a TCP socket and stores it in server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    # Assigns IP address and Port 5000
    server.bind(("127.0.0.1", 5000))


    server.listen()
    print("Server is Online...")

    while True:
        client_socket, client_address = server.accept()         # Accepts new clients
        print("Client Address: ", client_address)
        num_clients_total += 1                                   # keeps count of number of clients
        client_name = "Client" + str(num_clients_total).zfill(2)                                  


        # Uses a lock to limit active connections to 3 clients
        with client_lock:
            if num_clients_active >= 3:
                server_full = True
            else:
                server_full = False
                num_clients_active += 1

         # sends client server full message      
        if server_full:                       
            server_capacity = "Server currently at full capacity"
            SendMessage(client_socket, server_capacity, "ERR")
            print("Currently at full capacity")
            client_socket.close()           # Closes the rejected client's connection
        else:                                # allows client 
            thread = threading.Thread(target = HandleClient , args=(client_socket, client_name))    # Creates a separate thread to handle each client
            with client_lock:
                client_cache[client_name] = {
                    "Connected": datetime.now(),
                    "Disconnected": None
                }
            thread.start()

        

if __name__ == "__main__":
    main()
