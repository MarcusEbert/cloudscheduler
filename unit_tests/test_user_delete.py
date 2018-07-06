from unit_test_common import execute_csv2_request, initialize_csv2_request, ut_id
import sys

# lno: UV - error code identifier.

def main(gvar, user_secret):
    if not gvar:
        gvar = {}
        if len(sys.argv) > 1:
            initialize_csv2_request(gvar, sys.argv[0], selections=sys.argv[1])
        else:
            initialize_csv2_request(gvar, sys.argv[0])
    
    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 401, unauthorized.',
        '/user/delete/',
        server_user='invalid-unit-test', server_pw=user_secret
    )

    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 403, forbidden.',
        '/user/delete/',
        server_user=ut_id(gvar, 'utu1'), server_pw=user_secret
    )

    execute_csv2_request(
        gvar, 1, 'UV12', 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'utu2')),
        '/user/delete/',
        server_user=ut_id(gvar, 'utu2'), server_pw=user_secret
    )

    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 403, forbidden.',
        '/user/delete/',
        server_user=ut_id(gvar, 'utu3'), server_pw=user_secret
    )

    execute_csv2_request(
        gvar, 1, 'UV11', 'invalid method "GET" specified.',
        '/user/delete/'
    )

    execute_csv2_request(
        gvar, 1, 'UV07', 'cannot switch to invalid group "invalid-unit-test".',
        '/user/delete/', form_data={'group': 'invalid-unit-test'}
    )

    execute_csv2_request(
        gvar, 1, 'UV07', 'cannot switch to invalid group "{}".'.format(ut_id(gvar, 'utg2')),
        '/user/delete/', form_data={'group': ut_id(gvar, 'utg2')}
    )

    execute_csv2_request(
        gvar, 1, 'UV08', 'request contained superfluous parameter "invalid-unit-test".',
        '/user/delete/', form_data={'invalid-unit-test': 'invalid-unit-test'}
    )

    execute_csv2_request(
        gvar, 1, 'UV08', 'value specified for "username" must be all lower case.',
        '/user/delete/', form_data={'username': 'Invalid-unit-test'}
    )

    execute_csv2_request(
        gvar, 1, 'UV08', 'request contained superfluous parameter "password".',
        '/user/delete/', form_data={'password': 'invalid-unit-test'}
    )

    execute_csv2_request(
        gvar, 1, 'UV08', 'request did not contain mandatory parameter "username".',
        '/user/delete/', form_data={'group': ut_id(gvar, 'utg1')},
        server_user=ut_id(gvar, 'utu4'), server_pw=user_secret
    )

    execute_csv2_request(
        gvar, 1, 'UV10', 'the request did not match any rows.',
        '/user/delete/', form_data={'username': 'invalid-unit-test'}
    )

    execute_csv2_request(
        gvar, 0, None, 'user "{}" successfully deleted.'.format(ut_id(gvar, 'utu5')),
        '/user/delete/', form_data={'username': ut_id(gvar, 'utu5')}
    )

if __name__ == "__main__":
    main(None)