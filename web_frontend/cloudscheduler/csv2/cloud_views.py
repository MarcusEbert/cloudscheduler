from django.conf import settings
config = settings.CSV2_CONFIG

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import requires_csrf_token
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.core.exceptions import PermissionDenied

from cloudscheduler.lib.view_utils import \
    diff_lists, \
    kill_retire, \
    lno, \
    qt, \
    qt_filter_get, \
    render, \
    service_msg, \
    set_user_groups, \
    table_fields, \
    validate_by_filtered_table_entries, \
    validate_fields, \
    verify_cloud_credentials

import bcrypt

from sqlalchemy import exists
from sqlalchemy.sql import select
from sqlalchemy import Table, MetaData
from cloudscheduler.lib.schema import *
from cloudscheduler.lib.log_tools import get_frame_info
from cloudscheduler.lib.signal_manager import send_signals

import sqlalchemy.exc
#import subprocess
import os
import psutil

import requests
import time


from cloudscheduler.lib.web_profiler import silk_profile as silkp

# lno: CV - error code identifier.
MODID = 'CV'

#-------------------------------------------------------------------------------

CLOUD_KEYS = {
    'auto_active_group': True,
    # Named argument formats (anything else is a string).
    'format': {
        'cloud_name':                           'lowerdash',
        'cloud_type':                           ('csv2_cloud_types', 'cloud_type'),
        'enabled':                              'dboolean',
        'priority':                             'integer',
        'flavor_name':                          'ignore',
        'flavor_option':                        ['add', 'delete'],
        'cores_ctl':                            'integer',
        'cores_softmax':                        'integer',
        'metadata_name':                        'ignore',
        'metadata_option':                      ['add', 'delete'],
        'ram_ctl':                              'integer',
        'spot_price':                           'float',
#       'vm_boot_volume':                       {"GBs": "integer", "options": {"per_core": "boolean"}},
        'vm_boot_volume':                       {"min_pick": 1, "pick": {"GBs": "integer", "GBs_per_core": "integer"}},
        'vm_keep_alive':                        'integer',

        'cores_slider':                         'ignore',
        'csrfmiddlewaretoken':                  'ignore',
        'group':                                'ignore',
        'ram_slider':                           'ignore',

        'server_meta_ctl':                      'reject',
        'instances_ctl':                        'reject',
        'personality_ctl':                      'reject',
        'image_meta_ctl':                       'reject',
        'personality_size_ctl':                 'reject',
        'server_groups_ctl':                    'reject',
        'security_group_rules_ctl':             'reject',
        'keypairs_ctl':                         'reject',
        'security_groups_ctl':                  'reject',
        'server_group_members_ctl':             'reject',
        'floating_ips_ctl':                     'reject',
        },
    'mandatory': [
        'cloud_name',
        ],
    'not_empty': [
        'authurl',
        'project',
        'username',
        'password',
        'region',
        ],
    }

METADATA_KEYS = {
    'auto_active_group': True,
    # Named argument formats (anything else is a string).
    'format': {
        'cloud_name':                           'lowerdash',
        'enabled':                              'dboolean',
        'priority':                             'integer',
        'metadata':                             'metadata',
        'metadata_name':                        'lowercase',
        'mime_type':                            ('csv2_mime_types', 'mime_type'),

        'csrfmiddlewaretoken':                  'ignore',
        'group':                                'ignore',
        },
    'mandatory': [
        'cloud_name',
        'metadata_name',
        ],
     'not_empty': [
        'metadata_name',
        ],
    }

IGNORE_METADATA_NAME = {
    'format': {
        'metadata_name':                         'ignore',
        },
    }

LIST_KEYS = {
    # Named argument formats (anything else is a string).
    'format': {
        'csrfmiddlewaretoken':                  'ignore',
        'group':                                'ignore',
        },
    }

METADATA_LIST_KEYS = {
    # Named argument formats (anything else is a string).
    'format': {
        'csrfmiddlewaretoken':                  'ignore',
        'group':                                'ignore',
        },
    }

#-------------------------------------------------------------------------------


def retire_cloud_vms(config, group_name, cloud_name):
    VM = config.db_map.classes.csv2_vms
    vm_list = config.db_session.query(VM).filter(VM.cloud_name == cloud_name, VM.group_name == group_name)
    for vm in vm_list:
        vm.retire = 1
        vm.updater= get_frame_info() + ":r1"
        config.db_session.merge(vm)
    config.db_session.commit()


#-------------------------------------------------------------------------------

@silkp(name="EC2 Default Filters")
def ec2_filters(config, group_name, cloud_name, cloud_type=None):
    """
    If the cloud_type is "amazon", ensure EC2 filters exist for the specified
    cloud. Otherwise, remove them.
    """

    # Verify EC2 filters exists for the specified cloud.
    ec2_image_filters = qt(config.db_connection.execute('select * from ec2_image_filters where group_name="%s" and cloud_name="%s"' % (group_name, cloud_name)))
    if len(ec2_image_filters) > 0:
        ec2_image_filter = True
    else:
        ec2_image_filter = False

    ec2_instance_type_filters = qt(config.db_connection.execute('select * from ec2_instance_type_filters where group_name="%s" and cloud_name="%s"' % (group_name, cloud_name)))
    if len(ec2_instance_type_filters) > 0:
        ec2_instance_type_filter = True
    else:
        ec2_instance_type_filter = False

    # Ensure EC2 filters exist for amazon clouds.
    if cloud_type == 'amazon':
        if not ec2_image_filter:
            defaults = config.get_config_by_category('ec2_image_filter')

            table = Table('ec2_image_filters', MetaData(bind=config.db_engine), autoload=True)
            rc, msg = config.db_session_execute(table.insert().values({
                'group_name': group_name,
                'cloud_name': cloud_name,
                'architectures': defaults['ec2_image_filter']['architectures'],
                'like': defaults['ec2_image_filter']['location_like'],
                'not_like': defaults['ec2_image_filter']['location_not_like'],
                'operating_systems': defaults['ec2_image_filter']['operating_systems'],
                'owner_aliases': defaults['ec2_image_filter']['owner_aliases'],
                'owner_ids': defaults['ec2_image_filter']['owner_ids']
                }))
            if rc != 0:
                return 1, 'failed to add EC2 image filter - %s' % msg

        if not ec2_instance_type_filter:
            defaults = config.get_config_by_category('ec2_instance_type_filter')

            table = Table('ec2_instance_type_filters', MetaData(bind=config.db_engine), autoload=True)
            rc, msg = config.db_session_execute(table.insert().values({
                'group_name': group_name,
                'cloud_name': cloud_name,
                'cores': defaults['ec2_instance_type_filter']['cores'],
                'families': defaults['ec2_instance_type_filter']['families'],
                'memory_max_gigabytes_per_core': defaults['ec2_instance_type_filter']['memory_max_gigabytes_per_core'],
                'memory_min_gigabytes_per_core': defaults['ec2_instance_type_filter']['memory_min_gigabytes_per_core'],
                'operating_systems': defaults['ec2_instance_type_filter']['operating_systems'],
                'processors': defaults['ec2_instance_type_filter']['processors'],
                'processor_manufacturers': defaults['ec2_instance_type_filter']['processor_manufacturers']
                }))
            if rc != 0:
                return 1, 'failed to add EC2 instance_type filter - %s' % msg

    # Ensure EC2 filters do not exist for non-amazon clouds.
    else:
        if ec2_image_filter:
            table = Table('ec2_image_filters', MetaData(bind=config.db_engine), autoload=True)
            rc, msg = config.db_session_execute(table.delete((table.c.group_name==group_name) & (table.c.cloud_name==cloud_name)))
            if rc != 0:
                return 1, 'failed to delete EC2 image filter - %s' % msg

        if ec2_instance_type_filter:
            table = Table('ec2_instance_type_filters', MetaData(bind=config.db_engine), autoload=True)
            rc, msg = config.db_session_execute(table.delete((table.c.group_name==group_name) & (table.c.cloud_name==cloud_name)))
            if rc != 0:
                return 1, 'failed to delete EC2 instance type filter - %s' % msg

    return 0, None

