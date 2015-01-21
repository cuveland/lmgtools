#!/usr/bin/python

# lmg670.py
#
# Implement interface to ZES Zimmer LMG670 1 to 7 Channel Power Analyzer
#
# 2015-01, Jan de Cuveland

import socket

EOS = "\n"
TIMEOUT = 2

class lmg670_socket:
    def __init__(self, host = ""):
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if host != "":
            self.connect(host, 5025)

    def connect(self, host, port):
        self._s.connect((host, port))
        self._host = host
        self._port = port
        self._s.settimeout(TIMEOUT)
        
    def send(self, msg):
        self._s.sendall(msg + EOS)

    def recv_str(self):
        response = ""
        while response[-len(EOS):] != EOS:
            try:
                response += self._s.recv(4096)
            except socket.timeout as e:
                print "error:", e
                return ""
        return response[:-len(EOS)]

    def send_cmd(self, cmd):
        result = self.query(cmd + ";*opc?")
        if result != "1":
            print "opc returned unexpected value:", result

    def send_brk(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._host, self._port + 1))
        s.settimeout(TIMEOUT)
        s.sendall("break\n")
        response = ""
        while response[-len(EOS):] != EOS:
            try:
                response += s.recv(256)
            except socket.timeout as e:
                print "error:", e
                s.close()
                return False
        s.close()
        return (response[:-len(EOS)] == "0 ok")

    def query(self, msg):
        self.send(msg)
        return self.recv_str()

    def close(self):
        self._s.close()
    
    def __del__(self):
        self.close()


class lmg670(lmg670_socket):
    _short_commands_enabled = False

    def reset(self):
        self.send_brk()
        self._short_commands_enabled = False
        self.send_cmd("*rst;*cls")

    def goto_short_commands(self):
        if not self._short_commands_enabled:
            self.send("*zlang short")
        self._short_commands_enabled = True

    def goto_scpi_commands(self):
        if self._short_commands_enabled:
            self.send("*zlang scpi")
        self._short_commands_enabled = False

    def send_short(self, msg):
        self.goto_short_commands()
        self.send(msg)

    def send_scpi(self, msg):
        self.goto_scpi_commands()
        self.send(msg)

    def send_short_cmd(self, cmd):
        self.goto_short_commands()
        self.send_cmd(cmd)

    def send_scpi_cmd(self, cmd):
        self.goto_scpi_commands()
        self.send_cmd(cmd)

    def query_short(self, msg):
        self.goto_short_commands()
        return self.query(msg)

    def query_scpi(self, msg):
        self.goto_scpi_commands()
        return self.query(msg)

    def goto_local(self):
        self.send("gtl")

    def read_id(self):
        return self.query("*idn?").split(",")

    def read_errors(self):
        return self.query_scpi("syst:err:all?")

    def set_ranges(self, current, voltage):
        for c in range(1, 8):
            cmd = "iauto{0} 0;uauto{0} 0;irng{0} {1};urng{0} {2}".format(c, current, voltage)
            self.send_short_cmd(cmd)

    def select_values(self, values):
        self.send_short('actn;' + "?;".join(values) + "?")

    def read_raw_values(self):
        return self.recv_str().split(";")
        
    def read_float_values(self):
        values_raw = self.read_raw_values()
        return [ float(x) for x in values_raw ]

    def cont_on(self):
        self.send_short("cont on")

    def cont_off(self):
        self.send_short("cont off")
        
    def disconnect(self):
        self.read_errors()
        self.goto_local()
