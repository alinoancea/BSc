#!/usr/bin/env

import os
import sys
import datetime
import json
import threading

import bottle

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')

import lib.vboxmachine as vboxmachine
from exception import VBoxLibException


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__)) + '/..'
TASKS = []



class LogFile:


    def __init__(self, filename):
        self.filename = filename
        line = '=' * 80
        time = datetime.datetime.now()
        open(self.filename, 'a').write('%s\nServer started @ %s\n%s\n' % (line, time.strftime("%m/%d/%Y, %H:%M:%S"),
                line))


    def write(self, s):
        open(self.filename, 'a').write(s)


    def flush(self):
        pass



class ExperimentTask(threading.Thread):


    def __init__(self, vm_name, vm_snapshot, vm_username, vm_password, malware_file):
        super().__init__()
        self.name = vm_name
        self.snapshot = vm_snapshot
        self.username = vm_username
        self.password = vm_password
        self.sample = malware_file
        self.finish = False
        self.response = 'done'


    def run(self):
        try:
            vbx = vboxmachine.VBoxMachine(self.name, self.snapshot, self.username, self.password, self.sample)

            vbx.restore_snapshot()
            vbx.launch()
            vbx.deploy_necessary_files()
            vbx.launch_client_app()
            vbx.power_off()
        except VBoxLibException as e:
            try:
                vbx.power_off()
            except:
                pass
            self.response = str(e)
        
        self.finish = True



def start_webapp(interface='0.0.0.0', port=8080, logfile='webapp.log'):
    if not os.path.isdir('logs'):
        os.mkdir('logs')

    sys.stdout = sys.stderr = LogFile(os.path.join('logs', logfile))
    bottle.run(host=interface, port=port)


def available_reports():
    reports_path = os.path.join(PROJECT_DIR, 'results')
    results = []

    r, d, _ = next(os.walk(reports_path))
    for dr in d:
        try:
            one_experiment = {
                'date': dr
            }
            info = json.loads(open(os.path.join(r, dr, 'info.json')).read())
            one_experiment['sample'] = os.path.basename(info['malware'])

            results.append(one_experiment)
        except:
            continue

    return results


def run_experiment(args):
    if TASKS and TASKS[-1].finish:
        t = ExperimentTask(**args)
        TASKS.append(t)
        t.start()
        return 200, 'ok'
    elif not TASKS:
        t = ExperimentTask(**args)
        TASKS.append(t)
        t.start()
        return 200, 'ok'
    else:
        return 400, 'Task already in progess!'


def get_status_experiment():
    if TASKS:
        if TASKS[-1].finish:
            return 200, TASKS[-1].response
        else:
            return 200, 'in progress'
    return 200, 'no tasks'


def get_experiment_report(report_path):
    rsp = {
        'date': os.path.basename(report_path)
    }
    rsp.update(json.loads(open(os.path.join(report_path, 'info.json')).read()))
    rsp.update({'folders': open(os.path.join(report_path, 'logs', 'folder_changes.txt')).read().split('\n')})
    rsp.update({'registry': open(os.path.join(report_path, 'logs', 'registry_changes.txt')).read().split('\n')})

    return rsp

