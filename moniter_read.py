import requests
import time

speed = '0'
cpu = '0'
backoff = 2
while(True):
    try:
        sys.stdout.write('\r')
        sys.stdout.flush()
        res = requests.get('http://127.0.0.1:8080')
        backoff = 2
        speed, cpu, alive, dead = res.text.split(',')
        print('\rSpeed: ' + speed + ' CPU: ' + cpu + ' ' + alive + ' ' + dead, end='')
        time.sleep(1)
    except:
        for i in range(backoff):
            print('\rConnection Error... retrying in '
                  + str(backoff - i - 1) + '/'
                  + str(backoff) + ' Seconds\t', end='')
            time.sleep(1)
        backoff *= 2
