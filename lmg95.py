# lmg95.py
#
# Implement interface to ZES Zimmer LMG95 1 Phase Power Analyzer
# via RS232-Ethernet converter
#
# 2012-07, Jan de Cuveland, Dirk Hutter
# 2024-10, Jan de Cuveland

import socket
import telnetlib

EOS = "\r\n"
TIMEOUT = 5

class scpi_socket:
    def __init__(self, host = "", port = 0):
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if port > 0:
            self.connect(host, port)

    def connect(self, host, port) -> None:
        self._s.connect((host, port))
        self._s.settimeout(TIMEOUT)

    def send(self, msg: str) -> None:
        self._s.sendall((msg + EOS).encode('ascii'))

    def recv_str(self) -> str:
        response = ""
        while response[-len(EOS):] != EOS:
            try:
                response += self._s.recv(4096).decode('ascii')
            except socket.timeout as e:
                print("error:", e)
                return ""
        return response[:-len(EOS)]

    def send_cmd(self, cmd: str) -> None:
        result = self.query(cmd + ";*OPC?")
        if result != "1":
            print("opc returned unexpected value:", result)

    def send_brk(self) -> None:
        pass

    def query(self, msg: str) -> str:
        self.send(msg)
        return self.recv_str()

    def close(self) -> None:
        self._s.close()

    def __del__(self):
        self.close()


class scpi_telnet:

    def __init__(self, host = "", port = 0):
        self._t = telnetlib.Telnet()
        if port > 0:
            self.connect(host, port)

    def connect(self, host, port) -> None:
        self._t.open(host, port, TIMEOUT)

    def close(self) -> None:
        self._t.close()

    def recv_str(self) -> str:
        response = self._t.read_until(EOS.encode("ascii"), TIMEOUT).decode('ascii')
        if response[-len(EOS):] != EOS:
            print("error: recv timeout")
        return response[:-len(EOS)]

    def send(self, msg: str) -> None:
        self._t.write((msg + EOS).encode('ascii'))

    def send_raw(self, msg: bytes) -> None:
        self._t.get_socket().sendall(msg)

    def query(self, cmd: str) -> str:
        self.send(cmd)
        return self.recv_str()

    def send_cmd(self, cmd: str) -> None:
        result = self.query(cmd + ";*OPC?")
        if result != "1":
            print("opc returned unexpected value:", result)

    def send_brk(self) -> None:
        self.send_raw(b"\xff\xf3")

    def get_socket(self) -> socket.socket:
        return self._t.get_socket()

    def __del__(self):
        self.close()


class lmg95(scpi_telnet):
    _short_commands_enabled = False

    def reset(self) -> None:
        self.send_brk()
        self.send_cmd("*cls")
        self.send_cmd("*rst")

    def goto_short_commands(self) -> None:
        if not self._short_commands_enabled:
            self.send("syst:lang short")
        self._short_commands_enabled = True

    def goto_scpi_commands(self) -> None:
        if self._short_commands_enabled:
            self.send("lang scpi")
        self._short_commands_enabled = False

    def send_short(self, msg: str) -> None:
        self.goto_short_commands()
        self.send(msg)

    def send_scpi(self, msg: str) -> None:
        self.goto_scpi_commands()
        self.send(msg)

    def send_short_cmd(self, cmd: str) -> None:
        self.goto_short_commands()
        self.send_cmd(cmd)

    def send_scpi_cmd(self, cmd: str) -> None:
        self.goto_scpi_commands()
        self.send_cmd(cmd)

    def query_short(self, msg: str) -> str:
        self.goto_short_commands()
        return self.query(msg)

    def query_scpi(self, msg: str) -> str:
        self.goto_scpi_commands()
        return self.query(msg)

    def goto_local(self) -> None:
        self.send("gtl")

    def read_id(self) -> list[str]:
        return self.query("*idn?").split(",")

    def beep(self) -> None:
        self.send_short_cmd("beep")

    def read_errors(self) -> str:
        return self.query_scpi("syst:err:all?")

    def set_ranges(self, current=None, voltage=None) -> None:
        if current is not None:
            self.send_short_cmd("iam manual")
            self.send_short_cmd(f"irng {current}")
        else:
            self.send_short_cmd("iam auto")
        if voltage is not None:
            self.send_short_cmd("uam manual")
            self.send_short_cmd(f"urng {voltage}")
        else:
            self.send_short_cmd("uam auto")

    def select_values(self, values: list[str]) -> None:
        self.send_short("actn;" + "?;".join(values) + "?")

    def read_values(self) -> list[float]:
        values_raw = self.recv_str().strip()
        if len(values_raw) == 0:
            return []
        return [ float(x) for x in values_raw.split(";") ]

    def cont_on(self) -> None:
        self.send_short("cont on")

    def cont_off(self) -> None:
        self.send_short("cont off")

    def disconnect(self) -> None:
        self.read_errors()
        self.goto_local()
