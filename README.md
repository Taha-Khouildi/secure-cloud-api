# Secure Cloud API

A containerized **Todo REST API** built with **FastAPI** and **PostgreSQL**, deployed to **Microsoft Azure** using **Terraform**, with automated testing, Docker image publishing, and vulnerability scanning through **GitHub Actions**.

The API is intentionally simple. The goal of this portfolio project is to learn **DevOps, cloud infrastructure, CI/CD, and cloud security** by building and documenting a complete deployment workflow.

**Current status:** The API has been successfully deployed and tested on an Azure Linux VM and a local k3s cluster. The Azure infrastructure was destroyed afterward to conserve Azure for Students credits. Local Kubernetes security testing verified explicit security contexts, read-only root filesystems, and a PostgreSQL NetworkPolicy for the tested connection paths. The PostgreSQL password has since been rotated; database connectivity and existing Todo records still need verification after rotation. Detailed results are recorded in [notes.md](notes.md).

## Features

- Create a Todo with a title (`POST /todos`).
- List saved Todos (`GET /todos`).
- Check API availability (`GET /health`).
- Check PostgreSQL connectivity (`GET /db-health`).
- Persist Todo data in a Docker volume.
- Initialize the database table automatically on first startup.
- Build and run the application with Docker Compose.
- Provision Azure infrastructure using Terraform.
- Configure the Azure VM automatically with cloud-init.
- Run automated tests using GitHub Actions.
- Scan Docker images with Trivy.
- Publish tested Docker images to GitHub Container Registry (GHCR).
- Deploy the published image to Azure using Docker Compose.
- Run FastAPI and PostgreSQL on local k3s with readiness probes and persistent database storage.
- Harden Kubernetes containers and restrict PostgreSQL ingress to FastAPI Pods.
- Expose Prometheus metrics at `GET /metrics`.

## Technology Stack

| Component | Technology | Purpose |
| --- | --- | --- |
| API | Python 3.14, FastAPI, Uvicorn | Handle HTTP requests |
| Database | PostgreSQL 18 | Persist Todo records |
| Database driver | psycopg 3 | Connect Python to PostgreSQL |
| Containers | Docker, Docker Compose | Package and run the application |
| Kubernetes | k3s | Run and secure the local cluster deployment |
| Infrastructure | Terraform, AzureRM provider | Provision cloud resources |
| Cloud platform | Microsoft Azure | Host the deployment |
| VM configuration | cloud-init | Install software and clone the repository |
| CI/CD | GitHub Actions | Test, scan, and publish images |
| Container registry | GitHub Container Registry | Store the application image |
| Security scanning | Trivy | Detect container vulnerabilities and configuration findings |
| Observability configuration | Prometheus, Grafana, Loki, Alloy | Define metrics, dashboards, alerts, and log collection |
| Version control | Git, GitHub | Manage source code and automation |

## Project Structure

```text
secure-cloud-api/
├── .github/
│   └── workflows/
│       └── ci.yml             # CI, image scanning, and publishing
├── app/
│   ├── main.py                # API endpoints
│   └── database.py            # PostgreSQL connection helper
├── db/
│   └── init.sql               # Initial database schema
├── k8s/                       # Deployments, Services, PVC, NetworkPolicy, ServiceMonitor
├── monitoring/                # Monitoring values, dashboard, and alert rule
├── security-tests/
│   └── postgres-readonly.yaml  # Isolated PostgreSQL read-only filesystem test
├── terraform/
│   ├── main.tf                # Azure infrastructure resources
│   ├── providers.tf           # Terraform provider configuration
│   └── cloud-init.yaml        # Automatic VM setup
├── tests/                     # Automated API tests
├── Dockerfile                 # FastAPI container image
├── compose.yaml               # Local application configuration
├── compose.deploy.yaml        # Deployment image override
├── requirements.txt           # Runtime Python dependencies
├── requirements-dev.txt       # Development and test dependencies
├── .dockerignore
├── .gitignore
├── .env.example               # Environment variable template
├── README.md
└── notes.md                   # Learning notes and troubleshooting
```

Terraform-related files and tests may contain additional configuration files not shown in this simplified tree.

## Architecture

