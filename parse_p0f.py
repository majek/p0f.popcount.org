#!/usr/bin/env python

import json

from redis import StrictRedis

redis_address = {'host':'127.0.0.1', 'port':6379, 'password':None, 'db':0}
redis         = StrictRedis(**redis_address)


while True:
    try:
        line = raw_input()
    except EOFError:
        break

    a,b, rest = line.split(' ', 2)
    date = a + ' ' + b

    #import datetime
    #date = datetime.datetime.strptime(a + ' ' + b, '[%Y/%m/%d %H:%M:%S]')
    kv = {}
    kv['date'] = date
    for k_v in rest.split('|'):
        k, v = k_v.split('=',1)
        kv[k] = v
    redis.hset(kv['cli'], kv['mod'], json.dumps(kv))
    print date, kv['cli'], kv['mod']
    print 'publish', "%(cli)s %(mod)s" % kv
    redis.publish("%(cli)s %(mod)s" % kv, '1')

