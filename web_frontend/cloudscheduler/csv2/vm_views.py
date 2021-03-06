from django.conf import settings
config = settings.CSV2_CONFIG

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import requires_csrf_token
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied


from cloudscheduler.lib.view_utils import \
    kill_retire, \
    lno, \
    qt, \
    qt_filter_get, \
    render, \
    set_user_groups, \
    table_fields, \
    validate_fields
from collections import defaultdict
import bcrypt
import time

from sqlalchemy import exists
from sqlalchemy.sql import select
from sqlalchemy.sql import and_
from cloudscheduler.lib.schema import *
from cloudscheduler.lib.log_tools import get_frame_info
import sqlalchemy.exc

from cloudscheduler.lib.web_profiler import silk_profile as silkp

# lno: VV - error code identifier.
MODID = 'VV'

#-------------------------------------------------------------------------------
ALIASES = {'poller_status': {'native': ['manual', 'error', 'unregistered', 'retiring', 'running', 'other']}}

VM_KEYS = {
    'auto_active_group': True,
    # Named argument formats (anything else is a string).
    'format': {
        'poller_status':                                                ['native', 'idle', 'starting', 'manual', 'error', 'unregistered', 'retiring', 'running', 'other'],
        'vm_option':                                                    ['kill', 'retain', 'retire', 'manctl', 'sysctl'],

        'cloud_name':                                                   'ignore',
        'csrfmiddlewaretoken':                                          'ignore',
        'group':                                                        'ignore',
        'vm_hosts':                                                     'lowercase',
        },
    }

LIST_KEYS = {
    # Named argument formats (anything else is a string).
    'format': {
        'csrfmiddlewaretoken':                                          'ignore',
        'group':                                                        'ignore',
        },
    }

MANDATORY_KEYS = {
    'mandatory': [
        'vm_hosts',
        'vm_option',
        ]
    }
#-------------------------------------------------------------------------------

@silkp(name="Foreign List")
@requires_csrf_token
def foreign(request):

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/foreign.html', {'response_code': 1, 'message': '%s %s' % (lno(MODID), msg)})

    # Validate input fields (should be none).
    rc, msg, fields, tables, columns = validate_fields(config, request, [LIST_KEYS], [], active_user)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/foreign.html', {'response_code': 1, 'message': '%s vm list, %s' % (lno(MODID), msg)})

    global_view = active_user.kwargs['global_view']

    if global_view=='1':
        s = select([view_foreign_flavors])
        foreign_list = qt(config.db_connection.execute(s))

    else:
        # Retrieve VM information.
        s = select([view_foreign_flavors]).where(view_foreign_flavors.c.group_name == active_user.active_group)
        foreign_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['cloud_name'], active_user.kwargs))
#   vm_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['cloud_name', 'poller_status', 'hostname'], selector.split('::'), aliases=ALIASES), convert={


    config.db_close()

    #if cloud_name in vm_name:



    # Render the page.
    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'foreign_list': foreign_list,
            'global_view' : global_view,
            'response_code': 0,
            'message': None,
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
        }

    return render(request, 'csv2/foreign.html', context)

#-------------------------------------------------------------------------------

@silkp(name="VM List")
@requires_csrf_token
def list(request, args=None, response_code=0, message=None):

    # open the database.
    config.db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s %s' % (lno(MODID), msg)})

    # Validate input fields (should be none).
    
    if args==None:
        args=active_user.kwargs
        rc, msg, fields, tables, columns = validate_fields(config, request, [LIST_KEYS], [], active_user)
        if rc != 0:
            config.db_close()
            return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s vm list, %s' % (lno(MODID), msg)})

    # Retrieve VM information.
    s = select([view_vms]).where(view_vms.c.group_name == active_user.active_group)

    vm_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['cloud_name', 'poller_status', 'hostname'], args, aliases=ALIASES), convert={
        'htcondor_slots_timestamp': 'datetime',
        'htcondor_startd_time': 'datetime',
        'last_updated': 'datetime',
        'retire_time': 'datetime',
        'start_time': 'datetime',
        'status_changed_time': 'datetime',
        'terminate_time': 'datetime'
        })

    config.db_close()

    # Render the page.
    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'vm_list': vm_list,
            'response_code': response_code,
            'message': message,
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
        }

    return render(request, 'csv2/vms.html', context)

#-------------------------------------------------------------------------------

@silkp(name="VM Update")
@requires_csrf_token
def update(
    request, 
    ):
    """
    Update VMs.
    """

    # open the database.
    config.db_open()
    
    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request, super_user=False)
    if rc != 0:
        config.db_close()
        return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s %s' % (lno(MODID), msg), 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})
