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

    # 1
    execute_csv2_request(
        gvar, 2, None, 'HTTP response code 401, unauthorized.',
        '/cloud/metadata-update/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user='invalid-unit-test', server_pw=user_secret
    )

    # 2
    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu1')),
        '/cloud/metadata-update/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu1'), server_pw=user_secret
    )

    # 3
    execute_csv2_request(
        gvar, 1, None, 'user "{}" is not a member of any group.'.format(ut_id(gvar, 'ctu2')),
        '/cloud/metadata-update/?"{}"'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu2'), server_pw=user_secret
    )

    # 4
    execute_csv2_request(
        gvar, 1, 'CV', 'cloud metadata-update request did not contain mandatory parameters "cloud_name" and "metadata_name".',
        '/cloud/metadata-update/?{}'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 5
    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "invalid-unit-test".',
        '/cloud/metadata-update/?invalid-unit-test',
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 6
    execute_csv2_request(
        gvar, 1, None, 'cannot switch to invalid group "{}".'.format(ut_id(gvar, 'ctg2')),
        '/cloud/metadata-update/?{}'.format(ut_id(gvar, 'ctg2')),
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 7
    execute_csv2_request(
        gvar, 1, 'CV', 'cloud metadata-update request did not contain mandatory parameters "cloud_name" and "metadata_name".',
        '/cloud/metadata-update/?{}'.format(ut_id(gvar, 'ctg1')),
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 8
    execute_csv2_request(
        gvar, 1, 'CV', 'cloud metadata-update request did not contain mandatory parameter "cloud_name".',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')), 
        form_data={'metadata_name': 'invalid-unit-test'},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 9
    execute_csv2_request(
        gvar, 1, 'CV', 'cloud metadata-update request did not contain mandatory parameter "metadata_name".',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={'cloud_name': 'invalid-unit-test'},
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 10
    execute_csv2_request(
        gvar, 1, 'CV', 'cloud metadata-update request contained a bad parameter "invalid-unit-test".',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'invalid-unit-test',
            'metadata_name': 'invalid-unit-test',
            'invalid-unit-test': 'invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 11
    execute_csv2_request(
        gvar, 1, 'CV', 'value specified for "cloud_name" must be all lower case, numeric digits, and dashes but cannot start or end with dashes.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'Invalid-unit-test',
            'metadata_name': 'invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 12
    execute_csv2_request(
        gvar, 1, 'CV', 'value specified for "cloud_name" must be all lower case, numeric digits, and dashes but cannot start or end with dashes.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'invalid-unit-test-',
            'metadata_name': 'invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 13
    execute_csv2_request(
        gvar, 1, 'CV', 'value specified for "cloud_name" must be all lower case, numeric digits, and dashes but cannot start or end with dashes.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'invalid-unit-test!',
            'metadata_name': 'invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 14
    execute_csv2_request(
        gvar, 1, 'CV', 'value specified for "metadata_name" must be all lower case.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'invalid-unit-test',
            'metadata_name': 'Invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 15
    execute_csv2_request(
        gvar, 1, 'CV', 'boolean value specified for "enabled" must be one of the following: true, false, yes, no, 1, or 0.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'invalid-unit-test',
            'metadata_name': 'invalid-unit-test',
            'enabled': 'invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 16
    execute_csv2_request(
        gvar, 1, 'CV', 'value specified for "mime_type" must be one of the following options: [\'cloud-config\', \'ucernvm-config\'].',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'invalid-unit-test',
            'metadata_name': 'invalid-unit-test',
            'mime_type': 'invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 17
    execute_csv2_request(
        gvar, 1, 'CV', 'the request did not match any rows.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': 'invalid-unit-test',
            'metadata_name': 'invalid-unit-test',
            'priority': 1
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 18
    execute_csv2_request(
        gvar, 1, 'CV', 'the request did not match any rows.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': 'invalid-unit-test',
            'priority': 1
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 19
    execute_csv2_request(
        gvar, 1, 'CV', 'You have an error in your SQL syntax',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3')
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 20
    execute_csv2_request(
        gvar, 1, 'CV', 'yaml value specified for "metadata (metadata_name)" is invalid - scanner error',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3.yaml'),
            'metadata': 'foo: this is invalid: yaml'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 21
    execute_csv2_request(
        gvar, 1, 'CV', 'value specified for "priority" must be an integer value.',
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3.yaml'),
            'priority': 'invalid-unit-test'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 22
    execute_csv2_request(
        gvar, 0, None, 'cloud metadata file "{}::{}::{}" successfully  updated.'.format(ut_id(gvar, 'ctg1'), ut_id(gvar, 'ctc3'), ut_id(gvar, 'cty3')),
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3'),
            'metadata': 'foo: this is invalid: yaml'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 23
    execute_csv2_request(
        gvar, 0, None, 'cloud metadata file "{}::{}::{}" successfully  updated.'.format(ut_id(gvar, 'ctg1'), ut_id(gvar, 'ctc3'), ut_id(gvar, 'cty3.yaml')),
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3.yaml'),
            'metadata': '- foo: this is valid yaml'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 24
    execute_csv2_request(
        gvar, 0, None, 'cloud metadata file "{}::{}::{}" successfully  updated.'.format(ut_id(gvar, 'ctg1'), ut_id(gvar, 'ctc3'), ut_id(gvar, 'cty3.yaml')),
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3.yaml'),
            'priority': 1
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 25
    execute_csv2_request(
        gvar, 0, None, 'cloud metadata file "{}::{}::{}" successfully  updated.'.format(ut_id(gvar, 'ctg1'), ut_id(gvar, 'ctc3'), ut_id(gvar, 'cty3.yaml')),
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3.yaml'),
            'mime_type': 'ucernvm-config'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

    # 26
    execute_csv2_request(
        gvar, 0, None, 'cloud metadata file "{}::{}::{}" successfully  updated.'.format(ut_id(gvar, 'ctg1'), ut_id(gvar, 'ctc3'), ut_id(gvar, 'cty3.yaml')),
        '/cloud/metadata-update/', group=(ut_id(gvar, 'ctg1')),
        form_data={
            'cloud_name': ut_id(gvar, 'ctc3'),
            'metadata_name': ut_id(gvar, 'cty3.yaml'),
            'enabled': 'false'
        },
        server_user=ut_id(gvar, 'ctu3'), server_pw=user_secret
    )

if __name__ == "__main__":
    main(None)