#-------------------------------------------------------------------------------

@silkp(name="Cloud Manage Metadata Exclusions")
def manage_cloud_flavor_exclusions(tables, active_group, cloud_name, flavor_names, option=None):
    """
    Ensure all the specified flavor exclusions (flavor_names) and only the specified
    flavor exclusions are defined for the specified cloud. The specified cloud and
    exclusions have all been pre-verified.
    """

    table = tables['csv2_cloud_flavor_exclusions']

    # if there is only one flavor_name, make it a list anyway
    if flavor_names:
        if isinstance(flavor_names, str):
            flavor_name_list = flavor_names.split(',')
        else:
            flavor_name_list = flavor_names
    else:
        flavor_name_list = []

    # Retrieve the list of flavor exclusions the cloud already has.
    exclusions=[]
    
    s = select([table]).where((table.c.group_name==active_group) & (table.c.cloud_name==cloud_name))
    exclusion_list = qt(config.db_connection.execute(s))

    for row in exclusion_list:
        exclusions.append(row['flavor_name'])

    if not option or option == 'add':
        # Get the list of flavor exclusions (flavor_names) specified that the cloud doesn't already have.
        add_exclusions = diff_lists(flavor_name_list, exclusions)

        # Add the missing exclusions.
        for flavor_name in add_exclusions:
            rc, msg = config.db_session_execute(table.insert().values(group_name=active_group, cloud_name=cloud_name, flavor_name=flavor_name))
            if rc != 0:
                return 1, msg

    if not option:
        # Get the list of flavor exclusions (flavor_names) that the cloud currently has but were not specified.
        remove_exclusions = diff_lists(exclusions, flavor_name_list)
        
        # Remove the extraneous exclusions.
        for flavor_name in remove_exclusions:
            rc, msg = config.db_session_execute(table.delete((table.c.group_name==active_group) & (table.c.cloud_name==cloud_name) & (table.c.flavor_name==flavor_name)))
            if rc != 0:
                return 1, msg

    elif option == 'delete':
        # Get the list of flavor exclusions (flavor_names) that the cloud currently has and were specified.
        remove_exclusions = diff_lists(flavor_name_list, exclusions, option='and')
        
        # Remove the extraneous exclusions.
        for flavor_name in remove_exclusions:
            rc, msg = config.db_session_execute(table.delete((table.c.group_name==active_group) & (table.c.cloud_name==cloud_name) & (table.c.flavor_name==flavor_name)))
            if rc != 0:
                return 1, msg

    return 0, None

#-------------------------------------------------------------------------------

@silkp(name="Cloud Manage Metadata Exclusions")
def manage_group_metadata_exclusions(tables, active_group, cloud_name, metadata_names, option=None):
    """
    Ensure all the specified metadata exclusions (metadata_names) and only the specified
    metadata exclusions are defined for the specified cloud. The specified cloud and
    exclusions have all been pre-verified.
    """

    table = tables['csv2_group_metadata_exclusions']

    # if there is only one metadata_name, make it a list anyway
    if metadata_names:
        if isinstance(metadata_names, str):
            metadata_name_list = metadata_names.split(',')
        else:
            metadata_name_list = metadata_names
    else:
        metadata_name_list = []

    # Retrieve the list of metadata exclusions the cloud already has.
    exclusions=[]
    
    s = select([table]).where((table.c.group_name==active_group) & (table.c.cloud_name==cloud_name))
    exclusion_list = qt(config.db_connection.execute(s))

    for row in exclusion_list:
        exclusions.append(row['metadata_name'])

    if not option or option == 'add':
        # Get the list of metadata exclusions (metadata_names) specified that the cloud doesn't already have.
        add_exclusions = diff_lists(metadata_name_list, exclusions)

        # Add the missing exclusions.
        for metadata_name in add_exclusions:
            rc, msg = config.db_session_execute(table.insert().values(group_name=active_group, cloud_name=cloud_name, metadata_name=metadata_name))
            if rc != 0:
                return 1, msg

    if not option:
        # Get the list of metadata exclusions (metadata_names) that the cloud currently has but were not specified.
        remove_exclusions = diff_lists(exclusions, metadata_name_list)
        
        # Remove the extraneous exclusions.
        for metadata_name in remove_exclusions:
            rc, msg = config.db_session_execute(table.delete((table.c.group_name==active_group) & (table.c.cloud_name==cloud_name) & (table.c.metadata_name==metadata_name)))
            if rc != 0:
                return 1, msg

    elif option == 'delete':
        # Get the list of metadata exclusions (metadata_names) that the cloud currently has and were specified.
        remove_exclusions = diff_lists(metadata_name_list, exclusions, option='and')
        
        # Remove the extraneous exclusions.
        for metadata_name in remove_exclusions:
            rc, msg = config.db_session_execute(table.delete((table.c.group_name==active_group) & (table.c.cloud_name==cloud_name) & (table.c.metadata_name==metadata_name)))
            if rc != 0:
                return 1, msg

    return 0, None

#-------------------------------------------------------------------------------

@silkp(name="Cloud Manage Group Metadata Verification")
def manage_group_metadata_verification(tables, active_group, cloud_names, metadata_names):
    """
    Make sure the specified cloud, and metadata names exist.
    """

    if cloud_names:
        # if there is only one cloud, make it a list anyway
        if isinstance(cloud_names, str):
            cloud_name_list = cloud_names.split(',')
        else:
            cloud_name_list = cloud_names

        # Get the list of valid clouds.
        table = tables['csv2_clouds']
        s = select([table]).where(table.c.group_name==active_group)
        cloud_list = qt(config.db_connection.execute(s))

        valid_clouds = {}
        for row in cloud_list:
            valid_clouds[row['cloud_name']] = False

        # Check the list of specified clouds.
        for cloud in cloud_name_list:
            if cloud not in valid_clouds:
                return 1, 'specified cloud "%s::%s" does not exist' % (active_group, cloud)
            elif valid_clouds[cloud]:
                return 1, 'cloud "%s" was specified twice' % cloud
            else:
                valid_clouds[cloud] = True

    if metadata_names:
        # if there is only one metadata name, make it a list anyway
        if isinstance(metadata_names, str):
            metadata_name_list = metadata_names.split(',')
        else:
            metadata_name_list = metadata_names

        # Get the list of valid metadata names.
        table = tables['csv2_group_metadata']
        s = select([table]).where(table.c.group_name==active_group)
        metadata_list = qt(config.db_connection.execute(s))

        valid_metadata = {}
        for row in metadata_list:
            valid_metadata[row['metadata_name']] = False

        # Check the list of specified metadata names.
        for metadata_name in metadata_name_list:
            if metadata_name not in valid_metadata:
                return 1, 'specified metadata_name "%s" does not exist' % metadata_name
            elif valid_metadata[metadata_name]:
                return 1, 'metadata name "%s" was specified twice' % metadata_name
            else:
                valid_metadata[metadata_name] = True

    return 0, None

#-------------------------------------------------------------------------------

