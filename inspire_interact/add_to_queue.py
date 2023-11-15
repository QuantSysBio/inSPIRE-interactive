""" Functions to add inspire to queue.
"""
import sys
import os
import pandas as pd

def main():
    user = sys.argv[1]
    project = sys.argv[2]
    with open(f'projects/{user}/{project}/inspire_pids.txt', 'r') as pid_file:
        task_id = int(pid_file.readline().strip())
    if os.path.exists('locks/inspireQueue.csv'):
        queue_df = pd.read_csv('locks/inspireQueue.csv')
    else:
        queue_df = pd.DataFrame({
            'user': [],
            'project': [],
            'taskID': [],
            'status': [],
        })

    append_df = pd.DataFrame({
        'user': [user],
        'project': [project],
        'taskID': [task_id],
        'status': 'waiting',
    })
    queue_df = pd.concat([queue_df, append_df])
    queue_df.to_csv('locks/inspireQueue.csv', index=False)

if __name__ == '__main__':
    main()