#       return list(request, selector, response_code=1, message='%s %s' % (lno(MODID), msg), user_groups=user_groups)

    if request.method == 'POST':
        # Validate input fields.
        rc, msg, fields, tables, columns = validate_fields(config, request, [VM_KEYS, MANDATORY_KEYS], ['csv2_vms,n', 'condor_machines,n'], active_user)
        if rc != 0:
            config.db_close()
            return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s vm update %s' % (lno(MODID), msg), 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})
#           return list(request, selector, response_code=1, message='%s vm update %s' % (lno(MODID), msg), user_groups=user_groups)

        if fields['vm_option'] == 'kill':
            table = tables['csv2_vms']
            verb = 'killed'
        elif fields['vm_option'] == 'retire':
            table = tables['csv2_vms']
            verb = 'retired'
        elif fields['vm_option'] == 'retain':
            if fields['vm_hosts'].isnumeric():
                verb = 'killed or retired'
            else:
                config.db_close()
                return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s vm update, the "--vm-hosts" parameter must be numeric when "--vm-option retain" is specified.' % lno(MODID), 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})
#               return list(request, selector, response_code=1, message='%s vm update, the "--vm-hosts" parameter must be numeric when "--vm-option retain" is specified.' % lno(MODID))
        elif fields['vm_option'] == 'manctl':
            table = tables['csv2_vms']
            verb = 'set to manual control'
        elif fields['vm_option'] == 'sysctl':
            table = tables['csv2_vms']
            verb = 'set to system control'
        else:
            return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s vm update, option "%s" is invalid.' % (lno(MODID), fields['vm_option']), 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})


        # Retrieve VM information.
        #if fields['vm_hosts'].isnumeric():
        if isinstance(fields['vm_hosts'], int):
           
            if 'cloud_name' in fields:
                count = kill_retire(config, active_user.active_group, fields['cloud_name'], fields['vm_option'], fields['vm_hosts'], get_frame_info())
#               count = kill_retire(config, active_user.active_group, fields['cloud_name'], 'control', [50,1000000], get_frame_info())
            else:
                count = kill_retire(config, active_user.active_group, '-', fields['vm_option'], fields['vm_hosts'], get_frame_info())
        else:
            count = 0
            if fields['vm_hosts'] != '':
                if fields['vm_hosts'] == 'all':
                    s = select([view_vms]).where(view_vms.c.group_name == active_user.active_group)
                    vm_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['cloud_name', 'poller_status'], fields, aliases=ALIASES))
                else:
                    fields['hostname'] = fields['vm_hosts']
                    s = select([view_vms]).where(view_vms.c.group_name == active_user.active_group)
                    vm_list = qt(config.db_connection.execute(s), filter=qt_filter_get(['cloud_name', 'hostname', 'poller_status'], fields, aliases=ALIASES))

                for vm in vm_list:
                    if fields['vm_option'] == 'kill':
                        update = table.update().where(table.c.vmid == vm['vmid']).values({'terminate': 2, 'updater': get_frame_info()})
                    elif fields['vm_option'] == 'retire':
                        update = table.update().where(table.c.vmid == vm['vmid']).values({'retire': 1, 'updater': get_frame_info()})
                    elif fields['vm_option'] == 'manctl':
                        update = table.update().where(table.c.vmid == vm['vmid']).values({'manual_control': 1})
                    elif fields['vm_option'] == 'sysctl':
                        update = table.update().where(table.c.vmid == vm['vmid']).values({'manual_control': 0})

                    rc, msg = config.db_session_execute(update, allow_no_rows=True)
                    if rc == 0:
                        count += msg
                    else:
                        config.db_close()
                        return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s vm update (%s) failed - %s' % (lno(MODID), fields['vm_option'], msg), 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})
#                       return list(request, selector, response_code=1, message='%s vm update (%s) failed - %s' % (lno(MODID), fields['vm_option'], msg))

        if count > 0:
            config.db_close(commit=True)
        else:
            config.db_close()


        args={}
        if 'cloud_name' in fields:
            args['cloud_name'] =  fields['cloud_name']
        if 'poller_status' in fields:
            args['poller_status'] = fields['poller_status']
        args['hostname'] = ''

        return list(request, args, response_code=0, message='vm update, VMs %s: %s.' % (verb, count))

    ### Bad request.
    else:
        return render(request, 'csv2/vms.html', {'response_code': 1, 'message': '%s vm update, invalid method "%s" specified.' % (lno(MODID), request.method), 'active_user': active_user.username, 'active_group': active_user.active_group, 'user_groups': active_user.user_groups})
#       return list(request, selector, response_code=1, message='%s vm update, invalid method "%s" specified.' % (lno(MODID), request.method))
