# Azure infrastructure and application guide

[Back to README](../README.md#2-azure-deployment)

Sources: [Terraform](../terraform/main.tf), [bootstrap](../terraform/cloud-init.yaml), [Compose override](../compose.deploy.yaml), and [notes, sections 12–13](../notes.md#12-azure-infrastructure-with-terraform). Run local commands from the repository root unless a directory change is shown.

Historical provisioning, SSH access, and cleanup are recorded in notes.md. Full application deployment with the current bootstrap is **not verified**. Commands moved from the previous README are instructions; they have not been executed during this edit.

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

The source defines nine resources. The next plan and apply results are **not verified**; review the actual plan.

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

The cloud-init configuration specifies:

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

# Deploy the application

The full Azure application deployment is **not verified** in notes.md. The commands below are retained operating instructions, not recorded execution results.

## Step 1 — Provision the VM

Follow the infrastructure instructions above to run:

```bash
terraform apply
```

Connect to the newly created VM and confirm that cloud-init has finished.

The remaining deployment commands in this section run **inside the Azure VM**.

## Step 2 — Open the Project Directory

```bash
cd /opt/secure-cloud-api
```

The bootstrap is configured to clone the repository here. Its completion with the current configuration is **not verified** in notes.md; check initialization before continuing.

## Step 3 — Configure the Database Password

Create an environment file with restrictive permissions:

```bash
sudo sh -c 'umask 077; touch .env'
sudo nano .env
```

Set `POSTGRES_PASSWORD` to a unique password in the editor. No password value is included in this guide.

Verify permissions:

```bash
sudo ls -l .env
```

Expected permissions:

```text
-rw-------
```

Create `.env` only on the VM for this deployment and keep it out of GitHub and Terraform configuration.

**Note:** Environment files are not an encrypted secrets-management system. A managed secrets service would be more appropriate for production.

## Step 4 — Start the Containers

The deployment override file is:

```text
compose.deploy.yaml
```

It removes the local API build setting and selects the GHCR `latest` tag. Image availability and any private-registry authentication must be checked before starting.

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

### Verification status

[notes.md, section 13](../notes.md#13-vm-bootstrap-and-application-deployment) lists VM bootstrap, image access, application health, Todo creation/retrieval, and persistence checks as work to verify. Their success on the current VM configuration is **not verified**. JSON examples above are expected application responses, not evidence of a completed Azure deployment.

# Destroy Azure resources after testing

**Important:** Azure resources can incur charges while deployed.

The earlier infrastructure practice session recorded destruction and resource-group removal. Current Azure resource state is **not verified** by that historical result.

First, exit the VM:

```bash
exit
```

Then, on your **local computer**, return to the Terraform directory. If the local shell is already there, stay in that directory; the following command applies from the repository root:

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

Destroying the VM removes its local database volume and `.env` file. Preserve any required data before cleanup; see notes.md, section 12.

**Never assume Azure charges have stopped merely because application containers are stopped.** Verify infrastructure cleanup.
