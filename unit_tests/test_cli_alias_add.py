from unit_test_common import execute_csv2_command, initialize_csv2_request, ut_id, sanity_commands, parameters_commands
from sys import argv

# lno: AV - error code identifier.

def main(gvar):
    if not gvar:
        gvar = {}
        if len(argv) > 1:
            initialize_csv2_request(gvar, selections=argv[1])
        else:
            initialize_csv2_request(gvar)

    # 01 - 13
    sanity_commands(gvar, 'alias')

    # 14 - 26
    sanity_commands(gvar, 'alias', 'add')

    PARAMETERS = {
        # 27 Give an invalid parameter.
        # 28 Omit name.
        '--cloud-name': {'valid': ut_id(gvar, 'clc2'), 'test_cases': {
            # 29
            '': 'cloud alias add, value specified for "cloud_name" must not be the empty string.',
            # 30
            'Invalid-Unit-Test': 'cloud alias add, value specified for "cloud_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 31
            'invalid-unit--test': 'cloud alias add, value specified for "cloud_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 32
            'invalid-unit-test-': 'cloud alias add, value specified for "cloud_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 33
            'invalid-unit-test!': 'cloud alias add, value specified for "cloud_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 34
            'invalid,unit,test': 'cloud alias add, value specified for "cloud_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 35 Specify a cloud that does not exist.
            'invalid-unit-test': 'cloud alias add, "invalid-unit-test" failed - specified value in list of values does not exist: cloud_name=invalid-unit-test, group_name={}.'.format(ut_id(gvar, 'clg1'))
        }, 'mandatory': True},
        # 36 Omit alias.
        '--alias-name': {'valid': 'invalid-unit-test', 'test_cases': {
            # 37
            '': 'cloud alias add, value specified for "alias_name" must not be the empty string.',
            # 38
            'Invalid-Unit-Test': 'cloud alias add, value specified for "alias_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 39
            'invalid-unit--test': 'cloud alias add, value specified for "alias_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 40
            'invalid-unit-test-': 'cloud alias add, value specified for "alias_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 41
            'invalid-unit-test!': 'cloud alias add, value specified for "alias_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 42
            'invalid,unit,test': 'cloud alias add, value specified for "alias_name" must be all lowercase letters, digits, dashes, underscores, periods, and colons, and cannot contain more than one consecutive dash or start or end with a dash.',
            # 43
            'alias-name-that-is-too-long-for-the-database': 'Data too long for column \'alias_name\' at row 1',
            # 44 Attempt to create a cloud that already exists.
            ut_id(gvar, 'cla1'): 'cloud alias add "{}.{}" failed - specified alias already exists.'.format(ut_id(gvar, 'clg1'), ut_id(gvar, 'cla1'))
        }, 'mandatory': True},
    }

    parameters_commands(gvar, 'alias', 'add', ut_id(gvar, 'clg1'), ut_id(gvar, 'clu3'), PARAMETERS)

    # 45 Create an alias properly.
    execute_csv2_command(
        gvar, 0, None, 'cloud alias "{}.{}" successfully added.'.format(ut_id(gvar, 'clg1'), ut_id(gvar, 'cla3')),
        ['alias', 'add', '-g', ut_id(gvar, 'clg1'), '--alias-name', ut_id(gvar, 'cla3'), '--cloud-name', ut_id(gvar, 'clc2'), '-su', ut_id(gvar, 'clu3')],
    )

if __name__ == "__main__":
    main(None)
