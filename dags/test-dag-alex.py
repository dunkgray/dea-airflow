from airflow import DAG
from datetime import datetime
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.trigger_rule import TriggerRule

def get_date():
    # Fail on a Tuesday, Tuesday is 1, because 0 based.
    if datetime.today().weekday() == 0:
        raise ValueError("It's a Tuesday and I hate Tuesdays")
    return datetime.today()

def say_hello():
    return "Hello world, it'll be ok."

default_args = {
    'owner': 'Alex Leith',
    'start_date': datetime(2020, 1, 1),
    'email': ['alex.leith@ga.gov.au']
}

dag = DAG(
    'testdag-alex',
    description="Alex's test dag that does something fancy",
    default_args=default_args,
    schedule_interval="@daily"
)

task_error = t1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    trigger_rule=TriggerRule.ALL_FAILED,
    dag=dag,
)

task_1 = PythonOperator(
    task_id='get_date',
    python_callable=get_date,
    on_failure_callback=task_error,
    dag=dag
)

task_3 = PythonOperator(
    task_id='say_hello',
    python_callable=say_hello,
    dag=dag
)

task_1 >> task_3
