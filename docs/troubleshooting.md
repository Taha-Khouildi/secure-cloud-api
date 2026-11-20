# Troubleshooting

[Back to README](../README.md#7-operating-guides)

This diagnostic checklist and its commands were moved from the previous README. It is not a record that every listed failure occurred or that each remedy was tested; those outcomes are **not verified** unless recorded in [notes.md](../notes.md). Run Compose commands from the repository root or the VM project directory.

Recorded incidents include PostgreSQL AppArmor startup failures, a missing `todo_db`, a read-only socket lock-file failure, and PostgreSQL reachability from an unrelated Pod. See [Kubernetes debugging](../notes.md#stage-4--kubernetes-postgresql-debugging) for their evidence. Configuration references: [Compose](../compose.yaml), [database Deployment](../k8s/postgres-deployment.yaml), [NetworkPolicy](../k8s/postgres-networkpolicy.yaml), [Terraform](../terraform/main.tf), and [ServiceMonitor](../k8s/api-servicemonitor.yaml).

| Problem | What to check |
| --- | --- |
| `no configuration file provided` | Run commands from the directory containing `compose.yaml`. |
| `Dockerfile: no such file or directory` | Build from the repository root. |
| FastAPI returns HTTP `405` | Confirm the requested endpoint supports that HTTP method. |
| `/todos` returns HTTP `500` | Inspect application and database logs. |
| PostgreSQL connection fails | Check the database container and environment variables. |
| Database authentication fails after password rotation | Confirm the `todo_user` password matches `postgres-secret` and FastAPI was restarted to receive the updated credentials. |
| PostgreSQL reports a read-only socket lock file | Confirm the writable `emptyDir` mount at `/var/run/postgresql`; retain the database PVC and `/tmp` mount. |
| FastAPI cannot connect after a NetworkPolicy change | Check Pod labels (`app=fastapi`), the `secure-cloud-api` namespace, TCP port `5432`, readiness, and credentials. |
| `no matches for kind "ServiceMonitor"` | Deploy the core application manifests separately, then install Prometheus Operator before applying the ServiceMonitor. |
| Terraform fails authentication | Verify `az login` and the selected subscription. |
| SSH connection times out | Check the VM public IP and the allowed SSH source IP. |
| Docker permission denied | Use `sudo docker` rather than granting Docker group access. |
| Cloud-init setup incomplete | Check `cloud-init status --wait` and cloud-init logs. |
| Deployment image cannot be pulled | Verify the GHCR image name, publication status, and registry access. |
| Terraform reports unexpected existing resources | Inspect Terraform state and actual Azure resources before changing anything. |

Inspect container logs:

```bash
sudo docker compose logs --tail=50 api
sudo docker compose logs --tail=50 db
```

For the Azure deployment, include both Compose files:

```bash
sudo docker compose \
  -f compose.yaml \
  -f compose.deploy.yaml \
  logs --tail=50 api
```

Terraform state and local secrets must never be committed to the public repository.