@silkp(name="Cloud Add")
@requires_csrf_token
def add(request):
    """
    This function should recieve a post request with a payload of cloud configuration
    to add a cloud to a given group.
    """

    # open the database.
    config.db_open()


    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    if request.method == 'POST':

        # Validate input fields.
        rc, msg, fields, tables, columns = validate_fields(config, request, [CLOUD_KEYS], ['csv2_clouds', 'csv2_cloud_flavor_exclusions,n', 'csv2_group_metadata,n', 'csv2_group_metadata_exclusions,n'], active_user)
        if rc != 0: 
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud add %s' % (lno(MODID), msg))

        if 'flavor_name' in fields and fields['flavor_name']:
            rc, msg = validate_by_filtered_table_entries(config, fields['flavor_name'], 'flavor_name', 'cloud_flavors', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]], allow_value_list=True)
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud add, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_flavor' in fields and fields['vm_flavor']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_flavor'], 'vm_flavor', 'cloud_flavors', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud add, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_image' in fields and fields['vm_image']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_image'], 'vm_image', 'cloud_images', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud add, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_keyname' in fields and fields['vm_keyname']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_keyname'], 'vm_keyname', 'cloud_keypairs', 'key_name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud add, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_network' in fields and fields['vm_network']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_network'], 'vm_network', 'cloud_networks', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud add, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_security_groups' in fields and fields['vm_security_groups']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_security_groups'], 'vm_security_groups', 'cloud_security_groups', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]], allow_value_list=True)
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud add, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        # Validity check the specified metadata exclusions.
        if 'metadata_name' in fields:
            rc, msg = manage_group_metadata_verification(tables, fields['group_name'], None, fields['metadata_name']) 
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud add, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        # Verify cloud credentials.
        rc, msg, owner_id = verify_cloud_credentials(config, fields, active_user)
        if rc == 0:
            fields['ec2_owner_id'] = owner_id
        else:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud add "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # Add the cloud.
        table = tables['csv2_clouds']
        rc, msg = config.db_session_execute(table.insert().values(table_fields(fields, table, columns, 'insert')))
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud add "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # Add the cloud's flavor exclusions.
        if 'flavor_name' in fields:
            rc, msg = manage_cloud_flavor_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['flavor_name'])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s add flavor exclusions for cloud "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # Add the cloud's group metadata exclusions.
        if 'metadata_name' in fields:
            rc, msg = manage_group_metadata_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['metadata_name'])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s add group metadata exclusion for cloud "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # For EC2 clouds, add default filters.
        rc, msg = ec2_filters(config, fields['group_name'], fields['cloud_name'], fields['cloud_type'])
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud add "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        #signal the pollers a new cloud has been added
        send_signals(config, "insert_csv2_clouds")
        config.db_close(commit=True)
        return list(request, active_user=active_user, response_code=0, message='cloud "%s::%s" successfully added.' % (fields['group_name'], fields['cloud_name']))
                    
    ### Bad request.
    else:
        return list(request, active_user=active_user, response_code=1, message='%s cloud add request did not contain mandatory parameter "cloud_name".' % lno(MODID))

#-------------------------------------------------------------------------------

@silkp(name="Cloud Delete")
@requires_csrf_token
def delete(request):
    """
 function should recieve a post request with a payload of cloud name
    to be deleted.
    """

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    if request.method == 'POST':
        # Validate input fields.
        rc, msg, fields, tables, columns = validate_fields(config, request, [CLOUD_KEYS, IGNORE_METADATA_NAME], ['csv2_clouds', 'csv2_cloud_metadata', 'csv2_group_metadata_exclusions'], active_user)
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud delete %s' % (lno(MODID), msg))

        # For EC2 clouds, delete filters.
        rc, msg = ec2_filters(config, fields['group_name'], fields['cloud_name'])
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud delete "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # Delete any metadata files for the cloud.
        table = tables['csv2_cloud_metadata']
        rc, msg = config.db_session_execute(table.delete((table.c.group_name==fields['group_name']) & (table.c.cloud_name==fields['cloud_name'])), allow_no_rows=True)
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-delete "%s::%s.*" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # Delete any metadata exclusions files for the cloud.
        table = tables['csv2_group_metadata_exclusions']
        rc, msg = config.db_session_execute(table.delete((table.c.group_name==fields['group_name']) & (table.c.cloud_name==fields['cloud_name'])), allow_no_rows=True)
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s delete group metadata exclusion for cloud "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # Delete the cloud.
        table = tables['csv2_clouds']
        rc, msg = config.db_session_execute(
            table.delete((table.c.group_name==fields['group_name']) & (table.c.cloud_name==fields['cloud_name']))
            )
        if rc == 0:
            config.db_close(commit=True)
            return list(request, active_user=active_user, response_code=0, message='cloud "%s::%s" successfully deleted.' % (fields['group_name'], fields['cloud_name']))
        else:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud delete "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

    ### Bad request.
    else:
#       return list(request, active_user=active_user, response_code=1, message='%s cloud delete, invalid method "%s" specified.' % (lno(MODID), request.method))
        return list(request, active_user=active_user, response_code=1, message='%s cloud delete request did not contain mandatory parameter "cloud_name".' % lno(MODID))

#-------------------------------------------------------------------------------

