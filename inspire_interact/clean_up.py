""" Scripts for cleaning up after cancelations/failures.
"""
import os
import signal

import pandas as pd

from inspire_interact.constants import QUEUE_PATH
from inspire_interact.queue_manager import remove_from_queue
from inspire_interact.utils import get_pids


def get_user_and_project(home_key, job_id):
    """ Function to get the user and project name from a job ID.
    """
    queue_df = pd.read_csv(
        QUEUE_PATH.format(home_key=home_key)
    )
    queue_df = queue_df[
        queue_df['taskID'] == job_id
    ]
    if len(queue_df):
        return queue_df['user'].iloc[0], queue_df['project'].iloc[0]
    return None, None

def clear_queue(interact_home):
    """ Function to cancel all running jobs and clear the queue.
    """
    if os.path.exists(QUEUE_PATH.format(home_key=interact_home)):
        queue_df = pd.read_csv(QUEUE_PATH.format(home_key=interact_home))
        for _, df_row in queue_df.iterrows():
            cancel_job_helper(interact_home, df_row['user'], df_row['project'], df_row['taskID'])


def cancel_job_helper(home_key, user, project, job_id):
    """ Function to cancel a job and delete it from the queue.
    """
    if user is None:
        user, project = get_user_and_project(home_key, job_id)
    project_home = f'{home_key}/projects/{user}/{project}'

    if job_id is None:
        pids = get_pids(project_home, 'inspire')
    else:
        pids = [int(job_id)]

    if pids is None:
        return 'No task was running. Please refresh the page.'

    remove_from_queue(home_key, int(pids[0]))

    task_killed = False
    for pid in pids:
        try:
            os.kill(int(pid), signal.SIGTERM)
            task_killed = True
        except OSError:
            continue

    if not task_killed:
        return 'No task was running. Please refresh the page.'

    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    task_df['status'] = 'Job Cancelled'
    task_df.to_csv(f'{project_home}/taskStatus.csv', index=False)

    return 'Task cancelled. Please refresh the page.'
