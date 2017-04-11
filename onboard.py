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
                print "%s already exists with ID %s" % (i[1]['name'], i[1]['id'])
                project = i[1]
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
            project = project['tenant']
            print "Project Name: %s" % project['name']
            print "project ID: %s" % project['id']
        # Get user roles
        url = "http://172.16.0.120:35357/v2.0/OS-KSADM/roles"
        request = http.request(
            'GET',
            url,
            headers=headers)
        data = json.loads(request.data)
        print data
        for i in enumerate(data['roles']):
            if i[1]['name'] == "_member_":
                memberId = i[1]['id']

        # get openstack user list
        url = "http://172.16.0.120:35357/v2.0/users"
        request = http.request(
            'GET',
            url,
            headers=headers)
        users = json.loads(request.data)
        # assign member role to kgreenwell user for new project
        for i in enumerate(templateVars['project']['members']):
            for user in enumerate(users['users']):
                print i, user
                if i['name'] in user['name']:
                    url = "http://172.16.0.120:35357/v2.0/tenants/%s/users/%s/roles/OS-KSADM/%s" % (project['id'], user['id'], memberId)
                    request = http.request(
                        'PUT',
                        url,
                        headers=headers)
                    print json.loads(request.data)

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
_member_ role: 9fe2ff9ee4384b1894a90878d3e92bab
'''
