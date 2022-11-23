import sys
import os
from socket import *
import json
import threading
import select


def create_user():
    """
    For a username not recognised by the server
    prompts the user to set a new password for the account

    Returns:    True to indicate successful completion of signup process
                False if something goes wrong on server end (We can assume it never will however)

    """
    password = input('Enter a new password: ')
    client_socket.send(password.encode())
    response = client_socket.recv(1024).decode()

    if response != 'Logged in':
        return False
    else:
        print('Welcome to the forum')
        return True


def login_user():
    """
    Attempts to login to server via an existing account.
    Prompts user for password, giving a relevant error message if
    password is wrong or someone is already using the account

    Returns:    True if sign-in is successful
                False if password is wrong

    """
    password = input('Enter password: ')
    client_socket.send(password.encode())

    #Wait for response from server on whether password correct or not
    response = client_socket.recv(1024).decode()

    if response != 'correct':
        print(response)
        return False

    print('Welcome to the forum')
    return True


def CRT():
    """
    Client end code for using the create thread
    (CRT) command. Prints an error if wrong argument count
    supplied
    """
    if len(command) != 2:
        print("Incorrect syntax for CRT")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "threadtitle" : command[1]
        }
        
        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        res = client_socket.recv(1024).decode()
        print(res)


def MSG():
    """
    Client end code for using the message (MSG)
    command. Prints an errror if wrong arg count given
    """
    if len(command) < 3:
        print("Incorrect syntax for MSG")
    else:

        #cut off start of string
        ignore = len(command[0]) + len(command[1]) + 2
        msg = raw_command[ignore:]

        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "thread" : command[1],
            "msg" : msg
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        res = client_socket.recv(1024).decode()
        print(res)


def DLT():
    """
    Client end code for using message delete (DLT)
    command. Prints errors if invalid arg count, invalid
    access privilidges or invalid thread title
    """
    if len (command) != 3:
        print("Incorrect syntax for DLT")
    elif command[2].isdigit() == False:
        print("Line number must be supplied as a (positive) numeric")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "thread" : command[1],
            "number" : command[2]
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        res = client_socket.recv(1024).decode()
        print(res)


def EDT():
    """
    Client end code for using message edit (EDT)
    command. Prints errors if invalid arg count, invalid
    access privilidges or invalid thread title
    """
    if len(command) < 4:
        print("Incorrect syntax for EDT")
    elif command[2].isdigit() == False:
        print("Line number must be supplied as a (positive) numeric")
    else:
        ignore = len(command[0]) + len(command[1]) + len(command[2]) + 3
        msg = raw_command[ignore:]

        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "thread" : command[1],
            "number" : command[2],
            "msg" : msg
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        res = client_socket.recv(1024).decode()
        print(res)


def LST():
    """
    Client end code for using the list thread (LST) command.
    Prints an error if too many args given, otherwise prints
    all threads
    """

    if len(command) != 1:
        print("Incorrect syntax for LST")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0]
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        data = client_socket.recv(1024).decode()
        threads = json.loads(data)
        threads.sort()
        
        for title in threads:
            print(title)
    

def RDT():
    """
    Client side code for read thread (RDT) command.
    Prints an error if no thread is found matching description
    """
    
    if len(command) != 2:
        print("Incorrect syntax for RDT")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "thread" : command[1]
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        #need to fix getting error message
        res = client_socket.recv(1024).decode()

        if res.isdigit() == False:
            print(res)
        else:
            line_count = int(res)
            client_socket.send("got".encode())
            curr_count = 0
            
            while curr_count < line_count:
                line = client_socket.recv(1024).decode()
                print(line[:-1])
                curr_count = curr_count + 1

            
def UPD():
    """
    Client end code for the upload file (UPD) command
    we can assume file is in our client directory. The
    server gives an error if the targeted thread for upload
    does not exist. We are allowed to assume no duplicate files
    will be uploaded
    """
    if len(command) != 3:
        print("Incorrect sytanx for UPD")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "thread" : command[1],
            "filename" : command[2]
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        #This will tell us whether we should send file
        res = client_socket.recv(1024).decode()

        if res != "all good":
            print(res)
        else:
            with open(command[2], "rb") as f:
                #send file size to server
                file_size = str(os.path.getsize(command[2]))
                client_socket.send(file_size.encode())
                while True:
                    data = f.read(1024)
                    client_socket.send(data)
                    if len(data) < 1024:
                        break
            
            print(cmd_dict["filename"]+" uploaded to thread "+ cmd_dict["thread"])


