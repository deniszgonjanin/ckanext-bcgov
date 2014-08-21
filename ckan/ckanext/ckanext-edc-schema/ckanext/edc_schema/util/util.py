import urllib2
import urllib
import json
import pprint

import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.common import  c

import ckan.logic as logic

from ckanext.edc_schema.commands.base import (site_url,
                                              api_key)
from ckanext.edc_schema.util.helpers import get_record_type_label 

ValidationError = logic.ValidationError

#site_url = 'http://127.0.0.1:5000' #pylons.config['ckan.site_url'].rstrip('/')

def edc_type_label(item):
    rec_type = item['display_name']
    return get_record_type_label(rec_type)


def get_edc_tags(vocab_id):
    tags = []
    try:
        tags = toolkit.get_action('tag_list')(
                data_dict={'vocabulary_id': vocab_id})
    except toolkit.ObjectNotFound:
        return []
    
    return tags

#Return the name of an organization with the given id
def get_organization_id(org_title):

    data_string = urllib.quote(json.dumps({'all_fields': True}))
    try:
        request = urllib2.Request(site_url + '/api/3/action/organization_list')
        request.add_header('Authorization', api_key)
        response = urllib2.urlopen(request, data_string)
        assert response.code == 200

        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        assert response_dict['success'] is True

        # package_create returns the created package as its result.
        orgs = response_dict['result']
    except:
        orgs = []

    for org in orgs:
        if org_title and org_title.startswith(org['title']) :
            return org['id']
    return None


def get_user_id(user_name):
    user_info = None
    data_string = urllib.quote(json.dumps({'id':user_name}))

    request = urllib2.Request(site_url + '/api/3/action/user_show')
    request.add_header('Authorization', api_key)
    try:
        response = urllib2.urlopen(request, data_string)
        assert response.code == 200

        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        assert response_dict['success'] is True

        # package_create returns the created package as its result.
        user_info = response_dict['result']

        return user_info['id']

    except Exception:
        return None

def get_username(id):
    try:
        user = toolkit.get_action('user_show')(data_dict={'id': id})
        return user['name']
    except toolkit.ObjectNotFound:
        #No vocabulary exist with the given vocabulary id.
        return None

def check_user_member_of_org(user_id, org_id):
#    print user_id, org_id
    orgs = get_user_orgs(user_id)

#    pprint.pprint(orgs)

    member_orgs = [org.id for org in orgs if org.id == org_id]

    if member_orgs :
        return True

    return False


def get_user_toporgs(user_id, role=None):
    '''
    Returns the list of orgs that the given user belongs to and has the given role('admin', 'member', 'editor', ...)
    '''
    
    orgs = []
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}
    org_model = context['model']
    sub_orgs = []

    #Get the list of all first level organizations.
#    all_orgs = [org.id for org in org_model.Group.get_top_level_groups(type="organization")]
    all_orgs = org_model.Group.get_top_level_groups(type="organization")

#    pprint.pprint(all_orgs)

    for org in all_orgs:
        members = []
        try:
            member_dict = {'id': org.id, 'object_type': 'user', 'capacity': role}
            #Get the list of id's of all admins of the organization
            members = [member[0] for member in toolkit.get_action('member_list')(data_dict=member_dict)]
        except toolkit.ObjectNotFound:
            members = []
#        pprint.pprint(members)

        #Add the org if user is a member of at least one suborg.
        group = org_model.Group.get(org.id)
        suborgs = group.get_children_groups(type = 'organization')

        #If the user id in the list of org's admins then add the org to the final list.
        if user_id in members:
            orgs.append(org)
            for suborg in suborgs :
                sub_orgs.append(suborg)
        else :
            found = False        
            for suborg in suborgs :
                members = []
                try:
                    member_dict = {'id': suborg.id, 'object_type': 'user', 'capacity': role}
                    #Get the list of id's of all admins of the organization
                    members = [member[0] for member in toolkit.get_action('member_list')(data_dict=member_dict)]
                except toolkit.ObjectNotFound:
                    members = []

                #If the user id in the list of org's admins then add the org to the final list.
                if user_id in members:
                    sub_orgs.append(suborg)
                    found = True
            if found :
                orgs.append(org)

            

    #pprint.pprint(orgs)
    #pprint.pprint(sub_orgs)
    return (orgs, sub_orgs)

def get_user_orgs(user_id, role=None):
    '''
    Returns the list of orgs and suborgs that the given user belongs to and has the given role('admin', 'member', 'editor', ...)
    '''
    '''
    Returns the list of orgs that the given user belongs to and has the given role('admin', 'member', 'editor', ...)
    '''
    
    orgs = []
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}
    org_model = context['model']

    #Get the list of all first level organizations.
