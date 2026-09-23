from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = Path(__file__).resolve().parents[3]
PYTHON = PROJECT_DIR / "venv" / "bin" / "python"
COMPOSE_FILE = PROJECT_DIR / "code" / "deployment" / "docker-compose.yml"

default_args = {
    "owner": "airflow",
    "retries": 0,
}

with DAG(
    dag_id="house_price_pipeline",
    description="Data prep -> train -> deploy for the house price model",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
) as dag:

    prepare = BashOperator(
        task_id="prepare_data",
        bash_command=f"{PYTHON} {PROJECT_DIR / 'code' / 'datasets' / 'prepare.py'}",
    )

    train = BashOperator(
        task_id="train_model",
        bash_command=f"{PYTHON} {PROJECT_DIR / 'code' / 'models' / 'train.py'}",
    )

    deploy = BashOperator(
        task_id="deploy",
        bash_command=(
            f"docker compose -f {COMPOSE_FILE} up -d --build --force-recreate"
        ),
    )

    prepare >> train >> deploy
