#!/usr/bin/python
import socket
import sys
import os
import cPickle
import re

server = "irc.freenode.org"       #settings
channel = "#larufpb"

admins = ["gustavokatel"]

admins = cPickle.load(open('man', 'rb'))
cPickle.dump(admins, open('man', 'wb'))

f = open( os.path.join(os.path.dirname(os.path.realpath(__file__)), "client") )

lines = f.readlines()

botnick = "larufpb_botname"
if len(lines) > 0:
    botnick = lines[0].replace("\r", "").replace("\n", "")

msg_regex = r":(.*)!.* \#larufpb :(.*)"

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #defines the socket
print "connecting to:"+server
irc.connect((server, 6667))                                                         #connects to the server
irc.send("USER "+ botnick +" "+ botnick +" "+ botnick +" :LAR-UFPB Slave Testing!\n") #user authentication
irc.send("NICK "+ botnick +"\n")                            #sets nick
irc.send("PRIVMSG nickserv :iNOOPE\r\n")    #auth
irc.send("JOIN "+ channel +"\n")        #join the chan

while 1:    #puts it in a loop
    text=irc.recv(2040)  #receive the text

    if text.find('PING') != -1:                          #check if 'PING' is found
        irc.send('PONG ' + text.split() [1] + '\r\n') #returnes 'PONG' back to the server (prevents pinging out!)
        continue

    m = re.search(msg_regex, text)

    if m != None:
        user = m.group(1)
        msg = m.group(2)

        if user not in admins:
            print "User: %s not authorized" % user
            continue
