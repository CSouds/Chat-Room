######################################################################
# Connor Souders
# CMP_SC 4850
# client.py
# Date: 03/20/2026
# Program Description: This is the client for a simple chat room application for up to 3 users. It allows users to login, create new accounts, send messages, and logout. The client communicates with a server using TCP sockets.
######################################################################

import socket
import threading
import sys
import time
import os

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # setup TCP/IP socket
server_ip = "10.0.0.20" # localhost IP address
server_port = 12439 # 1 + last four student number

logged_in = False
looking = False
found = False

def receive_messages(sock): # multithreading function to run while getting input
    global logged_in, looking, found
    while True:
        try:
            response_data = sock.recv(1024) # get server data
            if(not response_data):
                os._exit(0)
            message = response_data.decode('utf-8').strip() # decode data
            if(not looking or ":" in message or "joins." in message or "left." in message): # filter message types
                print(message) # message for printing
            else:
                found = message # message for function
        except:
            break

def login(args):
    global logged_in, looking, found
    userPassword = args.split() # split arguments into userID and password
    if(len(userPassword) != 2): # check for argument formatting
        print("Denied. Invalid format.")
        return
    client_socket.sendall(f"login {args}".encode()) # send login command with arguments to server

    looking = "login"
    while(not found): # loop until receive info back from server
        time.sleep(0.05)

    print(found) # print message from server
    if(found == "login confirmed"): # check for successful login
        looking = False # reset variables
        found = False
        return True
    else:
        looking = False # reset variables
        found = False
        return False

def newuser(args):
    global logged_in, looking, found
    userPassword = args.split() # split arguments into userID and password
    if(len(userPassword) != 2): # check for argument formatting
        print("Invalid format.")
        return
    elif(len(userPassword[0]) < 3 or len(userPassword[0]) > 32): # check for userID length
        print("UserID must be 3 to 32 characters")
        return
    elif(len(userPassword[1]) < 4 or len(userPassword[1]) > 8): # check for password length
        print("Password must be 4 to 8 characters")
        return
    client_socket.sendall(f"newuser {args}".encode()) # send newuser command with arguments to server

    looking = "newuser" # loop while looking waiting on server
    while(not found):
        time.sleep(0.05)

    print(found) # print message from server
    looking = False
    found = False

def send(args):
    global logged_in

    targetMessage = args.split(" ", 1)
    if(len(targetMessage) != 2 or len(targetMessage[1]) < 1 or len(targetMessage[1]) > 256): # check for message length
        print("Message must be 1 to 256 characters.") # print error message and return if message length is invalid
        return

    client_socket.sendall(f"send {args}".encode()) # send send command with message to server

def who():
    global logged_in, looking, found

    client_socket.sendall("who".encode()) # send who command to server
    looking = "who"

    while(not found): # loop while waiting on server
        time.sleep(0.05)

    print(found)

    looking = False # reset variables
    found = False

def logout():
    global logged_in
    client_socket.sendall("logout".encode()) # send logout command to server

    time.sleep(0.1)
    client_socket.close() # close socket connection

    return False

def main():
    listener_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
    listener_thread.start()

    global logged_in, looking, found # variable to track if user is logged in for command permissions

    while True:
        try: commandArgs = input() # get command and arguments from user input
        except:
            print("Quit.")
            exit(0)
        if not commandArgs.strip(): # if no input, continue loop
            continue

        parts = commandArgs.split(" ", 1) # split command from arguments, max 1 split to preserve message formatting
        command = parts[0] # extract command
        args = parts[1] if len(parts) > 1 else "" # extract arguments if exist

        match command.lower(): # match command for execution
            case "login": # login user with provided userID and password
                if(logged_in == True): # check if user is already logged in for permission to login
                    print("Already logged in.")
                else:
                    logged_in = login(args) # call login and update logged_in status
            case "newuser":
                if(logged_in == True): # check if user is already logged in
                    print("Already logged in.")
                else:
                    newuser(args) # create new user account with provided userID and password
            case "send": # send message to server for distribution to other clients
                if(logged_in == True):
                    send(args) # call send to send message to server if logged in
                else:
                    print("Denied. Please login first.") # user not logged in, cannot send message
            case "who":
                if(logged_in):
                    who()
                else:
                    print("Denied. Please login first.")
            case "logout": # logout user and close connection
                if(logged_in):
                    logged_in = logout()
                    break
                else:
                    print("Denied. Please login first.") # user not logged in, cannot logout
            case _:
                print("Invalid command.") # no matching commmand

if __name__ == "__main__":
    try:
        client_socket.connect((server_ip, server_port)) # connect to server socket
    except:
        print("Server is offline. Exiting.")
        exit(1)
    print("My chat room client. Version Two.", end = "\n\n") # header

    main()