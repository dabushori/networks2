import socket
import sys
import os

# types of codes
CODE_ERROR = '404'
CODE_SUCCESS = '200'
CODE_REDIRECT = '301'

# the information of the codes
REDIRECT_INFO = 'Moved Permanently'
ERROR_INFO = 'Not Found'
SUCCESS_INFO = 'OK'

# line of the redirect
REDIRECT_LOCATION = 'Location: /result.html\n'

# end of the command
END_OF_COMMAND = '\r\n\r\n'

# the constant HTTP format for all the writing
HTTP_CONST = 'HTTP/1.1'

# type of connections
CLOSE_CONNECTION = 'close'
KEEP_CONECTION = 'keep-alive'

# socket info
BUFFER_SIZE = 1024
TIMEOUT = 1.0

# the port that the server is binding to
serverPort = int(sys.argv[1])

# method: THis method is checking if the info that the client
# entered is valid or not
#
# input - the input is a list of words that the client entered


def checkInput(input):
    if len(input) < 4:
        return False

    if input[0] != 'GET':
        return False

    if input[2] != HTTP_CONST:
        return False

    return True

# method: This method is searching in the input if the client is staying
# for another command or not
#
# input - the input argument is a list of words that the client entered.


def findConnection(input):
    # The connection can only start from index 4
    # because the rest is the command
    index = 0
    for word in input:

        if word == 'Connection:':
            if input[index + 1] == CLOSE_CONNECTION:
                return CLOSE_CONNECTION
            if input[index + 1] == KEEP_CONECTION:
                return KEEP_CONECTION

        index = index + 1

    return CLOSE_CONNECTION

# method - This method is sending the format message to the client
# according to the code of the command
#
# input - socket of the client, code of the command, next connection
# and length of the file in bytes


def sendMessage(clientSocket, code, connection, length):
    message = [HTTP_CONST, 'Connection: ']
    if code == CODE_ERROR:
        message[0] = message[0] + ' ' + CODE_ERROR + ' ' + ERROR_INFO + '\n'
        message[1] = message[1] + connection + '\n'
    elif code == CODE_REDIRECT:
        message[0] = message[0] + ' ' + \
            CODE_REDIRECT + ' ' + REDIRECT_INFO + '\n'
        message[1] = message[1] + connection + '\n'
        message.append(REDIRECT_LOCATION)
    elif code == CODE_SUCCESS:
        message[0] = message[0] + ' ' + \
            CODE_SUCCESS + ' ' + SUCCESS_INFO + '\n'
        message[1] = message[1] + connection + '\n'
        message.append('Content-Length: ' + str(length) + '\n')
    message.append('\r\n')
    clientSocket.send(''.join(message).encode())

# method - This method is reciving data from the client until '\r\n\r\n' is recived. it also uses the given total data
# in case that there was a message left after the last time the client sent info.
#
# input - socket of the client, and the total-data from the last time the client sent data


def getCurrentRequest(socket, totalData):
    if totalData == '' or totalData.find(END_OF_COMMAND) == -1:
        recived = socket.recv(BUFFER_SIZE).decode()
        if recived == '':
            return ''
        totalData = totalData + recived
    try:
        index = totalData.index(END_OF_COMMAND)
        curr = totalData[0:index]
        index = index + len(END_OF_COMMAND)
        totalData = totalData[index:]
        return curr, totalData
    except ValueError:
        return getCurrentRequest(socket, totalData)

# method - This method is closing the socket and retrning an empty string which will be assigned to the totalData variable
#
# input - socket of the client


def closeSocket(socket):
    socket.close()
    return ''


# opening the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', serverPort))
server.listen(1)
# this boolian will check if we need to connect to a new client after a command
nextClient = True
totalData = ''

while True:
    if nextClient:
        clientSocket, clientAddress = server.accept()
    try:
        # this will give the client 1 second to write his command
        clientSocket.settimeout(TIMEOUT)
        data, totalData = getCurrentRequest(clientSocket, totalData)
    except:
        # case of client not sending anything
        totalData = closeSocket(clientSocket)
        nextClient = True
        continue
    # print the recived command
    print(data, end='\n\n')
    # checking if the data is empty
    if len(data) <= 1:
        totalData = closeSocket(clientSocket)
        nextClient = True
        continue
    input = data.split()
    # check that the inputs are valid
    if not checkInput(input):
        totalData = closeSocket(clientSocket)
        nextClient = True
        continue
    get = input[0]
    fileUrl = None
    http = input[2]
    # if the url is a / we want it to be index.html
    if input[1] == '/':
        fileUrl = '/index.html'
    else:
        fileUrl = input[1]
    # checking if we have redirect code
    if fileUrl == '/redirect':
        nextClient = True
        sendMessage(clientSocket, CODE_REDIRECT, CLOSE_CONNECTION, 0)
        totalData = closeSocket(clientSocket)
        continue
    fileUrl = 'files' + fileUrl
    # if the file doesnt exist we need to send error message
    if not os.path.exists(fileUrl):
        nextClient = True
        sendMessage(clientSocket, CODE_ERROR, CLOSE_CONNECTION, 0)
        totalData = closeSocket(clientSocket)
        continue
    # using the method to find if we keep talking with this client
    connection = findConnection(input)
    # we check if we keep talking with this client after the command
    if connection == KEEP_CONECTION:
        nextClient = False
    else:
        nextClient = True
    fileLength = os.stat(fileUrl).st_size
    file = None
    fileData = None
    # sending the message in the format
    sendMessage(clientSocket, CODE_SUCCESS, connection, fileLength)
    file = open(fileUrl, 'rb')
    # reading & sending the file's bytes
    fileBytes = bytes()
    while (byte := file.read(1)):
        fileBytes = fileBytes + byte
    file.close()
    clientSocket.send(fileBytes)
    # if we need to close the connection with the client
    if nextClient:
        totalData = closeSocket(clientSocket)
