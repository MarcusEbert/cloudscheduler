from unit_test_common import execute_csv2_command, initialize_csv2_request, ut_id
from sys import argv

def main(gvar, user_secret):
    if not gvar:
        gvar = {}
        if len(argv) > 1:
            initialize_csv2_request(gvar, argv[0], selections=argv[1])
        else:
            initialize_csv2_request(gvar, argv[0])

    # 01
    execute_csv2_command(
        gvar, 1, None, 'No action specified for object "defaults"',
        ['cloudscheduler', 'defaults', '-s', 'unit-test-un']
    )

    # 02
    execute_csv2_command(
        gvar, 1, None, 'Invalid action "invalid-unit-test" for object "defaults"',
        ['cloudscheduler', 'defaults', 'invalid-unit-test']
    )

    # 03
    execute_csv2_command(
        gvar, 0, None, 'Help requested for "cloudscheduler defaults".',
        ['cloudscheduler', 'defaults', '-h']
    )

    # 04
    execute_csv2_command(
        gvar, 0, None, 'General Commands Manual',
        ['cloudscheduler', 'defaults', '-H']
    )

    #### SET ####

    # 05
    execute_csv2_command(
        gvar, 1, None, 'the following mandatory parameters must be specfied on the command line',
        ['cloudscheduler', 'defaults', 'set']
    )

    # 06
    execute_csv2_command(
        gvar, 1, None, 'The following command line arguments were unrecognized: [\'-xx\', \'yy\']',
        ['cloudscheduler', 'defaults', 'set', '-xx', 'yy']
    )

    # 07
    execute_csv2_command(
        gvar, 0, None, 'Help requested for "cloudscheduler defaults set".',
        ['cloudscheduler', 'defaults', 'set', '-h']
    )

    # 08
    execute_csv2_command(
        gvar, 0, None, 'General Commands Manual',
        ['cloudscheduler', 'defaults', 'set', '-H']
    )

    # 09
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'set', '-s', ut_id(gvar, 'cld1')]
    )

    #### LIST ####

    # 10
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'list']
    )

    # 11
    execute_csv2_command(
        gvar, 1, None, 'The following command line arguments were unrecognized: [\'-xx\', \'yy\']',
        ['cloudscheduler', 'defaults', 'list', '-xx', 'yy']
    )

    # 12
    execute_csv2_command(
        gvar, 0, None, 'Help requested for "cloudscheduler defaults list".',
        ['cloudscheduler', 'defaults', 'list', '-h']
    )

    # 13
    execute_csv2_command(
        gvar, 0, None, 'General Commands Manual',
        ['cloudscheduler', 'defaults', 'list', '-H']
    )

    # 14
    execute_csv2_command(
        gvar, 1, None, 'the specified server "invalid-unit-test" does not exist in your defaults.',
        ['cloudscheduler', 'defaults', 'list', '-s', 'invalid-unit-test']
    )

    # 15
    execute_csv2_command(
        gvar, 0, None, 'Rows: 1',
        ['cloudscheduler', 'defaults', 'list', '-s', ut_id(gvar, 'cld1')]
    )

    # 16
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'list', '-ok'],
        list='', columns=[]
    )

    # 17
    execute_csv2_command(
        gvar, 0, None, 'defaults list, 1. Defaults (default server = dev): keys=server, columns=alias-name,backup-key,backup-repository,cacerts,cloud-address,cloud-enabled,cloud-flavor-exclusion,cloud-flavor-option,cloud-name,cloud-option,cloud-password,cloud-priority,cloud-project,cloud-project-domain,cloud-project-domain-id,cloud-region,cloud-spot-price,cloud-type,cloud-user,cloud-user-domain,cloud-user-domain-id,comma-separated-values,comma-separated-values-separator,config-category,default-job-group,default-server,delete-cycle-interval,ec2-image-architectures,ec2-image-like,ec2-image-not_like,ec2-image-operating_systems,ec2-image-owner_aliases,ec2-image-owner_ids,ec2-instance-type-cores,ec2-instance-type-families,ec2-instance-type-memory-max-gigabytes-per-core,ec2-instance-type-memory-min-gigabytes-per-core,ec2-instance-type-operating_systems,ec2-instance-type-processor-manufacturers,ec2-instance-type-processors,enable-glint,expose-API,file-path,force,group,group-metadata-exclusion,group-metadata-option,group-name,group-option,help,htcondor-container-hostname,htcondor-fqdn,htcondor-users,job-cores,job-disk,job-hold,job-id,job-image,job-priority,job-ram,job-request-cpus,job-request-disk,job-request-ram,job-request-swap,job-requirements,job-status,job-swap,job-target-clouds,job-user,log-file,log-level,long-help,metadata-enabled,metadata-mime-type,metadata-name,metadata-priority,no-limit-default,no-view,only-keys,rotate,server,server-address,server-grid-cert,server-grid-key,server-password,server-user,sleep-interval-cleanup,sleep-interval-command,sleep-interval-flavor,sleep-interval-image,sleep-interval-job,sleep-interval-keypair,sleep-interval-limit,sleep-interval-machine,sleep-interval-main-long,sleep-interval-main-short,sleep-interval-network,sleep-interval-vm,status-global-switch,status-refresh-internal,super-user,text-editor,user-common-name,user-option,user-password,username,view,view-columns,vm-cores,vm-cores-softmax,vm-disk,vm-flavor,vm-foreign,vm-hosts,vm-image,vm-keep-alive,vm-keyname,vm-network,vm-option,vm-ram,vm-security-groups,vm-status,vm-swap,with,yes',
        ['cloudscheduler', 'defaults', 'list', '-VC']
    )

    # 18
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'list', '-NV'],
        list='Defaults', columns=['server', 'alias-name', 'backup-key', 'backup-repository', 'cacerts', 'cloud-address', 'cloud-enabled', 'cloud-flavor-exclusion', 'cloud-flavor-option', 'cloud-name', 'cloud-option', 'cloud-password', 'cloud-priority', 'cloud-project', 'cloud-project-domain', 'server', 'cloud-project-domain-id', 'cloud-region', 'cloud-spot-price', 'cloud-type', 'cloud-user', 'cloud-user-domain', 'cloud-user-domain-id', 'comma-separated-values', 'comma-separated-values-separator', 'config-category', 'default-job-group', 'default-server', 'server', 'delete-cycle-interval', 'ec2-image-architectures', 'ec2-image-like', 'ec2-image-not_like', 'ec2-image-operating_systems', 'ec2-image-owner_aliases', 'ec2-image-owner_ids', 'ec2-instance-type-cores', 'ec2-instance-type-families', 'server', 'ec2-instance-type-memory-max-gigabytes-per-core', 'ec2-instance-type-memory-min-gigabytes-per-core', 'ec2-instance-type-operating_systems', 'ec2-instance-type-processor-manufacturers', 'ec2-instance-type-processors', 'enable-glint', 'expose-API', 'file-path', 'server', 'force', 'group', 'group-metadata-exclusion', 'group-metadata-option', 'group-name', 'group-option', 'help', 'htcondor-container-hostname', 'htcondor-fqdn', 'htcondor-users', 'job-cores', 'job-disk', 'job-hold', 'job-id', 'job-image', 'job-priority', 'server', 'job-ram', 'job-request-cpus', 'job-request-disk', 'job-request-ram', 'job-request-swap', 'job-requirements', 'job-status', 'job-swap', 'job-target-clouds', 'job-user', 'log-file', 'log-level', 'long-help', 'metadata-enabled', 'metadata-mime-type', 'metadata-name', 'server', 'metadata-priority', 'no-limit-default', 'no-view', 'only-keys', 'rotate', 'server', 'server-address', 'server-grid-cert', 'server-grid-key', 'server-password', 'server-user', 'sleep-interval-cleanup', 'sleep-interval-command', 'server', 'sleep-interval-flavor', 'sleep-interval-image', 'sleep-interval-job', 'sleep-interval-keypair', 'sleep-interval-limit', 'sleep-interval-machine', 'sleep-interval-main-long', 'sleep-interval-main-short', 'sleep-interval-network', 'sleep-interval-vm', 'server', 'status-global-switch', 'status-refresh-internal', 'super-user', 'text-editor', 'user-common-name', 'user-option', 'user-password', 'username', 'view', 'view-columns', 'vm-cores', 'vm-cores-softmax', 'vm-disk', 'vm-flavor', 'vm-foreign', 'vm-hosts', 'vm-image', 'server', 'vm-keep-alive', 'vm-keyname', 'vm-network', 'vm-option', 'vm-ram', 'vm-security-groups', 'vm-status', 'vm-swap', 'with', 'yes']
    )

    # 19
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'list', '-V', 'server-address,server-user'],
        list='Defaults', columns=['server', 'server-address', 'server-user']
    )

    # 20
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'list'],
        list='Defaults', columns=['server', 'server-address', 'server-user']
    )

    # 21
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'list', '-V', ''],
        list='Defaults', columns=['server', 'alias-name', 'backup-key', 'backup-repository', 'cacerts', 'cloud-address', 'cloud-enabled', 'cloud-flavor-exclusion', 'cloud-flavor-option', 'cloud-name', 'cloud-option', 'cloud-password', 'cloud-priority', 'cloud-project', 'cloud-project-domain', 'server', 'cloud-project-domain-id', 'cloud-region', 'cloud-spot-price', 'cloud-type', 'cloud-user', 'cloud-user-domain', 'cloud-user-domain-id', 'comma-separated-values', 'comma-separated-values-separator', 'config-category', 'default-job-group', 'default-server', 'server', 'delete-cycle-interval', 'ec2-image-architectures', 'ec2-image-like', 'ec2-image-not_like', 'ec2-image-operating_systems', 'ec2-image-owner_aliases', 'ec2-image-owner_ids', 'ec2-instance-type-cores', 'ec2-instance-type-families', 'server', 'ec2-instance-type-memory-max-gigabytes-per-core', 'ec2-instance-type-memory-min-gigabytes-per-core', 'ec2-instance-type-operating_systems', 'ec2-instance-type-processor-manufacturers', 'ec2-instance-type-processors', 'enable-glint', 'expose-API', 'file-path', 'server', 'force', 'group', 'group-metadata-exclusion', 'group-metadata-option', 'group-name', 'group-option', 'help', 'htcondor-container-hostname', 'htcondor-fqdn', 'htcondor-users', 'job-cores', 'job-disk', 'job-hold', 'job-id', 'job-image', 'job-priority', 'server', 'job-ram', 'job-request-cpus', 'job-request-disk', 'job-request-ram', 'job-request-swap', 'job-requirements', 'job-status', 'job-swap', 'job-target-clouds', 'job-user', 'log-file', 'log-level', 'long-help', 'metadata-enabled', 'metadata-mime-type', 'metadata-name', 'server', 'metadata-priority', 'no-limit-default', 'no-view', 'only-keys', 'rotate', 'server', 'server-address', 'server-grid-cert', 'server-grid-key', 'server-password', 'server-user', 'sleep-interval-cleanup', 'sleep-interval-command', 'server', 'sleep-interval-flavor', 'sleep-interval-image', 'sleep-interval-job', 'sleep-interval-keypair', 'sleep-interval-limit', 'sleep-interval-machine', 'sleep-interval-main-long', 'sleep-interval-main-short', 'sleep-interval-network', 'sleep-interval-vm', 'server', 'status-global-switch', 'status-refresh-internal', 'super-user', 'text-editor', 'user-common-name', 'user-option', 'user-password', 'username', 'view', 'view-columns', 'vm-cores', 'vm-cores-softmax', 'vm-disk', 'vm-flavor', 'vm-foreign', 'vm-hosts', 'vm-image', 'server', 'vm-keep-alive', 'vm-keyname', 'vm-network', 'vm-option', 'vm-ram', 'vm-security-groups', 'vm-status', 'vm-swap', 'with', 'yes']
    )

    # 22
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'list', '-r'],
        list='Defaults', columns=['Key', 'Value']
    )

    #### DELETE ####

    # 23
    execute_csv2_command(
        gvar, 1, None, 'the following mandatory parameters must be specfied on the command line',
        ['cloudscheduler', 'defaults', 'delete']
    )

    # 24
    execute_csv2_command(
        gvar, 1, None, 'The following command line arguments were unrecognized: [\'-xx\', \'yy\']',
        ['cloudscheduler', 'defaults', 'delete', '-xx', 'yy']
    )

    # 25
    execute_csv2_command(
        gvar, 0, None, 'Help requested for "cloudscheduler defaults delete".',
        ['cloudscheduler', 'defaults', 'delete', '-h']
    )

    # 26
    execute_csv2_command(
        gvar, 0, None, 'General Commands Manual',
        ['cloudscheduler', 'defaults', 'delete', '-H']
    )

    # 27
    execute_csv2_command(
        gvar, 1, None, 'Error: the specified server "invalid-unit-test" does not exist in your defaults.',
        ['cloudscheduler', 'defaults', 'delete', '-s', 'invalid-unit-test']
    )

    # 28
    execute_csv2_command(
        gvar, 0, None, None,
        ['cloudscheduler', 'defaults', 'delete', '-s', ut_id(gvar, 'cld1'), '-Y']
    )

    # 29
    execute_csv2_command(
        gvar, None, None, None,
        ['cloudscheduler', 'defaults', '-s', 'unit-test']
    )

if __name__ == "__main__":
    main(None)
