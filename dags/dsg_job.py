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
        'year': '2019'
    }
}

fc_products = [
    'ls7_fc_albers',
    'ls8_fc_albers',
]

# tags is in airflow >1.10.8
# My local env is airflow 1.10.7...
dag = DAG(
    'nci_fractional_cover',
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
        {% set work_dir = '/g/data/v10/work/' + params.product + '/' + ts_nodash %}

        module use /g/data/v10/public/modules/modulefiles;
        module load {{ params.module }};

        """

    product = 'the_shizzle'
    test_tasks = SSHOperator(
        command=COMMON + """
        cd {{work_dir}}
        datacube-fc run -vv --dry-run --input-filename {{work_dir}}/tasks.pickle
        """,
        params={},
        task_id=f'test_tasks_{product}',
        timeout=60 * 20,
    )

    submit_task_id = f'submit_C3_ARD'
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
    
    wait_for_completion = PBSJobSensor(
        task_id=f'wait_for_{product}',
        pbs_job_id="{{ ti.xcom_pull(task_ids='%s') }}" % submit_task_id,
        timeout=60 * 60 * 24 * 7,
    )
    
    start >> generate_tasks >> test_tasks >> submit_fc_job >> wait_for_completion >> completed