#    all_orgs = [org.id for org in org_model.Group.get_top_level_groups(type="organization")]
    all_orgs = org_model.Group.get_top_level_groups(type="organization")

#    pprint.pprint(all_orgs)

    for org in all_orgs:
        members = []
        try:
            member_dict = {'id': org.id, 'object_type': 'user', 'capacity': role}
            #Get the list of id's of all admins of the organization
            members = [member[0] for member in toolkit.get_action('member_list')(data_dict=member_dict)]
        except toolkit.ObjectNotFound:
            members = []
#        pprint.pprint(members)

        #Add the org if user is a member of at least one suborg.
        group = org_model.Group.get(org.id)
        suborgs = group.get_children_groups(type = 'organization')

        #If the user id in the list of org's admins then add the org to the final list.
        if user_id in members:
            orgs.append(org)
            for suborg in suborgs :
                orgs.append(suborg)
        else :
            for suborg in suborgs :
                members = []
                try:
                    member_dict = {'id': suborg.id, 'object_type': 'user', 'capacity': role}
                    #Get the list of id's of all admins of the organization
                    members = [member[0] for member in toolkit.get_action('member_list')(data_dict=member_dict)]
                except toolkit.ObjectNotFound:
                    members = []

                #If the user id in the list of org's admins then add the org to the final list.
                if user_id in members:
                    orgs.append(suborg)
    
    return orgs
    
def get_user_orgs_id(user_id, role=None):
    user_orgs = get_user_orgs(user_id, role)
    return [org.id for org in user_orgs]

def get_organization_branches(org_id):
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}
    org_model = context['model']

    #Get the list of all children of the organization with the given id
    group = org_model.Group.get(org_id)
    branches = group.get_children_groups(type = 'organization')
    
    #should only return branches the user is a member of
    return branches



def edc_state_activity_create(user_name, edc_record, old_state):

    activity_data = {'package' : edc_record}
    activity_info = {'user_id' : user_name,
                     'object_id' : edc_record['id'],
                     'activity_type' : 'changed package',
                     'data' : activity_data}

    data_string = urllib.quote(json.dumps(activity_info))
    request = urllib2.Request(site_url + '/api/3/action/activity_create')
    request.add_header('Authorization', api_key)

    try:
        response = urllib2.urlopen(request, data_string)
        assert response.code == 200

        # Use the json module to load CKAN's response into a dictionary.
        response_dict = json.loads(response.read())
        assert response_dict['success'] is True
        activity_result = response_dict['result']
    except:
        return False

    return True


#Getting the proper values for the possible states of a dataset
def get_state_values(user_id, pkg):
    '''
    This methods creates a list of possible values for the state of given dataset
    based on the current state of dataset and the user that updates the dataset.
    :param user_id: The id of the current user.
    :param pkg : The given dataset.
    :returns: A list of possible values of the state of the dataset.
    '''
    states = []

#    pprint.pprint(pkg)

    if not pkg or not pkg.has_key('id'):
        return ['DRAFT']

    id = pkg['id']
    org_id = pkg['owner_org']


    #Get the list of admins of the dataset

    member_data = {
                   'id' : org_id,
                   'object_type' : 'user',
                   'capacity' : 'admin'
                   }

    if org_id :
        admins = [admin[0] for admin in toolkit.get_action('member_list')(data_dict=member_data)]
    else :
        admins = []

#    pprint.pprint(user_id)
#    pprint.pprint(admins)

    current_state = pkg['edc_state']
    author_id = pkg['author']

    #If the current state is 'Draft' or 'Rejected' and user is org_admin or the author of dataset
    #then possible states are ('Draft', 'Pending Publish')

    if current_state == 'DRAFT':
        states = ['DRAFT', 'PENDING PUBLISH']
    elif current_state == 'REJECTED' :
        states = ['DRAFT', 'PENDING PUBLISH', 'REJECTED']
    elif current_state == 'PENDING PUBLISH':
        if user_id in admins :
            states = ['PENDING PUBLISH', 'PUBLISHED', 'REJECTED']
        else :
            states = ['DRAFT', 'PENDING PUBLISH']
    elif current_state == 'PUBLISHED' :
        if user_id in admins :
            states = ['PENDING PUBLISH', 'PUBLISHED', 'PENDING ARCHIVE']
        else :
            states = ['PUBLISHED', 'PENDING ARCHIVE']
    elif current_state == 'PENDING ARCHIVE' :
        if user_id in admins :
            states = ['PUBLISHED', 'PENDING ARCHIVE', 'ARCHIVED']
        else :
            states = ['PUBLISHED', 'PENDING ARCHIVE']
    elif current_state == 'ARCHIVED' :
        if user_id in admins:
            states = ['PENDING ARCHIVE', 'ARCHIVED']
        else :
            states = ['ARCHIVED']

    return states