The deployment follows this workflow:

```text
Developer
    |
    | git push
    v
GitHub Repository
    |
    v
GitHub Actions
    |
    +--> Install dependencies
    +--> Run pytest
    +--> Build Docker image
    +--> Scan image with Trivy
    |
    v
GitHub Container Registry
    |
    | Published Docker image
    |
    v
Azure Linux VM
    |
    +--> Docker Compose
           |
           +--> FastAPI container
           |
           +--> PostgreSQL container
                  |
                  +--> Docker volume
```

Azure infrastructure is provisioned separately using Terraform.

The GitHub Actions workflow automates testing, scanning, and image publishing. **Deployment to the Azure VM is currently performed manually** after Terraform provisions the infrastructure.

---

# 1. Run Locally with Docker Compose

## Prerequisites

- Git
- Docker Engine
- Docker Compose plugin

You do not need to install Python or PostgreSQL directly on your computer. Both run inside containers.

The commands use `sudo docker` because the project was tested on Ubuntu without adding the user to the Docker group.

## Clone the Repository

```bash
git clone https://github.com/Taha-Khouildi/secure-cloud-api.git
cd secure-cloud-api
```

## Configure Environment Variables

Create a local `.env` file:

```bash
cp .env.example .env
nano .env
```

Set a password:

```dotenv
POSTGRES_PASSWORD=your-strong-password
```

Replace the placeholder with your own password.

**Never commit `.env` or real credentials to GitHub.**

## Start the Application

```bash
sudo docker compose up -d --build
```

Check container status:

```bash
sudo docker compose ps
```

Both `api` and `db` should be running.

FastAPI listens on `127.0.0.1:8000`. PostgreSQL is accessible to the API through the internal Docker network and is not published to the host.

## Test the API

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

Check database connectivity:

```bash
curl http://127.0.0.1:8000/db-health
```

Expected:

```json
{"database":"connected"}
```

List Todos:

```bash
curl http://127.0.0.1:8000/todos
```

On a new database, the expected response is:

```json
[]
```

## Create a Todo

```bash
curl -i -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Learn DevOps"}'
```

Expected: HTTP `201 Created`, with a response similar to:

```json
{
  "id": 1,
  "title": "Learn DevOps",
  "completed": false
}
```

The ID may differ. Titles must contain between 1 and 255 characters.

Retrieve the saved Todo:

```bash
curl http://127.0.0.1:8000/todos
```

## Stop the Application

```bash
sudo docker compose down
```

The PostgreSQL volume remains available for future runs.

**Warning:** `docker compose down -v` also deletes the Compose-managed database volume and its data.

The database initialization script runs only when PostgreSQL initializes an empty data directory. It is not a database migration system.

---

# 2. Azure Infrastructure with Terraform

Terraform is used to provision the cloud infrastructure required for deployment.

## Provisioned Resources

The configuration creates nine Azure resources:

1. Resource Group
2. Virtual Network
3. Subnet
4. Network Security Group
5. SSH security rule
6. Subnet-to-NSG association
7. Static Public IP
8. Network Interface
9. Ubuntu Linux Virtual Machine

### Infrastructure Configuration

| Setting | Configuration |
| --- | --- |
| Cloud provider | Microsoft Azure |
| Region | France Central |
| Operating system | Ubuntu Server 24.04 |
| VM size | Standard_B1ms |
| Virtual network | `10.0.0.0/16` |
| Subnet | `10.0.1.0/24` |
| SSH | Port 22, restricted to an explicitly allowed public IP |
| API port | Bound to VM localhost; not publicly exposed |
| Infrastructure management | Terraform |

The VM is intended for development and portfolio demonstrations, not a production workload.

## Prerequisites

On your local Ubuntu computer:

- Azure CLI installed
- Terraform installed
- An Azure subscription
- An SSH key pair configured for the VM
- Azure CLI authentication completed

Authenticate:

```bash
az login
```

Check the active subscription:

```bash
az account show
```

## Deploy the Infrastructure

On your **local computer**, navigate to the Terraform directory:

```bash
cd terraform
```

Set the Azure subscription ID:

```bash
export ARM_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
```

Allow SSH from your current public IPv4 address:

