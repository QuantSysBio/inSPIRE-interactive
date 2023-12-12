""" Functions to deal with returning results.
"""
import os
import time

from flask import render_template
import pandas as pd
import plotly.graph_objects as go

from inspire_interact.constants import QUEUE_PATH
from inspire_interact.utils import safe_job_id_fetch

EPITOPE_CANDIDATE_ROUTE = 'inspireOutput/epitope/potentialEpitopeCandidates.csv'
NS_PERC_PSMS_PATH = 'inspireOutput/non_spectral.percolator.psms.txt'
NS_PERC_SEP_PSMS_PATH = 'inspireOutput/non_spectral.percolatorSeparate.psms.txt'
PERC_PSMS_PATH = 'inspireOutput/final.percolator.psms.txt'
PERC_SEP_PSMS_PATH = 'inspireOutput/final.percolatorSeparate.psms.txt'
QUANT_FILE_PATH = 'inspireOutput/quant/quantified_per_file.csv'



def fetch_queue_and_task(project_home, home_key):
    """ Function to fetch interact queue and the job ID of an
        inSPIRE execution.
    """
    job_id = safe_job_id_fetch(project_home)

    if not job_id:
        time.sleep(3)
        job_id = safe_job_id_fetch(project_home)
    queue_df = pd.read_csv(
        QUEUE_PATH.format(home_key=home_key)
    )
    if not queue_df.shape[0]:
        time.sleep(2)
        queue_df = pd.read_csv(
            QUEUE_PATH.format(home_key=home_key)
        )
    return queue_df, job_id


def create_queue_fig(interact_home, project_home):
    """ Function to create an svg plot of the inSPIRE-interactive queue.
    """
    queue_df = pd.read_csv(QUEUE_PATH.format(home_key=interact_home))
    queue_length = queue_df.shape[0]
    task_colors = []
    for idx in range(4):
        task_colors.append([])
        for row_idx in range(queue_length):
            if row_idx > 0:
                task_colors[idx].append('#AFEEEE')
            else:
                task_colors[idx].append('#FFE4B5')

    fig = go.Figure(
        data=[
            go.Table(
                header={
                    'height': 25,
                    'values': [
                        'User',
                        'Project',
                        'Job ID',
                        'Task Status',
                    ],
                    'line_color': 'black',
                    'align': 'left',
                },
                cells={
                    'height': 20,
                    'values': [
                        queue_df.user,
                        queue_df.project,
                        queue_df.taskID,
                        queue_df.status,
                    ],
                    'fill_color': task_colors,
                    'line_color': 'black',
                    'align': 'left',
                },
                columnwidth = [200, 200, 100, 300],
            )
        ]
    )
    total_height = (queue_df.shape[0]*20) + 25 + 4
    fig.update_layout(
        width=800,
        height=total_height+20,
        margin={'r':30, 'l':30, 't':10, 'b':10}
    )

    fig.write_image(f'{project_home}/queue.svg', engine='kaleido')

def create_status_fig(project_home):
    """ Function to create an svg plot of the status of all tasks within
        an inSPIRE job.
    """
    if not os.path.exists(f'{project_home}/taskStatus.csv'):
        return
    task_df = pd.read_csv(f'{project_home}/taskStatus.csv')
    task_colors = []
    for idx in range(3):
        task_colors.append([])
        for task_status in task_df['status'].tolist():
            if task_status == 'Queued':
                task_colors[idx].append('#AFEEEE')
            if task_status == 'Completed':
                task_colors[idx].append('darkseagreen')
            if task_status == 'Failed':
                task_colors[idx].append('lightcoral')
            if task_status == 'Running':
                task_colors[idx].append('#FFE4B5')
            if task_status == 'Skipped':
                task_colors[idx].append('#FFE4B5')
            if task_status == 'Job Cancelled':
                task_colors[idx].append('#dec8d1')

    fig = go.Figure(
        data=[
            go.Table(
                header={
                    'height': 25,
                    'values': [
                        'Task Index',
                        'Task',
                        'Task Status',
                    ],
                    'line_color': 'black',
                    'align': 'left',
                },
                cells={
                    'height': 20,
                    'values': [
                        task_df.taskIndex,
                        task_df.taskName,
                        task_df.status,
                    ],
                    'fill_color': task_colors,
                    'line_color': 'black',
                    'align': 'left',
                },
                columnwidth = [120,200,120],
            )
        ]
    )
    total_height = (task_df.shape[0]*20) + 25 + 4
    padding = (300 - total_height)/2
    fig.update_layout(
        width=500,
        height=300,
        margin={'r':30, 'l':30, 't':padding, 'b':padding}
    )

    fig_html = fig.to_html()
    fig.write_image(
        f'{project_home}/progress.svg', engine='kaleido'
    )
    with open(
        f'{project_home}/progress.html',
        mode='w',
        encoding='UTF-8',
    ) as html_out:
        html_out.write(fig_html)

