"""
# Produce and Index Fractional Cover on the NCI
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.contrib.operators.ssh_operator import SSHOperator
from airflow.operators.dummy_operator import DummyOperator

from sensors.pbs_job_complete_sensor import PBSJobSensor

default_args = {
    'owner': 'Duncan Gray',
    'depends_on_past': False,  # Very important, will cause a single failure to propagate forever
    'start_date': datetime(2020, 2, 17),
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
    'ssh_conn_id': 'dsg547',
    'params': {
        'project': 'u46',
        'queue': 'normal',
        'module': 'dea/unstable',
        'module_ass': 'ard-scene-select-py3-dea/20200814',
        'index_env': '/g/data/v10/projects/c3_ard/dea-ard-scene-select/scripts/prod/ard_env/index-datacube.env',
        'wagl_env': '/g/data/v10/projects/c3_ard/dea-ard-scene-select/scripts/prod/ard_env/prod-wagl.env',
    }
}

# tags is in airflow >1.10.8
# My local env is airflow 1.10.10...
dag = DAG(
    'nci_dsg_job',
    default_args=default_args,
    catchup=False,
    schedule_interval=None,
    default_view='graph',
    tags=['nci', 'landsat_c2'],
)

with dag:
    start = DummyOperator(task_id='start')
    completed = DummyOperator(task_id='completed')

    COMMON = """
        #  ts_nodash timestamp no dash.
        {% set log_dir = '/home/547/dsg547/dump/airflow/' + ts_nodash %}
        {% set work_dir = '/home/547/dsg547/dump/airflow' %}
    
        #module use /g/data/v10/public/modules/modulefiles;
        #module load {{ params.module }};

        """

    product = 'used_by_params'
    set_up = SSHOperator(
        command=COMMON + """
        # make the dir here so the output from the submit task is minimal
        mkdir -p {{ log_dir }}
        """,
        params={},
        task_id=f'set_up',
        timeout=60 * 20,
    )

    submit_task_id = f'submit_fc_job'
    submit_fc_job = SSHOperator(
        task_id=submit_task_id,
        command=COMMON + """
        # TODO Should probably use an intermediate task here to calculate job size
        # based on number of tasks.
        # Although, if we run regularaly, it should be pretty consistent.
        # Last time I checked, FC took about 30s per tile (task).
        
        cd {{work_dir}}
        
        qsub -N {{ params.product}}_{{ params.year }} \
        -q {{ params.queue }} \
        -W umask=33 \
        -l wd,walltime=5:00:00,mem=190GB,ncpus=48 -m abe \
        -l storage=gdata/v10+gdata/fk4+gdata/rs0+gdata/if87 \
        -M nci.monitor@dea.ga.gov.au \
        -P {{ params.project }} -o {{ work_dir }} -e {{ work_dir }} \
        -- /bin/bash -l -c \
        "module use /g/data/v10/public/modules/modulefiles/; \
        module load {{ params.module }}; \
        datacube-fc run -vv --input-filename {{work_dir}}/tasks.pickle --celery pbs-launch"
        """,
        params={'product': product},
        timeout=60 * 20,
        do_xcom_push=True,
    )

    # An example of remotely starting a qsub job (all it does is ls)
    submit_task_id = f'submit_ls'
    submit_ls_job = SSHOperator(
        task_id=submit_task_id,
        command=COMMON + """
        # TODO Should probably use an intermediate task here to calculate job size
        # based on number of tasks.
        # Although, if we run regularaly, it should be pretty consistent.
        # Last time I checked, FC took about 30s per tile (task).
        
        cd {{work_dir}}
        
        qsub -N dsg_ls_{{ params.year }} \
        -q {{ params.queue }} \
        -W umask=33 \
        -l wd,walltime=00:01:00,mem=190GB,ncpus=1 -m abe \
        -l storage=gdata/v10+gdata/fk4+gdata/rs0+gdata/if87 \
        -M duncan.gray@dea.ga.gov.au \
        -P {{ params.project }} -o {{ log_dir }} -e {{ log_dir }} \
        -- /bin/bash -l -c \
        "module use /g/data/v10/public/modules/modulefiles/; \
        ls"
        """,
        timeout=60 * 20,
        do_xcom_push=True,
    )

    # An example of remotely starting a qsub job (all it does is ls)
    submit_task_id = f'submit_help'
    submit_ls_job = SSHOperator(
        task_id=submit_task_id,
        command=COMMON + """
        mkdir -p {{ log_dir }} # remove this later.
        cd {{work_dir}} # no need to do this
        
        qsub -N ard_scene_select \
              -q  {{ params.queue }}  \
              -W umask=33 \
              -l wd,walltime=0:30:00,mem=15GB,ncpus=1 -m abe \
              -l storage=gdata/v10+scratch/v10+gdata/if87+gdata/fj7+scratch/fj7+scratch/u46+gdata/u46 \
              -P  {{ params.project }} -o {{ log_dir }} -e {{ log_dir }}  \
              -- /bin/bash -l -c \
                  "module use /g/data/v10/public/modules/modulefiles/; \
                  module use /g/data/v10/private/modules/modulefiles/; \
                  module load {{ params.module_ass }}; \
                  ard-scene-select --help"
        """,
        timeout=60 * 20,
        do_xcom_push=True,
    )

    # An example of remotely starting a qsub job (all it does is ls)
    submit_task_id = f'submit_non_prod'
    submit_ls_job = SSHOperator(
        task_id=submit_task_id,
        command=COMMON + """
        mkdir -p {{ log_dir }} # remove this later.
        cd {{work_dir}} # no need to do this
        
        qsub -N ard_scene_select \
              -q  {{ params.queue }}  \
              -W umask=33 \
              -l wd,walltime=0:30:00,mem=15GB,ncpus=1 -m abe \
              -l storage=gdata/v10+scratch/v10+gdata/if87+gdata/fj7+scratch/fj7+scratch/u46+gdata/u46 \
              -P  {{ params.project }} -o {{ log_dir }} -e {{ log_dir }}  \
              -- /bin/bash -l -c \
                  "module use /g/data/v10/public/modules/modulefiles/; \
                  module use /g/data/v10/private/modules/modulefiles/; \
                  module load {{ params.module_ass }}; \
                  ard-scene-select --workdir {{ log_dir }} \
                  --pkgdir {{ log_dir }} --logdir {{ log_dir }} \
                  --env {{ params.wagl_env }}  \
                  --index-datacube-env {{ params.index_env }}  \
                   --project {{ params.project }} \
                   --walltime 05:00:00"
        """,
        timeout=60 * 20,
        do_xcom_push=True,
    )

    wait_for_completion = PBSJobSensor(
        task_id=f'wait_for_{product}',
        pbs_job_id="{{ ti.xcom_pull(task_ids='%s') }}" % submit_task_id,
        timeout=60 * 60 * 24 * 7,
    )
    # A simple initial test
    ls_task = SSHOperator(command="ls",
        task_id=f'ls_task',
        timeout=60 * 20,)
    
    start >> set_up >> wait_for_completion >> completed
