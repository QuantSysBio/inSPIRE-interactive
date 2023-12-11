""" Scripts for managing inSPIRE jobs running on after another.
"""
from argparse import ArgumentParser
import os
from time import sleep

import pandas as pd

from inspire_interact.constants import QUEUE_PATH

def get_arguments():
    """ Function to collect command line arguments.

    Returns
    -------
    args : argparse.Namespace
        The parsed command line arguments.
    """
    parser = ArgumentParser(description='inSPIRE-Interactive Helper.')

    parser.add_argument(
        '--interact_home',
        required=True,
        help='All configurations.',
    )
    parser.add_argument(
        '--project_home',
        required=True,
        help='All configurations.',
    )
    parser.add_argument(
        '--queue_task',
        required=True,
    )
    parser.add_argument(
        '--inspire_task',
        required=False,
    )
    parser.add_argument(
        '--inspire_status',
        required=False,
    )

    return parser.parse_args()


def add_to_queue(project_home, interact_home):
    """ Function to add an inSPIRE job to the inSPIRE-Interactive queue.
    """
    with open(f'{project_home}/inspire_pids.txt', 'r', encoding='UTF-8') as pid_file:
        task_id = int(pid_file.readline().strip())
    if os.path.exists(QUEUE_PATH.format(home_key=interact_home)):
        queue_df = pd.read_csv(QUEUE_PATH.format(home_key=interact_home))
    else:
        queue_df = pd.DataFrame({
            'user': [],
            'project': [],
            'taskID': [],
            'status': [],
        })

    user = project_home.split('/')[-2]
    project = project_home.split('/')[-1]
    append_df = pd.DataFrame({
        'user': [user],
        'project': [project],
        'taskID': [task_id],
        'status': 'waiting',
    })
    queue_df = pd.concat([queue_df, append_df])
    queue_df.to_csv(QUEUE_PATH.format(home_key=interact_home), index=False)

def remove_from_queue(interact_home, job_id):
    """ Function to remove an inSPIRE job from the inSPIRE interactive queue.
    """
    queue_df = pd.read_csv(QUEUE_PATH.format(home_key=interact_home))
    if queue_df[queue_df['taskID'] == job_id].shape[0]:
        drop_index = queue_df[queue_df['taskID'] == job_id].index[0]
        queue_df = queue_df.drop(drop_index, axis=0)
        queue_df.to_csv(QUEUE_PATH.format(home_key=interact_home), index=False)

def update_status(project_home, interact_home, inspire_task, inspire_status):
    """ Function to update the status of a task in the taskStatus file.
    """
    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    queue_df = pd.read_csv(QUEUE_PATH.format(home_key=interact_home))
    if inspire_task == 'start':
        task_df['status'].iloc[0] = 'Running'
        queue_df.iloc[
            0, queue_df.columns.get_loc('status')
        ] = task_df.iloc[
            0, task_df.columns.get_loc('taskName')
        ]
    else:
        index = task_df.index[task_df['taskId'] == inspire_task].tolist()[0]
        if inspire_status == '0':
            task_df['status'].iloc[index] = 'Completed'
            if index + 1 < len(task_df):
                task_df['status'].iloc[index + 1] = 'Running'
                queue_df.iloc[0, queue_df.columns.get_loc('status')] = task_df.iloc[
                    index + 1, task_df.columns.get_loc('taskName')
                ]
        else:
            task_df['status'].iloc[index] = 'Failed'
            for following_idx in range(index+1, len(task_df)):
                task_df['status'].iloc[following_idx] = 'Skipped'

    task_df.to_csv(f'{project_home}/taskStatus.csv', index=False)
    queue_df.to_csv(QUEUE_PATH.format(home_key=interact_home), index=False)


def check_queue(project_home, interact_home):
    """ Function to check if the job is first in the queue.
    """
    with open(f'{project_home}/inspire_pids.txt', 'r', encoding='UTF-8') as pid_file:
        task_id = int(pid_file.readline().strip())

    while True:
        queue_df = pd.read_csv(QUEUE_PATH.format(home_key=interact_home))
        if int(queue_df['taskID'].iloc[0]) == task_id:
            break
        sleep(60)