def safe_fetch(file_path):
    """ Function to check if a file_path exists and return the contents
        if so.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='UTF-8') as file_contents:
            return file_contents.read()
    return ''

def deal_with_queue(interact_home, project_home, server_address, header_and_footer):
    """ Function to provide information if the inSPIRE execution is still queued.
    """
    create_queue_fig(interact_home, project_home)
    queue_svg = safe_fetch(f'{project_home}/queue.svg')
    return render_template(
        'queued.html',
        server_address=server_address,
        queue_svg=queue_svg,
        **header_and_footer
    )

def deal_with_failure(project_home, server_address, user, project, workflow, header_and_footer):
    """ Function to provide information if the inSPIRE execution has failed.
    """
    create_status_fig(project_home)
    progress_html = safe_fetch(f'{project_home}/progress.html')

    return render_template(
        'failed.html',
        server_address=server_address,
        user=user,
        project=project,
        workflow=workflow,
        progress_html=progress_html,
        **header_and_footer,
    )

def deal_with_waiting(project_home, server_address, user, project, header_and_footer):
    """ Function to return waiting screen if data is still processing.
    """
    create_status_fig(project_home)
    progress_svg = safe_fetch(f'{project_home}/progress.svg')
    return render_template(
        'waiting.html',
        progress_html=progress_svg,
        project=project,
        server_address=server_address,
        user=user,
        **header_and_footer,
    )

def deal_with_success(
        project_home,
        server_address,
        user,
        project,
        workflow,
        inspire_select_visible,
        header_and_footer,
    ):
    """ Function to return the results screen if inSPIRE has executed successfully
    """
    # Fetch the plots to be shown on results page.
    create_status_fig(project_home)
    progress_svg = safe_fetch(f'{project_home}/progress.svg')
    psm_fdr_svg = safe_fetch(f'{project_home}/inspireOutput/img/psm_fdr_curve.svg')
    ep_bar = safe_fetch(f'{project_home}/inspireOutput/img/epitope_bar_plot.svg')
    quant_svg = safe_fetch(f'{project_home}/inspireOutput/img/peptide_volcano.svg')
    if not quant_svg:
        quant_svg = safe_fetch(f'{project_home}/inspireOutput/img/norm_correlation.svg')

    return render_template(
        'ready.html',
        server_address=server_address,
        user=user,
        project=project,
        workflow=workflow,
        inspire_select_visible=inspire_select_visible,
        psm_fdr_html=psm_fdr_svg,
        ep_bar=ep_bar,
        quant_html=quant_svg,
        progress_html=progress_svg,
        inspire_increase=get_inspire_increase(project_home, 'total'),
        pathogen_increase=get_inspire_increase(project_home, 'pathogen'),
        inspire_quantified_count=get_quant_count(project_home),
        **header_and_footer
    )


def get_inspire_increase(project_home, variant):
    """ Function to calculate the percentage increase in peptides/PSMs by inSPIRE.
    """
    if variant == 'total':
        try:
            if os.path.exists(f'{project_home}/{PERC_PSMS_PATH}'):
                inspire_df = pd.read_csv(f'{project_home}/{PERC_PSMS_PATH}', sep='\t')
            elif os.path.exists(f'{project_home}/{PERC_SEP_PSMS_PATH}'):
                inspire_df = pd.read_csv(f'{project_home}/{PERC_SEP_PSMS_PATH}', sep='\t')
            else:
                inspire_df = pd.DataFrame({'q-value': []})
        except pd.errors.EmptyDataError:
            inspire_df = pd.DataFrame({'q-value': []})
        inspire_count = len(inspire_df[inspire_df['q-value'] < 0.01])

        try:
            if os.path.exists(f'{project_home}/{NS_PERC_PSMS_PATH}'):
                ns_df = pd.read_csv(f'{project_home}/{NS_PERC_PSMS_PATH}', sep='\t')
            elif os.path.exists(f'{project_home}/{NS_PERC_SEP_PSMS_PATH}'):
                ns_df = pd.read_csv(f'{project_home}/{NS_PERC_SEP_PSMS_PATH}', sep='\t')
            else:
                ns_df = pd.DataFrame({'q-value': []})
        except pd.errors.EmptyDataError:
            ns_df = pd.DataFrame({'q-value': []})
        ns_count = len(ns_df[ns_df['q-value'] < 0.01])

        if ns_count <= 0:
            return ''
        increase = round(100*(inspire_count - ns_count)/ns_count, 2)

        return f'inSPIRE increased overall PSM yield by {increase}% at 1% FDR.'

    if not os.path.exists(f'{project_home}/{EPITOPE_CANDIDATE_ROUTE}'):
        return 'No epitope candidates found.'
    pathogen_df = pd.read_csv(f'{project_home}/{EPITOPE_CANDIDATE_ROUTE}')
    shared_count = len(pathogen_df[
        pathogen_df['foundBySearchEngine'] == 'Yes'
    ])
    inspire_count = len(pathogen_df[
        pathogen_df['foundBySearchEngine'] == 'No'
    ])
    if shared_count == 0:
        increase = '>100'
    else:
        increase = round(100*inspire_count/shared_count, 2)

    return f'inSPIRE increased pathogen peptide yield by {increase}%.'


def get_quant_count(project_home):
    """ Function to get the number of peptides quantified via Skyline.
    """
    if os.path.exists(f'{project_home}/{QUANT_FILE_PATH}'):
        quant_df = pd.read_csv(f'{project_home}/{QUANT_FILE_PATH}')
        quant_count = quant_df.shape[0]
    else:
        quant_count = 0

    return f'inSPIRE quantified {quant_count} peptides via Skyline.'
