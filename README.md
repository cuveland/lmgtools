# Cross-platform Tools for ZES Zimmer Precision Power Analyzers

This is a collection of scripts to read measurements from the ZES LMG series
of professional precision power analyzers. The main application is to continuously
log the measured power values for later time-dependent analysis.

### Motivation

As an application example, these scripts are used in energy-efficient
supercomputing. Here, precisely measuring the power input of a
computer system during an HPL run is the basis for system optimization
and may finally be used for submission to the [Green500] list.

[Green500]: http://green500.org/ "Green500 List"

## Supported Devices

Currently supported devices include:

- ZES Zimmer LMG95 1 Phase Power Analyzer (via RS232-Ethernet converter)
- ZES Zimmer LMG670 1 to 7 Channel Power Analyzer

Other devices from the LMG600 series such as the LMG640 are untested but will
most likely just work. As the interface language of different LMG devices is similar
but not identical, other models will probably require some changes.

## Configuration and Measurement

The steps required to start logging measurements depend on the employed LMG model.
Tests have been performed with LMG95 and LMG670. Example configuration instructions
for these devices are outlined below.

### LMG95

**How to set up:**

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

**How to start a measurement:**

- Enter, e.g.: `./powerlog95.py power.example.com powerlog`  
  with the IP address or hostname of the Ethernet device server

### LMG670

**How to set up:**

- Connect the ZES Zimmer LMG670 to your DHCP-enabled network
- Switch on LMG670
- Note the assigned IP address (INSTR -> Interface -> IP Address)

**Hot to start a measurement:**

- Enter, e.g.: `./powerlog670.py 192.0.2.2 powerlog`  
  with the assigned IP address of the LMG670

## Contributors

2012-2015, Jan de Cuveland, Goethe-Universität Frankfurt am Main