@silkp(name='Cloud List')
@requires_csrf_token
def list(request, active_user=None, response_code=0, message=None):

    cloud_list_path = '/cloud/list/'

    if request.path!=cloud_list_path and request.META['HTTP_ACCEPT'] == 'application/json':
        return render(request, 'csv2/clouds.html', {'response_code': response_code, 'message': message, 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    if active_user is None:
        rc, msg, active_user = set_user_groups(config, request, super_user=False)
        if rc != 0:
            config.db_close()
            return render(request, 'csv2/clouds.html', {'response_code': 1, 'message': '%s %s' % (lno(MODID), msg)})

    # Validate input fields when request is for /cloud/list/.
    rc, msg, fields, tables, columns = validate_fields(config, request, [LIST_KEYS], [], active_user)
    if rc != 0 and request.path==cloud_list_path:
        config.db_close()
        return render(request, 'csv2/clouds.html', {'response_code': 1, 'message': '%s cloud list, %s' % (lno(MODID), msg)})

    s = select([csv2_cloud_types])
    type_list = qt(config.db_connection.execute(s))

    # Retrieve cloud information.
    if request.META['HTTP_ACCEPT'] == 'application/json':
        s = select([view_clouds_with_metadata_names]).where(view_clouds_with_metadata_names.c.group_name == active_user.active_group)
        cloud_list = qt(config.db_connection.execute(s), prune=['password'])
        metadata_dict = {}
    else:
        s = select([view_clouds_with_metadata_info]).where(view_clouds_with_metadata_info.c.group_name == active_user.active_group)
        cloud_list, metadata_dict = qt(
            config.db_connection.execute(s),
            keys = {
                'primary': [
                    'group_name',
                    'cloud_name'
                    ],
                'secondary': [
                    'metadata_name',
                    'metadata_enabled',
                    'metadata_priority',
                    'metadata_mime_type',
                    ]
                },
            prune=['password']    
            )

    # Get all the images in group:
    s = select([cloud_images]).where(cloud_images.c.group_name==active_user.active_group)
    image_list = qt(config.db_connection.execute(s))

    # Get all the flavors in group:
    s = select([cloud_flavors]).where(cloud_flavors.c.group_name==active_user.active_group)
    flavor_list = qt(config.db_connection.execute(s))

    # Retrieve the list of flavor exclusions:
    s = select([csv2_cloud_flavor_exclusions]).where(csv2_cloud_flavor_exclusions.c.group_name==active_user.active_group)
    flavor_exclusion_list = qt(config.db_connection.execute(s))

    # Get all the keynames in group:
    s = select([cloud_keypairs]).where(cloud_keypairs.c.group_name==active_user.active_group)
    keypairs_list = qt(config.db_connection.execute(s))

    # Get all the networks in group:
    s = select([cloud_networks]).where(cloud_networks.c.group_name==active_user.active_group)
    network_list = qt(config.db_connection.execute(s))

    # Get all the security groups in group:
    s = select([cloud_security_groups]).where(cloud_security_groups.c.group_name==active_user.active_group)
    security_groups_list = qt(config.db_connection.execute(s))

    # Get the group default metadata list:
    s = select([view_groups_with_metadata_info]).where(view_groups_with_metadata_info.c.group_name==active_user.active_group)
    group_metadata_dict = qt(config.db_connection.execute(s))

    # Retrieve the list of metadata exclusions:
    s = select([csv2_group_metadata_exclusions]).where(csv2_group_metadata_exclusions.c.group_name==active_user.active_group)
    group_metadata_exclusion_list = qt(config.db_connection.execute(s))

    # Retrieve the list ec2 regions:
    s = select([ec2_regions])
    ec2_regions_list = qt(config.db_connection.execute(s))


    # Position the page.
    if len(cloud_list) > 0:
        current_cloud = str(cloud_list[0]['cloud_name'])
    else:
        current_cloud = ''

    # Render the page.
    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'cloud_list': cloud_list,
            'type_list': type_list,
            'metadata_dict': metadata_dict,
            'group_metadata_dict': group_metadata_dict,
            'group_metadata_exclusion_list': group_metadata_exclusion_list,
            'image_list': image_list,
            'flavor_list': flavor_list,
            'flavor_exclusion_list': flavor_exclusion_list,
            'keypairs_list': keypairs_list,
            'network_list': network_list,
            'security_groups_list': security_groups_list,
            'ec2_regions_list': ec2_regions_list,
            'current_cloud': current_cloud,
            'response_code': response_code,
            'message': message,
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
        }

    config.db_close()
    return render(request, 'csv2/clouds.html', context)

#-------------------------------------------------------------------------------

@silkp(name='Cloud Metadata Add')
@requires_csrf_token
def metadata_add(request):
    """
    This function should recieve a post request with a payload of metadata configuration
    to add to a given group/cloud.
    """

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    if request.method == 'POST':
        # Validate input fields.
        rc, msg, fields, tables, columns = validate_fields(config, request, [METADATA_KEYS], ['csv2_cloud_metadata', 'csv2_clouds,n'], active_user)
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-add %s' % (lno(MODID), msg))

        # Check cloud already exists.
        table = tables['csv2_clouds']
        s = select([csv2_clouds]).where(csv2_clouds.c.group_name == active_user.active_group)
        cloud_list = config.db_connection.execute(s)
        found = False
        for cloud in cloud_list:
            if active_user.active_group == cloud['group_name'] and fields['cloud_name'] == cloud['cloud_name']:
                found = True
                break

        if not found:
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-add failed, cloud name  "%s" does not exist.' % (lno(MODID), fields['cloud_name']))

        # Add the cloud metadata file.
        table = tables['csv2_cloud_metadata']
        payload = table.insert().values(table_fields(fields, table, columns, 'insert'))
        rc, msg = config.db_session_execute(payload)
        if rc == 0:
            config.db_close(commit=True)

            message = 'cloud metadata file "%s::%s::%s" successfully added.' % (fields['group_name'], fields['cloud_name'], fields['metadata_name'])

            context = {
                'group_name': fields['group_name'],
                'response_code': 0,
                'message': message,
            }
            return render(request, 'csv2/reload_parent.html', context)

        else:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-add "%s::%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], fields['metadata_name'], msg))

    ### Bad request.
    else:
#       return list(request, active_user=active_user, response_code=1, message='%s cloud metadata_add, invalid method "%s" specified.' % (lno(MODID), request.method))
        return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-add request did not contain mandatory parameters "cloud_name" and "metadata_name".' % lno(MODID))

#-------------------------------------------------------------------------------

@silkp(name="Cloud Metadata Add")
@requires_csrf_token
def metadata_collation(request):

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/clouds_metadata_list.html', {'response_code': 1, 'message': '%s cloud metadata-list, %s' % (lno(MODID), msg)})

    # Validate input fields (should be none).
    rc, msg, fields, tables, columns = validate_fields(config, request, [METADATA_LIST_KEYS], [], active_user)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/clouds_metadata_list.html', {'response_code': 1, 'message': '%s cloud metadata-list, %s' % (lno(MODID), msg)})

    # Retrieve cloud/metadata information.
    s = select([view_metadata_collation]).where(view_metadata_collation.c.group_name == active_user.active_group)
    cloud_metadata_list = qt(config.db_connection.execute(s))

    config.db_close()

    # Render the page.
    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'cloud_metadata_list': cloud_metadata_list,
            'response_code': 0,
            'message': None,
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
        }

    return render(request, 'csv2/cloud_metadata_list.html', context)

#-------------------------------------------------------------------------------

@silkp(name='Cloud Metadata Delete')
@requires_csrf_token
def metadata_delete(request):
    """
    This function should recieve a post request with a payload of metadata configuration
    to add to a given group/cloud.
    """

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    if request.method == 'POST':

        # Validate input fields.
        rc, msg, fields, tables, columns = validate_fields(config, request, [METADATA_KEYS], ['csv2_cloud_metadata'], active_user)
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-delete %s' % (lno(MODID), msg))

        # Delete the cloud metadata file.
        table = tables['csv2_cloud_metadata']
        rc, msg = config.db_session_execute(
            table.delete( \
                (table.c.group_name==fields['group_name']) & \
                (table.c.cloud_name==fields['cloud_name']) & \
                (table.c.metadata_name==fields['metadata_name']) \
                )
            )
        if rc == 0:
            config.db_close(commit=True)

            #**********************************************************************************
            '''
            #This block of code checks to make sure the metadata was successfully deleted
            config.db_open()

            found = True
            while(found==True):

                s = select([view_clouds_with_metadata_info]).where((view_clouds_with_metadata_info.c.group_name == active_user.active_group) & (view_clouds_with_metadata_info.c.cloud_name == fields['cloud_name']) & (view_clouds_with_metadata_info.c.metadata_name == fields['metadata_name']))
                meta_list = qt(config.db_connection.execute(s))
                if not meta_list:
                    found = False

            config.db_close()
            '''

            #**********************************************************************************



            message = 'cloud metadata file "%s::%s::%s" successfully deleted.' % (fields['group_name'], fields['cloud_name'], fields['metadata_name'])

            context = {
                'group_name': fields['group_name'],
                'response_code': 0,
                'message': message,
            }
            return render(request, 'csv2/reload_parent.html', context)



        else:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-delete "%s::%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], fields['metadata_name'], msg))

    ### Bad request.
    else:
#       return list(request, active_user=active_user, response_code=1, message='%s cloud metadata_delete, invalid method "%s" specified.' % (lno(MODID), request.method))
        return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-delete request did not contain mandatory parameters "cloud_name" and "metadata_name".' % lno(MODID))

#-------------------------------------------------------------------------------

