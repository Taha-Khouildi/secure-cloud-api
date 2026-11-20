# Local Kubernetes deployment guide

[Back to README](../README.md#4-local-kubernetes-deployment)

Sources: [manifests](../k8s/), [database initialization](../db/init.sql), and [notes](../notes.md#stage-4--kubernetes-postgresql-debugging).

Local k3s application checks are recorded in [notes.md](../notes.md#stage-4--kubernetes-postgresql-debugging). Fresh-cluster initialization is **not verified**. Commands below were moved from the previous README and are deployment instructions, not a record of a new run. Run them from the repository root.

## Kubernetes resources

The `k8s/` directory contains YAML manifests defining:

- FastAPI Deployment and ClusterIP Service.
- PostgreSQL Deployment and ClusterIP Service.
- PersistentVolumeClaim for PostgreSQL data.
- Readiness probes for FastAPI and PostgreSQL.
- Pod and container security settings, including read-only root filesystems.
- PostgreSQL ingress NetworkPolicy allowing FastAPI Pods in the same namespace.
- CPU and memory requests and limits for both workloads.
- A SHA-256 digest-pinned FastAPI image with `imagePullPolicy: IfNotPresent`.

The optional `k8s/api-servicemonitor.yaml` defines Prometheus scraping and requires Prometheus Operator resources in a separate `monitoring` namespace.

The application also uses a Kubernetes Secret named `postgres-secret` for database credentials and a ConfigMap named `postgres-init` containing the SQL initialization script.

## Deployment

**Prerequisites:** A running k3s cluster with NetworkPolicy enforcement enabled, the `secure-cloud-api` namespace, and access to the published GHCR image.

Create the PostgreSQL Secret securely before deploying. See the [learning notes](../notes.md) for the configuration and security considerations.

Create the SQL ConfigMap from the repository's existing script:

```bash
sudo k3s kubectl create configmap postgres-init \
  -n secure-cloud-api \
  --from-file=init.sql=db/init.sql
```

Apply the core application manifests:

```bash
sudo k3s kubectl apply \
  -f k8s/postgres-pvc.yaml \
  -f k8s/postgres-service.yaml \
  -f k8s/postgres-networkpolicy.yaml \
  -f k8s/postgres-deployment.yaml \
  -f k8s/api-service.yaml \
  -f k8s/api-deployment.yaml
```

Wait for both Deployments:

```bash
sudo k3s kubectl rollout status deployment/postgres \
  -n secure-cloud-api --timeout=120s
sudo k3s kubectl rollout status deployment/fastapi \
  -n secure-cloud-api --timeout=120s
```

Check the application and storage:

```bash
sudo k3s kubectl get pods,pvc,services,networkpolicies -n secure-cloud-api
```

Forward the API Service to your laptop:

```bash
sudo k3s kubectl port-forward \
  -n secure-cloud-api svc/fastapi \
  8000:8000 --address 127.0.0.1
```

In another terminal, test:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/db-health
curl http://127.0.0.1:8000/todos
curl http://127.0.0.1:8000/metrics
```

## Initialization limitation

The recorded existing-volume deployment required manual creation of `todo_db` and execution of `db/init.sql`. The SQL mount in the manifest does not establish a successful fresh-cluster run. Fresh-cluster initialization is **not verified**.

## Monitoring resources

The repository includes a `/metrics` endpoint, a ServiceMonitor, Prometheus/Grafana values, a Grafana dashboard, a `FastAPIDown` alert rule, and Loki/Alloy values for log collection. These files describe the monitoring setup. The user reported earlier interactive verification of FastAPIDown firing and clearing and FastAPI/PostgreSQL logs visible in Grafana through Loki. Supporting monitoring artifacts were not preserved. See [Stage 5 observations](../notes.md#stage-5--earlier-monitoring-observations). External alert notification is **not verified** and remains unimplemented in the documented setup.

Once Prometheus Operator, its custom resource definitions, and the `monitoring` namespace are available, apply the monitoring resources:

```bash
sudo k3s kubectl apply -f k8s/api-servicemonitor.yaml
sudo k3s kubectl apply -f monitoring/fastapi-alerts.yaml
```

The ServiceMonitor and alert rule use the label `release=monitoring`; the Prometheus installation must select these resources.

See the README for [recorded findings](../README.md#5-security-findings) and [accepted PostgreSQL risks](../README.md#accepted-postgresql-startup-risks).
