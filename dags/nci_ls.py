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
    'nci_ls',
    default_args=default_args,
    catchup=False,
    schedule_interval=None,
    default_view='graph',
    tags=['nci', 'landsat_c3'],
)

with dag:
    start = DummyOperator(task_id='start')
    completed = DummyOperator(task_id='completed')

    COMMON = """
        {% set work_dir = '/g/data/v10/work/c3_ard/' + ts_nodash %}

        module use /g/data/v10/public/modules/modulefiles;
        module load {{ params.module }};

        """

    for product in fc_products:
        generate_tasks = SSHOperator(
            command=COMMON + """
                APP_CONFIG="$(datacube-fc list | grep "{{ params.product }}")";
                
                # 2020-03-19 - Workaround to avoid TCP connection timeouts on gadi.
                # TODO: Get PGBouncer configuration updated
                export DATACUBE_CONFIG_PATH=~/datacube-nopgbouncer.conf
              
                #mkdir -p {{ work_dir }}
                cd {{work_dir}}
                datacube --version
                datacube-fc --version
                #datacube-fc generate -vv --app-config=${APP_CONFIG} --output-filename tasks.pickle
            """,
            params={'product': product},
            task_id=f'generate_tasks_{product}',
            timeout=60 * 20,
        )
        ls_task = SSHOperator(command="ls",
            task_id=f'ls_task',
            timeout=60 * 20,)

        start >> ls_task  >> completed
