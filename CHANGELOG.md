# Cloud Scheduler version 2 Change Log

- stable-2.7.0:
  - Introduction of this change log.

  - AMQP used for signalling:
    - Introduction of csv2-signal-agent service.

  - All AMQP requests to be authenticated with user name and password. The guest account is locked.

  - TLS termination through HAProxy for all remote AMQP requests.

  - Process monitor changes:
    - graceful shutdown of services.
    - pause services for backup.
    - self reporting service statuses

  - Removal of 'target_clouds'.
  
  - Removal of apel_accounting

  - db_upgrade utility enhancements:
    - When in batch mode ('-i' option), error message and exit (rather than prompt) when manual input required.
    - Ephemeral data conversion: passes temporary directory to schema_backup and loads/converts the ephemeral
      data from there.

  - schema_backup utility enhancement:
    - New option (specifies temporary directory) to save ephemeral data.
    - To use service pause and release when taking backups.

  - Cloud control (retire/terminate) now via separate subprocess for each cloud. 
 
  - OpenStack credentials now verified prior to adding or updating any cloud.
  
  - Certificate Management Improvements
  
  - Configuration table merge and cleanup
  
  - Seperate logrotate files
  
  - Ansible installation playbook re-organization/enhancements.
  
  - Fixes:
    - Server configuration request to ignore the 'group' key (passed on all requests).
    - Log level change without service restart.
    - Ignore invalid default_group user setting (picks first valid group).
    - Remove group related data from tables (aliases, default groups, etc) when a group is deleted.
    - Cleanup local inventories to remove obsolete items at the end of each polling cycle.
     
