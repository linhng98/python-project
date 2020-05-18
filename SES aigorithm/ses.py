import os
import sys
import time
import json
import socket


def get_abs_dir():
    return os.path.abspath(os.path.dirname(sys.argv[0]))


def process_job(sock, list_server):
    list_server.remove(sock)    # remove this process socket from list
    print(len(list_server))
    return


def main():
    main_process = True
    child_process = []
    list_server = []
    hostinfo_path = '{0}/config/socket-host.json'.format(get_abs_dir())

    with open(hostinfo_path) as fopen:
        list_host = json.load(fopen)

    for host_info in list_host["host_info"]:  # create list listen socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host_info["host"], host_info["port"]))
        sock.listen()
        list_server.append(sock)  # add list server socket to list

    # fork new process
    for sock in list_server:
        child = os.fork()
        if child:   # in main process, add child id to list
            child_process.append(child)
        else:  # in child process, do the job
            main_process = False
            process_job(sock, list_server)
            break

    if main_process:  # if main process, wait child process complete
        for child in child_process:
            os.waitpid(child, 0)

    return 0


if __name__ == "__main__":
    main()
