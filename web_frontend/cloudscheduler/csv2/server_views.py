from django.conf import settings
config = settings.CSV2_CONFIG

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import requires_csrf_token
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

from cloudscheduler.lib.schema import csv2_configuration
from cloudscheduler.lib.view_utils import \
    cskv,  \
    lno,  \
    qt, \
    render, \
    set_user_groups

from collections import defaultdict
import bcrypt

from sqlalchemy import Table, MetaData
from sqlalchemy.sql import select
#import sqlalchemy.exc

from cloudscheduler.lib.web_profiler import silk_profile as silkp

# lno: SV - error code identifier.
MODID = 'SV'

#-------------------------------------------------------------------------------

@silkp(name="Server Config")
def configuration(request):
    """
    Update and list server configurations
    """

    config.db_open()
    message = None

    # Retrieve the active user, associated group list and optionally set the active group.
    rc, msg, active_user = set_user_groups(config, request)
    if rc == 0:
        if request.method == 'POST':
                if 'category' in request.POST:
                    if 'config_key_values' in request.POST:
                        rc, msg, key_values = cskv(request.POST['config_key_values'])
                        category = request.POST['category']

                    else:
                        rc = 0
                        key_values = {}
                        for key in request.POST:
                            key_values[key] = request.POST[key]

                        key_values.pop('csrfmiddlewaretoken', None)
                        category = key_values.pop('category', None)

                    if rc == 0:
                        config_list = qt(config.db_connection.execute('select config_key,config_type,config_value from csv2_configuration where category="%s"' % category))
                        if len(config_list) > 0:
                            config_keys = {}
                            for config_item in config_list:
                                config_keys[config_item['config_key']] = {'type': config_item['config_type'], 'value': config_item['config_value']}

                            message = None
                            for key in key_values:
                                if key in config_keys:
                                    if config_keys[key]['type'] == 'int':
                                        try:
                                            ignore = int(key_values[key])
                                        except:
                                            message = '%s server config update failed - value specified ("%s") for category="%s", config_key="%s" must be an integer.' % (lno(MODID), key_values[key], category, key)
                                            break
                                           
                                    elif config_keys[key]['type'] == 'str':
                                        pass

                                    elif config_keys[key]['type'] == 'bool':
                                        bool = key_values[key].lower()
                                        if bool == '0' or bool == 'no' or bool == 'off' or bool == 'false':
                                            key_values[key] = 'False'
                                        elif bool == '1' or bool == 'yes' or bool == 'on' or bool == 'true':
                                            key_values[key] = 'True'
                                        else:
                                            message = '%s server config update failed - value specified ("%s") for category="%s", config_key="%s" must be a boolean value.' % (lno(MODID), key_values[key], category, key)
                                            break

                                    elif config_keys[key]['type'] == 'decimal' or config_keys[key]['type'] == 'float':
                                        try:
                                            ignore = float(key_values[key])
                                        except:
                                            message = '%s server config update failed - value specified ("%s") for category="%s", config_key="%s" must be a decimal or floating point number.' % (lno(MODID), key_values[key], category, key)
                                            break

                                    else:
                                        raise Exception('unsupported config_type in csv2_configurations - category="%s", config_key="%s", config_type="%s".' % (category, key, config_keys[key]))

                                else:
                                    message = '%s server config update failed - category="%s", invalid key "%s" specified.' % (lno(MODID), category, key)
                                    break

                            if not message:
                                keys = []
                                table = Table('csv2_configuration', MetaData(bind=config.db_engine), autoload=True)
                                for key in key_values:
                                    if key_values[key] != config_keys[key]['value']:
                                        keys.append(key)
                                        rc, msg = config.db_session_execute(table.update().where((table.c.category==category) & (table.c.config_key==key)).values({table.c.config_value:key_values[key]}))
                                        if rc != 0:
                                            config.db_session.rollback()
                                            message = '{} server config update failed - {}'.format(lno(MODID), msg)
                                            break

                                if len(keys) > 0:
                                    config.db_session.commit()
                                    message = 'server config update successfully updated the following keys: %s' % ', '.join(keys)

                        else:
                            message = '%s server config update failed - invalid category "%s" specified.' % (lno(MODID), category)
                else:
                    message = '%s server config update failed - no category specified.' % lno(MODID)
                    
    else:
        message='{} {}'.format(lno(MODID), msg)

    if message and message[:2] == 'SV':
        response_code = 1
    else:
        response_code = 0

    s = select([csv2_configuration])
    config_list = qt(config.db_connection.execute(s))
    config_categories = list({v['category']:v for v in config_list})

    # Render the page.
    context = {
            'active_user': active_user.username,
            'active_group': active_user.active_group,
            'user_groups': active_user.user_groups,
            'config_list': config_list,
            'config_categories': config_categories,
            'response_code': response_code,
            'message': message,
            'is_superuser': active_user.is_superuser,
            'version': config.get_version()
        }

    config.db_close()
    return render(request, 'csv2/server_config.html', context)

