import sys
from time import sleep
import pandas as pd

def main():
    user = sys.argv[1]
    project = sys.argv[2]
    with open(f'projects/{user}/{project}/inspire_pids.txt', 'r') as pid_file:
        task_id = int(pid_file.readline().strip())

    queue_df = pd.read_csv('locks/inspireQueue.csv')
    drop_index = queue_df[queue_df['taskID'] == task_id].index[0]
    queue_df = queue_df.drop(drop_index, axis=0)
    queue_df.to_csv('locks/inspireQueue.csv', index=False)


if __name__ == '__main__':    
    main()
