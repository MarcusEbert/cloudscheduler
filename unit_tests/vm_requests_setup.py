from unit_test_common import execute_csv2_request, initialize_csv2_request, ut_id, generate_secret
from sys import argv
import vm_requests_cleanup

def main(gvar, user_secret):
    if not gvar:
        gvar = {}
        if len(argv) > 1:
            initialize_csv2_request(gvar, argv[0], selections=argv[1])
        else:
            initialize_csv2_request(gvar, argv[0])
    if not user_secret:
        user_secret = generate_secret()
    
    vm_requests_cleanup.main(gvar)

    # unprivileged user in no groups
    execute_csv2_request(
        gvar, 0, None, 'user "{}" successfully added.'.format(ut_id(gvar, 'vtu1')),
        '/user/add/', form_data={
            'username': ut_id(gvar, 'vtu1'),
            'password1': user_secret,
            'password2': user_secret,
            'cert_cn': ut_id(gvar, 'vm test user one')
        }
    )
    
    # privileged user in no groups
    execute_csv2_request(
        gvar, 0, None, 'user "{}" successfully added.'.format(ut_id(gvar, 'vtu2')),
        '/user/add/', form_data={
            'username': ut_id(gvar, 'vtu2'),
            'password1': user_secret,
            'password2': user_secret,
            'cert_cn': ut_id(gvar, 'vm test user two'),
            'is_superuser': 1
        }
    )

    # group with users
    execute_csv2_request(
        gvar, 0, None, 'group "{}" successfully added.'.format(ut_id(gvar, 'vtg1')),
        '/group/add/', form_data={
            'group_name': ut_id(gvar, 'vtg1'),
            'htcondor_fqdn': 'unit-test-group-one.ca'
        }
    )

    # group without users
    execute_csv2_request(
        gvar, 0, None, 'group "{}" successfully added.'.format(ut_id(gvar, 'vtg2')),
        '/group/add/', form_data={
            'group_name': ut_id(gvar, 'vtg2'),
            'htcondor_fqdn': 'unit-test-group-two.ca'
        }
    )

    # unprivileged user in vtg1
    execute_csv2_request(
        gvar, 0, None, 'user "{}" successfully added.'.format(ut_id(gvar, 'vtu3')),
        '/user/add/', form_data={
            'username': ut_id(gvar, 'vtu3'),
            'password1': user_secret,
            'password2': user_secret,
            'cert_cn': ut_id(gvar, 'vm test user three'),
            'group_name.1': ut_id(gvar, 'vtg1')
        }
    )
    
    # privileged user in vtg1
    execute_csv2_request(
        gvar, 0, None, 'user "{}" successfully added.'.format(ut_id(gvar, 'vtu4')),
        '/user/add/', form_data={
            'username': ut_id(gvar, 'vtu4'),
            'password1': user_secret,
            'password2': user_secret,
            'cert_cn': ut_id(gvar, 'vm test user four'),
            'is_superuser': 1,
            'group_name.1': ut_id(gvar, 'vtg1')
        }
    )

if __name__ == "__main__":
    main(None)
