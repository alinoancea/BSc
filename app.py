#!/usr/bin/env python3

import argparse
import os
import json
import sys

# GLOBALS
PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))


def is_valid_path(parser, argument):
    if not os.path.isfile(argument):
        parser.error('file [%s] does not exist!' % (argument,))
    return argument


parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help='set configuration file with VMs')
parser.add_argument('-vm', '--vm_name', help='set VM name', required='--config' not in sys.argv)
parser.add_argument('-ss', '--snapshot', help='set which snapshot to revert')
parser.add_argument('-u', '--username', help='set username for VM', required='--config' not in sys.argv)
parser.add_argument('-p', '--password', help='set password for VM', required='--config' not in sys.argv)
parser.add_argument('-s', '--sample', help='set which sample to deploy on VM',
        required='--config' not in sys.argv, type=lambda x: is_valid_path(parser, x))


if __name__ == '__main__':
    args = parser.parse_args()
    vms = []

    if args.config:
        if os.path.isfile(args.config):
            try:
                config_file = json.loads(open(args.config).read())

                for e in config_file:
                    if 'name' not in e and not args.vm_name:
                        print('[!] Missing VM name from:\n%s' % (json.dumps(e, indent=4),))
                        continue
                    if ('username' not in e or 'password' not in e) and not (args.username and args.password):
                        print('[!] Missing username/password from:\n%s' % (json.dumps(e, indent=4),))
                        continue
                    if 'sample' not in e and not args.sample:
                        print('[!] Missing sample from:\n%s' % (json.dumps(e, indent=4),))
                        continue

                    vms.append({
                        'name': e.get('name') or args.vm_name,
                        'username': e.get('username') or args.username,
                        'password': e.get('password') or args.password,
                        'sample': e.get('sample') or args.sample,
                        'snapshot': e.get('snapshot') or args.snapshot
                    })
            except Exception as e:
                print('[!] [%s] is not a valid JSON file!\nERROR: %s' % (args.config, str(e)))
                sys.exit(-1)
        else:
            print('[!] [%s] is not a valid path!' % (args.config,))
            sys.exit(-1)
    else:
        vms.append({
            'name': args.vm_name,
            'username': args.username,
            'password': args.password,
            'sample': args.sample,
            'snapshot': args.snapshot
        })

    print(vms)
