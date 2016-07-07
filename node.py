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
        self.connect()

        self.status = Status.idle
        self.currentCommand = ""
        self.lastCommand = ""

    def close(self):
        print "closing connection"
        self.ssh.close()
        print "closed"

    def runCommand(self, cmd):
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

            self.lastCommand = cmd
            self.currentCommand = ""

            self.status = Status.idle
            for line in stdout:
                print '... ' + line.strip('\n')
        except:
            return

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
                port=int(self.port)
            )
            self.status = Status.idle
            print "connected"
        except Exception as e:
            print e
            self.status = Status.closed

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "%s (%s)" % (self.name, Status.toStr(self.status))
