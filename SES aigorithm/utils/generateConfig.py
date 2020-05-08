import sys
import os

configFormat = '''- process{0}:
    host: "127.0.0.1"
    port: 555{1}
'''

absPath = os.path.abspath(os.path.dirname(sys.argv[0]))
numProc = 15
if len(sys.argv) > 1:
    numProc = int(sys.argv[1])

with open('{}/config.generated'.format(absPath), "w") as fw:
    for i in range(numProc):
        fw.write(configFormat.format(i+1, "{:02d}".format(i+1)))
