import multiprocessing
from multiprocessing import Process
import time
import logging
import re
import os
import sys

from cloudscheduler.lib.db_config import Config
from cloudscheduler.lib.log_tools import get_frame_info
from cloudscheduler.lib.ProcessMonitor import ProcessMonitor

def apel_accounting_cleanup():
    multiprocessing.current_process().name = "APEL Accounting Cleanup"

    my_config_category = os.path.basename(sys.argv[0])
    config = Config('/etc/cloudscheduler/cloudscheduler.yaml', my_config_category, pool_size=4, refreshable=True)

    config.db_open()

    try:
        while True:
            logging.debug("Beginning APEL Accounting Cleanup cycle")
            config.refresh()

            obsolete_apel_accounting_rows = time.time() - (86400 * config.categories[my_config_category]['apel_accounting_keep_alive_days'])

            try:
                result = config.db_session.execute('delete from apel_accounting where (last_update>0 and last_update<%s) or (last_update<1 and start_time<%s);' % (obsolete_apel_accounting_rows, obsolete_apel_accounting_rows))
                config.db_session.commit()
                logging.info('APEL accounting, %s rows deleted.' % result.rowcount)

            except Exception as ex:
                logging.error('Delete of obsolete APEL accounting rows failed: %s' % ex)

            config.db_session.rollback()
            logging.debug("Completed APEL Accounting Cleanup cycle")
            time.sleep(config.categories[my_config_category]['sleep_interval_apel_cleanup'])

    except Exception as exc:
        logging.exception("VM data poller, while loop exception, process terminating...")
        logging.error(exc)
        del condor_session
        db_session.close()

def vm_data_poller():
    multiprocessing.current_process().name = "VM data poller"

    my_config_category = os.path.basename(sys.argv[0])
    config = Config('/etc/cloudscheduler/cloudscheduler.yaml', my_config_category, pool_size=4, refreshable=True)
    VMS = config.db_map.classes.csv2_vms

    if os.path.isfile(config.categories[my_config_category]['vm_data_poller_checkpoint']):
        with open(config.categories[my_config_category]['vm_data_poller_checkpoint']) as fd:
            checkpoint = int(fd.read())
    else:
        checkpoint = 0

    config.db_open()

    try:
        while True:
            logging.debug("Beginning VM data poller cycle")
            config.refresh()

            ssl_access_log_size = os.stat(config.categories[my_config_category]['ssl_access_log']).st_size
            if checkpoint > ssl_access_log_size:
                checkpoint = 0

            with open(config.categories[my_config_category]['ssl_access_log']) as fd:
                fd.seek(checkpoint)
                ssl_access_log =fd.read()

            ssl_access_log_size = len(ssl_access_log)

            apel_updates = []
            vms_in_error = {}
            for line in ssl_access_log.split('\n'):
                if '/CERT/' in line or '/STARTD/' in line:
                    ignore, ignore, ignore, hostname, type, errors = line.split('/', 5)
                    errors, ignore = errors.split(' ',1)
                    vms_in_error[hostname] = {'type': type, 'errors': errors[:VMS.htcondor_startd_errors.property.columns[0].type.length]}

                elif '/APEL_ACCOUNTING=' in line:
                    ignore, ignore, ignore, hostname, apel_accounting, ignore = line.replace('\\','').replace(' HTTP', '/HTTP').split('/', 5)
                    
                    group_name = None
                    cloud_name = None
                    keys = ['hostname="%s"' % hostname]
                    values = ['last_update=unix_timestamp()']

                    for key_val in apel_accounting[16:].split(','):
                        key, val = key_val.split(':', 1)
                        if val and val != '':
                            if key == 'group_name' or key == 'cloud_name':
                                keys.append('%s=%s' % (key, val))
                            else:
                                values.append('%s=%s' % (key, val))

                    if len(keys) == 3 and len(values) > 1:
                        apel_updates.append('update apel_accounting set %s where %s;' % (','.join(values), ' and '.join(keys)))

            updates = 0
            if len(vms_in_error) > 0:
                for hostname in sorted(vms_in_error):
                      if vms_in_error[hostname]['type'] == 'CERT':
                          config.db_session.execute('update csv2_vms set htcondor_startd_errors="%s",htcondor_startd_time=unix_timestamp(),retire=retire+1,updater="%s" where hostname="%s"' % (vms_in_error[hostname]['errors'], str(get_frame_info() + ":r+"), hostname))
                          updates += 1
                      elif vms_in_error[hostname]['type'] == 'STARTD':
                          config.db_session.execute('update csv2_vms set htcondor_startd_errors="%s",htcondor_startd_time=unix_timestamp() where hostname="%s"' % (vms_in_error[hostname]['errors'], hostname))
                          updates += 1

            for apel_update in apel_updates:
                try:
                    config.db_session.execute(apel_update)
                    updates += 1
                except Exception as ex:
                    logging.error('%s failed - %s' % (apel_update, ex))
                
            if updates > 0:
                config.db_session.commit()

            logging.info('%s updates commited.' % updates)

            config.db_session.rollback()
            checkpoint += ssl_access_log_size
            with open(config.categories[my_config_category]['vm_data_poller_checkpoint'], 'w') as fd:
                fd.write(str(checkpoint))

            logging.debug("Completed VM data poller cycle")
            time.sleep(config.categories[my_config_category]['sleep_interval_vm_data'])

    except Exception as exc:
        logging.exception("VM data poller, while loop exception, process terminating...")
        logging.error(exc)
        del condor_session
        db_session.close()

if __name__ == '__main__':

    process_ids = {
        'apel_cleanup':   apel_accounting_cleanup,
        'vm_data':        vm_data_poller,
    }

    my_config_category = os.path.basename(sys.argv[0])
    procMon = ProcessMonitor(config_params=[my_config_category, "general", 'ProcessMonitor'], pool_size=4, orange_count_row='csv2_jobs_error_count', process_ids=process_ids)
    config = procMon.get_config()
    logging = procMon.get_logging()
    version = config.get_version()

    logging.info("**************************** starting VM data monitor - Running %s *********************************" % version)

    # Wait for keyboard input to exit
    try:
        #start processes
        procMon.start_all()
        while True:
            procMon.check_processes()
            time.sleep(config.categories['ProcessMonitor']['sleep_interval_main_long'])
            
    except (SystemExit, KeyboardInterrupt):
        logging.error("Caught KeyboardInterrupt, shutting down threads and exiting...")

    except Exception as ex:
        logging.exception("Process Died: %s", ex)

    procMon.kill_join_all()


