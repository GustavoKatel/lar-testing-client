#!/usr/bin/python

import os
import thread
import string
import random
import errno

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
        self.currentCommand = ""
        self.lastCommand = ""

        cdir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists(cdir+"/nodes"):
            os.makedirs(cdir+"/nodes")

        self.fstdout = open(cdir+"/nodes/"+self.name+".out", "w")
        self.fstderr = open(cdir+"/nodes/"+self.name+".err", "w")
        self.fnodeerr = open(cdir+"/nodes/"+self.name+".nodeerr", "w")

        self.currentStdin = None

    def close(self):
        print "closing connection"
        self.ssh.close()
        self.status = Status.closed
        print "closed"

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

            stdin, stdout, stderr = self.ssh.exec_command(cmd)

            self.currentStdin = stdin

            print "done..."

            self.lastCommand = cmd
            self.currentCommand = ""

            self.status = Status.idle
            self.fstdout.write('-.-.-00-.-.- %s -.-.-00-.-.-\n' % cmd)
            for line in stdout:
                self.fstdout.write(line)
            self.fstdout.write('-.-.-00-.-.--.-.-00-.-.--.-.-00-.-.-\n')
            self.fstdout.flush()

            self.fstderr.write('-.-.-00-.-.- %s -.-.-00-.-.-\n' % cmd)
            for line in stderr:
                self.fstderr.write(line)
            self.fstderr.write('-.-.-00-.-.--.-.-00-.-.--.-.-00-.-.-\n')
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

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "%s (%s)" % (self.name, Status.toStr(self.status))
