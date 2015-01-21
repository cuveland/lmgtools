#!/usr/bin/python

# powerlog670.py
#
# Log measured values from ZES Zimmer LMG670 Power Analyzer
#
# 2015-01, Jan de Cuveland

import argparse, sys, lmg670

VAL = "tsnorm durnorm utrms itrms udc idc ucf icf uff iff p pf fcyc".split()
VAL = [v + str(c) for c in range(1, 7) for v in VAL]

def main():
    parser = argparse.ArgumentParser(
        description = "Log measured values from ZES Zimmer LMG670 Power Meter")
    parser.add_argument("host", help = "Hostname of LMG670")
    parser.add_argument("logfile", help = "Log file name")
    args = parser.parse_args()

    print "connecting to", args.host
    lmg = lmg670.lmg670(args.host)

    print "performing device reset"
    lmg.reset()

    print "device found:", lmg.read_id()[1]

    print "setting up device"
    lmg.set_ranges(10.0, 250.0)
    lmg.select_values(VAL)

    log = open(args.logfile, "w");
    i = 0
    try:
        lmg.cont_on()
        log.write("# " + " ".join(VAL) + "\n")
        print "writing values to", args.logfile
        print "press CTRL-C to stop"
        while True:
            data = lmg.read_raw_values()
            i += 1
            sys.stdout.write("\r{0}".format(i))
            sys.stdout.flush()
            log.write(" ".join(data) + "\n")
    except KeyboardInterrupt:
        print

    lmg.cont_off()
    log.close()

    lmg.disconnect()
    print "done,", i, "measurements written"


if __name__ == "__main__":
    main()
