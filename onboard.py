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

# Get initial token from Keystone API
def getToken(url):
    url = url + '/tokens'
    headers = {'Content-Type': 'application/json'}

    http = urllib3.PoolManager(
        cert_reqs = 'CERT_REQUIRED',
        ca_certs = os.environ['OS_CACERT']
        )
    jsonPayload = json.dumps({'auth' : {'tenantName' : os.environ['OS_TENANT_NAME'], 'passwordCredentials' : {'username' : os.environ['OS_USERNAME'], 'password' : os.environ['OS_PASSWORD']}}})
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
            services.append(dictbuilder)

                #Build response dict for return
        response = {'code': req.status, 'token_id': data['access']['token']['id'], 'expires': data['access']['token']['expires'], 'services': services}
        return response
    else:
        failure = {'code': req.status, 'data': data}
        return failure

# Check token for freshness and renew if necessary
def refreshToken(url, token):
    #If current time is greater or equal to epoch time of token's expiration, call getToken to refresh
    if time.time() >= str(datetime.strptime(token['expires'], "%Y-%m-%dT%H:%M:%SZ")):
        token = getToken(url)
        return token
    #Else, return the existing token back
    else:
        return token

def main():
    #Create jinja2 environment for rendering heat templates
    env = Environment(loader = PackageLoader('onboard','templates'), trim_blocks=True)
    template = env.get_template('heat_template.j2')
    #Read descriptor yaml file
    stream = file('vars.yml', 'r')
    templateVars = yaml.load(stream)
    stream.close()
    #Render jinja2 template to create heat template
    print template.render(templateVars)

    URL = 'https://10.75.25.138:13000/v2.0'
    token = getToken(URL)
    if str(token['code']) == "200":

    else:
        print "Response Code: %s" % token['code']
        print "Failure Reason: %s" % token['data']

if __name__ == "__main__":
   main()

        '''
        #Test API call
        headers = {'Content-Type': 'application/json', 'X-Auth-Token': str(token['token_id'])}
        print headers
        http = urllib3.PoolManager(
            cert_reqs = 'CERT_REQUIRED',
            ca_certs = os.environ['OS_CACERT'])
        novaListURL = str(token['services'][0]['publicURL']) + "/servers/detail"
        novaList = http.request(
            'GET',
            novaListURL,
            headers=headers)
        print novaList.data
        '''
