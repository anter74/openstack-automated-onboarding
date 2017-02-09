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

    env = Environment(loader = PackageLoader('onboard','templates'), trim_blocks=True)
    template = env.get_template('heat_template.j2')
    stream = file('vars.yml', 'r')
    templateVars = yaml.load(stream)
    stream.close()
    print template.render(templateVars)


    URL = 'https://10.75.25.138:13000/v2.0'
    token = getToken(URL)
    if str(token['code']) == "200":


        '''
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
    else:
        print "Response Code: %s" % token['code']
        print "Failure Reason: %s" % token['data']

if __name__ == "__main__":
   main()

'''
---
heat_template_version: 2015-10-15
description: Testing
resources:

  ansible_test:
    type: OS::Keystone::Project
    properties:
      name: ansible_test


  ansible_test_mgmt:
    type: OS::Neutron::Net
    depends_on: ansible_test
    properties:
      name: ansible_test_mgmt
      tenant_id: { get_resource: ansible_test }

  ansible_test_mgmt_sub:
    type: OS::Neutron::Subnet
    depends_on: ansible_test_mgmt
    properties:
      name: ansible_test_mgmt_sub
      network_id: { get_resource: ansible_test_mgmt }
      cidr: 10.0.0.0/24
      enable_dhcp: False

      tenant_id: { get_resource: ansible_test }


  ansible_test_sig:
    type: OS::Neutron::Net
    depends_on: ansible_test
    properties:
      name: ansible_test_sig
      tenant_id: { get_resource: ansible_test }

  ansible_test_sig_sub:
    type: OS::Neutron::Subnet
    depends_on: ansible_test_sig
    properties:
      name: ansible_test_sig_sub
      network_id: { get_resource: ansible_test_sig }
      cidr: 10.1.0.0/24
      enable_dhcp: True

      allocation_pools: [{ "start": "10.1.0.100", "end": "10.1.0.200" }]

      tenant_id: { get_resource: ansible_test }



  ansible_test_vm1:
    type: OS::Nova::Server
    depends_on: [ansible_test_mgmt_port1,ansible_test_sig_port1]
    properties:
      name: ansible_test_vm1
      flavor: m1.small
      image: centos-7-x86_64-v4-core
      tenant_id: { get_resource: ansible_test }
      networks: [{ "port": { get_resource: ansible_test_mgmt_port1 },"port": { get_resource: ansible_test_sig_port1 } }]


  ansible_test_mgmt_port1:
    type: OS::Neutron::Port
    depends_on: ansible_test_mgmt
    properties:
      name: ansible_test_mgmt_port1
      network: { get_resource: ansible_test_mgmt }

      fixed_ips: [{ "ip_address": "10.0.0.10" }]


  ansible_test_sig_port1:
    type: OS::Neutron::Port
    depends_on: ansible_test_sig
    properties:
      name: ansible_test_sig_port1
      network: { get_resource: ansible_test_sig }




  ansible_test_vm2:
    type: OS::Nova::Server
    depends_on: [ansible_test_mgmt_port2,ansible_test_mgmt_port2]
    properties:
      name: ansible_test_vm2
      flavor: m1.small
      image: centos-7-x86_64-v4-core
      tenant_id: { get_resource: ansible_test }
      networks: [{ "port": { get_resource: ansible_test_mgmt_port2 },"port": { get_resource: ansible_test_mgmt_port2 } }]


  ansible_test_mgmt_port2:
    type: OS::Neutron::Port
    depends_on: ansible_test_mgmt
    properties:
      name: ansible_test_mgmt_port2
      network: { get_resource: ansible_test_mgmt }

      fixed_ips: [{ "ip_address": "['10.0.0.11']" }]


  ansible_test_mgmt_port2:
    type: OS::Neutron::Port
    depends_on: ansible_test_sig
    properties:
      name: ansible_test_mgmt_port2
      network: { get_resource: ansible_test_sig }
'''
