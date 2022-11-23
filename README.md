# 3331-Networks-Project
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

### MSG: Post Message

```
MSG threadtitle message
```

### DLT: Delete Message

```
DLT threadtitle messagenumber
```

### EDT: Edit Message

```
EDT threadtitle messagenumber message
```

### LST: List Threads

```
LST
```

### RDT: Read Thread

```
RDT threadtitle
```

### UPD: Upload File

```
UPD threadtitle filename
```

### DWN: Download File

```
DWN threadtitle filename
```

### RMV: Remove Thread

```
RMV threadtitle
```

### XIT: Exit

```
XIT
```

### SHT: Shutdown

```
SHT admin_password
```
