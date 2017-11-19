import subprocess


def get_python_usage():
    cmd = ("ps aux | grep python | grep -v grep | awk '{print $2, $3}'")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    outwithoutreturn = (str(out, 'utf-8').rstrip('\n')).split('\n')
    dict = {}
    for i in outwithoutreturn:
        pid, usage = i.split(' ')
        dict[pid] = usage
    return dict


if __name__ == '__main__':
    print(get_python_usage())