@silkp(name="Cloud Metadata Fetch")
@requires_csrf_token
def metadata_fetch(request, response_code=0, message=None, metadata_name=None, cloud_name=None):

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    # Get mime type list:
    s = select([csv2_mime_types])
    mime_types_list = qt(config.db_connection.execute(s))


    # If we are NOT returning from an update, we are fetching from webpage
    if metadata_name == None:
        metadata_name = active_user.kwargs['metadata_name']

    if cloud_name == None:
        cloud_name = active_user.kwargs['cloud_name']


    # Retrieve metadata file.
    if cloud_name and metadata_name:
        METADATA = config.db_map.classes.csv2_cloud_metadata
        METADATAobj = config.db_session.query(METADATA).filter((METADATA.group_name == active_user.active_group) & (METADATA.cloud_name==cloud_name) & (METADATA.metadata_name==metadata_name))
        if METADATAobj:
            for row in METADATAobj:
                context = {
                    'group_name': row.group_name,
                    'cloud_name': row.cloud_name,
                    'metadata': row.metadata,
                    'metadata_enabled': row.enabled,
                    'metadata_priority': row.priority,
                    'metadata_mime_type': row.mime_type,
                    'metadata_name': row.metadata_name,
                    'mime_types_list': mime_types_list,
                    'response_code': response_code,
                    'message': message,
                    'is_superuser': active_user.is_superuser,
                    'version': config.get_version()
                    }

                config.db_close()
                return render(request, 'csv2/meta_editor.html', context)


    config.db_close()

    if 'cloud_name' in active_user.kwargs and 'metadata_name' in active_user.kwargs:
      return render(request, 'csv2/meta_editor.html', {'response_code': 1, 'message': 'cloud metadata_fetch, received an invalid metadata file id "%s::%s::%s".' % (active_user.active_group, active_user.kwargs['cloud_name'], active_user.kwargs['metadata_name'])})
    else:
      return render(request, 'csv2/meta_editor.html', {'response_code': 1, 'message': 'cloud metadata_fetch, metadata file id omitted.'})

#-------------------------------------------------------------------------------

@silkp(name="Cloud Metadata List")
@requires_csrf_token
def metadata_list(request):

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/clouds_metadata_list.html', {'response_code': 1, 'message': '%s cloud metadata-list, %s' % (lno(MODID), msg)})

    # Validate input fields (should be none).
    rc, msg, fields, tables, columns = validate_fields(config, request, [METADATA_LIST_KEYS], [], active_user)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/clouds_metadata_list.html', {'response_code': 1, 'message': '%s cloud metadata-list, %s' % (lno(MODID), msg)})

    # Retrieve cloud/metadata information.
    s = select([csv2_cloud_metadata]).where(csv2_cloud_metadata.c.group_name == active_user.active_group)
    cloud_metadata_list = qt(config.db_connection.execute(s))
    


    # Retrieve group/metadata information.
    s = select([view_groups_with_metadata_names]).where(view_groups_with_metadata_names.c.group_name == active_user.active_group)
    group_metadata_names = qt(config.db_connection.execute(s))

    # Retrieve cloud/metadata information.
    s = select([view_clouds_with_metadata_names]).where(view_clouds_with_metadata_names.c.group_name == active_user.active_group)
    cloud_metadata_names = qt(config.db_connection.execute(s))

    config.db_close()

    # Render the page.
    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'cloud_metadata_list': cloud_metadata_list,
            'group_metadata_names': group_metadata_names,
            'cloud_metadata_names': cloud_metadata_names,
            'response_code': 0,
            'message': None,
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
        }

    return render(request, 'csv2/metadata-list.html', context)

#-------------------------------------------------------------------------------
@silkp(name="Cloud Metadata Fetch")
@requires_csrf_token
def metadata_new(request):

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    # Get mime type list:
    s = select([csv2_mime_types])
    mime_types_list = qt(config.db_connection.execute(s))

    # Retrieve metadata file.
    if 'cloud_name' in active_user.kwargs:
        cloud_name = active_user.kwargs['cloud_name']

        context = {
            'group_name': active_user.active_group,
            'cloud_name': cloud_name,
            'metadata': "",
            'metadata_enabled': 0,
            'metadata_priority': 0,
            'metadata_mime_type': "",
            'metadata_name': "",
            'mime_types_list': mime_types_list,
            'response_code': 0,
            'message': "new-cloud-metadata",
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
            }

        config.db_close()
        return render(request, 'csv2/meta_editor.html', context)


    config.db_close()

    return render(request, 'csv2/meta_editor.html', {'response_code': 1, 'message': 'cloud metadata_new, received an invalid request: no metadata_name specified.'})

#-------------------------------------------------------------------------------

@silkp(name="Cloud Metadata query")
@requires_csrf_token
def metadata_query(request):

    keys = {
        'auto_active_group': True,
        # Named argument formats (anything else is a string).
        'format': {
            'cloud_name':                           'lowerdash',
            'metadata_name':                        'lowercase',

            'csrfmiddlewaretoken':                  'ignore',
            'group':                                'ignore',
            },
        'mandatory': [
            'cloud_name',
            'metadata_name',
            ],
        }

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/clouds_metadata_list.html', {'response_code': 1, 'message': '%s cloud metadata-query, %s' % (lno(MODID), msg)})

    # Validate input fields (should be none).
    rc, msg, fields, tables, columns = validate_fields(config, request, [keys], [], active_user)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/clouds_metadata_list.html', {'response_code': 1, 'message': '%s cloud metadata-query, %s' % (lno(MODID), msg)})

    # Retrieve cloud/metadata information.
    s = select([csv2_cloud_metadata]).where((csv2_cloud_metadata.c.group_name == active_user.active_group) & (csv2_cloud_metadata.c.cloud_name == fields['cloud_name']) & (csv2_cloud_metadata.c.metadata_name == fields['metadata_name']))
    cloud_metadata_list = qt(config.db_connection.execute(s))
    
    config.db_close()

    if len(cloud_metadata_list) < 1:
        metadata_exists = False
    else:
        metadata_exists = True

    # Render the page.
    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'metadata_exists': metadata_exists,
            'response_code': 0,
            'message': None,
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
        }

    return render(request, 'csv2/metadata-list.html', context)

#-------------------------------------------------------------------------------
@silkp(name="Cloud Metadata Update")
@requires_csrf_token
def metadata_update(request):
    """
    This function should recieve a post request with a payload of metadata configuration
    to add to a given group/cloud.
    """

    # open the database.
    config.db_open()
    
    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    if request.method == 'POST':
        # Validate input fields.
        rc, msg, fields, tables, columns = validate_fields(config, request, [METADATA_KEYS], ['csv2_cloud_metadata'], active_user)
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-update %s' % (lno(MODID), msg))

        # Update the cloud metadata file.
        table = tables['csv2_cloud_metadata']
        rc, msg = config.db_session_execute(table.update().where( \
            (table.c.group_name==fields['group_name']) & \
            (table.c.cloud_name==fields['cloud_name']) & \
            (table.c.metadata_name==fields['metadata_name']) \
            ).values(table_fields(fields, table, columns, 'update')))
        if rc == 0:
            if not 'metadata' in fields.keys():
                s = table.select(
                    (table.c.group_name==fields['group_name']) & \
                    (table.c.cloud_name==fields['cloud_name']) & \
                    (table.c.metadata_name==fields['metadata_name'])
                    )
                metadata_list = qt(config.db_connection.execute(s))
                if len(metadata_list) != 1:
                    return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-update could not retrieve metadata' % (lno(MODID), request.method))
                metadata = metadata_list[0]
            else:
                metadata = fields['metadata']

            config.db_close(commit=True)

            message='cloud metadata file "%s::%s::%s" successfully  updated.' % (fields['group_name'], fields['cloud_name'], fields['metadata_name'])

            return metadata_fetch(request, response_code=0, message=message, metadata_name=fields['metadata_name'], cloud_name=fields['cloud_name'])
        else:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-update "%s::%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], fields['metadata_name'], msg))

    ### Bad request.
    else:
