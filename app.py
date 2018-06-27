import time
import uuid
import sys
import socket
import elasticache_auto_discovery
import redis
import json
from errors import ClipError

from pymemcache.client.hash import HashClient

#elasticache settings
cache = redis.Redis(
    host='preprod-cloudclip2.xggwdh.0001.use2.cache.amazonaws.com',
    port=6379,
    charset="utf-8",
    decode_responses=True
    )
#EXPIRE_TIME = 86400
EXPIRE_TIME = 60

def handler(event, context):
    """
    This function puts into memcache and get from it.
    Memcache is hosted using elasticache
    """
    switcher = {
        "/newclip": addKey,
        "/clip/{clip}": handleClip,
    }
    try:
        func = switcher.get(event["resource"])
        message = func(event)
    except ClipError as inst :
        message, code = inst.args
        return {
            "statusCode": code,
            "body": message,
            "isBase64Encoded": False
        }

    #create an object that will hold the status code and body to use here
    response = {
        "statusCode": 200,
        "body": message,
        "isBase64Encoded": False
    }
    return response

def addKey(event):
    paramsObj = getParams(event)
    query = paramsObj.queryParameters
    if 'clip' not in query :
        raise ClipError("Clip parameter not found", 400)
    if 'owner' not in query :
        owner = "Annon"
    key = query['clip']
    #Checking key availability
    if cache.get(key) != None :
        raise ClipError("Key already used", 400)
    cache.lpush(key, owner)
    cache.expire(key, EXPIRE_TIME)
    return "Key added succesfully"

def addToClip(key, message):
    cache.lpush(key, message)
    cache.expire(key, EXPIRE_TIME)
    amount = cache.llen(key)

    return {
        'result' : 'ok',
        'amount' : amount,
    }

def getParams(event, type = 'query'):
    return ClipParameters(event['pathParameters'], event['queryStringParameters'])

def handleClip(event):
    paramsObj = getParams(event)
    path = paramsObj.pathParameters
    query = paramsObj.queryParameters
    if 'clip' not in path :
        raise ClipError("Clip parameter not found", 400)
    key = path['clip']
    if cache.exists(key) == 0:
        raise ClipError("Key not found", 404)
    method = event['httpMethod']
    if method == 'GET':
        page = path.get('page', 0)
        response = getClipList(key, page)
        print (response)
        return json.dumps(response)
    elif method == 'POST':
        if 'message' not in query:
            raise ClipError("No message", 400)
        response = addToClip(key, query['message'])
        return json.dumps(response)

def getClipList(key, page):
    list = cache.lrange(key, 20 * page, 20 * (page + 1))
    amount = cache.llen(key)
    cache.expire(key, EXPIRE_TIME)

    result = {
        'list' : list,
        'amount' : amount,
    }
    return result


class ClipParameters :
    pathParameters = ''
    queryParameters = ''

    def __init__(self, path, query):
        self.pathParameters = path
        self.queryParameters = query
