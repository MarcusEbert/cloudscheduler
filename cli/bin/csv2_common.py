def check_keys(gvar, mp, rp, op, key_map=None, requires_server=True):
    """
    Modify user settings.
    """

    import csv2_help
    from os import getenv

    # Summarize the mandatory, required, and optional parameters for the current command.
    mandatory = []
    required = []
    options = []
    valid_keys = []
    for key in gvar['command_keys']:
        # 0.short_name, 1.long_name, 2.key_value(bool)
        if key[0] in mp:
            mandatory.append([key[0], '%-4s |  %s' % (key[0], key[1]), key[1][2:]])
        if key[0] in rp:
            required.append([key[0], '%-4s |  %s' % (key[0], key[1]), key[1][2:]])
        if key[0] in op or (op == ['*'] and key[0] not in mp + rp):
            options.append([key[0], '%-4s |  %s' % (key[0], key[1]), key[1][2:]])
        if key[0] in mp + rp + op or (op == ['*'] and key[0] not in mp + rp):
            valid_keys.append(key[1][2:])
    
    # Check for invalid parameters
    for key in gvar['command_args']:
        if gvar['command_args'][key] and (key not in valid_keys):
            print('Error: The following command line arguments were invalid: {}'.format(key))
            exit(1)

    # Check if help requested.
    csv2_help.help(gvar, mandatory=mandatory, required=required,  options=options, requires_server=requires_server)

    # If the current command has mandatory parameters and they have not been specified, issue error messages and exit.
    form_data = {}
    missing = []
    for key in mandatory:
        if key[2] in gvar['command_args']:
            if key_map and key[0] in key_map:
#               form_data[key_map[key[0]]] = gvar['command_args'][key[2]]
                form_data[key_map[key[0]]] = _check_keys_for_password(gvar, key)
        else:
            missing.append(key[1])

    if missing:
        print('Error: "%s %s %s" - the following mandatory parameters must be specfied on the command line:' % (gvar['command_name'], gvar['object'], gvar['action']))
        for key in missing:
            print('  %s' % key)
        print('For more information, use -H.')
        exit(1)

    missing = []
    for key in required:
        if key[2] in gvar['user_settings']:
            if key_map and key[0] in key_map:
#               form_data[key_map[key[0]]] = gvar['user_settings'][key[2]]
                form_data[key_map[key[0]]] = _check_keys_for_password(gvar, key)
        elif not (key[2] == '-te' and getenv('EDITOR') is not None):
            missing.append(key[1])

    if missing:
        print('Error: "%s %s %s" - no value, neither default nor command line, for the following required parameters:' % (gvar['command_name'], gvar['object'], gvar['action']))
        for key in missing:
            print('  %s' % key)
        print('For more information, use -h or -H.')
        exit(1)

    if key_map:
        for key in options:
            if key[0] in key_map and key[2] in gvar['user_settings']:
                form_data[key_map[key[0]]] = _check_keys_for_password(gvar, key)

    return form_data

def _check_keys_for_password(gvar, key):
    """
    Internal function to prompt for passwords (if requested, iw -upw ?).
    """
    
    from getpass import getpass

    if key[2] != 'server-password' and key[2][-8:] == 'password' and len(gvar['user_settings'][key[2]]) > 0 and gvar['user_settings'][key[2]][0] == '?':
        while(1):
            pw1 = getpass('Enter %s: ' % key[2])
            if len(pw1) > 5:
                if len(gvar['user_settings'][key[2]]) > 1 and gvar['user_settings'][key[2]][1] == '?':
                    pw2 = getpass('Verify %s: ' % key[2])
                    if pw1 == pw2:
                        return pw1
                    else:
                        print('Passwords did not match.')
                else:
                    return pw1
            else:
                print('Passwords must be at least 6 characters long.')
    else:
       return gvar['user_settings'][key[2]]

