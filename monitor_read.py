import requests
import time
import sys

speed = '0'
cpu = '0'
backoff = 2
while(True):
    try:
        sys.stdout.write('\r')
        sys.stdout.flush()
        res = requests.get('http://127.0.0.1:8080')
        backoff = 2
        f_speed, f_sum, s_speed, s_sum, cpu = res.text.split(',')
        print('\rFiltered Speed: ' + f_speed + " Sum: " + f_sum + ' Saved Speed: ' + s_speed + ' Sum: ' + s_sum + ' CPU: ' + cpu, end='  ')
        time.sleep(1)
    except:
        for i in range(backoff):
            print('\rConnection Error... retrying in '
                  + str(backoff - i - 1) + '/'
                  + str(backoff) + ' Seconds\t', end='')
            time.sleep(1)
        backoff *= 2
