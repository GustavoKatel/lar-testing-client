#!/usr/bin/python

import os
import subprocess
import threading
import string
import random
import errno

exitFlag = 0

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):

    try:
        os.makedirs('outputs')
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir('outputs'):
            pass
        else:
            raise

    return 'outputs' + os.path.sep + ''.join(random.choice(chars) for _ in range(size))

class Process (threading.Thread):
    def __init__(self, cmd_str, output_file=id_generator()):
        threading.Thread.__init__(self)
        self.cmd_str = cmd_str
        self.output_file = output_file

        self.pid = None

    def run(self):
        log = open(self.output_file, 'a')  # so that data written to it will be appended
        self.process = subprocess.Popen(self.cmd_str, stdout=log, stderr=log, shell=True)

        self.pid = self.process.pid

        (stdout, stderr) = self.process.communicate()

        print stdout

    def kill(self):
        self.process.kill()

    def isRunning(self):
        return self.process.returncode==None
