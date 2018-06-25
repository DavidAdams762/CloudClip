import time
import uuid
import sys
import socket
import elasticache_auto_discovery
import redis
from errors import ClipError

from pymemcache.client.hash import HashClient

#elasticache settings
cache = redis.Redis(
    host='preprod-cloudclip2.xggwdh.0001.use2.cache.amazonaws.com',
    port=6379
    )

def handler(event, context):
    """
    This function puts into memcache and get from it.
    Memcache is hosted using elasticache
    """
    switcher = {
        "/newclip": addKey,
        "/addclip": addClip
    }
    try:
        func = switcher.get(event["resource"])
        func(event)
    except ClipError as inst :
        message, code = inst.args
        return {
            "statusCode": code,
            "body": message,
            "isBase64Encoded": False
        }

    response = {
        "statusCode": 200,
        "body": "Successful",
        "isBase64Encoded": False
    }
    return response

def addKey(event):
    params = getParams(event)
    if 'clip' not in params :
        raise ClipError("Clip parameter not found", 400)
    key = params['clip']
    #Checking key availability
    if cache.get(key) != None :
        raise ClipError("Key already used", 400)
    #cache.set(key, "Created", 86400)
    cache.set(key, "Created", 60) #for tests
    return True

def addClip(event):
    return event

def getParams(event):
    return event['queryStringParameters']