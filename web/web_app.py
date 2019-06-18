#!/usr/bin/env python3

import os
import sys
import argparse
import json

import bottle

import libweb


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))


@bottle.route('/', method='GET')
def main():
    return bottle.template('index.html', reports=libweb.available_reports())


@bottle.route('/static/<filepath:path>', method='GET')
def static_files(filepath):
    return bottle.static_file(filepath, root=os.path.join(PROJECT_DIR, 'static'))


@bottle.route('/favicon.ico', method='GET')
def favicon():
    return bottle.static_file('malware.png', root=os.path.join(PROJECT_DIR, 'static'))


@bottle.route('/experiment/create', method='POST')
def create_experiment():
    json_args = bottle.request.json
    status = 400
    body = ''
    if json_args:
        status, resp = libweb.run_experiment(json_args)

        return bottle.HTTPResponse(status=status, body=json.dumps({'status': resp}))

    return bottle.HTTPResponse(status=status, body=json.dumps({'status': body}) if body else '')


@bottle.route('/experiment/<date>', method='GET')
def get_experiment(date):
    if os.path.isdir(os.path.join(PROJECT_DIR, '..', 'results', date)):
        status_report = libweb.get_experiment_report(os.path.join(PROJECT_DIR, '..', 'results', date))
        return bottle.template('report.html', report=status_report)
    return bottle.HTTPResponse(status=404, body='Nothing here')


@bottle.route('/experiment/lastest', method='GET')
def status_experiment():
    status, response = libweb.get_status_experiment()
    
    bottle.response.content_type = 'application/json'
    return bottle.HTTPResponse(status=status, body=json.dumps({'status': response}))


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('-i', '--interface', default='0.0.0.0')
    args.add_argument('-p', '--port', type=int, default=8080)
    args.add_argument('-lf', '--log_file', default='webapp.log')

    argp = args.parse_args()

    libweb.start_webapp(argp.interface, argp.port, argp.log_file)

