import sys
from time import sleep
import pandas as pd

def main():
    user = sys.argv[1]
    project = sys.argv[2]
    with open(f'projects/{user}/{project}/inspire_pids.txt', 'r') as pid_file:
        task_id = int(pid_file.readline().strip())

    while True:
        queue_df = pd.read_csv('locks/inspireQueue.csv')
        if int(queue_df['taskID'].iloc[0]) == task_id:
            break
        sleep(60)

    return

if __name__ == '__main__':    
    main()
