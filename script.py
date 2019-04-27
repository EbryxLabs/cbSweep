import os
import csv
import json
import time
import logging
import argparse
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handler)


def get_params():

    parser = argparse.ArgumentParser()
    parser.add_argument('ipfile', help='input file having IPs.')
    parser.add_argument('-host', help='host name of carbon black.')
    parser.add_argument('-token', help='auth token for carbon black REST API.')
    parser.add_argument('-duration', help='duration of interval to look '
        'the dataset into. [e.g. 1w, 2d, 5m]', default='1d')
    
    args = parser.parse_args()
    if not os.path.isfile(args.ipfile):
        logger.info('No ip file found on filesystem: %s', args.ipfile)
        exit(1)
    if not args.token:
        logger.info('Auth token, specified by -token <TOKEN>, cannot be empty.')
        exit(1)
    if not args.host:
        logger.info('Host, specified by -host <HOST>, cannot be empty.')
        exit(1)

    return args


def process_response(res):

    
    for item in res:
        return {
            'IP': item.get('netFlow', dict()).get('destAddress', str()),
            'Endpoint': item.get('deviceDetails', dict()).get('deviceName', str()),
            'Owner': item.get('deviceDetails', dict()).get('email', str()),
            'Time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
                item.get('createTime') / 1000)) if item.get('createTime') else str(),
            'Process': item.get('processDetails', dict()).get('name', str())
        }


def write_to(filename, data):
    
    if not data:
        logger.info('No data to write. Skipping csv writing.')
        return

    with open(filename, 'w') as f:
        writer = csv.writer(f)
        for idx, entry in enumerate(data):
            if idx == 0:
                header = list(entry.keys())
                writer.writerow(header)

            values = list()
            for item in header:
                values.append(entry[item])

            writer.writerow(values)
    logger.info('Data written to: %s', filename)


def make_sweep(params):

    event_url = urljoin('https://%s' % (params.host),
                        'integrationServices/v3/event')

    data = list()
    for ip in [x.strip('\n') for x in open(params.ipfile).readlines()]:
        res = requests.get(
            event_url + '?netFlow.destAddress=%s&rows=1'
            '&searchWindow=%s' % (ip, params.duration),
            headers={'X-AUTH-TOKEN': params.token})

        if res.status_code < 400:
            logger.info('Requested for ip [%s]: %s', ip, res)
            data.append(process_response(res.json().get('results')))
        else:
            logger.info('Request failed for [%s]: %s', ip, res)

    logger.info(str())
    write_to(params.ipfile + '.csv', data)
  

if __name__ == "__main__":
    params = get_params()
    make_sweep(params)