def requests(gvar, request, form_data={}):
    """
    Make RESTful requests via the _requests function and return the response. This function will
    obtain a CSRF (for POST requests) prior to making the atual request.
    """
    
    # Obtain a CSRF as required.
    if form_data and not gvar['csrf']:
        response = _requests(gvar, '/settings/prepare/')
    
    # Group change requested but the request is not a POST.
    elif not form_data and 'group' in gvar['command_args']:
        if not gvar['csrf']:
            response = _requests(gvar, '/settings/prepare/')
    
        response = _requests(gvar,
                '/settings/prepare/',
                form_data = {
                    'group': gvar['user_settings']['group'],
                    }       
            ) 
        
    # Perform the callers request.
    return _requests(gvar, request, form_data=form_data)

def _requests(gvar, request, form_data={}):
    """
    Make RESTful request and return response.
    """
    
    from getpass import getpass
    import os
    import requests as py_requests

    EXTRACT_CSRF = str.maketrans('=;', '  ')

    if 'server-address' not in gvar['user_settings']:
        print('Error: user settings for server "%s" does not contain a URL value.' % gvar['server'])
        exit(1)

    if form_data:
        _function = py_requests.post
        _form_data = {**form_data, **{'csrfmiddlewaretoken': gvar['csrf']}}
    else:
        _function = py_requests.get
        _form_data = {}

    if 'server-grid-cert' in gvar['user_settings'] and \
        os.path.exists(gvar['user_settings']['server-grid-cert']) and \
        'server-grid-key' in gvar['user_settings'] and \
        os.path.exists(gvar['user_settings']['server-grid-key']):
        _r = _function(
            '%s%s' % (gvar['user_settings']['server-address'], request),
            headers={'Accept': 'application/json', 'Referer': gvar['user_settings']['server-address']},
            cert=(gvar['user_settings']['server-grid-cert'], gvar['user_settings']['server-grid-key']),
            data=_form_data,
            cookies=gvar['cookies']
            )

    elif 'server-user' in gvar['user_settings']:
        if 'server-password' not in gvar['user_settings'] or gvar['user_settings']['server-password'] == '?':
            gvar['user_settings']['server-password'] = getpass('Enter your %s password for server "%s": ' % (gvar['command_name'], gvar['server']))
        _r = _function(
            '%s%s' % (gvar['user_settings']['server-address'], request),
            headers={'Accept': 'application/json', 'Referer': gvar['user_settings']['server-address']},
            auth=(gvar['user_settings']['server-user'], gvar['user_settings']['server-password']),
            data=_form_data,
            cookies=gvar['cookies'] 
            )

    else:
        print(
            '***\n' \
            '*** Please identify the URL (-sa | --server-address) of the server with which you wish to communicate. Servers\n' \
            '*** require either certificate (-sC | --server-grid-cert, -sK | --server-grid-key) or username/password (-su |\n' \
            '*** --server-user, -spw | --server-password) authentication. These options can be saved for multiple servers\n' \
            '*** by name (there is always a "default" server) using the following command:\n' \
            '***\n' \
            '***     %s defaults set -s <sever_name> -sa <server_address> ...\n' \
            '***\n' \
            '*** Subsequently, commands will be directed to the last server selected via the (-s | --server)\n' \
            '*** argument.\n' \
            '***' % gvar['command_name']
            )
        exit(1)

    try:
        response = _r.json()
    except:
        if _r.status_code:
            response = {'response_code': 2, 'message': 'server "%s", HTTP response code %s, %s.' % (gvar['server'], _r.status_code, py_requests.status_codes._codes[_r.status_code][0])}
        else:
            response = {'response_code': 2, 'message': 'server "%s", internal server error.' % gvar['server']}

    if gvar['user_settings']['expose-API']:
        print("Expose API requested:\n" \
            "  py_requests.%s(\n" \
            "    %s%s,\n" \
            "    headers={'Accept': 'application/json', 'Referer': '%s'}," % (
                _function.__name__,
                gvar['user_settings']['server-address'],
                request,
                gvar['user_settings']['server-address'],
                )
            )

        if 'server-grid-cert' in gvar['user_settings'] and \
            os.path.exists(gvar['user_settings']['server-grid-cert']) and \
            'server-grid-key' in gvar['user_settings'] and \
            os.path.exists(gvar['user_settings']['server-grid-key']):
            print("    cert=('%s', '%s')," % (gvar['user_settings']['server-grid-cert'], gvar['user_settings']['server-grid-key']))
        else:
            print("    auth=('%s', <password>)," % gvar['user_settings']['server-user'])

        print("    data=%s,\n" \
            "    cookies='%s'\n" \
            "    )\n\n" \
            "  Response: {" % (
                _form_data,
                gvar['cookies']
                )
            )

        for key in response:
            if key == 'fields':
                print("    %s: {" % key)
                for subkey in response(key):
                    print("        %s: %s" % (subkey, response[key][subkey]))
                print("        }")
            else:
                print("    %s: %s" % (key, response[key]))
        print("    }\n")

    if response['response_code'] != 0:
        print('Error: %s' % response['message'])
        exit(1)

    if 'Set-Cookie' in _r.headers:
        new_csrf = _r.headers['Set-Cookie'].translate(EXTRACT_CSRF).split()[1]
        if new_csrf[1]:
            gvar['cookies'] = _r.cookies
            gvar['csrf'] = _r.headers['Set-Cookie'].translate(EXTRACT_CSRF).split()[1]

    if 'active_group' in response:
        gvar['active_group'] = response['active_group']

    if 'super_user' in response:
        gvar['super_user'] = response['super_user']

    return response

