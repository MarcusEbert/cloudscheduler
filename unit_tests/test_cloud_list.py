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
    #1 
    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 401, unauthorized.',
        '/cloud/list/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user='invalid-unit-test', server_pw=user_secret
    )
    #2
    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu1')),
        '/cloud/list/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu1'), server_pw=user_secret
    )
    #3
    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu2')),
        '/cloud/list/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu2'), server_pw=user_secret
    )
    #4
    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "invalid-unit-test".',
        '/cloud/list/?invalid-unit-test',
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )
    #5
    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "{}".'.format(ut_id(gvar, 'ctg2')),
        '/cloud/list/?{}'.format(ut_id(gvar, 'ctg2')),
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )
    #6
    execute_csv2_request(
        gvar, 0, None, None,
        '/cloud/list/?{}'.format(ut_id(gvar, 'ctg1')),
        list='cloud_list', filter={'cloud_name': ut_id(gvar, 'ctc2')},
        values={'cloud_name': ut_id(gvar, 'ctc2'), 'group_name': ut_id(gvar, 'ctg1')},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )
    #7
    execute_csv2_request(
        gvar, 1, 'CV', 'request contained a bad parameter "invalid-unit-test".',
        '/cloud/list/', group=(ut_id(gvar, 'ctg1')),
        form_data={'invalid-unit-test': 'invalid-unit-test'},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )
    #8
    execute_csv2_request(
        gvar, 0, None, None,
        '/cloud/list/?"{}"'.format(ut_id(gvar, 'ctg1')),
        list='cloud_list',
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret, html=True
    )

if __name__ == "__main__":
    main(None)
