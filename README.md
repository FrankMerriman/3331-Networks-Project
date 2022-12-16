# PythForum

## How to run
My source files `client.py` and `server.py` are written in python 3.7.3
### Server
To run the server, place `server.py` in an empty directory containing an empty file called "credentials.txt". From that directory, run the command: `python3 server.py port password`
(Substitute `port` and `password` for values of your liking)

### Client
To run the client, place `client.py` in an empty directory. Once you have started the server, from the client directory run the command: `python3 client.py 127.0.0.1 port`
(Substitute `port` for the value you entered when starting the server)


## Commands
### CRT: Create Thread

```
CRT threadtitle
```

Create a new thread with a given title. Titles can only be one word long.

### MSG: Post Message

```
MSG threadtitle message
```

Create a new message on a thread. Thread must already exist.

### DLT: Delete Message

```
DLT threadtitle messagenumber
```

Delete a message from a thread. Client must be original poster of message. Message numbers a cumulative across clients.

### EDT: Edit Message

```
EDT threadtitle messagenumber message
```

Overwrite a message on a thread. Client must be original poster of message.

### LST: List Threads

```
LST
```

List all existing threads.

### RDT: Read Thread

```
RDT threadtitle
```

See contents of a thread. Thread must already exist.

### UPD: Upload File

```
UPD threadtitle filename
```

Upload a file to a thread. Thread and file must exist. (*Files are sent in 1024 byte chunks, the two test files in the client diretory are for demoing this functionality*)

### DWN: Download File

```
DWN threadtitle filename
```

Download a file from a thread. Thread and file must exist.

### RMV: Remove Thread

```
RMV threadtitle
```

Delete a thread. Client must be creator of thread.

### XIT: Exit

```
XIT
```

Close clients TCP connection and disconnect from server safely.

### SHT: Shutdown

```
SHT admin_password
```

Send a signal forcing each client to close their TCP connection. Once clients are disconnected also wipes the server database (including all thread, uploaded files and credentials) before closing the program.