def DWN():
    """
    Client end code for handling the download file (DWN)
    command. If the file is found and no error messages are
    received, file contents are sent in 1kb chunks and written
    to a new binary file in the clients directory
    """
    if len(command) != 3:
        print("Incorrect sytanx for DWN")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "thread" : command[1],
            "filename" : command[2]
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        #This will tell us whether we will get the file
        res = client_socket.recv(1024).decode()
        if res == 'found':
            client_socket.send("waiting".encode())
            with open(cmd_dict["filename"], "wb") as f:
                file_size = int(client_socket.recv(1024).decode())
                curr_size = 0
                while True:
                    data = client_socket.recv(1024)
                    f.write(data)
                    curr_size = curr_size + len(data)
                    if curr_size >= file_size:
                        break

            print(cmd_dict["filename"]+" downloaded from thread "+ cmd_dict["thread"])
        else:
            print(res)

def RMV():
    """
    Client end code for remove thread (RMV) command.
    Client sends the name of a thread they wish to delete
    and if the client was the creator of said thread, the
    server deletes it
    """
    if len(command) != 2:
        print("Incorrect syntax for XIT")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "thread" : command[1]
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        res = client_socket.recv(1024).decode()
        print(res)


def XIT():
    """
    Client end code for using the exit (XIT) command.
    Prints an error and cancels the command if incorrect amount
    of arguments have been supplied
    """

    if len(command) != 1:
        print("Incorrect syntax for XIT")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0]
        }

        data = json.dumps(cmd_dict)
        client_socket.send(data.encode())

        client_socket.close()
        ping_socket.close()
        print("Goodbye!")
        os._exit(os.EX_OK)


def SHT():
    """
    Client end code for using the shutdown (SHT) command.
    Prints an error if admin password is wrong
    """
    if len(command) != 2:
        print("Incorrect syntax for SHT")
    else:
        cmd_dict = {
            "username" : username,
            "cmd" : command[0],
            "pwd" : command[1]
        }

        
        data = json.dumps(cmd_dict)

        client_socket.send(data.encode())

        response = client_socket.recv(1024).decode()

        if response == 'incorrect':
            print("Incorrect admin password. Shutdown cancelled.")


def SHT_receiver():
    """
    Runs on its own thread, constantly polling the
    server port to check if the server is still running
    """
    # poller_obj = select.poll()
    # poller_obj.register(ping_socket, select.POLLOUT)
    
    while True:
        # poll_results = poller_obj.poll()
        # print(len(poll_results))
        res = ping_socket.recv(1024).decode()

        if res == "":
            ping_socket.close()
            client_socket.close()
            print("\nServer is shutting down! Goodbye!")
            os._exit(os.EX_OK)



if __name__ == "__main__" and len(sys.argv) == 3:

    #Client should take arguments server_IP and server_port as command line args
    srvr_ip = str(sys.argv[1])
    srvr_port = int(sys.argv[2])
    client_socket = socket(AF_INET, SOCK_STREAM)
    ping_socket = socket(AF_INET, SOCK_STREAM)


    #Client should attempt to setup TCP connection with server
    try:
        client_socket.connect((srvr_ip, srvr_port))
        
        #set up monitoring thread
        ping_socket.connect((srvr_ip, srvr_port))
        sht_thread = threading.Thread(target=SHT_receiver)
        sht_thread.setDaemon(True)
        sht_thread.start()

    except:
        print(f'Failed to connect to {srvr_ip} on port {srvr_port}')
        exit(1)
    

    #Prompt user for username. Send input to server
    #Then wait for server to send response
    login_status = False
    username = ''

    while login_status == False:
        username = input('Enter Username: ')
        client_socket.send(username.encode())
        response = client_socket.recv(1024).decode()

        if response == 'online':
            print(username + ' has already logged in')
            
        elif response == 'invaliduser':
            login_status = create_user()
        else:
            login_status = login_user()

    #on login display message showing avaliable commands
    #and ask user for selection
    while True:
        raw_command = input('Enter one of the following commands: CRT,  MSG,  DLT, EDT,  LST, RDT,  UPD,  DWN, RMV, XIT, SHT: ')
        command = raw_command.split(" ")

        if len(command) == 0:
            print("No command entered!")
        elif command[0] == 'CRT':
            CRT()
        elif command[0] == 'XIT':
            XIT()
        elif command[0] == 'SHT':
            SHT()
        elif command[0] == "MSG":
            MSG()
        elif command[0] == "DLT":
            DLT()
        elif command[0] == "EDT":
            EDT()
        elif command[0] == "LST":
            LST()
        elif command[0] == "RDT":
            RDT()
        elif command[0] == "UPD":
            UPD()
        elif command[0] == "DWN":
            DWN()
        elif command[0] == "RMV":
            RMV()
        else:
            print("Invalid command")
