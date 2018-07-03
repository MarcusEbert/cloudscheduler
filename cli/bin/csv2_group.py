from csv2_common import check_keys, requests, show_active_user_groups, show_table, verify_yaml_file
from subprocess import Popen, PIPE

import filecmp
import os

KEY_MAP = {
    '-gn':  'group_name',
    '-gm':  'condor_central_manager',
    '-me':  'enabled',
    '-mmt': 'mime_type',
    '-mn':  'metadata_name',
    '-mp':  'priority',
    '-jc':  'job_cpus',
    '-jd':  'job_disk',
    '-jed': 'job_scratch',
    '-jr':  'job_ram',
    '-js':  'job_swap',
    '-un':  'username',
    '-uo':  'user_option',
    }

def _filter_by_group_name_and_or_metadata_name(gvar, qs):
    """
    Internal function to filter a query set by the specified group name.
    """

    if 'group-name' in gvar['command_args']:
        for _ix in range(len(qs)-1, -1, -1):
            if qs[_ix]['group_name'] != gvar['command_args']['group-name']:
                del(qs[_ix])

    if 'metadata-name' in gvar['command_args']:
        for _ix in range(len(qs)-1, -1, -1):
            if qs[_ix]['metadata_name'] != gvar['command_args']['metadata-name']:
                del(qs[_ix])

    return qs

def add(gvar):
    """
    Add a group to the active group.
    """

    # Check for missing arguments or help required.
    form_data = check_keys(
        gvar,
        ['-gm', '-gn'],
        [],
        ['-un'],
        key_map=KEY_MAP)

    # Create the group.
    response = requests(
        gvar,
        '/group/add/',
        form_data
        )
    
    if response['message']:
        print(response['message'])

def defaults(gvar):
    """
    Modify the specified group defaults.
    """

    # Check for missing arguments or help required.
    form_data = check_keys(
        gvar,
        [],
        [],
        ['-g', '-jc', '-jd', '-jed', '-jr', '-js'],
        key_map=KEY_MAP)

    # List the current defaults. If the form_data contains any optional fields,
    # those values will be updated before the list is retrieved.
    response = requests(
        gvar,
        '/group/defaults/',
        form_data
        )
    
    if response['message']:
        print(response['message'])

    # Print report
    show_active_user_groups(gvar, response)

    show_table(
        gvar,
        response['defaults_list'],
        [
            'group_name/Group,k',
            'job_cpus/Job Cores',
            'job_disk/Job Disk (GBs)',
            'job_scratch/Job Ephemeral Disk (GBs)',
            'job_ram/Job RAM (MBs)',
            'job_swap/Job Swap (GBs)',
            ],
            title="Active Group Defaults:",
        )

def delete(gvar):
    """
    Delete a group from the active group.
    """

    # Check for missing arguments or help required.
    check_keys(gvar, ['-gn'], [], [])

    # Check that the target group exists.
    response = requests(gvar, '/group/list/')
    _found = False
    for row in response['group_list']:
      if row['group_name'] == gvar['user_settings']['group-name']:
        _found = True
        break
   
    if not _found:
        print('Error: "%s group delete" cannot delete "%s", group doesn\'t exist.' % (gvar['command_name'], gvar['user_settings']['group-name']))
        exit(1)

    # Confirm group delete.
    if not gvar['user_settings']['yes']:
        print('Are you sure you want to delete group "%s"? (yes|..)' % gvar['user_settings']['group-name'])
        _reply = input()
        if _reply != 'yes':
          print('%s group delete "%s" cancelled.' % (gvar['command_name'], gvar['user_settings']['group-name']))
          exit(0)

    # Delete the group.
    response = requests(
        gvar,
        '/group/delete/',
        form_data = {
            'group_name': gvar['user_settings']['group-name']
            }
        )
    
    if response['message']:
        print(response['message'])

def list(gvar):
    """
    List groups.
    """

    # Check for missing arguments or help required.
    check_keys(gvar, [], [], ['-gn', '-ok'])

    # Retrieve data (possibly after changing the group).
    response = requests(gvar, '/group/list/')
    
    if response['message']:
        print(response['message'])

    # Filter response as requested (or not).
    group_list = _filter_by_group_name_and_or_metadata_name(gvar, response['group_list'])

    # Print report
    show_active_user_groups(gvar, response)

    show_table(
        gvar,
        group_list,
        [
            'group_name/Group,k',
            'condor_central_manager/Central Manager',
            'metadata_names/Metadata Filenames',
            ],
        title="Groups:",
        )

def update(gvar):
    """
    Modify the specified group.
    """

    # Check for missing arguments or help required.
    form_data = check_keys(
        gvar,
        ['-gn'],
        [],
        ['-gm', '-un', '-uo'],
        key_map=KEY_MAP)

    if len(form_data) < 2:
        print('Error: "%s group update" requires at least one option to update.' % gvar['command_name'])
        exit(1)

    # Create the group.
    response = requests(
        gvar,
        '/group/update/',
        form_data
        )
    
    if response['message']:
        print(response['message'])

