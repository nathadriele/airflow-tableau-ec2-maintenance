## Apache Airflow Tableau EC2 Maintenance

### Overview

This project automates weekly maintenance tasks for a Tableau server hosted on an EC2 instance using Apache Airflow. The maintenance workflow includes cleaning up temporary files, checking disk usage before and after the cleanup, and sending notifications with the results via AWS SNS.

### Prerequisites

- **Apache Airflow**: Ensure Airflow is installed and configured.
- **AWS Credentials**: AWS access and secret keys should be configured for SNS.
- **SSH Access**: Proper SSH access to the EC2 instance running the Tableau server.
    - `Airflow Variables`: Set the following Airflow variables:
    - `TABLEAU_SERVER_INSTANCE_IP`: IP address of the Tableau server EC2 instance.
    - `SNS_TOPIC_ARN_TSM`: ARN of the SNS topic to send notifications.
    - `tableau_ssh_conn`: Airflow SSH connection ID for the EC2 instance.

### Installation

1. Clone the repository:

```py
git clone https://github.com/nathadriele/airflow-tableau-ec2-maintenance.git
cd airflow-tableau-ec2-maintenance
```

2. Install required dependencies:
Ensure you have the necessary Python packages installed, either through Airflow's requirements or manually:

```py
pip install apache-airflow
pip install apache-airflow-providers-ssh
pip install apache-airflow-providers-amazon
```

3. Set Airflow Variables:
Use the Airflow UI or CLI to set the required variables:

```py
airflow variables --set TABLEAU_SERVER_INSTANCE_IP "your_instance_ip"
airflow variables --set SNS_TOPIC_ARN_TSM "your_sns_topic_arn"
```

### Usage

1. Deploy the DAG:
Place the DAG file in your Airflow DAGs directory:

```py
cp tsm_cleanup_tableau_dag.py /path/to/your/airflow/dags/
```

2. Start Airflow:
Ensure Airflow is running:

```py
airflow scheduler
airflow webserver
```

3. Trigger the DAG:

Trigger the DAG: The DAG is scheduled to run weekly on Mondays at 6 AM (for example). You can also trigger it manually via the Airflow UI.

### Code Explanation

#### Configuration and Constants

These variables configure the IP address, SSH connection, cleanup command, disk usage command, and SNS ARN for the DAG.

```py
INSTANCE_IP = Variable.get("TABLEAU_SERVER_INSTANCE_IP")
SSH_CONN_ID = 'tableau_ssh_conn'
CLEANUP_COMMAND = "tsm maintenance cleanup"
DISK_USAGE_COMMAND = "df /dev/nvme0n1p1 | tail -1 | awk '{print $5}'"
SNS_ARN = Variable.get('SNS_TOPIC_ARN_TSM')
```

- `INSTANCE_IP`: Holds the IP address of the Tableau server, used for connecting via SSH.
- `SSH_CONN_ID`: Contains the ID of the SSH connection configuration in Airflow.
- `CLEANUP_COMMAND`: The command to execute Tableau's maintenance cleanup.
- `DISK_USAGE_COMMAND`: Command to check disk usage on a specific partition.
- `SNS_ARN`: ARN of the SNS topic for sending notifications.

#### Default Arguments

Defines the default arguments for the DAG tasks, such as the owner, retry behavior, and dependencies.

#### Setting Dependencies

```py
check_disk_before_cleanup >> tsm_cleanup_task >> check_disk_after_cleanup
tsm_cleanup_task >> send_sns_failure_task
[check_disk_before_cleanup, tsm_cleanup_task, check_disk_after_cleanup] >> send_results_task
```

Defines the order in which tasks are executed and handles failure scenarios.

#### Python Function send_sns_message

This function pulls disk usage results before and after cleanup from XCom, decodes the results, and sends a notification via SNS.

#### DAG Definition

Defines the DAG, including its schedule, description, and tags. It sets up the tasks and their dependencies.

#### Tasks

1. `Check Disk Usage Before Cleanup`
2. `Execute TSM Maintenance Cleanup`
3. `Check Disk Usage After Cleanup`
4. `Send Failure Notification`
5. `Send Results`

### SNS Workflow in the Code

**`Before Cleanup:`**

**Task**: `check_disk_before_cleanup` executes an SSH command to check disk usage before the cleanup.
**Result**: The result is stored and used later for comparison.

**`Cleanup Execution:`**

**Task**: `tsm_cleanup_task` executes the cleanup command on the Tableau server.
**Result**: The cleanup is performed to optimize the server's performance.

**`After Cleanup:`**

**Task**: `check_disk_after_cleanup` executes an SSH command to check disk usage after the cleanup.
**Result**: The result is compared with the disk usage before the cleanup.

**`Sending Results:`**

**Task**: `send_results_task` calls the send_sns_message function, which prepares and sends a message to the SNS topic with the cleanup results.
**Objective**: Inform administrators about the success or failure of the cleanup task and its impact on disk usage.

- **Failure Notification**:
**Task**: `send_sns_failure_task` is triggered if the cleanup task fails, sending a failure notification to the SNS topic.

### Result

- After successful execution, the DAG will:
1. Perform disk cleanup on the Tableau server.
2. Check disk usage before and after cleanup.
3. Send an SNS notification with the results.
4. Log any errors encountered during the process.

### Contribution to Data Engineering

This automation ensures regular maintenance of the Tableau server, leading to improved performance and reliability. By integrating Airflow and AWS SNS, the workflow enhances operational efficiency and provides timely notifications, contributing to proactive monitoring and management of data infrastructure.

### Additional Information
- `Logging`: Logs are available in the Airflow UI for each task, providing detailed insights into the execution.
- `Customization`: Modify the schedule or commands as needed to fit your specific maintenance requirements.
