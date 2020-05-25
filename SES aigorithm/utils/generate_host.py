import sys
import os
import json


def gen_host(numProc, absPath):
    data = {}
    data['host_info'] = []

    for i in range(numProc):
        portNumber = 55500+i
        data['host_info'].append({
            'host': '127.0.0.1',
            'port': portNumber
        })
    with open(absPath, "w") as fw:
        json.dump(data, fw, indent=2)