```bash
export TF_VAR_ssh_allowed_ip="$(curl -4 -s https://api.ipify.org)"
```

Initialize Terraform if necessary:

```bash
terraform init
```

Review the infrastructure:

```bash
terraform plan
```

Create the resources:

```bash
terraform apply
```

Review the plan and enter `yes` to confirm.

For a fresh deployment, the expected plan contains nine resources to create.

## Connect to the VM

Find the current public IP:

```bash
az vm show \
  --resource-group rg-secure-cloud-api \
  --name vm-secure-cloud-api \
  --show-details \
  --query publicIps \
  --output tsv
```

Connect from your **local computer**:

```bash
ssh -i ~/.ssh/azure_secure_cloud_api azureuser@YOUR_VM_PUBLIC_IP
```

Replace `YOUR_VM_PUBLIC_IP` with the current public IP address and verify the VM's SSH host key before accepting it.

## Automatic VM Configuration with cloud-init

Terraform provides `terraform/cloud-init.yaml` to the VM during creation.

Cloud-init automatically:

- Updates package metadata.
- Installs Docker.
- Installs Docker Compose.
- Installs Git.
- Clones this repository into `/opt/secure-cloud-api`.

After connecting to the VM, verify initialization:

```bash
cloud-init status --wait
```

Expected:

```text
status: done
```

This automates initial server configuration but does not automatically start the application or configure secrets.

---

# 3. GitHub Actions CI/CD

The GitHub Actions workflow is stored in:

```text
.github/workflows/ci.yml
```

It runs on pushes and pull requests.

## CI Workflow

The workflow performs the following operations:

1. Checks out the repository.
2. Sets up Python 3.14.
3. Installs project and test dependencies.
4. Runs automated API tests with pytest.
5. Builds the application Docker image.
6. Scans the image using Trivy.
7. On a successful push to `main`, publishes the image to GitHub Container Registry.

The published image is:

```text
ghcr.io/taha-khouildi/secure-cloud-api:latest
```

## Automated Tests

The project uses:

- `pytest`
- `httpx`

The current CI tests verify basic FastAPI functionality, including the `/health` endpoint.

A comprehensive integration test suite for PostgreSQL and the complete Todo API is a future improvement.

## Security Scanning with Trivy

Trivy scans the built container image for vulnerabilities.

The CI workflow is configured to fail when it detects **fixable HIGH or CRITICAL vulnerabilities**.

It uses:

```text
ignore-unfixed: true
exit-code: 1
```

This means vulnerabilities without available fixes are not treated as CI-blocking findings. They still represent residual risk and should be monitored.

### Security Improvements Implemented

The Docker image includes several hardening measures:

- Runs the FastAPI application as a non-root user (`UID 10001`).
- Removes `pip` after installing dependencies to reduce unnecessary packaged components.
- Upgrades the vulnerable `zlib1g` package where a fix is available.
- Uses a slim Python base image.
- Keeps credentials outside the Docker image and source repository.

The Trivy gate passed after these changes.

**Passing Trivy does not mean the image is free of all vulnerabilities.** The current configuration prioritizes fixable HIGH and CRITICAL findings.

---

# 4. Deploy the Application to Azure

The Azure deployment was successfully tested using the Docker image published by GitHub Actions.

## Step 1 — Provision the VM

Follow the instructions in **Section 2** to run:

```bash
terraform apply
```

Connect to the newly created VM and confirm that cloud-init has finished.

The remaining deployment commands in this section run **inside the Azure VM**.

## Step 2 — Open the Project Directory

```bash
cd /opt/secure-cloud-api
```

The repository was cloned automatically by cloud-init.

## Step 3 — Configure the Database Password

Create an environment file with restrictive permissions:

```bash
sudo sh -c 'umask 077; touch .env'
sudo nano .env
```

Add:

```dotenv
POSTGRES_PASSWORD=your-strong-password
```

Replace the placeholder with a unique password.

Verify permissions:

```bash
sudo ls -l .env
```

Expected permissions:

```text
-rw-------
```

The `.env` file is stored only on the VM, not in GitHub or Terraform configuration.

