import sys
import os
from socket import *
import threading
import json

def start_new_client():
    client_socket, _ = srvr_socket.accept()
    print("Client connected")
    thread = threading.Thread(target=manage_client, args=(client_socket,))
    thread.setDaemon(True)
    thread.start()

    #This stuff is new for SHT
    ping_socket, _ = srvr_socket.accept()
    thread = threading.Thread(target=SHT_sender, args=(ping_socket,))
    thread.setDaemon(True)
    thread.start()

def SHT_sender(ping_socket,):
    """
    Constantly tells the client the server is alive.
    The client tracks this on a 2nd thread know that
    when these messages stop the server is closed

    Params:
        ping_socket (socket): The socket of the client with which we
        exchange server status checks
    """
    while True:
        try:
            ping_socket.send("alive".encode())
        except:
            pass


def manage_client(client_socket,):
    """
    Handles the exchange of data betweeen the server
    and a connected client. Handles logon and command input

    Params:
        client_socket (socket): The socket of the newly connected client

    Returns:
        none
    """    
    logged_in = False
    

    lock.acquire()
    try:
        #Wait for client to send a username
        while logged_in == False:
            #It could be more efficent to open file outside of loop
            #but if logins were allowed to happen at same time
            #you would want to get a new set of credentials on each login
            credentials = open('credentials.txt', 'r')
            
            username = client_socket.recv(1024).decode()

            in_use = check_active_user(client_socket, username)

            if in_use == False:
                user_info = check_existing_user(client_socket, username, credentials)

                #These methods are for password stage of login
                if len(user_info) == 0:
                    client_socket.send('invaliduser'.encode())
                    logged_in = add_user(client_socket, username)
                else:
                    logged_in = validate_user(client_socket, username, user_info)
            
            credentials.close()
    finally:
        lock.release()
    
    #We error check syntax of commands on client end
    #So we only need to check if contents are valid not command type/length
    run_thread = True
    while run_thread == True:
        data = client_socket.recv(1024).decode()
        cmd_dict = json.loads(data)

        #Calling lock.acquire() should make command execution thread safe
        #Not sure if best to call outside of all, or individually though
        lock.acquire()

        try:
            print(cmd_dict["username"]+" issued "+cmd_dict["cmd"]+" command")
            if cmd_dict["cmd"] == "CRT":
                CRT(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "MSG":
                MSG(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "DLT":
                DLT(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "EDT":
                EDT(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "LST":
                LST(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "RDT":
                RDT(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "UPD":
                UPD(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "DWN":
                DWN(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "RMV":
                RMV(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "XIT":
                run_thread = XIT(client_socket, cmd_dict)
            elif cmd_dict["cmd"] == "SHT":
                SHT(client_socket, cmd_dict)
        finally:
            lock.release()



def check_active_user(client_socket, username):
    """
    Check online users to make sure not the currernt login is not
    already active

    Params:     username (str) of current login attempt
                client_socket (socket) socket of client

    Returns:    Boolean true/false if the user is/is not online
    """
    for user in active_users:
        if username == user:
            print(username + ' has already logged in')
            client_socket.send('online'.encode())
            return True

    return False


def check_existing_user(client_socket, username, credentials):
    """
    Check first word of each credential line for username

    Params:     username (str) of currrent login attempt
                credentials (textIO) file containing all user info
                client_socket (socket) socket of client

    Returns:    ln_lst (list[str]) which contains data matching current
                login attempt. It will be empty if no match is found
    """
    for line in credentials:
        ln_lst = line.split()

        if len(ln_lst) == 2 and username == ln_lst[0]:
            client_socket.send('validuser'.encode())
            return ln_lst

    return []


def add_user(client_socket, username):
    """
    For a new username, ask for a password from client
    of which the two are added to the credential database.
    The user is automatically logged in

    Params:     username (str) of the new account being made
                client_socket (socket) socket of client
    
    Returns:    True (boolean) to indicate user is logged in
    """
    #Wait for client to send password
    password = client_socket.recv(1024).decode()

    #Append to file
    credentials = open('credentials.txt', 'a')
    credentials.write(username + ' '  + password + '\n')
    credentials.close()

    #Inform client they are logged in
    active_users.append(username)
    print(username + ' successful login')
    client_socket.send('Logged in'.encode())

    return True


def validate_user(client_socket, username, credentials):
    """
    For an existing user who is not currently online, compare
    credentials recieved from client to correct details stored
    on server. Login client if info is correct

    Params:     username (str) of the client logging in
                credentials (list[str]) that the client is attempting to match
                client_socket (socket) socket of client

    Returns:    true/false (bool) if the client successfully/unsuccessfully
                logged in
    """
    #Wait for client to send password
    password = client_socket.recv(1024).decode()
    
    #Compare to given credentials
    if username == credentials[0] and password == credentials[1]:
        active_users.append(username)
        print(username + ' successful login')
        client_socket.send('correct'.encode())
        return True

    else:
        message = 'Incorrect password'
        print(message)
        client_socket.send(message.encode())
        return False




##############################################################################################
#Commands
##############################################################################################

#CRT: Create Thread
def CRT(client_socket, cmd_dict):
    """
    Creates a new file using threadtitle as name (dont add .txt).
    Sets the first line to be the username of creator. Sends a
    response to client if thread was created successfully or not.

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """
    forum = cmd_dict["threadtitle"]
    user = cmd_dict["username"]

            
    if check_threads(forum) == True:
        res = "Thread "+forum+" already exists."
        print(res)
        client_socket.send(res.encode())
        return

    new_thread = open(forum, 'w')
    new_thread.write(user + "\n")

    #add thread to active list and its count of actual messages
    #to the message_no dict
    active_threads.append(forum)
    thread_message_no.update({forum : 0})

    res = "Thread "+forum+" created"
    print(res)
    client_socket.send(res.encode())



#MSG: Post Message
def MSG(client_socket, cmd_dict):
    """
    Appends given message data to thread matching
    given name. Messages are stored as:

    line_number poster_name msg_contents

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """

    user = cmd_dict["username"]
    msg = cmd_dict["msg"]
    thread = cmd_dict["thread"]

    if check_threads(thread) == True:
        # we get the count of lines from our dict that tracks how many
        # MESSAGE (not including upload) lines there are
        # we also update this count to reflect our new line
        thread_message_no[thread] = thread_message_no[thread] + 1
        line_count = thread_message_no[thread]

        file = open(thread, "a")
        file.write(str(line_count)+" "+user+": "+msg+"\n")
        file.close()
        

        res = "Message added successfully"
        print(res)
        client_socket.send(res.encode())
    else:
        res = "No thread matching name "+thread+" was found"
        print(res)
        client_socket.send(res.encode())



#DLT: Delete Message
def DLT(client_socket, cmd_dict):
    """
    Removes specified message from a specified thread. Message can only
    be delted by the original poster. Updates the message
    number of all messages after deleted message. Sends
    error messages to client if thread is invalid, if number
    is invalid or if username wrong

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client

    Returns:    None
    """

    user = cmd_dict["username"]
    title = cmd_dict["thread"]
    num = cmd_dict["number"]

    #Check if thread exists
    if check_threads(title) == False:
        res = "Thread "+title+" not found"
        print(res)
        client_socket.send(res.encode())
        return
    
    #Check if message no is valid
    if thread_message_no[title] < int(num):
        res = "Message number outside length of thread "+title
        print(res)
        client_socket.send(res.encode())
        return
    
    #Check if user wrote the line
    if user_wrote_line(user, title, num) == False:
        print(user+" did not write this message. Deletion Cancelled")
        client_socket.send("Cancelled: You didn't write that line".encode())
        return
 
    #If we make it here we know user did write the line and it exists
    l1 = thread_message_no[title]
    l2 = l1 - 1

    input = open(title, "r")
    output = open("temp "+title, "w")

    name_line = True
    for line in input:
        curr = line.split()
        if name_line == True: 
            output.write(line)
            name_line = False
        else:
            #Write msg lines with a num from dict
            if curr[0] != num and curr[0].isdigit():
                ignore = len(curr[0])
                new_line = str(l1 - l2) + line[ignore:]
                output.write(new_line)
                l2 = l2 - 1
            #Write upd lines without affecting num
            elif curr[0] != num:
                output.write(line)

    #update new line count
    thread_message_no[title] = thread_message_no[title] - 1

    input.close()
    output.close()

    #rewrite from temp onto original and delete temp file
    with open("temp "+title, "r") as input:
        with open(title, "w") as output: 
            for line in input:
                output.write(line)
    
    os.remove("temp "+title)
    
    res = "Line "+num+" deleted from "+title
    print(res)
    client_socket.send(res.encode())



#EDT: Edit Message
def EDT(client_socket, cmd_dict):
    """
    Updates a given line in a given thread with clients
    new message, provided client matches username of
    original poster. Sends errors to client if thread
    is invalid, if number is invalid or if username wrong

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client

    Returns:    None
    """
    user = cmd_dict["username"]
    title = cmd_dict["thread"]
    num = cmd_dict["number"]
    msg = cmd_dict["msg"]

    
    if check_threads(title) == False:
        #thread not found
        res = "Thread "+title+" not found"
        print(res)
        client_socket.send(res.encode())
        return


    if thread_message_no[title] < int(num):
        res = "Message number outside length of thread "+title
        print(res)
        client_socket.send(res.encode())
        return
    
    #check if user wrote the line
    if user_wrote_line(user, title, num) == False:
        print(user+" did not write this message. Edit Cancelled")
        client_socket.send("Cancelled: You didn't write that line".encode())
        return

    #If we make it here we know user did write the line and it exists
    input = open(title, "r")
    output = open("temp "+title, "w")

    name_line = True
    for line in input:
        curr = line.split()
        if name_line == True: 
            output.write(line)
            name_line = False
        else:
            if curr[0] == num:
                keep = len(curr[0]) + len(curr[1]) + 2
                new_line = line[0:keep] + msg + "\n"
                output.write(new_line)
            else:
                output.write(line)

    input.close()
    output.close()

    #rewrite from temp onto original and delete temp file
    with open("temp "+title, "r") as input:
        with open(title, "w") as output: 
            for line in input:
                output.write(line)
    
    os.remove("temp "+title)
    
    res = "Line "+num+" edited in "+title
    print(res)
    client_socket.send(res.encode())



#LST: List Threads
def LST(client_socket, cmd_dict):
    """
    Creates a list of all threads that exist and
    sends it to the client. Sends a unique message
    if no threads yet exist

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """
    if len(active_threads) == 0:
        print("No threads found!")
        res = json.dumps(["There are no existing threads"])
        client_socket.send(res.encode())
    else:
        res = json.dumps(active_threads)
        client_socket.send(res.encode())



#RDT: Read Thread
def RDT(client_socket, cmd_dict):
    """
    Sends contents of a specified thread to client.
    Sends an error message if no thread was found.
    Doesn't send name of thread creator

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """
    user = cmd_dict["username"]
    title = cmd_dict["thread"]

    if check_threads(title) == False:
        #thread not found
        res = "Thread "+title+" not found"
        print(res)
        client_socket.send(res.encode())
        return

    
    with open(title, "r") as file:
        lines = file.readlines()
        #dont send first line
        lines.pop(0)

        #send to client how many lines they are receiving
        line_count = str(len(lines))
        client_socket.send(line_count.encode())
        #wait for a response from client so we dont
        #send data too quick messing up the file
        client_socket.recv(1024)

        #data = json.dumps(lines)
        for line in lines:
            client_socket.send(line.encode())
        

    
    print(title+" contents sent to "+user)



#UPD: Upload file
def UPD(client_socket, cmd_dict):
    """
    Takes in info from a client on a target thread
    to which a file should be uploaded. If thread exists
    append a message to that thread making record of
    the upload and ask client for file. If thread does
    not exist send an error.

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """
    user = cmd_dict["username"]
    title = cmd_dict["thread"]
    filename = cmd_dict["filename"]

    if check_threads(title) == False:
        res = "Thread "+title+" not found"
        print(res)
        client_socket.send(res.encode())
        return
    
    
    client_socket.send("all good".encode())

    #create new binary file and get ready to write
    with open(title+"-"+filename, "wb") as f:
        file_size = int(client_socket.recv(1024).decode())
        curr_size = 0
        while True:
            data = client_socket.recv(1024)
            f.write(data)
            curr_size = curr_size + len(data)

            if curr_size >= file_size:
                break
    
    with open(title, "a") as f:
        f.write(user+" uploaded "+filename+ "\n")

    print(user+" uploaded file "+filename+" to thread "+title)



#DWN: Download file
def DWN(client_socket, cmd_dict):
    """
    Sends the contents of a binary file to the client
    who requested it. The servers copy is not modified
    or deleted. Sends error messages if no file is found.
    First tells client size of file (if it does exist)

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """
    user = cmd_dict["username"]
    title = cmd_dict["thread"]
    filename = cmd_dict["filename"]

    if check_threads(title) == False:
        res = "Thread "+title+" not found"
        print(res)
        client_socket.send(res.encode())
        return

    target = title+'-'+filename
    found = False
    dir = os.getcwd()
    for file in os.listdir(dir):
        if file == target:
            found = True
            break
    
    if found == False:
        res = filename+" does not exist in thread "+title
        client_socket.send(res.encode)
        return
    

    client_socket.send("found".encode())
    #need to recv or it messes with following send
    client_socket.recv(1024)

    with open(title+"-"+filename, "rb") as f:
        #send file size to server
        file_size = str(os.path.getsize(title+"-"+filename))
        client_socket.send(file_size.encode())
        while True:
            data = f.read(1024)
            client_socket.send(data)
            if len(data) < 1024:
                break



#RMV: Remove Thread
def RMV(client_socket, cmd_dict):
    """
    Deltes a client-specified thread, its meta-data and
    any files uploaded to it. Only works if command
    was issued by user who created the thread

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """
    user = cmd_dict["username"]
    title = cmd_dict["thread"]

    if check_threads(title) == False:
        res = "Thread "+title+" not found"
        print(res)
        client_socket.send(res.encode())
        return

    with open(title, "r") as f:
        name = f.readline()
        #trim \n
        if name[:-1] != user:
            res = "Thread "+title+" not created by "+user
            print(res)
            client_socket.send(res.encode())
            return
    
    #Remove associate files + thread file
    dir = os.getcwd()
    for file in os.listdir(dir):
        if file.startswith(title):
            os.remove(file)

    #remove thread from active threads
    active_threads.remove(title)

    #remove thread from message count dict
    del thread_message_no[title]

    res = "Thread "+title+" has been deleted"
    print(res)
    client_socket.send(res.encode())
    


#XIT: Exit
def XIT(client_socket, cmd_dict):
    """
    The server removes the user from active users
    and stops the thread by exiting the loop

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client

    Returns:    False to indicate we want to end the thread
    """
    user = cmd_dict["username"]

    active_users.remove(user)
    print(user+" logged off")

    if len(active_users) == 0:
        print("Waiting for clients...")
    
    return False



#SHT: Shutdown
def SHT(client_socket, cmd_dict):
    """
    If correct password is supplied the server initiates
    shutdown, clearing all files except for server.py and sending
    a shutdown message to all clients, who then close their sockets

    Params:     cmd_dict (dict) which contains the
                information needed for processing the cmd

                client_socket (socket) socket of client
    """
    
    if cmd_dict["pwd"] == admin_passwd:
        print("Server shutting down")
        client_socket.send('correct'.encode())

        #socket closing here
        srvr_socket.close()

        #file removal here
        dir = os.getcwd()

        for file in os.listdir(dir):
            if file != "server.py":
                os.remove(file)

        #Exit code that means no error occurred.
        os._exit(os.EX_OK)

    else:
        client_socket.send('incorrect'.encode())
        print("Incorrect admin password")



def check_threads(title):
    """
    Helper function that checks if a thread exists

    Params:     title (str) name of thread

    Returns:    True/False if threads does/n't exist
    """
    for thread in active_threads:
        if thread == title:
            return True
    
    return False



def user_wrote_line(user, title, num):
    """
    Helper function that checks if a line was written
    by a given user. We were told not to worry
    about edge case where malicious user sets their
    name to a num

    Params:     title (str) name of thread
                user (str) name of user
                num (str) line number we are checking

    Returns:    True/False if user did/n't write the line
    """
    file = open(title, "r")
    for raw_line in file:
        line = raw_line.split(" ")
        if line[0] == num and line[1][:-1] != user:
            file.close()
            return False
        elif line[0] == num and line[1][:-1] == user:
            file.close()
            return True



###########################################################


#Server should take arguments server_port and admin_passwd
if __name__ == "__main__" and len(sys.argv) == 3:

    srvr_ip = '127.0.0.1'
    srvr_port = int(sys.argv[1])

    admin_passwd = str(sys.argv[2])
    active_users = []
    active_threads = []
    thread_message_no = {}

    srvr_socket = socket(AF_INET, SOCK_STREAM)

    lock = threading.Lock()
    

    #Bind socket and listen for connections
    srvr_socket.bind((srvr_ip, srvr_port))
    srvr_socket.listen(10)
    
    print("Waiting for clients...")

    while True:
        start_new_client()