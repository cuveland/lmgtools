#!/usr/bin/python

# powerlog670.py
#
# Log measured values from ZES Zimmer LMG670 Power Analyzer
#
# 2015-01, Jan de Cuveland

import argparse, sys, time, lmg670

VAL = "tsnorm durnorm utrms itrms udc idc ucf icf uff iff p pf fcyc".split()
VAL = [v + str(c) for c in range(1, 7) for v in VAL]

def main():
    parser = argparse.ArgumentParser(
        description = "Log measured values from ZES Zimmer LMG670 Power Meter")
    parser.add_argument("host", help = "Hostname of LMG670")
    parser.add_argument("logfile", help = "Log file name")
    parser.add_argument("-v", "--verbose", dest = "verbose", type = int, default=0, help = "Verbose")
    parser.add_argument("-i", "--interval", dest="interval", type=float, default=0.5,
                        help = "Measurement interval in seconds")
    args = parser.parse_args()

    print "connecting to", args.host
    lmg = lmg670.lmg670(args.host)

    print "performing device reset"
    lmg.reset()

    print "device found:", lmg.read_id()[1]

    print "setting up device"

    # set measuremnt interval
    lmg.send_short_cmd("CYCL " + str(args.interval));

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
            data.insert(0, time.time())
            if args.verbose >= 2:
                sys.stdout.write(" ".join([ str(x) for x in data ]) + "\n") #Output too long
            elif args.verbose:
                sys.stdout.write(" " + str(data[0]))
                for j in range(0, (len(data) - 1) / 13):
                    if float(data[j * 13 + 11]) > 0.1:
                        sys.stdout.write(" " + '%08f' % float(data[j * 13 + 11]) + " "  + '%08f' % float(data[j * 13 + 2]))
                sys.stdout.write("\n")
            else:
                sys.stdout.write("\r{0}".format(i))
            sys.stdout.flush()
            log.write(" ".join([ str(x) for x in data ]) + "\n")
            log.flush()
    except KeyboardInterrupt:
        print

    lmg.cont_off()
    log.close()

    lmg.disconnect()
    print "done,", i, "measurements written"


if __name__ == "__main__":
    main()
