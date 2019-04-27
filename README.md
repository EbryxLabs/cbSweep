# cbSweep
A short program to get latest event of IPs from carbon black using REST API.

Usage is as follows:
```
python script.py -host <CARBON_BLACK_HOST> -token <API_AUTH_TOKEN> \  
-duration <SEARCH_WINDOW> <input-file-having-ips>
```
Empty `host`, `token` will result in an error while an empty `duration` will defaults to `1d` of search window for REST API.
  
Input file given to script for ips can be of following format:
```
1.1.1.1
2.2.2.2
<ip-per-line>
...
```

## Pre-Requisites
You just need `requests` external module of python to make it work. You can simply call:
```
pip install -r requirements.txt
```

## Help
```
usage: script.py [-h] [-host HOST] [-token TOKEN] [-duration DURATION] ipfile

positional arguments:
  ipfile              input file having IPs.

optional arguments:
  -h, --help          show this help message and exit
  -host HOST          host name of carbon black.
  -token TOKEN        auth token for carbon black REST API.
  -duration DURATION  duration of interval to look the dataset into. [e.g. 1w, 2d, 5m]
```