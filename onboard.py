#!/usr/bin/python

import sys
import os

#Libraries for dealing with APIs
import json
import urllib3
import yaml
from jinja2 import Environment, PackageLoader
from osident import osident

#Libraries for dealing with auth token
import time
from calendar import timegm
from datetime import datetime

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

    identity = osident()
    token = identity.getToken()
    if str(token['code']) == "200":
        headers = {'Content-Type': 'application/json', 'X-Auth-Token': str(token['token_id'])}
        http = urllib3.PoolManager(
            cert_reqs = 'CERT_REQUIRED',
            ca_certs = os.environ['OS_CACERT'])
        novaListURL = str(identity.getServiceURL(token,"nova")) + "/os-hypervisors/statistics"
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