def show_active_user_groups(gvar, response):
    """
    Print the server response header.
    """

    if not gvar['user_settings']['view-columns']:
        print('Server: %s, Active User: %s, Active Group: %s, User\'s Groups: %s' % (gvar['server'], response['active_user'], response['active_group'], response['user_groups']))

def show_table(gvar, queryset, columns, allow_null=True, title=None):
    """
    Print a table from a SQLAlchemy query set.
    """

    from subprocess import Popen, PIPE
    import json
    import os
    import yaml

    # Organize user views.
    if 'views' not in gvar:
        if os.path.exists('%s/.csv2/views.yaml' % gvar['home_dir']):
            fd = open('%s/.csv2/views.yaml' % gvar['home_dir'])
            gvar['views'] = yaml.load(fd.read())
            fd.close()
        else:
            gvar['views'] = {}

        if 'view' in gvar['user_settings']:
            if gvar['object'] not in gvar['views']:
                gvar['views'][gvar['object']] = {}

            gvar['views'][gvar['object']][gvar['action']] = []

            w1 = gvar['user_settings']['view'].split('/')
            for w2 in w1:
                gvar['views'][gvar['object']][gvar['action']].append(w2.split(','))
                if gvar['views'][gvar['object']][gvar['action']][-1] == ['']:
                    gvar['views'][gvar['object']][gvar['action']][-1] = None

            fd = open('%s/.csv2/views.yaml' % gvar['home_dir'], 'w')
            fd.write(yaml.dump(gvar['views']))
            fd.close()

    if not gvar['user_settings']['no-view'] and gvar['object'] in gvar['views'] and gvar['action'] in gvar['views'][gvar['object']]:
        Selections = gvar['views'][gvar['object']][gvar['action']]
    else:
        Selections = None

    # Organize table definition.
    Rotated_Table = {
        'headers': {'key': 'Key', 'value': 'Value'},
        'lengths': {'key': 3, 'value': 5},
        'xref': {'key': 0, 'value': 1}
        }

    Table = {
        'columns_common': [],
        'columns_segment': [],
        'headers': {},
        'keys': {},
        'lengths': {},
        'super_headers': {},
        'xref': {}
        }

    if gvar['user_settings']['rotate']:
        Table['max_key_length'] = 3
        Table['max_value_length'] = 5

    elif 'display_size' not in gvar:
        p = Popen(['stty', 'size'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            ix = stdout.split()
            gvar['display_size'] = [int(ix[0]), int(ix[1])]
        else:
            gvar['display_size'] = [24, 80]

    for column_def in columns:
        w1 = column_def.split(',')
        w2 = w1[0].split('/')
        column = w2[0]

        # Set default value for header.
        if len(w2) < 2:
            w2.append(column)
        elif w2[1] == '':
           w2[1] = column

        # Set default value for super_header.
        if len(w2) < 3:
            w2.append('')

        if len(w1) > 1 and w1[1] == 'k':
            Table['keys'][column] = True
        else:
            if not gvar['user_settings']['view-columns']:
                if gvar['command_args']['only-keys']:
                    continue

                if Selections is not None and len(Selections) > gvar['tables_shown'] and Selections[gvar['tables_shown']] and len(Selections[gvar['tables_shown']]) > 0 and column not in Selections[gvar['tables_shown']]:
                    continue

            Table['keys'][column] = False

        Table['headers'][column] = w2[1]
        Table['super_headers'][column] = w2[2]

        if Table['keys'][column]:
           Table['columns_common'].append(column)
           if len(Table['super_headers'][column]) > len(Table['headers'][column]):
               Table['lengths'][column] = len(Table['super_headers'][column])
           else:
               Table['lengths'][column] = len(Table['headers'][column])

        else:
           Table['columns_segment'].append(column)
           if len(Table['super_headers'][column]) > len(Table['headers'][column]):
               Table['lengths'][column] = len(Table['super_headers'][column])
           else:
               Table['lengths'][column] = len(Table['headers'][column])

    for ix in range(len(Table['columns_common'] + Table['columns_segment'])):
        Table['xref'][(Table['columns_common'] + Table['columns_segment'])[ix]] = ix

    # If requested, print column names and return.
    if gvar['user_settings']['view-columns']:
        columns = [ [], [] ]
        for column in Table['columns_common'] + Table['columns_segment']:
            if Table['keys'][column]:
                columns[0].append(column)
            else:
                columns[1].append(column)
        print('%s %s, table #%s columns: keys=%s, columns=%s' % (gvar['object'], gvar['action'], gvar['tables_shown']+1, ','.join(Table['columns_common']), ','.join(Table['columns_segment'])))
        gvar['tables_shown'] += 1
        return

    # Normalize the queryset.
    if isinstance(queryset, str):
        _qs = json.loads(queryset)
    else:
        _qs = queryset

    # extract columns.
    lists = []
    for row in _qs:
        _row = []
        for column in Table['columns_common'] + Table['columns_segment']:
            if column in row:
              _value = row[column]
            elif 'fields' in row and column in row['fields']:
              _value = row['fields'][column]
            else:
              _value = '-'

            if isinstance(_value, bool):
               _len = 5
            elif isinstance(_value, int):
               _len = 11
            elif isinstance(_value, float):
               _len = 21
            elif _value is None:
               _len = 4
            else:
               _len = len(_value)

            if gvar['user_settings']['rotate']:
                if Table['super_headers'][column] == '':
                    lists.append([Table['headers'][column], _value])
                else:
                    lists.append(['%s-%s' % (Table['super_headers'][column], Table['headers'][column]), _value])

                if Rotated_Table['lengths']['key'] < len(lists[-1][0]):
                    Rotated_Table['lengths']['key'] = len(lists[-1][0])

                if Rotated_Table['lengths']['value'] < _len:
                    Rotated_Table['lengths']['value'] = _len

            elif Table['keys'][column]:
                _row.append(_value)
                if Table['lengths'][column] < _len:
                    Table['lengths'][column] = _len

            else:
                _row.append(_value)
                if Table['lengths'][column] < _len:
                    Table['lengths'][column] = _len

        if gvar['user_settings']['rotate']:
            lists.append(['', ''])
        else:
            lists.append(_row)

    if gvar['user_settings']['rotate']:
        segments = [ {'SH': False, 'table': Rotated_Table, 'columns': ['key', 'value'], 'headers': ['Key', 'Value']} ]

    else:
        segments = [ {'SH': False, 'table': Table, 'columns': [], 'super_headers': [],  'super_header_lengths': [], 'headers': [], 'length': 1} ]

        if len(Table['columns_segment']) > 0:
            for column in Table['columns_segment']:
                # If the next column causes segment to exceed the display width, start a new segment.
                if segments[-1]['length'] + 3 + Table['lengths'][column] > gvar['display_size'][1] - 5:
                    _show_table_set_segment(segments[-1], None)
                    segments.append({'SH': False, 'table': Table, 'columns': [], 'super_headers': [],  'super_header_lengths': [], 'headers': [], 'length': 1})

                # If starting a new segment, add all the common (key) columns.
                if segments[-1]['length'] == 1:
                    for common_column in Table['columns_common']:
                        _show_table_set_segment(segments[-1], common_column)
                    _show_table_set_segment(segments[-1], None)

                # Process the current (segment) column.
                _show_table_set_segment(segments[-1], column)
            _show_table_set_segment(segments[-1], None)

        else:
            # The table consists of only common (key) columns; add them all.
            for common_column in Table['columns_common']:
                _show_table_set_segment(segments[-1], common_column)
            _show_table_set_segment(segments[-1], None)

    for ix in range(len(segments)):
        column_underscore = []
        for column in segments[ix]['columns']:
            column_underscore.append('-' * (segments[ix]['table']['lengths'][column] + 2))
        ruler = '+%s+' % '+'.join(column_underscore)

        if title:
            if len(segments) > 1:
                print('\n%s (%s/%s)' % (title, ix+1, len(segments)))
            else:
                print('\n%s' % title)
        else:
            if len(segments) > 1:
                print('\n (%s/%s)' % (ix+1, len(segments)))
            else:
                print('\n')

        print(ruler)
        if segments[ix]['SH']:
            print('+ %s +' % ' | '.join(segments[ix]['super_headers']))
            print('+ %s +' % ' | '.join(segments[ix]['headers']))
        else:
            print('+ %s +' % ' | '.join(_show_table_pad(segments[ix]['columns'], segments[ix]['table']['headers'], segments[ix]['table']['lengths'])))
        print(ruler)

        for row in lists:
            if gvar['user_settings']['rotate'] and not allow_null and row[1] == '-':
                continue

            print('| %s |' % ' | '.join(_show_table_pad(segments[ix]['columns'], row, segments[ix]['table']['lengths'], values_xref=segments[ix]['table']['xref'])))

        print(ruler)

    print('Rows: %s' % len(_qs))
    gvar['tables_shown'] += 1

def _show_table_pad(columns, values, lengths, justify='left', values_xref=None):
    """
    Pad column values with blanks. The parameters have the following format:
       o columns is a list.
       o values is either a list or a dictionary.
       o lengths is a dictionary.
    """

    padded_columns = []

    for ix in range(len(columns)):
        if isinstance(values, list):
            if values_xref is None:
                value = str(values[ix])
            else:
                value = str(values[values_xref[columns[ix]]])
        else:
            value = str(values[columns[ix]])

        value_len = len(value)

        if justify == 'left':
            padded_columns.append('%s%s' % (value, ' ' * (lengths[columns[ix]] - value_len)))
        elif justify == 'right':
            padded_columns.append('%s%s' % (' ' * (lengths[columns[ix]] - value_len), value))
        else:
            len_lp = int((lengths[columns[ix]] - value_len)/2)
            len_rp = lengths[columns[ix]] - len_lp - value_len
            padded_columns.append('%s%s%s' % (' ' * len_lp, value, ' ' * len_rp))

    return padded_columns

def _show_table_set_segment(segment, column):
    """
    Determine if headers are single column or multi-column, setting them appropriately
    """

    # If processing a flush request (no column), finalize segment headers and return.
    if column is None:
        _show_table_set_segment_super_headers(segment)

    # Process new column for segment.
    else:
        # Process segments with super_headers.
        if segment['SH']:
            # Process super_header change.
            if segment['SH_low_ix'] and segment['table']['super_headers'][column] != segment['table']['super_headers'][segment['columns'][segment['SH_low_ix']]]:
                _show_table_set_segment_super_headers(segment)

                column_ix =_show_table_set_segment_insert_new_column(segment, column)

                if segment['table']['super_headers'][column] == '':
                    segment['SH_low_ix'] = None
                    segment['SH_hi_ix'] = None
                else:
                    segment['SH_low_ix'] = column_ix

                if segment['table']['super_headers'][column] == '':
                    segment['super_headers'].append(_show_table_pad([column], [''], segment['table']['lengths'], justify='centre')[0])
                    segment['headers'].append(_show_table_pad([column], [segment['table']['headers'][column]], segment['table']['lengths'], justify='centre')[0])
                else:
                    segment['SH_hi_ix'] = column_ix

            else:
                column_ix =_show_table_set_segment_insert_new_column(segment, column)

                if segment['table']['super_headers'][column] == '':
                    segment['super_headers'].append(_show_table_pad([column], [''], segment['table']['lengths'], justify='centre')[0])
                    segment['headers'].append(_show_table_pad([column], [segment['table']['headers'][column]], segment['table']['lengths'], justify='centre')[0])
                else:
                    if not segment['SH_low_ix']:
                        segment['SH_low_ix'] = column_ix

                    segment['SH_hi_ix'] = column_ix

        # Process segments without super_headers (yet).
        else:
            column_ix =_show_table_set_segment_insert_new_column(segment, column)

            if segment['table']['super_headers'][column] == '':
                segment['super_headers'].append(_show_table_pad([column], [''], segment['table']['lengths'], justify='centre')[0])
                segment['headers'].append(_show_table_pad([column], [segment['table']['headers'][column]], segment['table']['lengths'], justify='centre')[0])
            else:
                segment['SH'] = True
                segment['SH_low_ix'] = column_ix
                segment['SH_hi_ix'] = column_ix

def _show_table_set_segment_insert_new_column(segment, column):
    """
    Insert a new column into the current segment.
    """

    segment['columns'].append(column)
    segment['length'] += 3 + segment['table']['lengths'][column]
    return len(segment['columns']) - 1

def _show_table_set_segment_super_headers(segment):
    """
    Set the super_headers for a segment.
    """

    if segment['SH'] and segment['SH_low_ix']:
        column = segment['columns'][segment['SH_low_ix']]
        segment['headers'].append('   '.join(_show_table_pad(segment['columns'][segment['SH_low_ix']:], segment['table']['headers'], segment['table']['lengths'], justify='centre')))
        segment['super_header_lengths'].append(len(segment['headers'][-1]))
        segment['super_headers'].append(_show_table_pad([column], segment['table']['super_headers'], {column: segment['super_header_lengths'][-1]}, justify='centre')[0])


def verify_yaml_file(file_path):
    # Read the entire file.
    fd = open(file_path)
    file_string = fd.read()
    fd.close()

    # Verify yaml files.
    if (len(file_path) > 4 and file_path[-4:] == '.yml') or \
        (len(file_path) > 5 and file_path[-5:] == '.yaml') or \
        (len(file_path) > 7 and file_path[-7:] == '.yml.j2') or \
        (len(file_path) > 8 and file_path[-8:] == '.yaml.j2'):
        result = _yaml_load_and_verify(file_string)
        if not result[0]:
            print('Error: Invalid yaml file "%s": %s' % (result[1], result[2]))
            exit(1)

    return {
        'metadata': file_string,
        }

def _yaml_load_and_verify(yaml_string):
    import yaml

    try:
        _yaml = yaml.load(yaml_string)
        return [1, _yaml]
    except yaml.scanner.ScannerError as ex:
        return [0, 'scanner error', ex]
    except yaml.parser.ParserError as ex:
        return [0, 'parser error', ex]

