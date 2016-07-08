#!/usr/bin/python

import os
import thread
import threading
import string
import random
import errno
import time

import paramiko

class Status:
    @staticmethod
    def toStr(st):
        if st == Status.idle:
            return "IDLE"
        elif st == Status.running:
            return "RUNNING"
        elif st == Status.exited:
            return "EXITED"
        elif st == Status.connecting:
            return "CONNECTING"
        elif st == Status.closed:
            return "CLOSED"

    idle = 0
    running = 1
    exited = 2
    connecting = 3
    closed = 4

class Process(threading.Thread):
    def __init__(self, id, ssh, cmd, fstdout, fstderr, fnodeerr):
        threading.Thread.__init__(self)

        self.id = id

        self.ssh = ssh
        self.cmd = cmd

        self.status = Status.idle

        self.fstdout = fstdout
        self.fstderr = fstderr
        self.fnodeerr = fnodeerr

        self.stdin = None
        self.stdout = None
        self.stderr = None

        self.returnCode = 0

        self.running = False

        self.pid = -1

    def stop(self):
        print "closing"
        self.running = False

    def updatePid(self):
        try:
            stdin, stdout, stderr = self.ssh.exec_command("ps axo pid,cmd | grep OCTOPUS=%s | grep -v grep" % self.id)

            if stdout:
                for line in stdout:
                    print "PID: " + line
            else:
                self.pid = -1

        except Exception as e:
            print e
            self.stop()

    def run(self):
        try:
            self.running = True
            self.status = Status.running
            print "running..."

            self.stdin, self.stdout, self.stderr = self.ssh.exec_command('bash -c "%s #OCTOPUS=%s"' % (self.cmd, self.id) )

            self.updatePid()

            self.fstdout.write('-.-.-00-.-.- %s -.-.-00-.-.-\n' % self.cmd)
            for line in self.stdout:
                self.fstdout.write(line)
            self.fstdout.write('-.-.-00-.-.--.-.-00-.-.--.-.-00-.-.-\n')
            self.fstdout.flush()


            self.fstderr.write('-.-.-00-.-.- %s -.-.-00-.-.-\n' % self.cmd)
            for line in self.stderr:
                self.fstderr.write(line)
            self.fstderr.write('-.-.-00-.-.--.-.-00-.-.--.-.-00-.-.-\n')
            self.fstderr.flush()

            self.status = Status.exited

        except Exception as e:
            print e
            self.stop()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "%s (%s) (status: %s) - %s" % (self.id, self.pid, Status.toStr(self.status), self.cmd)

class Node:
    def __init__(self, name, username, hostname, port, pkey):
        self.name = name
        self.username = username
        self.hostname = hostname
        self.port = port
        self.pkey = pkey

        self.ssh = None
        # self.connect()

        self.currentProcessId = 0
        self.processMap = {}

        cdir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists(cdir+"/nodes"):
            os.makedirs(cdir+"/nodes")

        self.fstdout = open(cdir+"/nodes/"+self.name+".out", "w")
        self.fstderr = open(cdir+"/nodes/"+self.name+".err", "w")
        self.fnodeerr = open(cdir+"/nodes/"+self.name+".nodeerr", "w")

        self.status = Status.closed

    def close(self):
        print "closing connection"
        self.ssh.close()
        self.status = Status.closed
        print "closed"
        # TODO kill processes

    # def kill(self):
        # if self.status = Status.running and self.currentStdin:


    def runCommand(self, cmd):
        # Only one command at a time
        if self.status == Status.running:
            return False

        self.currentProcessId+=1
        process = Process(self.currentProcessId,
            self.ssh,
            cmd,
            self.fstdout,
            self.fstderr,
            self.fnodeerr
            )
        process.start()

        self.processMap[self.currentProcessId] = process
        print self.processMap[1]

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