#       return list(request, active_user=active_user, response_code=1, message='%s cloud metadata_update, invalid method "%s" specified.' % (lno(MODID), request.method))
        return list(request, active_user=active_user, response_code=1, message='%s cloud metadata-update request did not contain mandatory parameters "cloud_name" and "metadata_name".' % lno(MODID))

#-------------------------------------------------------------------------------

@silkp(name="Cloud Status")
@requires_csrf_token
def status(request, group_name=None):
    """
    This function generates a the status of a given groups operations
    VM status, job status, and machine status should all be available for a given group on this page
    """

    # open the database.
    config.db_open()
    config.refresh()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/clouds.html', {'response_code': 1, 'message': '%s %s' % (lno(MODID), msg), 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})

    GROUP_ALIASES = {'group_name': {"mygroups" :active_user.user_groups }}
    # get cloud status per group
    if active_user.flag_global_status:
        s = select([view_cloud_status])
        cloud_status_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

        s = select([view_condor_jobs_group_defaults_applied])
        job_cores_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

    else:
        s = select([view_cloud_status]).where(view_cloud_status.c.group_name == active_user.active_group)
        cloud_status_list = qt(config.db_connection.execute(s))

        s = select([view_condor_jobs_group_defaults_applied]).where(view_condor_jobs_group_defaults_applied.c.group_name == active_user.active_group)
        job_cores_list = qt(config.db_connection.execute(s))
    
    if len(cloud_status_list) < 1:
        cloud_total_list = []
        cloud_status_list_totals = []

    else:
        # calculate the totals for all rows
        cloud_status_list_totals = qt(cloud_status_list, keys={
            'primary': ['group_name'],
            'sum': [
                'VMs',
                'VMs_starting',
                'VMs_unregistered',
                'VMs_idle',
                'VMs_running',
                'VMs_retiring',
                'VMs_manual',
                'VMs_in_error',
                'Foreign_VMs',
                'cores_limit',
                'cores_foreign',
                'cores_idle',
                'cores_native',
                'cores_native_foreign',
                'cores_quota',
                'ram_quota',
                'ram_foreign',
                'ram_idle',
                'ram_native',
                'ram_native_foreign',
                'VMs_quota',
                'VMs_native_foreign', 
                'slot_count',
                'slot_core_count',
                'slot_idle_core_count'
                ]
            })

        cloud_total_list = cloud_status_list_totals[0]

        # calculate the group view totals for all rows
        cloud_status_global_totals = qt(cloud_status_list, keys={
            'primary': [],
            'sum': [
                'VMs',
                'VMs_starting',
                'VMs_unregistered',
                'VMs_idle',
                'VMs_running',
                'VMs_retiring',
                'VMs_manual',
                'VMs_in_error',
                'Foreign_VMs',
                'cores_limit',
                'cores_foreign',
                'cores_idle',
                'cores_native',
                'cores_native_foreign',
                'cores_quota',
                'ram_quota',
                'ram_foreign',
                'ram_idle',
                'ram_native',
                'ram_native_foreign',
                'VMs_quota',
                'VMs_native_foreign',
                'slot_count',
                'slot_core_count',
                'slot_idle_core_count'
                ]
            })

        global_total_list = cloud_status_global_totals[0]

        cloud_status_list_totals_xref = {}
        for ix in range(len(cloud_status_list_totals)):
            cloud_status_list_totals_xref[cloud_status_list_totals[ix]['group_name']] = ix
            cloud_status_list_totals[ix]['cloud_name'] = ''
            cloud_status_list_totals[ix]['display'] = 9
            cloud_status_list_totals[ix]['tag'] = '_total'

        current_group = ''
        cloud_count = 0
        # Loop through the cloud_status_list and insert the totals row after each group of clouds:
        for index, cloud in enumerate(cloud_status_list):
            cloud['tag'] = ''
            if current_group == cloud['group_name']:
                if 'display' not in cloud:
                    cloud['display'] = 0
            else:
                cloud['display'] = 1
                if current_group != '':
                    ix = cloud_status_list_totals_xref[current_group]
                    cloud_status_list.insert(index, cloud_status_list_totals[ix].copy())

                current_group = cloud['group_name']

        if current_group != '':
            ix = cloud_status_list_totals_xref[current_group]
            cloud_status_list.append(cloud_status_list_totals[ix].copy())

        # Append the global totals list to the main status list:
        global_total_list['group_name'] = ''
        global_total_list['cloud_name'] = ''
        global_total_list['display'] = 99
        global_total_list['tag'] = '_total'

        cloud_status_list.append(global_total_list.copy())


    job_cores_list_totals = qt(job_cores_list, keys={
        'primary': [
            'group_name',
            'request_cpus'
        ],
        'sum': [
            'js_idle',
            'js_running',
            'js_completed',
            'js_held',
            'js_other'
            ]
        })

    job_totals_list = job_cores_list_totals

    '''
    view_cloud_status_flavor_slot_detail
    view_cloud_status_flavor_slot_detail_summary
    view_cloud_status_flavor_slot_summary
    view_cloud_status_slot_detail
    view_cloud_status_slot_detail_summary
    view_cloud_status_slot_summary
    '''

    # Get slot type counts
    if active_user.flag_global_status:

        s = select([view_cloud_status_flavor_slot_detail])
        flavor_slot_detail = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

        s = select([view_cloud_status_flavor_slot_detail_summary])
        flavor_slot_detail_summary = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

        s = select([view_cloud_status_flavor_slot_summary])
        flavor_slot_summary = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

        s = select([view_cloud_status_slot_detail])
        slot_detail = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

        s = select([view_cloud_status_slot_detail_summary])
        slot_detail_summary = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

        s = select([view_cloud_status_slot_summary])
        slot_summary = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))

    else:

        s = select([view_cloud_status_flavor_slot_detail]).where(view_cloud_status_flavor_slot_detail.c.group_name == active_user.active_group)
        flavor_slot_detail = qt(config.db_connection.execute(s))

        s = select([view_cloud_status_flavor_slot_detail_summary]).where(view_cloud_status_flavor_slot_detail_summary.c.group_name == active_user.active_group)
        flavor_slot_detail_summary = qt(config.db_connection.execute(s))
        
        s = select([view_cloud_status_flavor_slot_summary]).where(view_cloud_status_flavor_slot_summary.c.group_name == active_user.active_group)
        flavor_slot_summary = qt(config.db_connection.execute(s))
        
        s = select([view_cloud_status_slot_detail]).where(view_cloud_status_slot_detail.c.group_name == active_user.active_group)
        slot_detail = qt(config.db_connection.execute(s))
        
        s = select([view_cloud_status_slot_detail_summary]).where(view_cloud_status_slot_detail_summary.c.group_name == active_user.active_group)
        slot_detail_summary = qt(config.db_connection.execute(s))
        
        s = select([view_cloud_status_slot_summary]).where(view_cloud_status_slot_summary.c.group_name == active_user.active_group)
        slot_summary = qt(config.db_connection.execute(s))


    '''
    # Calculate the group totals:
    slot_detail_total_list = qt(slot_detail_list, keys={
        'primary': ['group_name','slot_type', 'slot_id'],
        'sum': [
            'slot_count',
            'core_count'
            ]
        })


    # Calculate the global totals:
    slot_detail_global_total_list = qt(slot_detail_list, keys={
        'primary': ['slot_type', 'slot_id'],
        'sum': [
            'slot_count',
            'core_count'
            ]
        })

    # Append the totals to the main list:
    for slot in slot_detail_total_list:
        slot['cloud_name']=''
        slot_detail_list.append(slot.copy())

    # Append the GLOBAL totals to the main list:
    for slot in slot_detail_global_total_list:
        slot['group_name']=''
        slot['cloud_name']=''
        slot_detail_list.append(slot.copy())


    # Generate the slot detail values, grouping and summing slots by type.

    #slot_detail = gen_slot_detail(slot_list)

    #slot_detail_total = gen_slot_detail(slot_total_list)


    # get slot summary
    if active_user.flag_global_status:
        s = select([view_cloud_status_slot_summary])
        slot_summary_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))
    else:
        s = select([view_cloud_status_slot_summary]).where(view_cloud_status_slot_summary.c.group_name == active_user.active_group)
        slot_summary_list = qt(config.db_connection.execute(s))

    # Calculate the group totals:
    slot_summary_total_list = qt(slot_summary_list, keys={
        'primary': ['group_name', 'flavor'],
        'sum': [
            'VMs',
            'Active_CPUs',
            'Idle_CPUs',
            'Idle_Percent'
            ]
        })

    # Calculate the GLOBAL totals:
    slot_summary_global_total_list = qt(slot_summary_list, keys={
        'primary': ['flavor'],
        'sum': [
            'VMs',
            'Active_CPUs',
            'Idle_CPUs',



    # Append the group totals to the main list:
    for slot in slot_summary_total_list:
        slot['cloud_name']=''
        slot_summary_list.append(slot.copy())

    # Append the GLOBAL totals to the main list:
    for slot in slot_summary_global_total_list:
        slot['group_name']=''        
        slot['cloud_name']=''
        slot_summary_list.append(slot.copy())


    '''
    # get job status per group
    if active_user.flag_global_status:
        if active_user.flag_jobs_by_target_alias:
            s = select([view_job_status_by_target_alias])
        else:
            s = select([view_job_status])
        job_status_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['group_name'], ["mygroups"], aliases=GROUP_ALIASES, and_or='or'))
    else:    
        if active_user.flag_jobs_by_target_alias:
            s = select([view_job_status_by_target_alias]).where(view_job_status.c.group_name == active_user.active_group)
        else:
            s = select([view_job_status]).where(view_job_status.c.group_name == active_user.active_group)
        job_status_list = qt(config.db_connection.execute(s))

    # Get GSI configuration variables.
    gsi_config = config.get_config_by_category('GSI')

    # First get rows from csv2_system_status, if rows are out of date, do manual update
    system_list = {}

    s = select([csv2_system_status])
    try:
        query_result = qt(config.db_connection.execute(s))[0]
        
        if time.time() - query_result["last_updated"] < 120:
            # it has been updated in the last minute and we can just take it and go
            system_list.update(query_result)
        else:
            # throw exception
            raise Exception("System status info out of date, need to calculate manually")

    except:
        system_list["csv2_status_msg"] = service_msg("csv2-status")
        system_list["csv2_status_status"] = 0

        db_service_names = {
                        "csv2-main":        "csv2_main", 
                        "csv2-openstack":   "csv2_openstack", 
                        "csv2-jobs":        "csv2_jobs", 
                        "csv2-machines":    "csv2_machines", 
                        "csv2-timeseries":  "csv2_timeseries",
                        "csv2-ec2":         "csv2_ec2",
                        "csv2-htc-agent":   "csv2_htc_agent",
                        "csv2-watch":       "csv2_watch",
                        "csv2-startd-errors":"csv2_startd_errors",
                        "rabbitmq-server":  "rabbitmq_server",
                        "mariadb":          "mariadb", 
                        "condor":           "condor"
                   }

        #system_list = {'id': 0}
        for service, service_name in db_service_names.items():
            system_list[service_name + "_msg"] = service_msg(service)
            if "running" in system_list[service_name + "_msg"]:
                system_list[service_name + "_status"] = 1
                system_list[service_name + "_error_count"] = 0
            else:
                system_list[service_name + "_status"] = 0
                system_list[service_name + "_error_count"] = 1


        # Determine the system load, RAM and disk usage

        system_list["load"] = round(100*( os.getloadavg()[0] / os.cpu_count() ),1)

        system_list["ram"] = psutil.virtual_memory().percent
        system_list["ram_size"] = round(psutil.virtual_memory().total/1000000000 , 1)
        system_list["ram_used"] = round(psutil.virtual_memory().used/1000000000 , 1)

        system_list["swap"] = psutil.swap_memory().percent
        system_list["swap_size"] = round(psutil.swap_memory().total/1000000000 , 1)
        system_list["swap_used"] = round(psutil.swap_memory().used/1000000000 , 1)


        system_list["disk"] = round(100*(psutil.disk_usage('/').used / psutil.disk_usage('/').total),1)
        system_list["disk_size"] = round(psutil.disk_usage('/').total/1000000000 , 1)
        system_list["disk_used"] = round(psutil.disk_usage('/').used/1000000000 , 1)

    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'cloud_status_list': cloud_status_list,
            'cloud_total_list': cloud_total_list,
            'cloud_status_list_totals': cloud_status_list_totals,
            'gsi_config': gsi_config['GSI'],
            #'global_total_list': global_total_list,
            'job_status_list': job_status_list,
            'job_totals_list': job_totals_list,
            'system_list' : system_list,
            #'slot_detail_list' : slot_detail_list,
            #'slot_detail_total_list': slot_detail_total_list,
            #'slot_summary_list' : slot_summary_list,
            #'slot_summary_total_list': slot_summary_total_list,           
            #'slot_detail': slot_detail,
            #'slot_detail_total': slot_detail_total,
            'flavor_slot_detail': flavor_slot_detail,
            'flavor_slot_detail_summary': flavor_slot_detail_summary,
            'flavor_slot_summary': flavor_slot_summary,
            'slot_detail': slot_detail,
            'slot_detail_summary': slot_detail_summary,
            'slot_summary': slot_summary,
            'response_code': 0,
            'message': None,
            'is_superuser': active_user.is_superuser,
            'global_flag': active_user.flag_global_status,
            'jobs_by_target_alias_flag': active_user.flag_jobs_by_target_alias,
            'foreign_global_vms_flag': active_user.flag_show_foreign_global_vms,
            'slot_detail_flag': active_user.flag_show_slot_detail,
            'slot_flavor_flag': active_user.flag_show_slot_flavors,
            'status_refresh_interval': active_user.status_refresh_interval,
            'version': config.get_version()
        }

    config.db_close()
    return render(request, 'csv2/status.html', context)

