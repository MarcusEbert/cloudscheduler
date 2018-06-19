from unit_test_common import execute_csv2_request, initialize_csv2_request, ut_id
import sys

def main(gvar):
    if not gvar:
        gvar = {}
        if len(sys.argv) > 1:
            initialize_csv2_request(gvar, sys.argv[0], selections=sys.argv[1])
        else:
            initialize_csv2_request(gvar, sys.argv[0])
    
    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 401, unauthorized.',
        '/cloud/list/',
        server_user='invalid-unit-test', server_pw='Abc123'
    )

    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu1')),
        '/cloud/list/',
        server_user=ut_id(gvar, 'ctu1'), server_pw='Abc123'
    )

    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu2')),
        '/cloud/list/',
        server_user=ut_id(gvar, 'ctu2'), server_pw='Abc123'
    )

    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "invalid-unit-test".',
        '/cloud/list/', form_data={'group': 'invalid-unit-test'},
        server_user=ut_id(gvar, 'ctu3'), server_pw='Abc123'
    )

    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "jodiew-ctg2".',
        '/cloud/list/', form_data={'group': ut_id(gvar, 'ctg2')},
        server_user=ut_id(gvar, 'ctu3'), server_pw='Abc123'
    )

    execute_csv2_request(
        gvar, 0, None, None,
        '/cloud/list/', form_data={'group': ut_id(gvar, 'ctg1')},
        list='cloud_list', filter={'cloud_name': ut_id(gvar, 'ctc2')},
        values={'cloud_name': ut_id(gvar, 'ctc2'), 'group_name': ut_id(gvar, 'ctg1')},
        server_user=ut_id(gvar, 'ctu3'), server_pw='Abc123'
    )

    execute_csv2_request(
        gvar, 0, None, None,
        '/cloud/list/', form_data={'group': ut_id(gvar, 'ctg1')},
        list='cloud_list', filter={'cloud_name': ut_id(gvar, 'ctc2')},
        values={'cloud_name': ut_id(gvar, 'ctc2'), 'group_name': ut_id(gvar, 'ctg1')},
        server_user=ut_id(gvar, 'ctu3'), server_pw='Abc123', html=True
    )

if __name__ == "__main__":
    main(None)