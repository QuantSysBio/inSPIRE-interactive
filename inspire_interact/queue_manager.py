""" Scripts for managing inSPIRE jobs running on after another.
"""
from argparse import ArgumentParser
import os
from time import sleep

import pandas as pd


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
    with open(f'{project_home}/inspire_pids.txt', 'r') as pid_file:
        task_id = int(pid_file.readline().strip())
    if os.path.exists(f'{interact_home}/locks/inspireQueue.csv'):
        queue_df = pd.read_csv(f'{interact_home}/locks/inspireQueue.csv')
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
    queue_df.to_csv(f'{interact_home}/locks/inspireQueue.csv', index=False)

def remove_from_queue(project_home, interact_home):
    with open(f'{project_home}/inspire_pids.txt', 'r') as pid_file:
        task_id = int(pid_file.readline().strip())

    queue_df = pd.read_csv(f'{interact_home}/locks/inspireQueue.csv')
    drop_index = queue_df[queue_df['taskID'] == task_id].index[0]
    queue_df = queue_df.drop(drop_index, axis=0)
    queue_df.to_csv(f'{interact_home}/locks/inspireQueue.csv', index=False)

def update_status(project_home, interact_home, inspire_task, inspire_status):
    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    queue_df = pd.read_csv(f'{interact_home}/locks/inspireQueue.csv')
    if inspire_task == 'start':
        task_df['status'].iloc[0] = 'Running'
        queue_df.iloc[0, queue_df.columns.get_loc('status')] = task_df.iloc[0, task_df.columns.get_loc('taskName')]
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
    queue_df.to_csv(f'{interact_home}/locks/inspireQueue.csv', index=False)

    if inspire_task == 'start' or inspire_status == '0':
        exit(0)
    else:
        exit(1)


def check_queue(project_home, interact_home):
    with open(f'{project_home}/inspire_pids.txt', 'r') as pid_file:
        task_id = int(pid_file.readline().strip())

    while True:
        queue_df = pd.read_csv(f'{interact_home}/locks/inspireQueue.csv')
        if int(queue_df['taskID'].iloc[0]) == task_id:
            break
        sleep(60)

def main():
    args = get_arguments()
    if args.queue_task == 'add':
        add_to_queue(args.project_home, args.interact_home)
    if args.queue_task == 'remove':
        remove_from_queue(args.project_home, args.interact_home)
    if args.queue_task == 'check':
        check_queue(args.project_home, args.interact_home)
    if args.queue_task == 'update':
        update_status(args.project_home, args.interact_home, args.inspire_task, args.inspire_status)


if __name__ == '__main__':    
    main()