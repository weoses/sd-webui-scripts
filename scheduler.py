import sys
import threading
import time
import schedule
import config as config
import logging
import subprocess
import custom_log

logger = custom_log.create_logger(__name__)

def process_always(job_name, job_command):
    logger_inner = custom_log.create_logger('job_'+job_name)
    def payload():
        while True:
            logger_inner.info(f'Start shell - {job_command}')
            completed = subprocess.run(job_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
            logger_inner.error(f'Exited with {completed.returncode}')  
            time.sleep(5)
    
    threading.Thread(target=payload, name=f"Thread for job {job_name}").start()


def process_schedule(job_name, job_commands, exec_at):
    logger_inner =  custom_log.create_logger('job_'+job_name)

    def payload_start(command, part_name):
        logger_inner.info(f'Starting {part_name}')
        try:
            logger_inner.info(f'Start shell  - {command}')
            completed = subprocess.run(command, shell=True)
            logger_inner.info(f'{part_name} exited with {completed.returncode}')
        except Exception as e:
            logger_inner.exception(e)
    
    def payload():
        for command in job_commands:
            payload_start(command['command'], command["name"])


    def thread_wrapper():
        threading.Thread(target=payload, name=f"Thread for job {job_name}").start()

    logger_inner.info(f'Adding to schedule')
    schedule.every().day.at(exec_at).do(thread_wrapper)


def main():
    logging.basicConfig(level=logging.DEBUG)

    conf  = config.load_schedule()
    for job in conf["jobs"]:
        if job['type'] == 'schedule':
            process_schedule(
                job['name'],
                job['parts'],
                job['run_at'])

        if job['type'] == 'always':
            process_always(
                job['name'],
                job['command'])

    while 1 :
        time.sleep(1)
        schedule.run_pending()

if __name__ == '__main__':
    main()
