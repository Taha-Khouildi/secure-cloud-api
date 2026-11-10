# Secure Cloud API

A containerized **Todo REST API** built with **FastAPI** and **PostgreSQL**, deployed to **Microsoft Azure** using **Terraform**, with automated testing, Docker image publishing, and vulnerability scanning through **GitHub Actions**.

The API is intentionally simple. The goal of this portfolio project is to learn **DevOps, cloud infrastructure, CI/CD, and cloud security** by building and documenting a complete deployment workflow.

**Current status:** The API has been successfully deployed and tested on an Azure Linux VM. The infrastructure was destroyed afterward to conserve Azure for Students credits.

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

## Technology Stack

| Component | Technology | Purpose |
| --- | --- | --- |
| API | Python 3.14, FastAPI, Uvicorn | Handle HTTP requests |
| Database | PostgreSQL 18 | Persist Todo records |
| Database driver | psycopg 3 | Connect Python to PostgreSQL |
| Containers | Docker, Docker Compose | Package and run the application |
| Infrastructure | Terraform, AzureRM provider | Provision cloud resources |
| Cloud platform | Microsoft Azure | Host the deployment |
| VM configuration | cloud-init | Install software and clone the repository |
| CI/CD | GitHub Actions | Test, scan, and publish images |
| Container registry | GitHub Container Registry | Store the application image |
| Security scanning | Trivy | Detect container vulnerabilities |
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

# 6. Troubleshooting

| Problem | What to check |
| --- | --- |
| `no configuration file provided` | Run commands from the directory containing `compose.yaml`. |
| `Dockerfile: no such file or directory` | Build from the repository root. |
| FastAPI returns HTTP `405` | Confirm the requested endpoint supports that HTTP method. |
| `/todos` returns HTTP `500` | Inspect application and database logs. |
| PostgreSQL connection fails | Check the database container and environment variables. |
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
- Cloud infrastructure destroyed after testing to reduce cost and exposure.

## Current Limitations

- No user authentication or authorization.
- No TLS termination or public HTTPS endpoint.
- No production secrets-management service.
- No automated deployment from GitHub Actions to Azure.
- No Kubernetes orchestration.
- No centralized monitoring or alerting.
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
| 4 | k3s deployment | Planned |
| 5 | Prometheus, Grafana, Loki, and alerting | Planned |
| 6 | Security testing and findings write-up | Planned |
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