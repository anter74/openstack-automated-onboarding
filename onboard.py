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

    #Read project descriptor yaml file
    stream = file('vars.yml', 'r')
    templateVars = yaml.load(stream)
    stream.close()

    #Create jinja2 environment for rendering heat templates
    #env = Environment(loader = PackageLoader('onboard','templates'), trim_blocks=True)
    #template = env.get_template('template.j2')
    #Render jinja2 template to create heat template
    #stream = open('project.yml', 'w')
    #stream.write(template.render(templateVars))
    #stream.close()

    #Create new identity object for OS token management
    identity = osident()
    token = identity.getToken()

    if str(token['code']) == "200":
        # Set default headers and SSL certificate information for http object
        headers = {'Content-Type': 'application/json', 'X-Auth-Token': str(token['token_id'])}
        http = urllib3.PoolManager(
            cert_reqs = 'CERT_REQUIRED',
            ca_certs = os.environ['OS_CACERT'])

        # Get tenant list and for each tenant returned, compare to project name in templateVars
        # If project is found, return project name & ID
        # If no match is found, create project and return project name & ID
        url = str(identity.getAdminURL(token,"keystone")) + "/tenants"
        request = http.request(
            'GET',
            url,
            headers=headers)
        projectList = json.loads(request.data)
        for i in enumerate(projectList['tenants']):
            if templateVars['project']['name'] in i[1]['name']:
                print "%s already exists with ID %s" % (i[1]['name'], i[1]['id'])
                project = i[1]
                break
        else:
            url = str(identity.getAdminURL(token,"keystone")) + "/tenants"
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

        # Get user roles and pull id from _member_ role
        url = str(identity.getAdminURL(token,"keystone")) + "/OS-KSADM/roles"
        request = http.request(
            'GET',
            url,
            headers=headers)
        roles = json.loads(request.data)
        for i in enumerate(roles['roles']):
            if i[1]['name'] == "_member_":
                memberId = i[1]['id']

        # get openstack user list
        url = str(identity.getAdminURL(token,"keystone")) + "/users"
        request = http.request(
            'GET',
            url,
            headers=headers)
        users = json.loads(request.data)

        # assign member role to members from templateVars for new project
        # For each member in templateVars, iterate over Openstack users and compare name
        # If a match is found, add _member_ role to user in project matching templateVars
        for i in enumerate(templateVars['project']['members']):
            for user in enumerate(users['users']):
                if i[1]['name'] in user[1]['name']:
                    url = str(identity.getAdminURL(token,"keystone")) + "/tenants/%s/users/%s/roles/OS-KSADM/%s" % (project['id'], user[1]['id'], memberId)
                    request = http.request(
                        'PUT',
                        url,
                        headers=headers)
                    print "Response from OpenStack: %s" % request.status

        # Update quotas using templateVars data
        # This will update all quotas except those related to block storage
        # FUTURE: Add volume related quota API call? Is this necessary or relevant?
        url = str(identity.getServiceURL(token,"nova")) + "/os-quota-sets/%s" % project['id']
        jsonPayload = json.dumps({"quota_set": {"instances": templateVars['project']['quota']['instances'], "cores": templateVars['project']['quota']['cores'], "ram": templateVars['project']['quota']['ram'], "floating_ips": templateVars['project']['quota']['floating_ips']}})
        request = http.request(
            'PUT',
            url,headers=headers,
            body=jsonPayload)
        print "Response from Openstack: %s" % request.status
        print "Raw response data: %s" % json.loads(request.data)

    else:
        print "Response Code: %s" % token['code']
        print "Failure Reason: %s" % token['data']

if __name__ == "__main__":
   main()
