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
        'the dataset into.', default='1d', choices=['3h', '1d', '1w', '2w'])
    
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


def process_response(res, ips):

    return [{
        'IP': item.get('netFlow', dict()).get('destAddress', str()),
        'Endpoint': item.get('deviceDetails', dict()).get('deviceName', str()),
        'Owner': item.get('deviceDetails', dict()).get('email', str()),
        'Time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(
            item.get('createTime') / 1000)) if item.get('createTime') else str(),
        'Process': item.get('processDetails', dict()).get('name', str())
    } for item in res if item.get('netFlow', dict()).get(
        'destAddress', str()) in ips]


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
    ips = [x.strip('\n').strip(' ') for x in open(
        params.ipfile).readlines()]

    data = list()
    iter_count = 0
    data_count = 10000
    while (not data_count or len(data) < data_count) and iter_count < 3:
        url = event_url + '?eventType=NETWORK&start=%d&rows=%s' \
            '&searchWindow=%s' % (len(data) + 1, len(data) + 5000, params.duration)

        res = requests.get(url, headers={'X-AUTH-TOKEN': params.token})
        data_count = res.json().get('totalResults') \
            if not data_count else data_count

        if res.status_code < 400:
            iter_count = 0
            results = res.json().get('results')
            data.extend(process_response(results, params))
            logger.info('[%d/%d] entries fetched.', len(data), data_count)
        else:
            logger.info('%s, Request failed: %s', res, url)

        iter_count += 1
        time.sleep(20)

    logger.info(str())
    write_to(params.ipfile + '.csv', data)
  

if __name__ == "__main__":
    params = get_params()
    make_sweep(params)
