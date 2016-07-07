#!/usr/bin/python

import signal
import sys
import time
import json

from node import Node
from interfaces.telegram import Telegram

interface = None
nodes = []
conf = {}

def quit(signum, frame):
    print 'quit'
    interface.stop()

    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)

    nodes = []

    conf_file = open('octopus.conf')
    conf = json.load(conf_file)

    for data in conf["nodes"]:
        node = Node(
            data["name"],
            data["username"],
            data["hostname"],
            data["port"],
            conf["auth"]["private_key"]
        )
        nodes.append(node)

    # cli = node.Node("gustavokatel", "127.0.0.1", 22)
    # time.sleep(5)
    # cli.runCommand("touch test.txt && ls")

    interface = Telegram(nodes, conf)
    interface.start()

    while True:
        time.sleep(10)
