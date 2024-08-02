## Airflow Tableau EC2 Maintenance

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





