**Note:** Environment files are not an encrypted secrets-management system. A managed secrets service would be more appropriate for production.

## Step 4 — Start the Containers

The deployment override file is:

```text
compose.deploy.yaml
```

It replaces the local API build configuration with the image published to GHCR.

Start the application:

```bash
sudo docker compose \
  -f compose.yaml \
  -f compose.deploy.yaml \
  up -d --no-build
```

The `--no-build` option ensures the deployment uses the published image instead of rebuilding the application on the VM.

Check both containers:

```bash
sudo docker compose \
  -f compose.yaml \
  -f compose.deploy.yaml \
  ps
```

Both `api` and `db` should be running.

## Step 5 — Verify the Deployment

Test FastAPI:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

Test the PostgreSQL connection:

```bash
curl http://127.0.0.1:8000/db-health
```

Expected:

```json
{"database":"connected"}
```

Create a Todo:

```bash
curl -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"Deployed my API to Azure"}'
```

Retrieve Todos:

```bash
curl http://127.0.0.1:8000/todos
```

### Deployment Result

The Azure deployment test successfully confirmed:

- Both Docker containers started.
- FastAPI responded to health checks.
- FastAPI connected to PostgreSQL.
- The API created a Todo record.
- The API retrieved the saved Todo record.

All tests were performed from inside the Azure VM.

The API was bound to `127.0.0.1`, and the network security configuration did not expose port 8000 to the public internet.

---

# 5. Destroy Azure Resources After Testing

**Important:** Azure resources can incur charges while deployed.

The project uses an Azure for Students subscription with limited credits, so the infrastructure is destroyed after deployment tests.

First, exit the VM:

```bash
exit
```

Then, on your **local computer**, return to the Terraform directory:

```bash
cd terraform
```

Destroy the infrastructure:

```bash
terraform destroy
```

Review the plan and type `yes` to confirm.

Verify that the Resource Group no longer exists:

```bash
az group exists --name rg-secure-cloud-api
```

Expected:

```text
false
```

Terraform destroys the VM and its managed infrastructure, including the VM's database volume and local `.env` file.

The GitHub repository, published container image, Terraform source code, and local SSH key remain available.

**Never assume Azure charges have stopped merely because application containers are stopped.** Verify infrastructure cleanup.

---

## Local Kubernetes Deployment (Stage 4)

The FastAPI and PostgreSQL application has been successfully deployed to a local single-node Kubernetes cluster using k3s.

### Kubernetes resources

The `k8s/` directory contains YAML manifests defining:

- FastAPI Deployment and ClusterIP Service.
- PostgreSQL Deployment and ClusterIP Service.
- PersistentVolumeClaim for PostgreSQL data.
- Readiness probes for FastAPI and PostgreSQL.
- Pod and container security settings, including read-only root filesystems.
- PostgreSQL ingress NetworkPolicy allowing FastAPI Pods in the same namespace.

The optional `k8s/api-servicemonitor.yaml` defines Prometheus scraping and requires Prometheus Operator resources in a separate `monitoring` namespace.

The application also uses a Kubernetes Secret named `postgres-secret` for database credentials and a ConfigMap named `postgres-init` containing the SQL initialization script.

### Deployment

**Prerequisites:** A running k3s cluster with NetworkPolicy enforcement enabled, the `secure-cloud-api` namespace, and access to the published GHCR image.

Create the PostgreSQL Secret securely before deploying. See the [learning notes](notes.md) for the configuration and security considerations.

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

### Verification

The local deployment was tested successfully:

- FastAPI and PostgreSQL Pods reached `Ready`.
- The API connected to PostgreSQL through its ClusterIP Service.
- Creating and retrieving Todos worked.
- PostgreSQL data survived a Pod replacement.
- After enabling PostgreSQL's read-only root filesystem, existing data remained accessible (`SELECT COUNT(*) FROM todos;` returned `1`) and `/db-health` returned `{"database":"connected"}`.
- After applying the NetworkPolicy, the unrelated `network-test` Pod's connection attempt failed with exit code `1`, while FastAPI retained database connectivity.

These are recorded local test results. Fresh-cluster initialization and other network paths require separate verification.

### PostgreSQL password rotation

