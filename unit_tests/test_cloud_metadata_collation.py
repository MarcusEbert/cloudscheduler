from unit_test_common import execute_csv2_request, initialize_csv2_request, ut_id
from sys import argv

# lno: CV - error code identifier.

def main(gvar, user_secret):
    if not gvar:
        gvar = {}
        if len(argv) > 1:
            initialize_csv2_request(gvar, argv[0], selections=argv[1])
        else:
            initialize_csv2_request(gvar, argv[0])
    
    # 01
    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 401, unauthorized.',
        '/cloud/metadata-collation/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user='invalid-unit-test', server_pw=user_secret
    )

    # 02
    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu1')),
        '/cloud/metadata-collation/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu1'), server_pw=user_secret
    )

    # 03
    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu2')),
        '/cloud/metadata-collation/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu2'), server_pw=user_secret
    )

    # 04
    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "invalid-unit-test".',
        '/cloud/metadata-collation/?invalid-unit-test',
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 05
    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "{}".'.format(ut_id(gvar, 'ctg2')),
        '/cloud/metadata-collation/?{}'.format(ut_id(gvar, 'ctg2')),
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 06
    execute_csv2_request(
        gvar, 1, 'CV', 'request contained a bad parameter "invalid-unit-test".',
        '/cloud/metadata-collation/', group=(ut_id(gvar, 'ctg1')),
        form_data={'invalid-unit-test': 'invalid-unit-test'},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 07
    execute_csv2_request(
        gvar, 0, None, None,
        '/cloud/metadata-collation/?{}'.format(ut_id(gvar, 'ctg1')),
        list='cloud_metadata_list', filter={'metadata_name': ut_id(gvar, 'cty1'), 'cloud_name': ut_id(gvar, 'ctc2'), 'group_name': ut_id(gvar, 'ctg1')},
        values={'type': 'group'},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 08
    execute_csv2_request(
        gvar, 0, None, None,
        '/cloud/metadata-collation/?{}'.format(ut_id(gvar, 'ctg1')),
        list='cloud_metadata_list', filter={'metadata_name': ut_id(gvar, 'cty1'), 'cloud_name': ut_id(gvar, 'ctc3'), 'group_name': ut_id(gvar, 'ctg1')},
        values={'type': 'group'},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 09
    execute_csv2_request(
        gvar, 0, None, None,
        '/cloud/metadata-collation/?{}'.format(ut_id(gvar, 'ctg1')),
        list='cloud_metadata_list', filter={'metadata_name': ut_id(gvar, 'cty1'), 'cloud_name': ut_id(gvar, 'ctc2'), 'group_name': ut_id(gvar, 'ctg1')},
        values={'type': 'group'},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

if __name__ == "__main__":
    main(None)
