import os
import requests
import psutil
import time
import os
import subprocess
import json

class Logger:
    curr_file = None
    curr_file_size = 0
    agg_dict = {}

    def __init__(self, columns):
        self.create_new_log_file(columns)

    def create_new_log_file(self, columns):
        if self.curr_file is not None:
            self.curr_file.close()
        self.curr_file = time.strftime('%Y-%m-%d %H:%M:%S.csv',
                                       time.localtime(time.time()))
        self.curr_file = open(self.curr_file, 'w')
        self.curr_file_size = 0
        header = ''
        for i in columns:
            header += i + ','
        self.curr_file.write(header[:-1]+'\n')

    def add_agg_type(self, type, agg):
        '''
        Adds a filter for aggregation
        'speed' = Number of Logs in a short period
        'sum' = Number of Logs from start
        '''
        if agg == 'speed':
            self.agg_dict[type + '_' + agg] = list()
        elif agg == 'sum':
            self.agg_dict[type + '_' + agg] = 0
        else:
            print('No such aggregation type!!')

    def send_status(self):
        status = {}
        for i in self.agg_dict:
            if type(self.agg_dict[i]) == int:

                status[i] = self.agg_dict[i]
            else:
                if len(self.agg_dict[i]) == 0:
                    status[i] = 0
                else:
                    print(i, self.agg_dict[i])
                    length = len(self.agg_dict[i])
                    status[i] = length / (time.time() - self.agg_dict[i][0])
                    print(length, time.time() - self.agg_dict[i][0])
                    if length > 200:
                        self.agg_dict[i] = (self.agg_dict[i])[100:]
        requests.put('http://127.0.0.1:8080', params={'status': json.dumps(status)})

    def log(self, log_entry):
        '''
        log_entry : {
            'time': #float epoch time,
            'type': One of {
                        'SAVED',
                        'FAILED_TO_SAVE',
                        'FAILED_AT',
                        'FILTERED'
                    }
            'name': name of the file or name of the point of failure
        }
        '''
        if self.curr_file_size > 50000:
            self.create_new_log_file()
        if (log_entry['type'] + '_speed') in self.agg_dict:
            (self.agg_dict[log_entry['type'] + '_speed']).append(log_entry['time'])
        if (log_entry['type'] + '_sum') in self.agg_dict:
            self.agg_dict[log_entry['type'] + '_sum'] += 1
        log_ = time.strftime('%Y-%m-%d %H:%M:%S.%u', time.localtime(log_entry['time']))
        log_ += ',' + log_entry['type']
        log_ += ',' + log_entry['name']
        self.curr_file.write(log_ + '\n')
        self.curr_file_size += 1

    def close(self):
        self.curr_file.close()
