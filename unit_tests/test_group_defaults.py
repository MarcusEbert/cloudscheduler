from unit_test_common import execute_csv2_request, initialize_csv2_request, ut_id
from sys import argv

# lno: GV - error code identifier.

def main(gvar, user_secret):
    if not gvar:
        gvar = {}
        if len(argv) > 1:
            initialize_csv2_request(gvar, argv[0], selections=argv[1])
        else:
            initialize_csv2_request(gvar, argv[0])

#   gvar['user_settings']['expose-API'] = True

    # 1
    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 401, unauthorized.',
        '/group/defaults/?"{}"'.format(ut_id(gvar, 'gtg4')),
        server_user=ut_id(gvar, 'invalid-unit-test'), server_pw=user_secret
    )

    # 2
    execute_csv2_request(
        gvar, 1, 'GV', 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'gtu1')),
        '/group/defaults/?{}'.format(ut_id(gvar, 'gtg4')),
        server_user=ut_id(gvar, 'gtu1'), server_pw=user_secret
    )

    # 3
    execute_csv2_request(
        gvar, 0, None, None,
        '/group/defaults/?"{}"'.format(ut_id(gvar, 'gtg4')),
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 4
    execute_csv2_request(
        gvar, 1, 'GV', 'cannot switch to invalid group "invalid-unit-test".',
        '/group/defaults/?invalid-unit-test',
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 5
    execute_csv2_request(
        gvar, 1, 'GV', 'cannot switch to invalid group "{}".'.format(ut_id(gvar, 'gtg7')),
        '/group/defaults/?{}'.format(ut_id(gvar, 'gtg7')),
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 6
    execute_csv2_request(
        gvar, 1, 'GV', 'request contained a bad parameter "invalid-unit-test".',
        '/group/defaults/', group=(ut_id(gvar, 'gtg4'))
, form_data={'invalid-unit-test': 'invalid-unit-test'},
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 7
    execute_csv2_request(
        gvar, 1, 'GV', 'default update/list value specified for "job_cpus" must be an integer value.',
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'job_cpus': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 8
    execute_csv2_request(
        gvar, 1, 'GV', 'default update/list value specified for "job_ram" must be an integer value.',
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'job_ram': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 9
    execute_csv2_request(
        gvar, 1, 'GV', 'default update/list value specified for "job_disk" must be an integer value.',
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'job_disk': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 10
    execute_csv2_request(
        gvar, 1, 'GV', 'request contained a rejected/bad parameter "job_scratch".',
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'job_scratch': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 11
    execute_csv2_request(
        gvar, 1, 'GV', 'default update/list value specified for "job_swap" must be an integer value.',
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'job_swap': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 12
    execute_csv2_request(
        gvar, 1, 'GV', 'default update/list value specified for "vm_keep_alive" must be an integer value.',
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'vm_keep_alive': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 13
    execute_csv2_request(
        gvar, 0, None, '"{}" successfully updated.'.format(ut_id(gvar, 'gtg4')),
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'job_cpus': 1,
            'job_ram': 1,
            'job_disk': 1,
            'job_swap': 1,
            'vm_keep_alive': 1,
            'vm_flavor': '',
            'vm_image': '',
            'vm_keyname': '',
            'vm_network': '',
        },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 14
    execute_csv2_request(
        gvar, 1, 'GV', 'group defaults update specified item does not exist: vm_image=invalid-unit-test, group_name={0}.'.format(ut_id(gvar, 'gtg4')),
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'vm_image': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 15
    execute_csv2_request(
        gvar, 1, 'GV', 'group defaults update specified item does not exist: vm_flavor=invalid-unit-test, group_name={0}.'.format(ut_id(gvar, 'gtg4')),
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'vm_flavor': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 16
    execute_csv2_request(
        gvar, 1, 'GV', 'group defaults update specified item does not exist: vm_network=invalid-unit-test, group_name={0}.'.format(ut_id(gvar, 'gtg4')),
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'vm_network': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

    # 17
    execute_csv2_request(
        gvar, 1, 'GV', 'group defaults update specified item does not exist: vm_keyname=invalid-unit-test, group_name={0}.'.format(ut_id(gvar, 'gtg4')),
        '/group/defaults/', group=ut_id(gvar, 'gtg4'), form_data={
            'vm_keyname': 'invalid-unit-test'
            },
        server_user=ut_id(gvar, 'gtu3'), server_pw=user_secret
    )

if __name__ == "__main__":
    main(None)
