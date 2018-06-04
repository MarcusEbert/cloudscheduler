from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import requires_csrf_token
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

from django.contrib.auth.models import User #to get auth_user table
from .models import user as csv2_user
from . import config

from .view_utils import \
    db_execute, \
    db_open, \
    getAuthUser, \
    getcsv2User, \
    getSuperUserStatus, \
    lno, \
    qt, \
    render, \
    set_user_groups, \
    table_fields, \
    validate_fields, \
    verifyUser
from collections import defaultdict
import bcrypt

from sqlalchemy import exists
from sqlalchemy.sql import select
from sqlalchemy.sql import and_
from lib.schema import *
import sqlalchemy.exc

# lno: CV - error code identifier.

#-------------------------------------------------------------------------------

CLOUD_KEYS = {
    'auto_active_group': True,
    # Named argument formats (anything else is a string).
    'format': {
        'cloud_name':          'lowerdash',

        'cores_slider':        'ignore',
        'csrfmiddlewaretoken': 'ignore',
        'group':               'ignore',
        'ram_slider':          'ignore',
        },
    }

YAML_KEYS = {
    'auto_active_group': True,
    # Named argument formats (anything else is a string).
    'format': {
        'cloud_name':          'lowerdash',
        'yaml_name':           'lowercase',

        'csrfmiddlewaretoken': 'ignore',
        'group':               'ignore',
        },
    }

IGNORE_YAML_NAME = {
    'format': {
        'yaml_name':           'ignore',
        },
    }

#-------------------------------------------------------------------------------

@requires_csrf_token
def list(
    request,
    selector=None,
    group_name=None,
    response_code=0,
    message=None,
    active_user=None,
    user_groups=None,
    attributes=None
    ):

    if not verifyUser(request):
        raise PermissionDenied

    # open the database.
    db_engine,db_session,db_connection,db_map = db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    if not active_user:
        rc, msg, active_user, user_groups = set_user_groups(request, db_session, db_map)
        if rc != 0:
            db_connection.close()
            return render(request, 'csv2/clouds.html', {'response_code': 1, 'message': msg})

    # Position the page.
    obj_act_id = request.path.split('/')
    if selector:
        if selector == '-':
            current_cloud = ''
            cloud_column_prune = ['']
            s = select([view_vms]).where(view_vms.c.group_name == active_user.active_group)
        else:
            current_cloud = selector
            cloud_column_prune = ['cloud_name']
            s = select([view_vms]).where(and_(view_vms.c.group_name == active_user.active_group, view_vms.c.cloud_name == current_cloud))
        # elif len(obj_act_id) > 3 and len(obj_act_id[3]) > 0:
        #     current_cloud = str(obj_act_id[3])
        #     cloud_column_prune = [cloud_name]
    else:
        # if len(cloud_list) > 0:
        #     current_cloud = str(cloud_list[0]['cloud_name'])
        #     cloud_column_prune = ['cloud_name']
        # else:
        #     current_cloud = ''
        #     cloud_column_prune = ['']
        current_cloud = ''
        cloud_column_prune = ['']
        s = select([view_vms]).where(view_vms.c.group_name == active_user.active_group)

    # Retrieve VM information.
    # s = select([view_vms]).where(view_vms.c.group_name == active_user.active_group)
    vm_list = qt(db_connection.execute(s)), prune=cloud_column_prune)

    db_connection.close()

    # Render the page.
    context = {
            'active_user': active_user,
            'active_group': active_user.active_group,
            'attributes': attributes,
            'user_groups': user_groups,
            'vm_list': vm_list,
            'response_code': response_code,
            'message': message,
            'enable_glint': config.enable_glint
        }

    return render(request, 'csv2/vms.html', context)
