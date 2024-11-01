#!/usr/bin/env python3
"""
powerlog95.py

Log measured values from ZES Zimmer LMG95 Power Analyzer.

This script connects to a ZES Zimmer LMG95 Power Meter via an RS232-Ethernet
converter, logs the measured values to a specified log file, and optionally
writes the data to an InfluxDB database.

Author:
    Jan de Cuveland (2012-07, 2024-10)
"""

import argparse
import sys
import time
import lmg95

HAS_INFLUXDB = False
try:
    import influxdb
    HAS_INFLUXDB = True
except ImportError:
    pass

#VAL = "count sctc cycr utrms itrms udc idc ucf icf uff iff p pf s q freq".split()

VAL = [
    "count", # Measurement cycle count. Wraps back to 0 after 65535.
    "sctc",  # Last ADC measurement count of the cycle. Wraps back to 0 after 2^31-1.
    "cycr",  # True cycle time in seconds. Corresponds to an integer number
             # of signal periods. On average, this time is equal to the cycle time.
    "freq",  # Frequency in Hz.

    ### Voltage and current values
    "utrms", # True RMS voltage in V.
    "itrms", # True RMS current in A.
    # DC value. For a sinusoidal signal, this is 0.
    "udc",   # DC voltage in V.
    "idc",   # DC current in A.
    # Crest factor: The ratio of the peak value to the RMS value. For a
    #               sinusoidal signal, this is sqrt(2) ≈ 1.414.
    "ucf",   # Voltage crest factor.
    "icf",   # Current crest factor.
    # Form factor: The ratio of the RMS value to the average value. For a
    #              sinusoidal signal, this is pi/(2*sqrt(2)) ≈ 1.11.
    "uff",   # Voltage form factor.
    "iff",   # Current form factor.

    ### Power values
    "p",     # Active power in W.
    "q",     # Reactive power in var.
    "s",     # Apparent power in VA.
    "pf",    # Power factor.
]


def send_to_influxdb(influx, data: list[float]) -> None:
    """Send data to InfluxDB"""
    item = {
        "measurement": "powerlog",
        "tags": {},
        "time": int(data[0] * 1000),
        "fields": dict(zip(VAL, data[1:])),
    }

    # Set value to None if it is 9.91e+37 (NaN),
    # 9.9E+37 (Infinity), or -9.9e+37 (-Infinity)
    for key in item["fields"]:
        if item["fields"][key] in [9.91e37, 9.9e37, -9.9e37]:
            item["fields"][key] = None

    influx.write_points([item], time_precision="ms")


def main():
    """Application entry point"""
    parser = argparse.ArgumentParser(
        description = "Log measured values from ZES Zimmer LMG95 Power Meter")
    parser.add_argument("host", help = "Hostname of RS232-Ethernet converter")
    parser.add_argument("-L", "--logfile", help = "Log values to file")
    parser.add_argument("-p", "--port", type = int, default=2101,
                        help = "TCP port of RS232-Ethernet converter")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help = "Dump measurements to stdout")
    parser.add_argument("-l", "--lowpass", action="store_true", default=False,
                        help = "Enable 60 Hz low pass filter")
    parser.add_argument("-i", "--interval", type=float, default=0.5,
                        help = "Measurement interval in seconds")
    if HAS_INFLUXDB:
        parser.add_argument("-I", "--influxdb", action="store_true", default=False,
                            help = "Write data to InfluxDB")
    args = parser.parse_args()

    if HAS_INFLUXDB and args.influxdb:
        influx = influxdb.InfluxDBClient(database="powerlog")
        influx.create_database("powerlog")

    print("connecting to", args.host, "at port", args.port)
    lmg = lmg95.lmg95(args.host, args.port)

    print("performing device reset")
    lmg.cont_off()
    lmg.reset()

    print("device found:", lmg.read_id()[1])

    print("setting up device")
    lmg.read_errors()

    # set measurement interval
    lmg.send_short_cmd(f"CYCL {args.interval}")

    # 60Hz low pass filter
    if args.lowpass:
        lmg.send_short_cmd("FAAF 0")
        lmg.send_short_cmd("FILT 4")

    lmg.set_ranges(10., 250.)
    lmg.select_values(VAL)

    if args.logfile:
        log = open(args.logfile, "w", encoding="utf-8")
    i = 0
    try:
        lmg.cont_on()
        if args.logfile:
            log.write("# time " + " ".join(VAL) + "\n")
            print("writing values to", args.logfile)
        print("press CTRL-C to stop")
        while True:
            data = lmg.read_values()
            i += 1
            data.insert(0, time.time())
            if args.verbose:
                sys.stdout.write(" ".join([str(x) for x in data]) + "\n")
            else:
                sys.stdout.write(f"\r{i}")
            sys.stdout.flush()
            if args.logfile:
                log.write(" ".join([str(x) for x in data]) + "\n")
                log.flush()
            if HAS_INFLUXDB and args.influxdb:
                send_to_influxdb(influx, data)
    except KeyboardInterrupt:
        print()

    lmg.cont_off()
    if args.logfile:
        log.close()

    lmg.disconnect()
    print("done,", i, "measurements written")


if __name__ == "__main__":
    main()
