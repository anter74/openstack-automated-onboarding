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
def getToken():
    url = os.environ['OS_AUTH_URL'] + '/tokens'
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
def refreshToken(token):
    #If current time is greater or equal to epoch time of token's expiration, call getToken to refresh
    if time.time() >= str(datetime.strptime(token['expires'], "%Y-%m-%dT%H:%M:%SZ")):
        token = getToken(os.environ['OS_AUTH_URL'])
        return token
    #Else, return the existing token back
    else:
        return token

#Retrieve Correct Service URL for API Call
def getServiceURL(token, service):
    token = refreshToken(token)
    urlBuilder = [i['publicURL'] for i in token['services'] if i['name'] == service]
    return str(urlBuilder[0])

def main():
    #Create jinja2 environment for rendering heat templates
    env = Environment(loader = PackageLoader('onboard','templates'), trim_blocks=True)
    template = env.get_template('heat_template.j2')
    #Read descriptor yaml file
    stream = file('vars.yml', 'r')
    templateVars = yaml.load(stream)
    stream.close()
    #Render jinja2 template to create heat template
    #print template.render(templateVars)

    token = getToken()
    if str(token['code']) == "200":
        headers = {'Content-Type': 'application/json', 'X-Auth-Token': str(token['token_id'])}
        http = urllib3.PoolManager(
            cert_reqs = 'CERT_REQUIRED',
            ca_certs = os.environ['OS_CACERT'])
        novaListURL = str(getServiceURL(token,"nova")) + "/os-hypervisors/statistics"
        novaList = http.request(
            'GET',
            novaListURL,
            headers=headers)
        print json.loads(novaList.data)

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

{'services': [
{'name': u'nova', 'publicURL': u'https://10.75.25.138:13774/v2.1/20187e9020f64f5594e605fde94d8283'},
 {'name': u'neutron', 'publicURL': u'https://10.75.25.138:13696/'},
  {'name': u'cinderv2', 'publicURL': u'https://10.75.25.138:13776/v2/20187e9020f64f5594e605fde94d8283'},
   {'name': u'glance', 'publicURL': u'https://10.75.25.138:13292/'},
    {'name': u'ceilometer', 'publicURL': u'https://10.75.25.138:13777/'},
     {'name': u'cinder', 'publicURL': u'https://10.75.25.138:13776/v1/20187e9020f64f5594e605fde94d8283'},
      {'name': u'heat', 'publicURL': u'https://10.75.25.138:13004/v1/20187e9020f64f5594e605fde94d8283'},
       {'name': u'swift', 'publicURL': u'https://10.75.25.138:13808/v1/AUTH_20187e9020f64f5594e605fde94d8283'},
        {'name': u'keystone', 'publicURL': u'https://10.75.25.138:13000/v2.0'}], 'token_id': u'01d62302dfc845efaac3da38efbbf785', 'code': 200, 'expires': u'2017-02-10T18:46:59Z'}
