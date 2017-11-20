import logger
import time

if __name__ == '__main__':
    counter = 0
    logger = logger.Logger(('time', 'type', 'name'))
    logger.add_agg_type('SAVED', 'speed')
    logger.add_agg_type('SAVED', 'sum')
    while(True):
        time.sleep(0.15)
        log_entry = {'time': time.time(), 'type': 'SAVED', 'name': str(counter)}
        logger.log(log_entry)
        logger.send_status()
        counter += 1
