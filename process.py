#!/usr/bin/python

import os
import subprocess
import threading

exitFlag = 0

class Process (threading.Thread):
    def __init__(self, cmd_str, output_file):
        threading.Thread.__init__(self)
        self.cmd_str = cmd_str
        self.output_file = output_file

        self.pid = None

    def run(self):
        log = open(self.output_file, 'a')  # so that data written to it will be appended
        self.process = subprocess.Popen(self.cmd_str, stdout=log, stderr=log, shell=True)

        self.pid = self.process.pid

        (stdout, stderr) = self.process.communicate()

    def kill(self):
        self.process.kill()

    def isRunning(self):
        return self.process.returncode==None