#-------------------------------------------------------------------------------
'''
@silkp(name="Generate slot detail list")
def gen_slot_detail(slot_list):

    # Generate the slot detail value, grouping and summing slots by type.
    slot_detail = []

    # Loop through all the slots in the list:
    for slot in slot_list:

        if 'slot_count' in slot:

            count = int(slot['slot_count'])
            slot_string = slot['slot_id']+': '+str(int(slot['core_count']))

            # Check if the slot type exists in the slot detail dict
            if not any(s["type"] == count for s in slot_detail):
            
                if 'cloud_name' in slot:
                    s = {'group_name': slot['group_name'], 'cloud_name': slot['cloud_name'], 'type': count, 'sum': int(slot['core_count']), 'list': {slot['slot_id'] : int(slot['core_count'])} }
                else:
                    s = {'group_name': slot['group_name'], 'type': count, 'sum': int(slot['core_count']), 'list': {slot['slot_id'] : int(slot['core_count']) } }

                slot_detail.append(dict(s))

            else:
                for d in slot_detail:
                    if d['type'] == count:
                        d['sum'] += int(slot['core_count'])

                        if slot['slot_id'] in d['list']:
                            d['list'][slot['slot_id']] += int(slot['core_count'])
                        else:
                            d['list'][slot['slot_id']] = int(slot['core_count'])


    return slot_detail
'''
#-------------------------------------------------------------------------------