Secret metadata inspection with `kubectl describe secret` showed that the original PostgreSQL password contained only `6 bytes`. It was replaced with a cryptographically random 48-character password. The `todo_user` account password and existing `postgres-secret` Kubernetes Secret were updated, and FastAPI was restarted to receive the new credentials.

Recorded checks after rotation:

- The Secret reports `POSTGRES_PASSWORD: 48 bytes`.
- FastAPI and PostgreSQL Pods are both `1/1 Running`.

**Status:** Password rotation completed; final database connectivity verification pending. With the API port-forward running, check `/db-health` and `/todos` using the commands above to confirm database authentication and access to existing Todo records. The earlier successful database tests predate this rotation.

See the [password finding in notes.md](notes.md#finding-weak-postgresql-password) for details. Production use of Kubernetes Secrets also requires appropriate RBAC and encryption-at-rest configuration.

### Kubernetes security settings

| Workload | Configured protections |
| --- | --- |
| FastAPI | Non-root execution as UID `10001`, privilege escalation disabled, all Linux capabilities dropped, read-only root filesystem, and Pod-level `RuntimeDefault` seccomp profile |
| PostgreSQL | Pod-level `RuntimeDefault` seccomp profile, read-only root filesystem, persistent storage at `/var/lib/postgresql`, and writable `emptyDir` volumes at `/var/run/postgresql` and `/tmp` |

The initial read-only PostgreSQL test failed because PostgreSQL could not create its socket lock file under `/var/run/postgresql`. The writable runtime and temporary volumes resolved that failure while keeping the root filesystem read-only. The isolated test manifest is in [security-tests/postgres-readonly.yaml](security-tests/postgres-readonly.yaml); it expects its own `postgres-security-test` namespace, Secret, ConfigMap, and PVC.

The [PostgreSQL NetworkPolicy](k8s/postgres-networkpolicy.yaml) selects Pods labeled `app=postgres` and allows incoming TCP port `5432` from Pods labeled `app=fastapi` in `secure-cloud-api`. It controls ingress; it does not define an egress policy. Pod labels determine the allowed sources, and PostgreSQL credentials remain necessary.

NetworkPolicy enforcement requires a supporting network controller. Policies are additive, so another policy selecting PostgreSQL could allow additional traffic. See the [Kubernetes NetworkPolicy documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/).

### Configuration scanning and recorded findings

With Trivy installed, scan Kubernetes configuration separately from the CI image vulnerability scan:

```bash
trivy config k8s/
```

This uses Trivy's [misconfiguration scanner](https://trivy.dev/docs/latest/scanner/misconfiguration/). The current GitHub Actions workflow scans the application image; Kubernetes configuration scanning is performed manually.

| Finding | Recorded result after the fix |
| --- | --- |
| FastAPI: KSV-0014 and KSV-0118 | HIGH findings decreased from `3` to `0`; `/health`, `/db-health`, and `/metrics` returned HTTP `200` |
| PostgreSQL: KSV-0118 | Explicit Pod seccomp profile added; HIGH findings decreased from `2` to `1` |
| PostgreSQL: KSV-0014 | Read-only filesystem and writable mounts added; Trivy reported `0` misconfigurations for `postgres-deployment.yaml` |
| PostgreSQL reachable from unrelated Pods | NetworkPolicy blocked the tested unrelated Pod while preserving FastAPI access |
| Weak PostgreSQL password | Rotated from `6 bytes` to a random 48-character password; Secret updated and FastAPI restarted; final database connectivity verification pending |

The repository's `trivy-config.txt` contains the earlier scan findings. Use a new scan for current results; a clean result for one manifest does not establish cluster-wide security. See [notes.md](notes.md) for the discovery, fixes, verification, and remaining limitations.

### Optional monitoring configuration

The repository includes a `/metrics` endpoint, a ServiceMonitor, Prometheus/Grafana values, a Grafana dashboard, a `FastAPIDown` alert rule, and Loki/Alloy values for log collection. These files describe the monitoring setup; end-to-end scraping, log ingestion, and alert delivery need their own verification.

Once Prometheus Operator, its custom resource definitions, and the `monitoring` namespace are available, apply the monitoring resources:

```bash
sudo k3s kubectl apply -f k8s/api-servicemonitor.yaml
sudo k3s kubectl apply -f monitoring/fastapi-alerts.yaml
```

The ServiceMonitor and alert rule use the label `release=monitoring`; the Prometheus installation must select these resources.

### Known limitation

On the local Ubuntu learning environment, an AppArmor/containerd compatibility problem prevented PostgreSQL from starting correctly. The PostgreSQL container currently uses `appArmorProfile: Unconfined` as a **temporary local workaround**.

This weakens container isolation and must not be treated as production-ready security configuration. The proper long-term solution is to restore AppArmor confinement with a compatible, corrected policy.

The existing PostgreSQL volume also required manual creation of `todo_db` and execution of `db/init.sql`. Therefore, **fully automated fresh-cluster initialization has not yet been verified**. Additional work is needed before the Kubernetes setup can be considered reproducible from scratch.

---

# 6. Troubleshooting

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

---

# 7. Security Considerations

This is an educational portfolio project, **not a production-ready service**.

## Implemented Security Measures

- SSH restricted to a specified public IP.
- Only SSH allowed through the configured Azure inbound NSG rule.
- FastAPI bound to localhost.
- PostgreSQL port not publicly exposed.
- Application container runs as a non-root user.
- Database credentials excluded from Git.
- Automated container vulnerability scanning.
- CI failure on fixable HIGH and CRITICAL findings.
- Kubernetes FastAPI non-root execution, disabled privilege escalation, and dropped Linux capabilities.
- Pod-level `RuntimeDefault` seccomp profiles and read-only root filesystems for FastAPI and PostgreSQL.
- PostgreSQL writable paths isolated in mounted volumes.
- PostgreSQL ingress restricted by NetworkPolicy to FastAPI-labeled Pods in the same namespace for the tested connection paths.
- Manual Trivy configuration scans and documented security findings.
- Cloud infrastructure destroyed after testing to reduce cost and exposure.

## Current Limitations

- No user authentication or authorization.
- No TLS termination or public HTTPS endpoint.
- No production secrets-management service.
- Kubernetes Secrets require appropriate RBAC and encryption at rest; database authentication and existing Todo records still need verification after the latest password rotation.
- No automated deployment from GitHub Actions to Azure.
- Local k3s deployment uses a temporary AppArmor workaround; fully automated fresh-cluster initialization remains unverified.
- Monitoring and logging configuration is present; end-to-end collection and alert delivery are not verified in the recorded results.
- PostgreSQL NetworkPolicy relies on Pod labels and network enforcement; it does not replace database authentication or restrict egress.
- No comprehensive security assessment.
- No production-grade backup or high-availability design.

Unfixed vulnerabilities may remain in the base image and its dependencies.

These limitations are intentionally documented so that completed work is not confused with planned work.

---

# 8. Project Progress

| Stage | Description | Status |
| --- | --- | --- |
| 1 | FastAPI + PostgreSQL with Docker Compose | ✅ Completed |
| 2 | Azure infrastructure with Terraform | ✅ Completed and tested |
| 3 | GitHub Actions, Trivy, GHCR, and VM deployment | ✅ Core workflow completed |
| 4 | k3s deployment | ✅ Locally tested with security settings and NetworkPolicy; fresh-cluster initialization unverified |
| 5 | Prometheus, Grafana, Loki, and alerting | Configuration present; end-to-end verification pending |
| 6 | Security testing and findings write-up | Local configuration and network findings fixed and documented; broader assessment pending |
| 7 | Final architecture diagram and portfolio documentation | Planned |

### Stage 3 Remaining Improvements

Although the core CI and deployment workflow works, several improvements remain:

- Automate deployment to the Azure VM.
- Expand the automated test suite.
- Add image-version pinning instead of relying only on `latest`
- Improve secret management.
- Add stronger supply-chain security checks.

These are future improvements, not completed features.

## Learning Documentation

See [`notes.md`](notes.md) for infrastructure decisions, troubleshooting, security findings, and lessons learned.

## Project Repository

[github.com/Taha-Khouildi/secure-cloud-api](https://github.com/Taha-Khouildi/secure-cloud-api)
