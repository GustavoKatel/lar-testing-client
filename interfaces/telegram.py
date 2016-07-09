import time
import threading
import re
import os
import json

import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from node import Status as NodeStatus
from node import Node

class Telegram(threading.Thread):

    def __init__(self, nodes, conf):
        threading.Thread.__init__(self)

        self.running = True
        self.nodes = nodes
        self.conf = conf

    def handle_inline(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)

        if not msg['from']['username'] in self.conf['telegram']['admins']:
            print "Not authorized: %s" % msg['from']
            self.bot.sendMessage(chat_id, """
-.-.-00-.-.-
>>> OCToPUS <<<<
-.-.-00-.-.-
            """)
            return

        self.interpreter(msg['message']['chat']['id'], data)

    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)

        # print msg
        if not msg['from']['username'] in self.conf['telegram']['admins']:
            print "Not authorized: %s" % msg['from']
            self.bot.sendMessage(chat_id, """
-.-.-00-.-.-
>>> OCToPUS <<<<
-.-.-00-.-.-
            """)
            return

        if content_type == 'document':
            doc = msg['document']
            cdir = os.path.dirname(os.path.realpath(__file__))
            if not os.path.exists(cdir+"/../data"):
                os.makedirs(cdir+"/../data")
            print "Downloading... " + doc['file_name']
            fd = open(cdir+'/../data/'+doc['file_name'], 'w')
            self.bot.download_file(doc['file_id'], fd)
            fd.close()

            for node in self.nodes:
                node.putFile(cdir+'/../data/'+doc['file_name'], doc['file_name'])

        elif content_type == 'text':
            text = msg['text']

            self.interpreter(chat_id, text)

    def filter_nodes(self, names):
        current_nodes = []
        if names == "*":
            current_nodes = self.nodes
        else:
            lnames = names.split(',')
            for node in self.nodes:
                if node.name in lnames:
                    current_nodes.append(node)

        return current_nodes

    def interpreter(self, chat_id, text):
        # /start
        if re.match(r'/start$', text):
            markup = InlineKeyboardMarkup(inline_keyboard=[
                     [dict(text='System information', callback_data='/info'),
                     dict(text='Node information', callback_data='/infoNode')],
                     [dict(text='Execute command', callback_data='/executeNode'),
                     dict(text='Read logs', callback_data='/logsNode')],
                     [dict(text='Download file', callback_data='/downloadNode'),
                     dict(text='Kill process', callback_data='/killNode')],
                     [dict(text='Help', callback_data='/help')],
                 ])

            self.bot.sendMessage(chat_id, '>>> OCToPUS <<<<', reply_markup=markup)

        # /infoNode inline keyboard
        elif re.match(r'/infoNode$', text):
            markup = InlineKeyboardMarkup(inline_keyboard=[
                     [dict(text=node.name, callback_data='/info %s' % node.name)] for node in self.nodes
                 ])

            self.bot.sendMessage(chat_id, '>>> OCToPUS <<<<\nChoose a node', reply_markup=markup)

        # /executeNode inline keyboard
        elif re.match(r'/executeNode$', text):


            self.bot.sendMessage(chat_id, """
            >>> OCToPUS <<<<\nPlease send:\n /exec LIST_OF_NAMES|* CMD: Execute the command CMD. Eg.: /exec s1,s2 ls -lah
            """
            )

        # /logsNode inline keyboard
        elif re.match(r'/logsNode$', text):
            buttons = []
            buttons += [dict(text=node.name, callback_data='/logs %s' % node.name) for node in self.nodes]
            markup = InlineKeyboardMarkup(inline_keyboard=[
                    [dict(text="All nodes", callback_data='/logs *')],
                    buttons
                 ])

            self.bot.sendMessage(chat_id, '>>> OCToPUS <<<<\nChoose a node', reply_markup=markup)

        # /downloadNode inline keyboard
        elif re.match(r'/downloadNode$', text):

            self.bot.sendMessage(chat_id, """
            >>> OCToPUS <<<<\nPlease send:\n /download LIST_OF_NAMES|* FILENAME: Download FILENAME from a node
            """
            )

        # /killNode inline keyboard
        elif re.match(r'/killNode$', text):
            buttons = []
            buttons += [dict(text=node.name, callback_data='/killNode %s' % node.name) for node in self.nodes]
            markup = InlineKeyboardMarkup(inline_keyboard=[
                    # [dict(text="All nodes", callback_data='/killNode *')],
                    buttons
                 ])

            self.bot.sendMessage(chat_id, '>>> OCToPUS <<<<\nChoose a node', reply_markup=markup)

        # /killNode inline keyboard - choose process
        elif re.match(r'/killNode ([a-zA-Z0-9_,]+|\*)', text):
            m = re.match(r'/killNode ([a-zA-Z0-9_,]+|\*)', text)
            names = m.group(1)

            current_nodes = self.filter_nodes(names)
            self.bot.sendChatAction(chat_id, "typing")
            for node in current_nodes:
                node.updateProcessList()

                if len(node.processList)<=0:
                    self.bot.sendMessage(chat_id, 'No process found. See /help')
                    continue

                markup = InlineKeyboardMarkup(inline_keyboard=[
                        [dict(text=process, callback_data='/exec %s kill -9 %s' % ( node.name, process.split(' ')[0] )) for process in node.processList]
                     ])

                self.bot.sendMessage(chat_id, 'Choose a process', reply_markup=markup)

        # /info
        elif re.match(r'/info$', text):
            self.bot.sendChatAction(chat_id, "typing")
            res = "Nodes list starts -.-.-00-.-.-\n\n"
            processTotal = 0
            for i,node in enumerate(self.nodes):
                node.updateProcessList()
                processTotal += node.processCount
                res += str(i) + "- " + str(node) + "\n"

            res += "\nTotal of %s process(es) runnning\n" % processTotal

            res += "\nNodes list ends -.-.-00-.-.-\n"
            self.bot.sendMessage(chat_id, res)

        # /info NAME
        elif re.match(r'/info [a-zA-Z0-9_]+', text):
            m = re.match(r'/info ([a-zA-Z0-9_]+)', text)
            name = m.group(1)
            for node in self.nodes:
                if node.name == name:
                    self.bot.sendChatAction(chat_id, "typing")
                    node.updateProcessList()
                    res = "Node info: %s -.-.-00-.-.-\n\n" % name
                    res += "hostname: %s\n" % node.hostname
                    res += "username: %s\n" % node.username
                    res += "port: %s\n" % node.port
                    res += "status: %s\n" % NodeStatus.toStr(node.status)
                    res += "last command: %s\n" % node.lastCommand
                    res += "Process count: %s\n" % node.processCount
                    res += "Process List:\n"
                    for p in node.processList:
                        res += "%s\n" % p
                    res += "\n"
                    res += "\nNode info ends -.-.-00-.-.-\n"
                    self.bot.sendMessage(chat_id, res)

        # /exec [LIST_OF_NAMES|*] CMD
        elif re.match(r'/exec ([a-zA-Z0-9_,]+|\*) (.+)', text):
            m = re.match(r'/exec ([a-zA-Z0-9_,]+|\*) (.+)', text)
            names = m.group(1)
            cmd = m.group(2)

            current_nodes = self.filter_nodes(names)
            for node in current_nodes:
                node.runCommand(cmd)
            self.bot.sendMessage(chat_id, "-.-.-00-.-.-")

        # /connect [LIST_OF_NAMES|*]
        elif re.match(r'/connect ([a-zA-Z0-9_,]+|\*)', text):
            m = re.match(r'/connect ([a-zA-Z0-9_,]+|\*)', text)
            names = m.group(1)

            current_nodes = self.filter_nodes(names)
            for node in current_nodes:
                self.bot.sendChatAction(chat_id, "typing")
                self.bot.sendMessage(chat_id, "Connecting to: %s -.-.-00-.-.-\n\n" % name)
                node.connect()
            self.bot.sendMessage(chat_id, "-.-.-00-.-.-")

        # /logs [LIST_OF_NAMES|*]
        elif re.match(r'/logs ([a-zA-Z0-9_,]+|\*)', text):
            m = re.match(r'/logs ([a-zA-Z0-9_,]+|\*)', text)
            names = m.group(1)

            current_nodes = self.filter_nodes(names)
            for node in current_nodes:
                cdir = os.path.dirname(os.path.realpath(__file__))
                f = open(cdir+"/../nodes/"+node.name+".out", "r")

                self.bot.sendChatAction(chat_id, "typing")
                res = "Reading logs: %s -.-.-00-.-.-\n\n" % node.name
                res += ''.join(f.readlines())
                res += "Reading logs ends: %s -.-.-00-.-.-\n\n" % node.name
                self.bot.sendMessage(chat_id, res)

                f.close()

        # /dump [LIST_OF_NAMES|*] [stdout|stderr]
        elif re.match(r'/dump ([a-zA-Z0-9_,]+|\*) (stdout|stderr)', text):
            m = re.match(r'/dump ([a-zA-Z0-9_,]+|\*) (stdout|stderr)', text)
            names = m.group(1)
            dump_type = m.group(2)

            current_nodes = self.filter_nodes(names)
            for node in current_nodes:
                cdir = os.path.dirname(os.path.realpath(__file__))
                if dump_type == "stdout":
                    f = open(cdir+"/../nodes/"+node.name+".out", "r")
                else:
                    f = open(cdir+"/../nodes/"+node.name+".err", "r")

                self.bot.sendChatAction(chat_id, "upload_document")
                self.bot.sendDocument(chat_id, f, "%s - %s" % (node.name, dump_type))

        # /download [LIST_OF_NAMES|*] filename
        elif re.match(r'/download ([a-zA-Z0-9_,]+|\*) (.+)', text):
            m = re.match(r'/download ([a-zA-Z0-9_,]+|\*) (.+)', text)
            names = m.group(1)
            filename = m.group(2)

            current_nodes = self.filter_nodes(names)
            for node in current_nodes:
                f = node.getFile(filename)
                self.bot.sendChatAction(chat_id, "upload_document")
                self.bot.sendDocument(chat_id, f, "%s - %s" % (node.name, filename))

        # /auth USERNAME
        elif re.match(r'/auth ([a-zA-Z0-9_]+)', text):
            m = re.match(r'/auth ([a-zA-Z0-9_]+)', text)
            username = m.group(1)
            self.conf['telegram']['admins'].append(username)

            js = json.dumps(self.conf, ensure_ascii=False, sort_keys=True, indent=4)
            with open('/opt/octopus/conf/octopus.conf', 'w') as f:
                f.write(js+'\n')

            self.bot.sendChatAction(chat_id, "typing")
            self.bot.sendMessage(chat_id, "New admin added: %s -.-.-00-.-.-\n\n" % username)

        # /killall [LIST_OF_NAMES|*]
        elif re.match(r'/killall ([a-zA-Z0-9_,]+|\*)', text):
            m = re.match(r'/killall ([a-zA-Z0-9_,]+|\*)', text)
            names = m.group(1)

            current_nodes = self.filter_nodes(names)
            for node in current_nodes:
                node.runCommand("pkill -f \"OCTOPUS\"")
                self.bot.sendMessage(chat_id, "-.-.-00-.-.-")

        # /killall [LIST_OF_NAMES|*] CMD_PATTERN
        elif re.match(r'/killall ([a-zA-Z0-9_,]+|\*) (.+)', text):
            m = re.match(r'/killall ([a-zA-Z0-9_,]+|\*) (.+)', text)
            names = m.group(1)
            pattern = m.group(2)

            current_nodes = self.filter_nodes(names)
            for node in current_nodes:
                node.runCommand("pkill -f %s" % pattern)
                self.bot.sendMessage(chat_id, "-.-.-00-.-.-")

        # /help
        elif re.match(r'/help$', text):
            self.bot.sendMessage(chat_id, self.helpText())

        else:
            self.interpreter(chat_id, "/start")

    def stop(self):
        self.running = False

    def run(self):
        self.bot = telepot.Bot(self.conf["telegram"]["token"])
        self.bot.message_loop({
            'chat': self.handle,
            'callback_query': self.handle_inline,
            'inline_query': self.handle_inline
        })
        self.running = True

        while self.running:
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                self.stop()

    def helpText(self):
        return """
-.-.-00-.-.-
>>> OCToPUS <<<<
-.-.-00-.-.-

Commands:
/info: Returns the list of nodes in the server

/info NAME: Returns information about a specif node

/exec LIST_OF_NAMES|* CMD: Execute the command CMD. Eg.: /exec [s1,s2] ls -lah

/connect LIST_OF_NAMES|*: Force a connection to the nodes in LIST_OF_NAMES

/logs LIST_OF_NAMES|*: Read the stdout from the node

/dump LIST_OF_NAMES|* stdout|stderr: Download the stdout or the stderr from a node

/download LIST_OF_NAMES|* FILENAME: Download FILENAME from a node

/auth USERNAME: Add USERNAME to the admin group

/killall LIST_OF_NAMES|*: Kill all processes created by the OCToPUS

/killall LIST_OF_NAMES|* PATTERN: Kill all processes that contains PATTERN in the command name (BE CAREFUL! THIS CAN KILL PROCESSES THAT WEREN'T CREATED BY OCToPUS)
"""