@silkp(name="Cloud Plot")
@requires_csrf_token
def request_ts_data(request):
    """
    This function should receive a post request with a payload of an influxdb query
    to update the timeseries plot.
    """

    params = {'db': 'csv2_timeseries','epoch': 'ms', 'q':request.body}
    url_string = 'http://localhost:8086/query'
    r = requests.get(url_string, params=params)
    # Check response status code
    r.raise_for_status()

    return JsonResponse(r.json())

#-------------------------------------------------------------------------------

@silkp(name="Cloud Update")
@requires_csrf_token
def update(request):
    """
    This function should recieve a post request with a payload of cloud configuration
    to update a given cloud.
    """

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return list(request, active_user=active_user, response_code=1, message='%s %s' % (lno(MODID), msg))

    if request.method == 'POST':

        # if the password is blank, remove the password field.
        if request.META['HTTP_ACCEPT'] != 'application/json' and len(request.POST['password']) == 0:
            # create a copy of the dict to make it mutable.
            request.POST = request.POST.copy()

            # remove the password field.
            del request.POST['password']

        # check if there was multiple securit groups posted
        #
        if len(request.POST.getlist("vm_security_groups")) > 1:
            # if there is a list more than 1 security group was selected
            # so we must cast the list as a string to match the format that comes from CLI
            request.POST["vm_security_groups"] = ",".join([str(x) for x in request.POST.getlist("vm_security_groups")])


        # Validate input fields.
        rc, msg, fields, tables, columns = validate_fields(config, request, [CLOUD_KEYS], ['csv2_clouds', 'csv2_cloud_flavor_exclusions,n', 'csv2_group_metadata,n', 'csv2_group_metadata_exclusions,n'], active_user)
        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud update %s' % (lno(MODID), msg))

        if 'flavor_name' in fields and fields['flavor_name']:
            rc, msg = validate_by_filtered_table_entries(config, fields['flavor_name'], 'flavor_name', 'cloud_flavors', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]], allow_value_list=True)
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_flavor' in fields and fields['vm_flavor']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_flavor'], 'vm_flavor', 'cloud_flavors', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_image' in fields and fields['vm_image']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_image'], 'vm_image', 'cloud_images', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_keyname' in fields and fields['vm_keyname']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_keyname'], 'vm_keyname', 'cloud_keypairs', 'key_name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_network' in fields and fields['vm_network']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_network'], 'vm_network', 'cloud_networks', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]])
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        if 'vm_security_groups' in fields and fields['vm_security_groups']:
            rc, msg = validate_by_filtered_table_entries(config, fields['vm_security_groups'], 'vm_security_groups', 'cloud_security_groups', 'name', [['group_name', fields['group_name']], ['cloud_name', fields['cloud_name']]], allow_value_list=True)
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        # Validity check the specified metadata exclusions.
        if 'metadata_name' in fields:
            rc, msg = manage_group_metadata_verification(tables, fields['group_name'], fields['cloud_name'], fields['metadata_name']) 
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update, "%s" failed - %s.' % (lno(MODID), fields['cloud_name'], msg))

        # Verify cloud credentials.
        rc, msg, owner_id = verify_cloud_credentials(config, fields, active_user)
        if rc == 0:
            fields['ec2_owner_id'] = owner_id
        else:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud update "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # update the cloud.
        table = tables['csv2_clouds']
        cloud_updates = table_fields(fields, table, columns, 'update')
        updates = len(cloud_updates)
        if updates > 0:
            rc, msg = config.db_session_execute(table.update().where((table.c.group_name==fields['group_name']) & (table.c.cloud_name==fields['cloud_name'])).values(cloud_updates))
            if rc != 0:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        # if the cloud is disabled call routine to retire all vms
        if 'enabled' in fields:
            if fields['enabled'] == 0:
                #call retire routine
                retire_cloud_vms(config, fields['group_name'], fields['cloud_name'])

        # If either the cores_ctl or the ram_ctl have been modified, call kill_retire to scale current usage.
        if 'cores_ctl' in fields and 'ram_ctl' in fields:
            updates += kill_retire(config, active_user.active_group, fields['cloud_name'], 'control', [fields['cores_ctl'], fields['ram_ctl']], get_frame_info())
        elif 'cores_ctl' in fields:
            updates += kill_retire(config, active_user.active_group, fields['cloud_name'], 'control', [fields['cores_ctl'], -1], get_frame_info())
        elif 'ram_ctl' in fields:
            updates += kill_retire(config, active_user.active_group, fields['cloud_name'], 'control', [-1, fields['ram_ctl']], get_frame_info())

        # Update the cloud's flavor exclusions.
        if request.META['HTTP_ACCEPT'] == 'application/json':
            if 'flavor_name' in fields:
                updates += 1
                if 'flavor_option' in fields and fields['flavor_option'] == 'delete':
                    rc, msg = manage_cloud_flavor_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['flavor_name'], option='delete')
                else:
                    rc, msg = manage_cloud_flavor_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['flavor_name'], option='add')

        else:
            updates += 1
            if 'flavor_name' in fields:
                rc, msg = manage_cloud_flavor_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['flavor_name'])
            else:
                rc, msg = manage_cloud_flavor_exclusions(tables, fields['group_name'], fields['cloud_name'], None)

        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s update cloud flavor exclusion for cloud "%s::%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], fields['flavor_name'], msg))

        # Update the cloud's group metadata exclusions.
        if request.META['HTTP_ACCEPT'] == 'application/json':
            if 'metadata_name' in fields:
                updates += 1
                if 'metadata_option' in fields and fields['metadata_option'] == 'delete':
                    rc, msg = manage_group_metadata_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['metadata_name'], option='delete')
                else:
                    rc, msg = manage_group_metadata_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['metadata_name'], option='add')

        else:
            updates += 1
            if 'metadata_name' in fields:
                rc, msg = manage_group_metadata_exclusions(tables, fields['group_name'], fields['cloud_name'], fields['metadata_name'])
            else:
                rc, msg = manage_group_metadata_exclusions(tables, fields['group_name'], fields['cloud_name'], None)

        if rc != 0:
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s update group metadata exclusion for cloud "%s::%s::%s" failed - %s.' % (lno(MODID), request.method))

        # For EC2 clouds, add default filters.
        if 'cloud_type' in fields:
            rc, msg = ec2_filters(config, fields['group_name'], fields['cloud_name'], fields['cloud_type'])
            if rc == 0:
                updates += 1
            else:
                config.db_close()
                return list(request, active_user=active_user, response_code=1, message='%s cloud update "%s::%s" failed - %s.' % (lno(MODID), fields['group_name'], fields['cloud_name'], msg))

        if updates > 0:
            act_usr = active_user.username
            #signal the pollers that a cloud has been updated
            send_signals(config, "update_csv2_clouds")
            config.db_close(commit=True)
            return list(request, active_user=active_user, response_code=0, message='cloud "%s::%s" successfully updated.' % (fields['group_name'], fields['cloud_name']))
        else:
            act_usr = active_user.username
            config.db_close()
            return list(request, active_user=active_user, response_code=1, message='%s cloud update must specify at least one field to update.' % lno(MODID))

    ### Bad request.
    else:
        return list(request, active_user=active_user, response_code=1, message='%s cloud update, invalid method "%s" specified.' % (lno(MODID), request.method))

