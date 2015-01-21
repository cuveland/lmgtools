Cross-platform Tools for ZES Zimmer Precision Power Meters
==========================================================
2012-2015, Jan de Cuveland, Goethe-Universität Frankfurt am Main

LMG95
-----

How to set up:

- Connect the "Digi Connect SP RS232" Ethernet device server to your network
- Web administration default credentials: root/dbps
- Configure the Ethernet device server to:
    - Port Profile: TCP Sockets
    - TCP Server Settings: Enable Raw TCP access (port: 2101)
    - Serial Configuration: 115200 8N1, Flow Control: Hardware
- Connect the LMG95 via straight RS232 cable, use port "COM A"
- Switch on LMG95
- Configure the LMG95 to:
    - I/O port "COM A", Profile: Custom
    - 115200 8N1, Echo: off, EOS: Terminal, Protocol: RTS/CTS

How to start a measurement:

- Enter, e.g.: "`./powerlog95.py power.example.com powerlog`"
  with the IP address or hostname of the Ethernet device server

LMG670
------

How to set up:

- Connect the ZES Zimmer LMG670 to your DHCP-enabled network
- Switch on LMG670
- Note the assigned IP address (INSTR -> Interface -> IP Address)

Hot to start a measurement:

- Enter, e.g.: "`./powerlog670.py 192.0.2.2 powerlog`"
  with the assigned IP address of the LMG670
