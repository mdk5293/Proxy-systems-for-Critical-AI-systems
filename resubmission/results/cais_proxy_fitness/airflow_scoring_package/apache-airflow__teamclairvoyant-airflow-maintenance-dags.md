# CAIS Proxy-Fitness Evidence Packet

- Anchor: `apache-airflow`
- Candidate: `teamclairvoyant/airflow-maintenance-dags`
- Repository URL: https://github.com/teamclairvoyant/airflow-maintenance-dags

## Repository metadata

Description: A series of DAGs/Workflows to help maintain the operation of Airflow

Topics: airflow, dag, workflow, airflow-maintenance-dags, maintenance, cleanup, apache-airflow

## Frozen rubric

### AIR01 — Workflow and dependency-graph execution

Critical: True

Supports construction or testing of multi-step workflows, DAGs, dependency graphs, or equivalent execution relationships.

Score: 

Evidence source: 

Evidence note: 

### AIR02 — Failure recovery and retry semantics

Critical: True

Supports testing retry, recovery, failure propagation, restart, or equivalent resilience behavior.

Score: 

Evidence source: 

Evidence note: 

### AIR03 — Connector and integration behavior

Critical: False

Supports integration with external data sources, services, connectors, or heterogeneous components.

Score: 

Evidence source: 

Evidence note: 

### AIR04 — Scheduling and execution semantics

Critical: False

Supports scheduled, triggered, queued, or coordinated execution behavior.

Score: 

Evidence source: 

Evidence note: 

### AIR05 — Pipeline or data consistency

Critical: False

Supports testing consistency or correctness of data or state as it moves through a workflow.

Score: 

Evidence source: 

Evidence note: 

### AIR06 — Operational observability

Critical: False

Provides logging, monitoring, task state, metrics, or equivalent evidence useful for observing workflow behavior.

Score: 

Evidence source: 

Evidence note: 

## Retrieved README

# airflow-maintenance-dags
A series of DAGs/Workflows to help maintain the operation of Airflow

## DAGs/Workflows

* [backup-configs](backup-configs)
    * A maintenance workflow that you can deploy into Airflow to periodically take backups of various Airflow configurations and files.
* [clear-missing-dags](clear-missing-dags)
    * A maintenance workflow that you can deploy into Airflow to periodically clean out entries in the DAG table of which there is no longer a corresponding Python File for it. This ensures that the DAG table doesn't have needless items in it and that the Airflow Web Server displays only those available DAGs.
* [db-cleanup](db-cleanup)
    * A maintenance workflow that you can deploy into Airflow to periodically clean out the DagRun, TaskInstance, Log, XCom, Job DB and SlaMiss entries to avoid having too much data in your Airflow MetaStore.
* [kill-halted-tasks](kill-halted-tasks)
    * A maintenance workflow that you can deploy into Airflow to periodically kill off tasks that are running in the background that don't correspond to a running task in the DB.
    * This is useful because when you kill off a DAG Run or Task through the Airflow Web Server, the task still runs in the background on one of the executors until the task is complete.
* [log-cleanup](log-cleanup)
    * A maintenance workflow that you can deploy into Airflow to periodically clean out the task logs to avoid those getting too big.
* [delete-broken-dags](delete-broken-dags)
    * A maintenance workflow that you can deploy into Airflow to periodically delete DAG files and clean out entries in the ImportError table for DAGs which Airflow cannot parse or import properly. This ensures that the ImportError table is cleaned every day.
* [sla-miss-report](sla-miss-report)
    * DAG providing an extensive analysis report of SLA misses broken down on a daily, hourly, and task level
