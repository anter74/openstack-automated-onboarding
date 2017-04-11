#!/usr/bin/python

import sys
import os

#Libraries for dealing with APIs
import json
import urllib3
import yaml
from jinja2 import Environment, PackageLoader
from osident import osident
import keystoneclient.v2_0.client as ksclient

def main():
    #Create jinja2 environment for rendering heat templates
    #env = Environment(loader = PackageLoader('onboard','templates'), trim_blocks=True)
    #template = env.get_template('template.j2')

    #Read descriptor yaml file
    stream = file('vars.yml', 'r')
    templateVars = yaml.load(stream)
    stream.close()

    #Render jinja2 template to create heat template
    #stream = open('project.yml', 'w')
    #stream.write(template.render(templateVars))
    #stream.close()

    #Create new identity object for OS token management
    identity = osident()
    token = identity.getToken()
    if str(token['code']) == "200":
        # Create openstack project
        headers = {'Content-Type': 'application/json', 'X-Auth-Token': str(token['token_id'])}
        http = urllib3.PoolManager(
            cert_reqs = 'CERT_REQUIRED',
            ca_certs = os.environ['OS_CACERT'])

        #url = str(identity.getServiceURL(token,"keystone")) + "/tenants"
        url = "http://172.16.0.120:35357/v2.0/tenants/"
        request = http.request(
            'GET',
            url,
            headers=headers)
        data = json.loads(request.data)
        for i in enumerate(data['tenants']):
            if i[1]['name'] == templateVars['project']['name']:
                print i[1]['name']
                print "Project %s already exists... Moving on" % i[1]['name']
                break
        else:
            url = "http://172.16.0.120:35357/v2.0/tenants"
            jsonPayload = json.dumps({ "tenant": { "name": templateVars['project']['name'], "Description": "Created with onboard.py", "enabled": True}})
            request = http.request(
                'POST',
                url,
                headers=headers,
                body=jsonPayload)
            project = json.loads(request.data)
            print "Project Name: %s" % project['tenant']['name']
            print "project ID: %s" % project['tenant']['id']
    else:
        print "Response Code: %s" % token['code']
        print "Failure Reason: %s" % token['data']

if __name__ == "__main__":
   main()

'''
{
  'services': [
    {'name': u'nova', 'publicURL': u'https://10.75.25.138:13774/v2.1/20187e9020f64f5594e605fde94d8283'},
    {'name': u'neutron', 'publicURL': u'https://10.75.25.138:13696/'},
    {'name': u'cinderv2', 'publicURL': u'https://10.75.25.138:13776/v2/20187e9020f64f5594e605fde94d8283'},
    {'name': u'glance', 'publicURL': u'https://10.75.25.138:13292/'},
    {'name': u'ceilometer', 'publicURL': u'https://10.75.25.138:13777/'},
    {'name': u'cinder', 'publicURL': u'https://10.75.25.138:13776/v1/20187e9020f64f5594e605fde94d8283'},
    {'name': u'heat', 'publicURL': u'https://10.75.25.138:13004/v1/20187e9020f64f5594e605fde94d8283'},
    {'name': u'swift', 'publicURL': u'https://10.75.25.138:13808/v1/AUTH_20187e9020f64f5594e605fde94d8283'},
    {'name': u'keystone', 'publicURL': u'https://10.75.25.138:13000/v2.0'}
  ],
'token_id': u'01d62302dfc845efaac3da38efbbf785', 'code': 200, 'expires': u'2017-02-10T18:46:59Z'
}
kgreenwell user id: 1eac5ee4ba584fe8809710c32ee710d3
'''
