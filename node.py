#!/usr/bin/python

import os
import thread
import string
import random
import errno
import re
import time

import paramiko

class Status:
    @staticmethod
    def toStr(st):
        if st == 0:
            return "IDLE"
        elif st == 1:
            return "RUNNING"
        elif st == 2:
            return "CLOSED"
        elif st == 3:
            return "CONNECTING"

    idle = 0
    running = 1
    closed = 2
    connecting = 3

class Node:
    def __init__(self, name, username, hostname, port, pkey):
        self.name = name
        self.username = username
        self.hostname = hostname
        self.port = port
        self.pkey = pkey

        self.ssh = None
        # self.connect()

        self.status = Status.idle
        self.lastCommand = ""

        self.processCount = 0
        self.processList = []

        cdir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists(cdir+"/nodes"):
            os.makedirs(cdir+"/nodes")

        self.fstdout = open(cdir+"/nodes/"+self.name+".out", "w")
        self.fstdout.write(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())+'\n')
        self.fstdout.flush()

        self.fstderr = open(cdir+"/nodes/"+self.name+".err", "w")
        self.fstderr.write(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())+'\n')
        self.fstderr.flush()

        self.fnodeerr = open(cdir+"/nodes/"+self.name+".nodeerr", "w")
        self.fnodeerr.write(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())+'\n')
        self.fnodeerr.flush()


    def close(self):
        print "[%s] closing connection" % self.name
        self.ssh.close()
        self.status = Status.closed
        print "[%s] closed" % self.name

    # def kill(self):
        # if self.status = Status.running and self.currentStdin:


    def runCommand(self, cmd):
        # Only one command at a time
        if self.status == Status.running:
            return False

        thread.start_new_thread( self._runCommandAsync, (cmd,) )

    def _runCommandAsync(self, cmd):
        if self.status == Status.closed:
            return

        try:
            self.status = Status.running
            print "running..."
            self.currentCommand = cmd

            stdin, stdout, stderr = self.ssh.exec_command("bash -c \"%s #OCTOPUS\"" % cmd)

            self.lastCommand = cmd

            self.status = Status.idle
            self.fstdout.write('-.-.-00-.-.- %s -.-.-00-.-.-\n' % cmd)
            for line in stdout:
                self.fstdout.write(line)
            self.fstdout.write('-.-.-00-.-.--.-.-00-.-.--.-.-00-.-.-\n\n')
            self.fstdout.flush()

            self.fstderr.write('-.-.-00-.-.- %s -.-.-00-.-.-\n' % cmd)
            for line in stderr:
                self.fstderr.write(line)
            self.fstderr.write('-.-.-00-.-.--.-.-00-.-.--.-.-00-.-.-\n\n')
            self.fstderr.flush()

        except:
            self.close()

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print "creating connection"
            self.status = Status.connecting
            self.ssh.connect(
                self.hostname,
                username=self.username,
                key_filename=self.pkey,
                port=int(self.port),
                timeout=10
            )

            self.status = Status.idle
            print "connected"
        except Exception as e:
            print e
            self.status = Status.closed

    def getFile(self, filename):
        if self.status == Status.closed or self.status == Status.connecting:
            return

        sftp = self.ssh.open_sftp()
        return sftp.open(filename, 'r')

    def putFile(self, filename, dest_name):
        if self.status == Status.closed or self.status == Status.connecting:
            return

        sftp = self.ssh.open_sftp()
        sftp.put(filename, dest_name)

    def updateProcessList(self):
        psCMD = "ps axo pid,cmd | grep \#OCTOPUS | grep -v grep"

        if self.status == Status.closed:
            return

        try:
            self.processCount = 0
            self.processList = []

            stdin, stdout, stderr = self.ssh.exec_command(psCMD)

            for line in stdout:
                self.processCount += 1

                if re.match(r'([0-9]+) bash -c (.*) #OCTOPUS', line.strip()):
                    m = re.match(r'([0-9]+) bash -c (.*) #OCTOPUS', line.strip())
                    self.processList.append("%s %s" % (m.group(1), m.group(2)))
                elif not line.strip() == '':
                    self.processList.append(line.strip())

        except:
            self.close()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "%s (%s) #%s" % (self.name, Status.toStr(self.status), self.processCount)
