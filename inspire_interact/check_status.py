""" Script to check the status of an inspire task.
"""
import sys

import pandas as pd
pd.options.mode.chained_assignment = None    # no warning message and no exception is raised


def main():
    task = sys.argv[1]
    status = sys.argv[2]
    project_home = sys.argv[3]
    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    queue_df = pd.read_csv('locks/inspireQueue.csv')
    if task == 'start':
        task_df['status'].iloc[0] = 'Running'
        queue_df.iloc[0, queue_df.columns.get_loc('status')] = task_df.iloc[0, task_df.columns.get_loc('taskName')]
    else:
        index = task_df.index[task_df['taskId'] == task].tolist()[0]
        if status == '0':
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
    queue_df.to_csv('locks/inspireQueue.csv', index=False)

    if task == 'start' or status == '0':
        exit(0)
    else:
        exit(1)


if __name__ == '__main__':
    main()