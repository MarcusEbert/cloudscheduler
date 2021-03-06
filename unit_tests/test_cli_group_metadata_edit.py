from unit_test_common import execute_csv2_command, initialize_csv2_request, ut_id
from os import environ
from sys import argv

# lno: GV - error code identifier.

def main(gvar, user_secret):
    if not gvar:
        gvar = {}
        if len(argv) > 1:
            initialize_csv2_request(gvar, argv[0], selections=argv[1])
        else:
            initialize_csv2_request(gvar, argv[0])
    
    execute_csv2_command(
        gvar, 1, None, 'the following mandatory parameters must be specfied on the command line',
        ['cloudscheduler', 'metadata', 'edit']
    )

    execute_csv2_command(
        gvar, 1, None, 'The following command line arguments were unrecognized: [\'-xx\', \'yy\']',
        ['cloudscheduler', 'metadata', 'edit', '-xx', 'yy']
    )

    execute_csv2_command(
        gvar, 1, None, 'The following command line arguments were invalid: job-cores',
        ['cloudscheduler', 'metadata', 'edit', '-jc', 'invalid-unit-test']
    )

    execute_csv2_command(
        gvar, 1, None, 'Error: the specified server "invalid-unit-test" does not exist in your defaults.',
        ['cloudscheduler', 'metadata', 'edit', '-mn', 'invalid-unit-test', '-te', 'vim', '-s', 'invalid-unit-test']
    )

    execute_csv2_command(
        gvar, 1, None, None,
        ['cloudscheduler', 'metadata', 'edit', '-s', 'unit-test-un']
    )

    execute_csv2_command(
        gvar, 0, None, 'Help requested for "cloudscheduler metadata edit".',
        ['cloudscheduler', 'metadata', 'edit', '-h']
    )

    execute_csv2_command(
        gvar, 0, None, 'General Commands Manual',
        ['cloudscheduler', 'metadata', 'edit', '-H']
    )

    execute_csv2_command(
        gvar, 1, None, 'Expose API requested',
        ['cloudscheduler', 'metadata', 'edit', '-xA', '-mn', 'invalid-unit-test', '-te', 'vim']
    )

    execute_csv2_command(
        gvar, 1, None, 'cannot switch to invalid group "invalid-unit-test".',
        ['cloudscheduler', 'metadata', 'edit', '-g', 'invalid-unit-test', '-mn', 'invalid-unit-test', '-te', 'vim']
    )

    execute_csv2_command(
        gvar, 1, None, 'the following mandatory parameters must be specfied on the command line',
        ['cloudscheduler', 'metadata', 'edit', '-g', ut_id(gvar, 'clg1')]
    )

    execute_csv2_command(
        gvar, 1, None, 'no value, neither default nor command line, for the following required parameters',
        ['cloudscheduler', 'metadata', 'edit', '-mn', 'invalid-unit-test']
    )

    execute_csv2_command(
        gvar, 1, None, 'file "{}::invalid-unit-test" does not exist.'.format(ut_id(gvar, 'clg1')),
        ['cloudscheduler', 'metadata', 'edit', '-mn', 'invalid-unit-test', '-te', 'invalid-unit-test']
    )

    execute_csv2_command(
        gvar, 1, None, None,
        ['cloudscheduler', 'metadata', 'edit', '-mn', ut_id(gvar, 'clm2'), '-te', 'invalid-unit-test']
    )

    environ['EDITOR'] = './editscript1'

    execute_csv2_command(
        gvar, 0, None, 'completed, no changes.',
        ['cloudscheduler', 'metadata', 'edit', '-mn', ut_id(gvar, 'clm2')]
    )

    environ.pop('EDITOR')

    execute_csv2_command(
        gvar, 1, None, 'Error: "cloudscheduler metadata edit" - no value, neither default nor command line, for the following required parameters:',
        ['cloudscheduler', 'metadata', 'edit', '-mn', ut_id(gvar, 'clm2')]
    )

    # The edit scripts in the next 4 tests will break easily as they rely on some system variables
    execute_csv2_command(
        gvar, 0, None, '"{}::{}" completed, no changes.'.format(ut_id(gvar, 'clg1'), ut_id(gvar, 'clm2')),
        ['cloudscheduler', 'metadata', 'edit', '-mn', ut_id(gvar, 'clm2'), '-te', './editscript1']
    )

    execute_csv2_command(
        gvar, 0, None, '"{}::{}" successfully  updated.'.format(ut_id(gvar, 'clg1'), ut_id(gvar, 'clm2')),
        ['cloudscheduler', 'metadata', 'edit', '-mn', ut_id(gvar, 'clm2'), '-te', './editscript2']
    )

    execute_csv2_command(
        gvar, 0, None, '"{}::{}" successfully  updated.'.format(ut_id(gvar, 'clg1'), ut_id(gvar, 'clm2.yaml')),
        ['cloudscheduler', 'metadata', 'edit', '-mn', ut_id(gvar, 'clm2.yaml'), '-te', './editscript3']
    )

    execute_csv2_command(
        gvar, 1, None, 'Invalid yaml file "scanner error": mapping values are not allowed here',
        ['cloudscheduler', 'metadata', 'edit', '-mn', ut_id(gvar, 'clm2.yaml'), '-te', './editscript4']
    )

if __name__ == "__main__":
    main(None)
