import os
import sys
import time
import json
import socket
import threading

lock = threading.Lock()
number_thread = 2
number_message = 2


def get_abs_dir():
    return os.path.abspath(os.path.dirname(sys.argv[0]))


def thread_job(params, idx):
    this_pos = params["this_pos"]
    vector_time = params["vector_time"]
    count_msg = params["count_msg"]
    host = params["host"]

    while count_msg[idx] < number_message:
        msg_content = {"content": "msg {0} from process {1}".format(
            count_msg[idx], this_pos+1)}

        buffer = json.dumps(msg_content, separators=(',', ':'))
        package = bytes("{0}\r\n{1}".format(len(buffer), buffer), "utf-8")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(host[idx])
            s.sendall(package)

        lock.acquire()
        vector_time[this_pos] += 1
        lock.release()

        count_msg[idx] += 1

    return


def process_job(sock, list_tuple_host, this_pos):

    # remove this host from list tuple
    list_tuple_host.remove(sock.getsockname())
    vector_time = [0]*(len(list_tuple_host)+1)
    count_msg = [0]*len(list_tuple_host)
    v_p = "V_P"+str(this_pos+1)
    list_thread = []

    params = {  # init params share between thread
        "vector_time": vector_time,
        "host": list_tuple_host,
        "count_msg": count_msg,
        "this_pos": this_pos,
        v_p: {}
    }

    for i in range(number_thread):  # create thread, detach
        x = threading.Thread(target=thread_job, args=[params, i], daemon=True)
        x.start()
        list_thread.append(x)

    count_recv_pkg = 0
    while count_recv_pkg < len(list_tuple_host)*number_message:
        conn, _ = sock.accept()
        list_char = []
        with conn:
            while True:
                list_char.append(conn.recv(1).decode("utf-8"))
                if len(list_char) > 2:
                    if list_char[-1] == '\n' and list_char[-2] == '\r':
                        list_char.pop()
                        list_char.pop()
                        break

            pkglen = int(''.join(list_char))
            pkg = conn.recv(pkglen).decode("utf-8")
            print(pkg)
            count_recv_pkg += 1

    for thread in list_thread:
        thread.join()
        
    sock.close()    # close socket
    return


def main():
    main_process = True
    child_process = []
    list_server_sock = []
    list_tuple_host = []
    hostinfo_path = '{0}/config/socket-host.json'.format(get_abs_dir())

    with open(hostinfo_path) as fopen:
        list_host = json.load(fopen)

    for host_info in list_host["host_info"]:
        list_tuple_host.append((host_info["host"], host_info["port"]))

    for host_tuple in list_tuple_host:  # create list listen socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(host_tuple)
        sock.listen()
        list_server_sock.append(sock)  # add list server socket to list

    # fork new process
    pos = 0
    for sock in list_server_sock:
        child = os.fork()
        if child:   # in main process, add child id to list
            child_process.append(child)
            pos += 1
        else:  # in child process, do the job
            main_process = False
            process_job(sock, list_tuple_host, pos)
            break

    if main_process:  # if main process, wait child process complete
        for child in child_process:
            os.waitpid(child, 0)

    return 0


if __name__ == "__main__":
    main()
