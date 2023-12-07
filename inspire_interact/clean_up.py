""" Scripts for cleaning up after cancelations/failures.
"""
import os
import signal

import pandas as pd

from inspire_interact.constants import QUEUE_PATH
from inspire_interact.utils import get_pids


def clear_queue(interact_home):
    """ Function to cancel all running jobs and clear the queue.
    """
    if os.path.exists(QUEUE_PATH.format(home_key=interact_home)):
        queue_df = pd.read_csv(QUEUE_PATH.format(home_key=interact_home))
        for _, df_row in queue_df.iterrows():
            cancel_job_helper(interact_home, df_row['user'], df_row['project'])


def cancel_job_helper(home_key, user, project):
    """ Function to cancel a job and delete it from the queue.
    """
    project_home = f'{home_key}/projects/{user}/{project}'
    pids = get_pids(project_home, 'inspire')
    if pids is None:
        return 'No task was running. Please refresh the page.'

    task_killed = False
    for pid in pids:
        try:
            os.kill(int(pid), signal.SIGTERM)
            task_killed = True
        except OSError:
            continue

    if not task_killed:
        return 'No task was running. Please refresh the page.'

    os.system(
        f'interact-queue --project_home {project_home} ' +
        f' --interact_home {home_key} ' +
        ' --queue_task remove\n'
    )
    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    task_df['status'] = 'Job Cancelled'
    task_df.to_csv(f'{project_home}/taskStatus.csv', index=False)

    return 'Task cancelled. Please refresh the page.'
