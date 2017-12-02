import random
import string
import cherrypy
import cpu_usage
import os
import json

pid_list = list()

@cherrypy.expose
class StringGeneratorWebService:
    speed = 0.0
    cpu = '0'
    sum = '0'
    f_speed = 0
    f_sum = 0
    s_speed = 0
    s_sum = 0
    @cherrypy.tools.accept(media='text/plain')
    def GET(self):
        if len(pid_list) == 0:
            return self.speed
        else:
            pids = cpu_usage.get_python_usage()
            cpu_sum = 0
            alive = 0
            dead = 0
            for i in pids:
                cpu_sum += float(pids[i])
            return format(self.f_speed, '.2f') + ',' + str(self.f_sum) + ',' + format(self.s_speed, '.2f') + ',' + str(self.s_sum) + ',' + format(cpu_sum, '.2f')

    def POST(self, length=8):
        some_string = ''.join(random.sample(string.hexdigits, int(length)))
        cherrypy.session['speed'] = some_string
        return some_string

    def PUT(self, status):
        print(status)
        print(type(status))
        self.s_speed = json.loads(status)['SAVED_speed']
        self.s_sum = json.loads(status)['SAVED_sum']
        self.f_speed = json.loads(status)['FILTERED_speed']
        self.f_sum = json.loads(status)['FILTERED_sum']

    def DELETE(self):
        cherrypy.session.pop('mystring', None)


def start_server():
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    cherrypy.quickstart(StringGeneratorWebService(), '/', conf)


def set_pid_list(input):
    for i in input:
        pid_list.append(i)

def run_server():
    input_pid_list = []
    input_pid_list.append(str(os.getpid()))
    set_pid_list(input_pid_list)
    start_server()

if __name__ == '__main__':
    run_server()
