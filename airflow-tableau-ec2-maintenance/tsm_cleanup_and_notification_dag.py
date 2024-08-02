import base64
import logging
from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.providers.amazon.aws.operators.sns import SnsPublishOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.models import Variable

# Configuration and constants.
INSTANCE_IP = Variable.get("TABLEAU_SERVER_INSTANCE_IP")
SSH_CONN_ID = 'tableau_ssh_conn'
CLEANUP_COMMAND = "tsm maintenance cleanup"
DISK_USAGE_COMMAND = "df /dev/nvme0n1p1 | tail -1 | awk '{print $5}'"
SNS_ARN = Variable.get('SNS_TOPIC_ARN_TSM')

# Default arguments for the DAG.
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def send_sns_message(**kwargs):
    """
    Sends an SNS notification with the results of the disk usage before and after cleanup.
    """
    ti = kwargs['ti']
    try:
        before_cleanup_result = ti.xcom_pull(task_ids='check_disk_usage_before_cleanup')
        after_cleanup_result = ti.xcom_pull(task_ids='check_disk_usage_after_cleanup')

        if before_cleanup_result and after_cleanup_result:
            before_cleanup_result = base64.b64decode(before_cleanup_result).decode('utf-8')
            after_cleanup_result = base64.b64decode(after_cleanup_result).decode('utf-8')

            message = (f"TSM cleanup task succeeded on Tableau EC2 instance! \n"
                       f"Disk usage before cleanup: {before_cleanup_result}\n"
                       f"Disk usage after cleanup: {after_cleanup_result}")

            sns_publish_task = SnsPublishOperator(
                task_id="sns_send_results",
                target_arn=SNS_ARN,
                message=message,
            )

            sns_publish_task.execute(dict())
        else:
            logging.error("Disk usage results are missing.")
    except Exception as e:
        logging.error(f"Failed to send SNS message: {e}")

with DAG(
    "tsm_cleanup_tableau",
    default_args=default_args,
    start_date=datetime(2023, 10, 10),
    max_active_runs=1,
    description="Performs tsm maintenance cleanup weekly",
    schedule_interval="0 6 * * *", # Runs daily at 6 AM.
    tags=["tableau", "ec2"],
    catchup=False,
) as dag:

    check_disk_before_cleanup = SSHOperator(
        task_id="check_disk_usage_before_cleanup",
        ssh_conn_id=SSH_CONN_ID,
        remote_host=INSTANCE_IP,
        command=DISK_USAGE_COMMAND,
        do_xcom_push=True,
    )

    tsm_cleanup_task = SSHOperator(
        task_id="execute_tsm_maintenance_cleanup",
        ssh_conn_id=SSH_CONN_ID,
        remote_host=INSTANCE_IP,
        command=CLEANUP_COMMAND,
        conn_timeout=600,
    )

    check_disk_after_cleanup = SSHOperator(
        task_id="check_disk_usage_after_cleanup",
        ssh_conn_id=SSH_CONN_ID,
        remote_host=INSTANCE_IP,
        command=DISK_USAGE_COMMAND,
        do_xcom_push=True,
    )

    send_sns_failure_task = SnsPublishOperator(
        task_id="sns_failure_of_execute_tsm_cleanup",
        target_arn=SNS_ARN,
        message="TSM cleanup task failed on Tableau EC2 instance.",
        trigger_rule="one_failed",
    )

    send_results_task = PythonOperator(
        task_id='send_results',
        python_callable=send_sns_message,
    )

    # Setting dependencies.
    check_disk_before_cleanup >> tsm_cleanup_task >> check_disk_after_cleanup
    tsm_cleanup_task >> send_sns_failure_task
    [check_disk_before_cleanup, tsm_cleanup_task, check_disk_after_cleanup] >> send_results_task
