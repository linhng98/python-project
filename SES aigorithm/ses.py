import os
import sys
import time
import json
import socket
import threading
import copy
import random
import utils.generate_host as utlh
import shutil
import os


lock = threading.Lock()
number_message = 150
number_host = 15


def get_abs_dir():
    return os.path.abspath(os.path.dirname(sys.argv[0]))


def compare_vector_time(vtA, vtB, pid):
    # 0 mean A >= B
    # 1 mean A < B
    if vtB == None:
        return 0

    if vtA == None:
        return 1

    for i in range(len(vtA)):
        if i != pid and vtB[i] > vtA[i]:
            return 1

    return 0

# merge vtB to vtA


def merge_vector_time(vtA, vtB):
    for i in range(len(vtA)):
        if vtB[i] > vtA[i]:
            vtA[i] = vtB[i]
    return


# merge vpB to vpA
def merge_list_vp(vpA, vpB, pid):
    for key in vpB:
        if key == "P{0}".format(pid+1):
            continue
        if vpA.get(key) == None:  # vt not exits
            vpA[key] = copy.deepcopy(vpB[key])
        else:   # vt exist, just merge
            merge_vector_time(vpA[key], vpB[key])

    return


def buffer_insert_package(buffer_pkg, pkg, pid):
    if len(buffer_pkg) == 0:  # list empty
        buffer_pkg.append(pkg)
    else:
        vtB = pkg["V_P"].get("P{0}".format(pid+1))
        for i in range(len(buffer_pkg)):
            vtA = buffer_pkg[i]["V_P"].get("P{0}".format(pid+1))
            if compare_vector_time(vtA, vtB, pid) == 0:
                buffer_pkg.insert(i, pkg)
                return
        buffer_pkg.append(pkg)


def thread_job(params, idx):
    pid = params["pid"]
    vector_time = params["vector_time"]
    count_msg = params["count_msg"]
    host = params["host"]
    v_p = params["V_P"]

    while count_msg[idx] < number_message:
        # send message, increase vector time
        lock.acquire()
        vector_time[pid] += 1

        msg_content = {"from_pid": pid+1,
                       "vector_time": copy.deepcopy(vector_time),
                       "V_P": copy.deepcopy(v_p),
                       "content": "msg {0} from process {1}".format(count_msg[idx]+1, pid+1)}

        # update vector process
        v_p["P{0}".format(idx+1)] = copy.deepcopy(vector_time)
        lock.release()

        buffer = json.dumps(msg_content, separators=(',', ':'))
        package = bytes("{0}\r\n{1}".format(len(buffer), buffer), "utf-8")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            sec = random.randint(0, 1000)/10000
            time.sleep(sec)
            s.connect(host[idx])
            s.sendall(package)

        count_msg[idx] += 1

    return


def process_job(sock, list_tuple_host, pid):
    number_host = len(list_tuple_host)
    vector_time = [0]*number_host
    count_msg = [0]*number_host
    list_thread = []
    number_thread = number_host-1
    buffer_pkg = []
    v_p = {}

    params = {  # init params share between thread
        "vector_time": vector_time,
        "host": list_tuple_host,
        "count_msg": count_msg,
        "pid": pid,
        "V_P": v_p
    }

    for i in range(number_thread+1):  # create thread, detach
        if i == pid:
            continue
        x = threading.Thread(target=thread_job, args=[params, i], daemon=True)
        x.start()
        list_thread.append(x)

    count_recv_pkg = 0
    fw = open("{0}/log/process_{1}.log".format(get_abs_dir(), pid+1), "w")
    while count_recv_pkg < (len(list_tuple_host)-1)*number_message:
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
            pkg_str = conn.recv(pkglen).decode("utf-8")

        pkg_content = json.loads(pkg_str)   # receive pkg, add to buffer

        fw.write("vt: {0}\n".format(vector_time))
        fw.write(pkg_str+"\n")
        if compare_vector_time(vector_time, pkg_content["V_P"].get("P{0}".format(pid+1)), pid) == 0:
            # log
            fw.write("{0} >= {1}\n".format(
                vector_time, pkg_content["V_P"].get("P{0}".format(pid+1))))
            fw.write("status: DELIVER\n")

            lock.acquire()
            merge_vector_time(vector_time, pkg_content["vector_time"])
            merge_list_vp(v_p, pkg_content["V_P"], pid)
            vector_time[pid] += 1
            lock.release()

            fw.write("updated vt: {0}\n".format(vector_time))
            fw.write("===================================================>\n\n")

            while(1):
                if len(buffer_pkg) == 0:  # buffer empty
                    break

                fpkg = buffer_pkg[0]   # get first package from buffer
                vpB = fpkg["V_P"]

                # check if this package can be deliver or not
                if compare_vector_time(vector_time, vpB.get("P{0}".format(pid+1)), pid) == 0:
                    # log
                    fw.write("vt: {0}\n".format(vector_time))
                    fw.write("GET PACKAGE FROM BUFFER\n")
                    fw.write("{0}\n".format(
                        json.dumps(fpkg, separators=(',', ':'))))
                    fw.write("{0} >= {1}\n".format(
                        vector_time, vpB.get("P{0}".format(pid+1))))
                    fw.write("status: RE-DELIVER\n")

                    lock.acquire()
                    merge_vector_time(vector_time, fpkg["vector_time"])
                    merge_list_vp(v_p, vpB, pid)
                    vector_time[pid] += 1
                    lock.release()

                    fw.write("updated vt: {0}\n".format(vector_time))
                    fw.write(
                        "===================================================>\n\n")

                    del buffer_pkg[0]   # remove first pkg
                    continue
                else:   # cant not deliver first package in buffer
                    break
        else:
            buffer_insert_package(buffer_pkg, pkg_content, pid)
            fw.write("{0} < {1}\n".format(
                vector_time, pkg_content["V_P"].get("P{0}".format(pid+1))))
            fw.write("status: BUFFER\n")
            fw.write("===================================================>\n\n")

        count_recv_pkg += 1

    fw.close()
    for thread in list_thread:
        thread.join()

    sock.close()    # close socket
    return


def main():
    global number_host
    global number_message
    n = len(sys.argv)
    if n >= 3:
        number_host = int(sys.argv[1])
        number_message = int(sys.argv[2])
    elif n >= 2:
        number_host = int(sys.argv[1])
    # generate host
    utlh.gen_host(number_host, "{0}/config/socket-host.json".format(get_abs_dir()))

    main_process = True
    child_process = []
    list_server_sock = []
    list_tuple_host = []
    hostinfo_path = '{0}/config/socket-host.json'.format(get_abs_dir())

    # clean log
    log_path = "{0}/log".format(get_abs_dir())
    shutil.rmtree(log_path)
    os.mkdir(log_path)

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
    pid = 0
    for sock in list_server_sock:
        child = os.fork()
        if child:   # in main process, add child id to list
            child_process.append(child)
            pid += 1
        else:  # in child process, do the job
            main_process = False
            process_job(sock, list_tuple_host, pid)
            break

    if main_process:  # if main process, wait child process complete
        for child in child_process:
            os.waitpid(child, 0)

    return 0


if __name__ == "__main__":
    main()
