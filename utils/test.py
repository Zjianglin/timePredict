# -*- coding: utf-8 -*-
import footprint
import sys, os
from petri_net import PetriNet

def main(argv):
    log = []
    with open(argv[1], 'r') as f:
        lines = f.readlines()
        for line in lines:
            log.append(line.strip().split(' '))
    print("Log:\n", log)
    print("---------------------")
    lm = footprint.Alpha(log)
    print(lm)
    pn = PetriNet()
    pn.from_alpha(lm, dotfile="{}.dot".format(os.path.basename(argv[1])))


if __name__ == "__main__":
    main(sys.argv)