def metadata_delete(gvar):
    """
    Delete a group metadata file.
    """

    # Check for missing arguments or help required.
    check_keys(gvar, ['-mn'], [], ['-g'])

    # Check that the target groupmetadata file exists.
    response = requests(gvar, '/group/list/')
    _found = False
    for row in response['group_list']:
        if row['group_name'] == gvar['active_group']:
            metadata_names = row['metadata_names'].split(',')
            for metadata_name in metadata_names:
                if row['group_name'] == gvar['active_group']:
                    _found = True
                    break
   
    if not _found:
        print('Error: "%s group metadata-delete" cannot delete "%s::%s", file doesn\'t exist.' % (gvar['command_name'], response['active_group'], gvar['user_settings']['metadata-name']))
        exit(1)

    # Confirm group metadata file delete.
    if not gvar['user_settings']['yes']:
        print('Are you sure you want to delete the metadata file "%s::%s"? (yes|..)' % (response['active_group'], gvar['user_settings']['metadata-name']))
        _reply = input()
        if _reply != 'yes':
            print('%s group metadata-delete "%s::%s" cancelled.' % (gvar['command_name'], response['active_group'], gvar['user_settings']['metadata-name']))
            exit(0)

    # Delete the group metadata file.
    response = requests(
        gvar,
        '/group/metadata-delete/',
        form_data = {
            'metadata_name': gvar['user_settings']['metadata-name'],
            }
        )
    
    if response['message']:
        print(response['message'])

def metadata_edit(gvar):
    """
    Edit the specified group metadata file.
    """

    # Check for missing arguments or help required.
    check_keys(gvar, ['-mn'], ['-te'], ['-g'])

    # Retrieve data (possibly after changing the group).
    response = requests(gvar, '/group/metadata-fetch/%s' % gvar['user_settings']['metadata-name'])

    # Ensure the fetch directory structure exists.
    fetch_dir = '%s/.csv2/%s/files/%s/metadata' % (
        gvar['home_dir'],
        gvar['server'],
        response['group_name'],
        )

    if not os.path.exists(fetch_dir):
        os.makedirs(fetch_dir, mode=0o700)  

    # Write the reference copy.
    fd = open('%s/.%s' % (fetch_dir, response['metadata_name']), 'w')
#   fd.write('# metadata_enabled: %s, metadata_mime_type: %s\n%s' % (response['metadata_enabled'], response['metadata_mime_type'], response['metadata']))
    fd.write(response['metadata'])
    fd.close()

    # Write the edit copy.
    fd = open('%s/%s' % (fetch_dir, response['metadata_name']), 'w')
#   fd.write('# metadata_enabled: %s, metadata_mime_type: %s\n%s' % (response['metadata_enabled'], response['metadata_mime_type'], response['metadata']))
    fd.write(response['metadata'])
    fd.close()

    # Edit the metadata file.
    p = Popen([gvar['user_settings']['text-editor'], '%s/%s' % (fetch_dir, response['metadata_name'])])
    p.communicate()

    if filecmp.cmp(
        '%s/.%s' % (fetch_dir, response['metadata_name']),
        '%s/%s' % (fetch_dir, response['metadata_name'])
        ):
        print('%s group metadata-edit "%s::%s" completed, no changes.' % (gvar['command_name'], response['group_name'],  response['metadata_name']))
        exit(0)

    # Verify the changed metadata file.
    form_data = {
        **verify_yaml_file('%s/%s' % (fetch_dir, response['metadata_name'])),
        'metadata_name': response['metadata_name'],
        }

    # Replace the metadata file.
    response = requests(
        gvar,
        '/group/metadata-update/',
        form_data
        )
    
    if response['message']:
        print(response['message'])

def metadata_list(gvar):
    """
    List clouds for the active group.
    """

    # Check for missing arguments or help required.
    check_keys(gvar, [], [], ['-cn', '-g', '-ok', '-mn'])

    # Retrieve data (possibly after changing the group).
    response = requests(gvar, '/group/metadata-list/')
    
    if response['message']:
        print(response['message'])

    # Filter response as requested (or not).
    group_metadata_list = _filter_by_group_name_and_or_metadata_name(gvar, response['group_metadata_list'])

    # Print report.
    show_active_user_groups(gvar, response)

    show_table(
        gvar,
        group_metadata_list,
        [
            'group_name/Group,k',
            'metadata_name/Metadata Filename,k',
            'enabled/Enabled',
            'priority/Priority',
            'mime_type/MIME Type',
        ],
        title="Active Group/Metadata:",
        )

def metadata_load(gvar):
    """
    Load a new group metadata file.
    """

    # Check for missing arguments or help required.
    form_data = check_keys(
        gvar,
        ['-f', '-mn'],
        [],
        ['-g', '-me', '-mmt', '-mp'],
        key_map=KEY_MAP)

    if not os.path.exists(gvar['user_settings']['file-path']):
        print('Error: The specified metadata file "%s" does not exist.' % gvar['user_settings']['file-path'])
        exit(1)

#   # Verify the changed metadata file and build input form data.
#   form_data = {
#       **verify_yaml_file(gvar['user_settings']['file-path']),
#       'metadata_name': gvar['user_settings']['metadata-name'],
#       }

    # Replace the metadata file.
    response = requests(
        gvar,
        '/group/metadata-add/',
        {
            **form_data,
            **verify_yaml_file(gvar['user_settings']['file-path']),
            }
        )
    
    if response['message']:
        print(response['message'])

def metadata_update(gvar):
    """
    Update metadata fiel information.
    """

    # Check for missing arguments or help required.
    form_data = check_keys(
        gvar,
        ['-mn'],
        [],
        ['-g', '-me', '-mmt', '-mp'],
        key_map=KEY_MAP)

    if len(form_data) < 2:
        print('Error: "%s group metadata-update" requires at least one option to modify.' % gvar['command_name'])
        exit(1)

    # Create the cloud.
    response = requests(
        gvar,
        '/group/metadata-update/',
        form_data
        )
    
    if response['message']:
        print(response['message'])

