#!/usr/bin/python

# lmg95.py
#
# Implement interface to ZES Zimmer LMG95 Power Meter
# via RS232-Ethernet converter
#
# 2012-07, Jan de Cuveland, Dirk Hutter

import socket, telnetlib

EOS = "\r\n"
TIMEOUT = 5

class scpi_socket:
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

    def send_brk(self, ctrl):
        pass

    def query(self, msg):
        self.send(msg)
        return self.recv_str()

    def close(self):
        self._s.close()
    
    def __del__(self):
        self.close()


class scpi_telnet:
    
    def __init__(self, host = "", port = 0): 
        self._t = telnetlib.Telnet() 
        if port > 0:
            self.connect(host, port)

    def connect(self, host, port):
        self._t.open(host, port, TIMEOUT)

    def close(self): 
        self._t.close()

    def recv_str(self):
        response = self._t.read_until(EOS, TIMEOUT)
        if response[-len(EOS):] != EOS:
            print "error: recv timeout"
        return response[:-len(EOS)]

    def send(self, msg):
        self._t.write(msg + EOS)

    def send_raw(self, msg):
        self._t.get_socket().sendall(msg)

    def query(self, cmd): 
        self.send(cmd) 
        return self.recv_str()

    def send_cmd(self, cmd):
        result = self.query(cmd + ";*OPC?")
        if result != "1":
            print "opc returned unexpected value:", result

    def send_brk(self):
        self.send_raw(chr(255) + chr(243))

    def get_socket(self):
        return self._t.get_socket()

    def __del__(self):
        self.close()


class lmg95(scpi_telnet):
    _short_commands_enabled = False

    def reset(self):
        self.send_brk()
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

    def set_ranges(self, current, voltage):
        self.send_short_cmd("iam manual");
        self.send_short_cmd("irng " + str(current))
        self.send_short_cmd("uam manual");
        self.send_short_cmd("urng " + str(voltage))

    def select_values(self, values):
        self.send_short("actn;" + "?;".join(values) + "?")

    def read_values(self):
        values_raw = self.recv_str().split(";")
        return [ float(x) for x in values_raw ]

    def cont_on(self):
        self.send_short("cont on")

    def cont_off(self):
        self.send_short("cont off")
        
    def disconnect(self):
        self.goto_local
        self.close()
