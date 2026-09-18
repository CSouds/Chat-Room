######################################################################
# Connor Souders
# CMP_SC 4850
# server.py
# Date: 03/20/2026
# Program Description: This is the server for a simple chat room application for up to 3 users. It handles user authentication, message broadcasting, and connection management. The server communicates with clients using TCP sockets.
######################################################################

import os
import socket
import threading

MAXCLIENTS = 3 # max users
active_users = {} # maintain active users globally
lock = threading.Lock() # multithreading lock to prevent data confusions

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # setup TCP/IP socket
server_ip = "0.0.0.0" # localhost IP address
server_port = 12439 # 1 + last four student number

users_db = {} # dictionary to store userID and password pairs for authentication
def load_users(): # Only load if it exists; do not create it here.
    if(os.path.exists("users.txt")):
        with open("users.txt", "r") as f:
            for line in f:
                clean_line = line.strip().strip('()') # clean line by stripping whitespace and parentheses
                parts = clean_line.split(',', 1) # split into userID and password
                if(len(parts) == 2): # check for proper formatting of line
                    current_id = parts[0].strip() # extract id
                    current_password = parts[1].strip() # extract password
                    users_db[current_id] = current_password # add userID and password to in-memory database

def login(conn, userID, password):
    global active_users
    if(userID in users_db and users_db[userID] == password): # check for user and password in database
        with lock:
            if(userID in active_users): # check if user already logged in
                try: conn.sendall("Denied. User already logged in.".encode())
                except: print("Client error.")
                return False

            active_users[userID] = conn # add connection to database

            try:
                conn.sendall(f"login confirmed".encode()) # success
                for user in active_users.values(): # iterate through connections
                    if(user == conn): continue # skip current user
                    user.sendall(f"{userID} joins.".encode())
            except:
                print("Client error.")
            print(f"{userID} login.") # print login message to server
            return userID # return userID for tracking logged in user
        
    try: conn.sendall("Denied. User name or password incorrect.".encode()) # incorrect credentials
    except: print("Client error.")
    return False # not logged in

def newuser(conn, userID, password):
    if userID in users_db: # userID already exists
        try: conn.sendall(f"Denied. User account already exists.".encode()) # failed to create
        except: print("Client error.")
        return
    
    users_db[userID] = password # add to databse
    
    with open("users.txt", "a") as f: # add user to file for persistence
        f.write(f"({userID}, {password})\n")
    print("New user account created") # print new user created
    try: conn.sendall(f"New user account created. Please login.".encode()) # send confirmationto client
    except: print("Client error.")

def sendall(conn, userID, message): # send message to client
    with lock:
        global active_users
        print(f"{userID}: {message}") # print message to server console
        try:
            for user in active_users.values(): # iterate through all users
                if(user != conn):
                    user.sendall(f"{userID}: {message}".encode()) # send message to clients except sender
        except: print("Client error.")

def senduser(conn, userID, userTo, message):
    with lock:
        global active_users
        if userTo in active_users: # Check if the user is actually online!
            print(f"{userID} (to {userTo}): {message}")
            try:
                active_users[userTo].sendall(f"{userID}: {message}".encode()) # send message to recipient and no one else
            except:
                print("Client error.")
        else:
            try:
                conn.sendall(f"User {userTo} is not logged in.".encode()) # error for receiver not being logged in
            except:
                print("Client error.")

def who(conn):
    with lock:
        try: 
            user_string = ", ".join(sorted(active_users.keys())) # sort all logged in users for printing
            conn.sendall(user_string.encode())
        except: print("Client error.")

def logout(conn, userID): # logout user and close connection
    with lock:
        if(userID in active_users): # delete user from db
            del active_users[userID]

        for user in active_users.values(): # broadcast logout message
            try: user.sendall(f"{userID} left.".encode())
            except: print("Client error.")
    
    try: conn.close()
    except: print("Client error")
    print(f"{userID} logout.") # print logout message

def handle_client(conn):
    logged_in_user = False # variable to track if user is logged in for command permissions

    while(True):
        try:
            data = conn.recv(1024) 
            if not data: break 
        except:
            print("Client disconnected unexpectedly.")
            if(logged_in_user):
                logout(conn, logged_in_user) # cleanup dangling users
            return False
        
        message = data.decode("utf-8") # decode message from client

        commandArgs = message # command + arguments in message

        parts = commandArgs.split(" ", 1) # split command from arguments
        command = parts[0] # extract command
        args = parts[1] if len(parts) > 1 else "" # extract arguments if exist

        match command.lower(): # match command for execution
            case "login":
                userAuth = args.split() # split arguments into userID and password
                if(len(userAuth) == 2): # check for proper arguments
                    logged_in_user = login(conn, userAuth[0], userAuth[1]) # call login
                else:
                    try: conn.sendall("Denied. Invalid format.".encode()) # invalid argument format
                    except: print("Client error.")
            case "newuser":
                userAuth = args.split() # split arguments into userID and password
                if(len(userAuth) == 2): # check for proper arguments
                    newuser(conn, userAuth[0], userAuth[1]) # create new user
                else:
                    try: conn.sendall("Denied. Invalid format.".encode()) # invalid argument format
                    except: print("Client error.")
            case "send":
                if(logged_in_user != False): # check for logged in
                    targetMessage = args.split(" ", 1) # split target and arguments
                    if(len(targetMessage) == 2):
                        target = targetMessage[0]
                        message = targetMessage[1] # Store in 'message' to avoid overwriting 'args'
                        
                        if(target == "all"): # check what type of send
                            sendall(conn, logged_in_user, message)
                        else:
                            senduser(conn, logged_in_user, target, message)
                    else:
                        try: conn.sendall("Denied. Invalid format.".encode()) # wrong targeting format
                        except: print("Client error.")
                else:
                    try: conn.sendall("Denied. Please login first.".encode()) 
                    except: print("Client error.")
            case "logout": # logout user and close connection
                if(logged_in_user != False): # check if user is logged in for permission to logout
                    break
                else:
                    try: conn.sendall("Denied. Please login first.".encode()) # user not logged in, cannot logout
                    except: print("Client error.")
            case "who": # who case for printing all users
                if(logged_in_user != False):
                    who(conn)
                else:
                    try: conn.sendall("Denied. Please login first.".encode())
                    except: print("Client error.")
            case _:
                try: conn.sendall("Invalid command.".encode()) # no matching command
                except: print("Client error.")

    if(logged_in_user): # handles user logout when exiting
        logout(conn, logged_in_user)

    return True

def main():
    server_socket.listen(5)
    print("My chat room server. Version Two.", end = "\n\n") # header

    while True: # constantly check for new users
        try: conn, addr = server_socket.accept() # create connection
        except KeyboardInterrupt: exit(0) # allow keyboard interupt for quit
        except Exception: continue # other errors continue

        with lock:
            if(len(active_users) >= MAXCLIENTS): # verify server capacity
                conn.sendall("Denied. Server is full.".encode())
                conn.close()
                continue
        client_thread = threading.Thread(target=handle_client, args=(conn,)) # create thread for each client
        client_thread.start()

if __name__ == "__main__":
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # set up socket
    
    server_socket.bind((server_ip, server_port))
    load_users() # load users.txt
    
    main()