import telepot
import time
import threading
import re

class Telegram(threading.Thread):

    def __init__(self, nodes, conf):
        threading.Thread.__init__(self)

        self.running = True
        self.nodes = nodes
        self.conf = conf

    def handle(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(content_type, chat_type, chat_id)

        if content_type == 'text':
            text = msg['text']

            # /list
            if re.match(r'/list.*', text):
                res = "Nodes list starts -.-.-00-.-.-\n\n"
                for i,node in enumerate(self.nodes):
                    res += str(i) + "- " + str(node) + "\n"
                res += "\nNodes list ends -.-.-00-.-.-\n"
                self.bot.sendMessage(chat_id, res)

            # /info NAME
            elif re.match(r'/info [a-zA-Z0-9_]+', text):
                m = re.match(r'/info ([a-zA-Z0-9_]+)', text)
                name = m.group(1)
                for node in self.nodes:
                    if node.name == name:
                        res = "Node info: %s -.-.-00-.-.-\n\n" % name
                        res += "hostname: %s\n" % node.hostname
                        res += "username: %s\n" % node.username
                        res += "port: %s\n" % node.port
                        res += "last command: %s\n" % node.lastCommand
                        res += "current command: %s\n" % node.currentCommand
                        res += "\nNode info ends -.-.-00-.-.-\n"
                        self.bot.sendMessage(chat_id, res)

            # /exec [LIST_OF_NAMES|*] CMD
            elif re.match(r'/exec \[([a-zA-Z0-9_,]+|\*)\] (.+)', text):
                m = re.match(r'/exec \[([a-zA-Z0-9_,]+|\*)\] (.+)', text)
                names = m.group(1)
                cmd = m.group(2)

                current_nodes = []
                if names == "*":
                    current_nodes = self.nodes
                else:
                    lnames = names.split(',')
                    for node in self.nodes:
                        if node.name in lnames:
                            current_nodes.append(node)

                for node in current_nodes:
                    node.runCommand(cmd)

            else:
                self.bot.sendMessage(chat_id, self.helpText())

    def stop(self):
        self.running = False

    def run(self):
        self.bot = telepot.Bot(self.conf["telegram"]["token"])
        self.bot.message_loop(self.handle)
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
/list: Returns the list of nodes in the server
/info NAME: Returns information about a specif node
/exec [LIST_OF_NAMES|*] CMD: Execute the command CMD. Eg.: /exec [s1,s2] ls -lah
"""
