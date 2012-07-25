#!/usr/bin/python

# lmg95.py
#
# Implement interface to ZES Zimmer LMG95 Power Meter
# via RS232-Ethernet converter
#
# 2012-07, Jan de Cuveland

import socket

EOS = "\r\n"
TIMEOUT = 5

class scpi:
    def __init__(self, host = "", port = 0):
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if port > 0:
            self.connect(host, port)

    def connect(self, host, port):
        self._s.connect((host, port))
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
        result = self.query(cmd + ";*OPC?")
        if result != "1":
            print "opc returned unexpected value:", result

    def query(self, msg):
        self.send(msg)
        return self.recv_str()

    def close(self):
        self._s.close()
    
    def __del__(self):
        self.close()


class lmg95(scpi):
    _short_commands_enabled = False

    def reset(self):
        self.send_cmd("*cls")
        self.send_cmd("*rst")
    
    def goto_short_commands(self):
        if not self._short_commands_enabled:
            self.send("syst:lang short")
        self._short_commands_enabled = True

    def goto_scpi_commands(self):
        if self._short_commands_enabled:
            self.send("lang scpi")
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

    def beep(self):
        self.send_short_cmd("beep")

    def read_errors(self):
        return self.query_scpi("syst:err:all?")

    def select_values(self, values):
        self.send_short("actn;" + "?;".join(values) + "?")

    def read_values(self):
        values_raw = self.recv_str().split(";")
        return [ float(x) for x in values_raw ]

    def cont_on(self):
        self.send_short("cont on")

    def cont_off(self):
        self.send_short("cont off")
        
