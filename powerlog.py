#!/usr/bin/python

# powerlog.py
#
# Log measured values from ZES Zimmer LMG95 Power Meter
#
# 2012-07, Jan de Cuveland

import argparse, sys, time, lmg95

VAL = "count sctc cycr utrms itrms udc idc ucf icf uff iff p pf freq".split()

def main():
    parser = argparse.ArgumentParser(
        description = "Log measured values from ZES Zimmer LMG95 Power Meter")
    parser.add_argument("host", help = "Hostname of RS232-Ethernet converter")
    parser.add_argument("logfile", help = "Log file name")
    parser.add_argument("-p", "--port", dest = "port", type = int, default=2101,
                        help = "TCP port of RS232-Ethernet converter")
    args = parser.parse_args()

    print "connecting to", args.host, "at port", args.port
    lmg = lmg95.lmg95(args.host, args.port)
     
    print "performing device reset"
    lmg.reset()
     
    print "device found:", lmg.read_id()[1]

    print "setting up device"
    errors = lmg.read_errors()
    lmg.set_ranges(10., 250.)
    lmg.select_values(VAL)

    log = open(args.logfile, "w");
    i = 0
    try:
        lmg.cont_on()
        log.write("# time " + " ".join(VAL) + "\n")
        print "writing values to", args.logfile
        print "press CTRL-C to stop"
        while True:
            data = lmg.read_values()
            i += 1
            sys.stdout.write("\r{}".format(i))
            sys.stdout.flush()
            data.insert(0, time.time())
            log.write(" ".join([ str(x) for x in data ]) + "\n")
    except KeyboardInterrupt:
        print
     
    lmg.cont_off()
    log.close()

    lmg.disconnect()
    print "done,", i, "measurements written"


if __name__ == "__main__":
    main()
