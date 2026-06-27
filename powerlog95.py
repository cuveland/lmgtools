#!/usr/bin/env python3
"""
powerlog95.py

Log measured values from ZES Zimmer LMG95 Power Analyzer.

This script connects to a ZES Zimmer LMG95 Power Meter via an RS232-Ethernet
converter, logs the measured values to a specified log file, and optionally
writes the data to an InfluxDB database and/or publishes it via MQTT.

Author:
    Jan de Cuveland (2012-07, 2024-10)
"""

import argparse
import json
import sys
import time
import lmg95

HAS_INFLUXDB = False
try:
    import influxdb
    HAS_INFLUXDB = True
except ImportError:
    pass

HAS_MQTT = False
try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    pass

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

# Metadata for MQTT Home Assistant Discovery: (friendly name, unit, device_class)
SENSOR_META = {
    "p":     ("Active Power",          "W",   "power"),
    "q":     ("Reactive Power",        "var", None),
    "s":     ("Apparent Power",        "VA",  None),
    "pf":    ("Power Factor",          None,  "power_factor"),
    "utrms": ("RMS Voltage",           "V",   "voltage"),
    "itrms": ("RMS Current",           "A",   "current"),
    "udc":   ("DC Voltage",            "V",   "voltage"),
    "idc":   ("DC Current",            "A",   "current"),
    "freq":  ("Frequency",             "Hz",  "frequency"),
    "ucf":   ("Voltage Crest Factor",  None,  None),
    "icf":   ("Current Crest Factor",  None,  None),
    "uff":   ("Voltage Form Factor",   None,  None),
    "iff":   ("Current Form Factor",   None,  None),
    "count": ("Cycle Count",           None,  None),
    "sctc":  ("ADC Count",             None,  None),
    "cycr":  ("Cycle Time",            "s",   None),
}


def nan_filter(value: float):
    """Return None for LMG95 sentinel NaN/Inf values."""
    if value in (9.91e37, 9.9e37, -9.9e37):
        return None
    return value


def send_to_influxdb(influx, data: list[float]) -> None:
    """Send a measurement row to InfluxDB."""
    fields = {k: nan_filter(v) for k, v in zip(VAL, data[1:])}
    item = {
        "measurement": "powerlog",
        "tags": {},
        "time": int(data[0] * 1000),
        "fields": fields,
    }
    influx.write_points([item], time_precision="ms")


def publish_mqtt_discovery(client, topic: str) -> None:
    """Publish Home Assistant MQTT Discovery messages for all sensors."""
    device = {
        "identifiers": ["lmg95"],
        "name": "LMG95 Power Analyzer",
        "model": "ZES Zimmer LMG95",
        "manufacturer": "ZES Zimmer",
    }
    state_topic = f"{topic}/state"
    for field, (name, unit, device_class) in SENSOR_META.items():
        payload = {
            "name": f"LMG95 {name}",
            "unique_id": f"lmg95_{field}",
            "state_topic": state_topic,
            "value_template": f"{{{{ value_json.{field} }}}}",
            "device": device,
        }
        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class
        discovery_topic = f"homeassistant/sensor/lmg95_{field}/config"
        client.publish(discovery_topic, json.dumps(payload), retain=True)


def publish_mqtt_state(client, topic: str, data: list[float]) -> None:
    """Publish current measurement values as a JSON state payload."""
    state = {k: nan_filter(v) for k, v in zip(VAL, data[1:])}
    client.publish(f"{topic}/state", json.dumps(state))


def main():
    """Application entry point"""
    parser = argparse.ArgumentParser(
        description="Log measured values from ZES Zimmer LMG95 Power Meter")
    parser.add_argument("host", help="Hostname of RS232-Ethernet converter")
    parser.add_argument("-L", "--logfile", help="Log values to file")
    parser.add_argument("-p", "--port", type=int, default=2101,
                        help="TCP port of RS232-Ethernet converter")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Dump measurements to stdout")
    parser.add_argument("-l", "--lowpass", action="store_true", default=False,
                        help="Enable 60 Hz low pass filter")
    parser.add_argument("-i", "--interval", type=float, default=0.5,
                        help="Measurement interval in seconds")

    influx_group = parser.add_argument_group("InfluxDB")
    influx_group.add_argument("--influxdb", action="store_true", default=False,
                              help="Write data to InfluxDB")
    influx_group.add_argument("--influxdb-host", default="localhost",
                              help="InfluxDB hostname (default: localhost)")
    influx_group.add_argument("--influxdb-port", type=int, default=8086,
                              help="InfluxDB port (default: 8086)")
    influx_group.add_argument("--influxdb-database", default="powerlog",
                              help="InfluxDB database name (default: powerlog)")

    mqtt_group = parser.add_argument_group("MQTT")
    mqtt_group.add_argument("--mqtt", action="store_true", default=False,
                            help="Publish data via MQTT")
    mqtt_group.add_argument("--mqtt-host", default="localhost",
                            help="MQTT broker hostname (default: localhost)")
    mqtt_group.add_argument("--mqtt-port", type=int, default=1883,
                            help="MQTT broker port (default: 1883)")
    mqtt_group.add_argument("--mqtt-topic", default="lmgtools",
                            help="MQTT base topic (default: lmgtools)")

    args = parser.parse_args()

    if args.influxdb and not HAS_INFLUXDB:
        print("error: influxdb package not installed", file=sys.stderr)
        sys.exit(1)
    if args.mqtt and not HAS_MQTT:
        print("error: paho-mqtt package not installed", file=sys.stderr)
        sys.exit(1)

    influx = None
    if args.influxdb:
        influx = influxdb.InfluxDBClient(
            host=args.influxdb_host,
            port=args.influxdb_port,
            database=args.influxdb_database,
        )
        influx.create_database(args.influxdb_database)

    mqtt_client = None
    if args.mqtt:
        mqtt_client = mqtt.Client()
        mqtt_client.connect(args.mqtt_host, args.mqtt_port)
        mqtt_client.loop_start()
        publish_mqtt_discovery(mqtt_client, args.mqtt_topic)

    print("connecting to", args.host, "at port", args.port)
    lmg = lmg95.lmg95(args.host, args.port)

    print("performing device reset")
    lmg.cont_off()
    lmg.reset()

    print("device found:", lmg.read_id()[1])

    print("setting up device")
    lmg.read_errors()

    lmg.send_short_cmd(f"CYCL {args.interval}")

    if args.lowpass:
        lmg.send_short_cmd("FAAF 0")
        lmg.send_short_cmd("FILT 4")

    lmg.set_ranges(10., 250.)
    lmg.select_values(VAL)

    log = None
    if args.logfile:
        log = open(args.logfile, "w", encoding="utf-8")

    i = 0
    try:
        lmg.cont_on()
        if log:
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
            if log:
                log.write(" ".join([str(x) for x in data]) + "\n")
                log.flush()
            if influx:
                send_to_influxdb(influx, data)
            if mqtt_client:
                publish_mqtt_state(mqtt_client, args.mqtt_topic, data)
    except KeyboardInterrupt:
        print()

    lmg.cont_off()
    if log:
        log.close()
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    lmg.disconnect()
    print("done,", i, "measurements written")


if __name__ == "__main__":
    main()
