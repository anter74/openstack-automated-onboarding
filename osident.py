#!/usr/bin/python

import sys
import os

#Libraries for dealing with APIs
import json
import urllib3
import yaml
from jinja2 import Environment, PackageLoader

#Libraries for dealing with auth token
import time
from calendar import timegm
from datetime import datetime

class osident:
    def __init__(self):
        self.url = os.environ['OS_AUTH_URL']
        self.tenantName = os.environ['OS_TENANT_NAME']
        self.userName = os.environ['OS_USERNAME']
        self.password = os.environ['OS_PASSWORD']

        # Get initial token from Keystone API
    def getToken(self):
        url = self.url + '/tokens'
        headers = {'Content-Type': 'application/json'}
        http = urllib3.PoolManager(
            cert_reqs = 'CERT_REQUIRED',
            ca_certs = os.environ['OS_CACERT']
        )
        jsonPayload = json.dumps({'auth' : {'tenantName' : self.tenantName, 'passwordCredentials' : {'username' : self.userName, 'password' : self.password}}})
        req = http.request(
            'POST',
            url,
            headers=headers,
            body=jsonPayload
        )
        data = json.loads(req.data)
        if req.status == 200:
            #Parse and cleanup services JSON
            services = []
            #Pull name from serviceCatalog
            for index, service in enumerate(data['access']['serviceCatalog']):
                dictbuilder = {'name': service['name']}
                #Pull publicURL from serviceCatalog
                for k,v in enumerate(service['endpoints']):
                    dictbuilder.update({'publicURL': v['publicURL']})
                    dictbuilder.update({'adminURL': v['adminURL']})
                services.append(dictbuilder)

            return {'code': req.status, 'token_id': data['access']['token']['id'], 'expires': data['access']['token']['expires'], 'services': services}
        else:

            return {'code': req.status, 'data': data}

    # Check token for freshness and renew if necessary
    def refreshToken(self, token):
        #If current time is greater or equal to epoch time of token's expiration, call getToken to refresh
        if time.time() >= str(datetime.strptime(token['expires'], "%Y-%m-%dT%H:%M:%SZ")):
            token = self.getToken()
            return token
        #Else, return the existing token back
        else:
            return token

    #Retrieve Correct Service URL for API Call
    def getServiceURL(self, token, service):
        token = self.refreshToken(token)
        urlBuilder = [i['publicURL'] for i in token['services'] if i['name'] == service]
        return str(urlBuilder[0])

    #Return admin URL for service
    def getAdminURL(self, token, service):
        token = self.refreshToken(token)
        urlBuilder = [i['adminURL'] for i in token['services'] if i['name'] == service]
        return str(urlBuilder[0])
