import logging
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.ioloop
import time
import json

import mako.lookup

from redis import StrictRedis
import rons



listen_port          = 9999
listen_address       = '0.0.0.0'
redis_address        = {'host':'127.0.0.1', 'port':6379, 'password':None, 'db':0}

template_directories = ['.']
cache_directory      = './tmp'



FORMAT_CONS = '%(asctime)s %(name)-12s %(levelname)8s\t%(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT_CONS)

log = logging.getLogger('site-p0f')


redis       = StrictRedis(**redis_address)
rons_client = rons.Client('redis://:%(password)s@%(host)s:%(port)s/%(db)s' % redis_address)


template_lookup = mako.lookup.TemplateLookup(directories=template_directories,
                                             output_encoding='utf-8',
                                             encoding_errors='replace')



class MyRequestHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        del self._headers['Server']

    def remote_address(self):
        forwarded_for = self.request.headers.get('X-Forwarded-For','')
        forwarded_for = forwarded_for.split(' ')[-1].split(',')[-1]
        if forwarded_for and ':' in forwarded_for:
            ip, port = forwarded_for.split(':', 1)
            return '%s/%s' % (ip, port)
        return None

    def local_address(self):
        ip, port = self.request.connection.address
        return '%s/%s' % (ip, port)


class Index(MyRequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    @rons.save_generator
    def get(self):
        needed = [(self.local_address(), 'http request')]
        if self.remote_address():
            needed.append( (self.remote_address(), 'ssl request') )
        while needed:
            data = redis.hget(needed[0][0], needed[0][1])
            if not data:
                print 'yield', needed[0]
                data = yield tornado.gen.Task( rons_client.subscribe, '%s %s' % needed[0])
            if data:
                needed.pop(0)
        
        local_data  = redis.hgetall(self.local_address()) 
        remote_data = redis.hgetall(self.remote_address()) 
        redis.delete(self.local_address(), self.remote_address())

        for key, value in local_data.iteritems():
            local_data[key] = json.loads(value)
        for key, value in remote_data.iteritems():
            remote_data[key] = json.loads(value)

        ctx = {
            'remote_address': self.remote_address(),
            'local_address': self.local_address(),
            'remote_data': remote_data,
            'local_data': local_data,
            }
        mytemplate = template_lookup.get_template("index.html")
        self.finish(mytemplate.render(**ctx))

    def on_connection_close(self):
        rons.stop_generator(self)



class Save(MyRequestHandler):
    def post(self):
        dd = {'address': get_address(self),
              'real_agent': self.request.headers.get('User-Agent', None)}
        for k in ['sig', 'domain', 'agent', 'os', 'browser', 'version', 'extra']:
            dd[k] = self.get_argument(k, None)
        name = 'submit-%s.txt' % (time.time(),)
        with open(name, 'w') as f:
            f.write(json.dumps(dd, sort_keys=True, indent=4))
        self.write('Got it, thanks!')



def run():
    application = tornado.web.Application([
            (r"/",         Index),
            (r"/save.cgi", Save),
            ])
    log.info("Listening on http://%s:%s" % (listen_address, listen_port))
    application.listen(listen_port, listen_address, no_keep_alive=True)
    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    run()
