#!/usr/bin/python3

import json
import argparse

#
# Parse command line arguments
#
parser = argparse.ArgumentParser(description='Parse a Kanban exported from workon.')
parser.add_argument('-b', '--backlog', dest='backlog', action='store_true', default=False,
                    help='Display the backlog')
parser.add_argument('-i', '--inprog', dest='inprog', action='store_true', default=False,
                    help='Display in progress')
parser.add_argument('-c', '--complete', dest='complete', action='store_true', default=False,
                    help='Display complete')
parser.add_argument('infile', help='path to the exported Kanban (json)')
args = parser.parse_args()

if args.backlog == False and args.inprog == False and args.complete == False:
    args.backlog = True
    args.inprog = True
    args.complete = True


try:
    with open(args.infile,'r') as fp:
        kanban = json.load(fp)

        for kb,attr in kanban.items():
            print("{}".format(kb))
            for col in attr['columns']:
                if (args.backlog and col['name'] == 'Backlog'):
                    print("\tBacklog")
                    for card in col['cards']:
                        print('\t\t{}'.format(card['name']))

                if (args.inprog and col['name'] == 'In Progress'):
                    print("\tIn Progress")
                    for card in col['cards']:
                        print('\t\t{}'.format(card['name']))

                if (args.complete and col['name'] == 'Complete'):
                    print("\tComplete")
                    for card in col['cards']:
                        print('\t\t{}'.format(card['name']))


except Exception as e:
    parser.print_help()
    print("Exception {}".format(e))
