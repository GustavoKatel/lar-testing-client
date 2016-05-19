#!/usr/bin/python

import threading

exitFlag = 0

class Command (threading.Thread):
    def __init__(self, cmd_str, output_file):
        threading.Thread.__init__(self)
        self.cmd_str = cmd_str
        self.output_file = output_file

    def run(self):
        log = open(self.output_file, 'a')  # so that data written to it will be appended
        c = subprocess.Popen(self.cmd_str, stdout=log, stderr=log, shell=True)
