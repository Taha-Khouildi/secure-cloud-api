# Secure Cloud API — Development Notes

## Project Overview

**Project:** Secure Cloud API — DevSecOps Portfolio Project

**Last updated:** 10 November 2026

**Current focus:** Verify the application deployment on Azure using the published container image.

**Status:** FastAPI, PostgreSQL, Docker Compose, a health endpoint test, and a CI pipeline are implemented. Azure infrastructure provisioning, SSH access, and cleanup were verified in an earlier practice session. VM bootstrapping and the deployment override are configured; a full application deployment still needs verification.

These notes record implementation decisions, troubleshooting, and lessons learned. Use [README.md](README.md) for the current setup and deployment instructions. Sections 1–7 preserve the original workstation setup journal; their versions and command outputs describe that earlier session.

### Project Goal

Build a small Todo REST API backed by PostgreSQL, then progressively deploy, automate, monitor, and secure it using Docker, Terraform, Azure, GitHub Actions, k3s, and security testing tools. The original plan mentioned AWS; the implemented infrastructure targets Azure.

The project's main purpose is to demonstrate practical Cloud, DevOps, and Security engineering skills rather than complex application development.

### Completion Criteria for Stage 1

The application and PostgreSQL database must start successfully using `docker compose up` from a fresh Git clone, with setup instructions documented in `README.md`.

The implementation and instructions are present. A clean-clone run remains a separate verification task; the existence of configuration files alone does not establish reproducibility.

### Progress Snapshot

| Area | Implemented or previously recorded | Still to verify or add |
| --- | --- | --- |
| Workstation | Ubuntu, Git, Docker Engine, and Compose setup recorded below | Docker daemon failure experiment remains unconfirmed |
| Application | Health checks, todo creation/listing, title validation, and PostgreSQL access | Automated database and input-validation tests |
| Containers | Local Compose stack, persistent database volume, non-root API image | Service readiness checks and clean-clone verification |
| CI | pytest, Docker build, Trivy scan, and GHCR publishing configured | Confirm successful workflow runs and image availability in GitHub |
| Azure infrastructure | Terraform provisioning, SSH, and cleanup previously verified | Repeat provisioning with the current cloud-init configuration |
| VM application | Docker installation/repository clone configured in cloud-init; GHCR Compose override present | Pull the image, start the stack, and verify through an SSH tunnel |

Configuration present in the repository and successful runtime verification are tracked separately throughout these notes.

---

## 1. Ubuntu Installation

Installed Ubuntu alongside Windows using dual boot.

### System Information

| Component | Details |
|---|---|
| Operating system | Ubuntu 26.04.1 LTS |
| Codename | resolute |
| Installation | Dual boot with Windows |
| Ubuntu partition | Approximately 60 GB |
| Root filesystem | `/dev/nvme0n1p6` |
| RAM | 30 GiB |
| Swap | 8 GiB |
| Python | 3.14.4 |
| Git | 2.53.0 |

### Partition Preparation

Before installing Ubuntu:

1. Checked Windows Fast Startup using `powercfg /a`.
2. Confirmed hibernation was disabled, making Fast Startup unavailable.
3. Checked Windows BitLocker using `manage-bde -status C:`.
4. Confirmed that C: was fully decrypted and BitLocker protection was off.
5. Shrunk the Windows partition by approximately 60 GB.
6. Installed Ubuntu alongside Windows.

### Storage Verification

Command:

```bash
df -h /
```

Observed output:

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p6   59G   24G   32G  43% /
```

**Lesson:** Disk storage must be monitored because Docker images, volumes, and development tools consume space.

### Memory Verification

Command:

```bash
free -h
```

Observed approximately 30 GiB RAM and 8 GiB swap.

**Lesson:** RAM and disk storage are different resources. RAM is used by running processes, while disk storage holds applications, files, images, and persistent data.

---

## 2. Ubuntu Package Management

Updated the package index:

```bash
sudo apt update
```

**Explanation:**

- `sudo`: Executes a command with elevated permissions.
- `apt`: Ubuntu's package manager.
- `update`: Refreshes package lists without upgrading installed software.

The update completed successfully.

---

## 3. Git Installation

Initially, Git was not installed.

Installed it with:

```bash
sudo apt install git
```

Verified the installation:

```bash
git --version
```

Result:

```text
git version 2.53.0
```

### Why Git?

Git tracks source-code changes, allows collaboration, and provides a version history.

At this point in the journal, GitHub hosting and GitHub Actions were planned. The repository now includes a CI workflow for testing, scanning, and publishing images; deployment is manual.

---

## 4. Docker Installation

### Why Docker?

Docker packages an application with its dependencies into an image.

Containers created from that image can run in compatible environments without manually installing the application's dependencies on each machine.

The planned Compose stack consisted of two separate services:

- FastAPI application.
- PostgreSQL database.

Docker Compose now manages them together in [compose.yaml](compose.yaml).

### Installation Method

Chose Docker Engine from Docker's official APT repository for the local workstation. The Azure VM bootstrap separately uses Ubuntu's `docker.io` and `docker-compose-v2` packages.

Installed or verified the prerequisites:

```bash
sudo apt install ca-certificates curl
```

Created the repository key directory:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
```

Downloaded Docker's signing key:

```bash
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
```

Made the key readable:

```bash
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

Configured Docker's APT repository in:

```text
/etc/apt/sources.list.d/docker.sources
```

For that workstation installation, the repository was configured with this Ubuntu codename:

```text
Suites: resolute
```

Then refreshed APT and installed the Docker packages:

```bash
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

## 5. Troubleshooting — Docker Repository Error

### Problem

APT returned:

```text
404 Not Found
The repository does not have a Release file.
```

### Root Cause

The Docker repository configuration mistakenly contained:

```text
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
```

The variable expression had been incorrectly escaped in a shell command, so Bash wrote it literally instead of expanding it.

APT therefore requested an invalid repository path.

### Fix

Opened the configuration:

```bash
sudo nano /etc/apt/sources.list.d/docker.sources
```

Corrected the release field:

```text
Suites: resolute
```

Then refreshed the package index:

```bash
sudo apt update
```

### Lesson Learned

When an APT repository returns a 404 error:

1. Inspect the repository URL and release codename.
2. Verify that the configured distribution exists.
3. Correct the repository definition.
4. Refresh the package lists.
5. Verify that the intended packages can be installed.

A repository configuration error is different from a Docker runtime failure.

---

## 6. Docker Verification

Ran:

```bash
sudo docker run hello-world
```

The image downloaded successfully and Docker returned:

```text
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

### What Happened?

1. Docker CLI contacted the Docker daemon.
2. Docker checked for the image locally.
3. Docker downloaded `hello-world` from Docker Hub.
4. Docker created a container from the image.
5. The container executed its program and exited.

### Docker Concepts

| Concept | Meaning |
|---|---|
| Dockerfile | Instructions used to build an image |
| Image | Packaged application and dependencies |
| Container | An instance created from an image |
| Docker Engine | Service responsible for managing containers |
| Docker Compose | Tool for defining and running multi-container applications |

### Docker Compose Verification

Command:

```bash
docker compose version
```

Result:

```text
Docker Compose version v5.6.1
```

### Verification Result

Docker successfully downloaded and ran a container. Docker Compose is installed and available.

---

## 7. Planned Docker Failure Experiment

The following experiment was proposed but has not yet been confirmed as completed.

Stop Docker:

```bash
sudo systemctl stop docker docker.socket
```

Attempt to run a container:

```bash
sudo docker run hello-world
```

Expected result: Docker cannot connect to its daemon.

Restore Docker:

```bash
sudo systemctl start docker
```

Verify again:

```bash
sudo docker run hello-world
```

**Purpose:** Learn the difference between a Docker CLI command and the Docker daemon responsible for running containers.

---

## 8. Current Progress

### Workstation Setup Recorded Earlier

- [x] Installed Ubuntu alongside Windows
- [x] Verified RAM and root filesystem storage
- [x] Updated Ubuntu package information
- [x] Installed Git
- [x] Installed Docker Engine
- [x] Installed Docker Compose
- [x] Successfully executed `hello-world`
- [x] Diagnosed and fixed a Docker repository configuration error

### Implemented in the Repository

- [x] Initialized the Git repository and configured a GitHub remote
- [x] Implemented FastAPI application and database health endpoints
- [x] Added todo creation and listing backed by PostgreSQL
- [x] Added a Dockerfile and local Compose stack
- [x] Added an environment template and persistent database volume
- [x] Added a health endpoint test and development requirements
- [x] Added CI tests, a Docker build, a Trivy scan, and conditional GHCR publishing
- [x] Added Azure infrastructure with Terraform
- [x] Added cloud-init to install Docker/Compose/Git and clone the repository
- [x] Added a Compose override to use the published GHCR image

### Verification Still Pending

- [ ] Confirm Git author name and email for future commits
- [ ] Complete the optional Docker daemon failure experiment from section 7
- [ ] Verify the documented local setup from a fresh clone
- [ ] Record a successful health test run in a suitable environment
- [ ] Verify a successful CI run and the published image
- [ ] Verify cloud-init and the complete application stack on a newly provisioned VM
- [ ] Confirm database persistence across container recreation on that VM

The earlier practice session verified Terraform provisioning, key-based SSH access, resource destruction, and resource-group removal. It did not establish that the current application deployment works end to end.

---

## 9. Application and Database Implementation

The application is defined in [app/main.py](app/main.py), with database connection settings in [app/database.py](app/database.py).

| Endpoint | Behavior | Database required |
| --- | --- | --- |
| `GET /health` | Returns `{"status":"ok"}` | No |
| `GET /db-health` | Executes `SELECT 1` and reports connectivity | Yes |
| `GET /todos` | Returns todos in ascending ID order | Yes |
| `POST /todos` | Creates a todo and returns HTTP `201` | Yes |

Todo titles must contain 1–255 characters. New rows default to `completed: false`; update, completion, and deletion endpoints are not implemented. Todo creation uses a parameterized SQL value.

[db/init.sql](db/init.sql) creates the initial table. PostgreSQL only runs this script when initializing an empty data directory, so changing it does not migrate an existing database.

**Lessons:** Application liveness and database connectivity answer different questions. A successful `/health` request does not establish that todos can be stored. Database initialization and schema migration are also separate concerns.

## 10. Container Configuration and Storage

- The application image uses `python:3.14-slim` and installs the pinned runtime dependencies.
- The Dockerfile upgrades `zlib1g`, removes `pip` after dependency installation, and runs the application as `appuser` with UID `10001`.
- Compose runs PostgreSQL 18 and the API on its internal network.
- Only the API port is published, at `127.0.0.1:8000`; PostgreSQL has no host port mapping.
- `POSTGRES_PASSWORD` comes from the root `.env` file and is supplied to both services.
- PostgreSQL stores its data in the `todo-postgres-data` named volume mounted at `/var/lib/postgresql`.

**Lessons:** Rebuilding an image does not reset the database volume. Changing the password in `.env` does not update the password already stored by PostgreSQL. `docker compose down` preserves the volume; adding `--volumes` deletes its data.

Compose currently has no service health checks or startup dependencies. Container status alone does not establish database readiness; use `pg_isready` and `/db-health` before testing persistence.

## 11. Automated Testing and CI

[tests/test_health.py](tests/test_health.py) uses FastAPI's `TestClient` to check the status code and JSON returned by `/health`. It does not connect to PostgreSQL. [requirements-dev.txt](requirements-dev.txt) includes the runtime requirements, pytest, and httpx.

The [CI workflow](.github/workflows/ci.yml) runs on pushes and pull requests:

1. Install dependencies with Python 3.14.
2. Run pytest.
3. Build `secure-cloud-api:test`.
4. Scan the built image with Trivy, failing on fixable `HIGH` and `CRITICAL` vulnerabilities while ignoring unfixed findings.
5. On pushes to `main` only, publish the image to `ghcr.io/taha-khouildi/secure-cloud-api:latest` using `GITHUB_TOKEN`.

**Lessons:** A workflow file describes the intended checks; a successful workflow run supplies execution evidence. The image scan covers container vulnerability findings, while API behavior and database integration need their own tests. Publishing an image does not deploy it to a VM.

During the documentation refresh, the local health test was collected but stalled and was interrupted. No passing result was recorded for that run. README link checks, Bash syntax checks, whitespace checks, and parsing the merged deployment Compose configuration passed.

## 12. Azure Infrastructure with Terraform

The configuration in [terraform/main.tf](terraform/main.tf) defines the resource group, virtual network, subnet, Network Security Group and association, SSH rule, public IP, network interface, and Linux VM.

| Setting | Current configuration |
| --- | --- |
| Resource group | `rg-secure-cloud-api` |
| Region | `francecentral` |
| VM | `vm-secure-cloud-api`, size `Standard_B1ms` |
| VM operating system | Ubuntu 24.04 LTS |
| OS disk | 32 GB, `StandardSSD_LRS` |
| Administrator | `azureuser`, SSH key authentication |
| SSH public key file | `~/.ssh/azure_secure_cloud_api.pub` |
| SSH source | `ssh_allowed_ip`, with `/32` appended by Terraform |

### Earlier Practice Session

The previous README recorded successful Terraform initialization, validation, planning, provisioning, SSH access, destruction, and confirmation that the resource group no longer existed. Those are historical results, rather than a new deployment performed during this documentation update.

### Provider Registration Issue

Automatic Azure Resource Provider registration stalled during that session. The AzureRM provider was configured with:

```hcl
resource_provider_registrations = "none"
```

This disables automatic registration; the resource providers needed by the configuration must already be registered in the subscription. VM SKU availability and CPU quota were also checked before the earlier deployment.

**Lessons:** Terraform manages infrastructure, while Compose runs the application on it. Preserve the Terraform state until cleanup is complete. Destroying the VM also removes its local database volume; a named volume is not an external backup.

## 13. VM Bootstrap and Application Deployment

[terraform/cloud-init.yaml](terraform/cloud-init.yaml) is supplied to the VM through Terraform's `custom_data`. During initial provisioning it updates package lists, installs `docker.io`, `docker-compose-v2`, and `git`, and clones this repository into `/opt/secure-cloud-api`.

The bootstrap does not create `.env`, pull the GHCR image, or start the stack. These remain manual actions, documented in the [Azure deployment guide](docs/azure.md).

[compose.deploy.yaml](compose.deploy.yaml) selects the GHCR image and uses `!reset null` to remove the local build setting. It must be combined with the base Compose file. The VM needs a Compose version that supports that tag; check it after cloud-init finishes.

**Deployment verification sequence:**

1. Wait for `sudo cloud-init status --wait` to finish successfully and verify Compose is available.
2. Create the VM's `.env` with restricted file permissions and set the database password.
3. Confirm the GHCR image exists and authenticate if the package is private.
4. Pull and start services using both Compose files.
5. Wait for PostgreSQL readiness, then check `/health` and `/db-health` on the VM.
6. Open an SSH tunnel from the local computer and create/list a todo through it.
7. Recreate the containers without deleting volumes and confirm the todo remains.
8. Destroy the practice infrastructure and confirm the resource group was removed.

**Lessons:** The VM's API remains bound to loopback, so access uses an SSH tunnel. The `latest` image tag can change between deployments. Pulling an image updates the application image, but does not update the repository files cloned by cloud-init.

## 14. Next Tasks

- Complete the clean-clone and Azure application verification above, recording commands and actual results.
- Add tests for todo creation, listing, invalid titles, and database failures.
- Add service readiness checks and database migrations.
- Add versioned image tags, a deployment workflow, and a rollback procedure.
- Add authentication, TLS, backups, and stronger secret management before expanding access.
- Explore monitoring, security testing, and k3s after the Compose deployment is verified.

For future journal entries, record the change, commands run, observed result, problem encountered, and next action. Mark planned work as pending rather than treating it as a completed experiment.

---

## 15. References

Project sources:

- [README and operating instructions](README.md)
- [Application routes](app/main.py) and [database connection](app/database.py)
- [Local Compose stack](compose.yaml) and [deployment override](compose.deploy.yaml)
- [CI workflow](.github/workflows/ci.yml)
- [Terraform configuration](terraform/main.tf) and [VM bootstrap](terraform/cloud-init.yaml)

Documentation links retained from the original setup journal:

- [Docker Engine installation](https://docs.docker.com/engine/install/ubuntu/)
- [Docker overview](https://docs.docker.com/get-started/docker-overview/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Git documentation](https://git-scm.com/docs)
- [FastAPI documentation](https://fastapi.tiangolo.com/)

---

## Stage 4 — Kubernetes: PostgreSQL Debugging

### Problem 1: PostgreSQL was Running but not accepting connections

**Symptoms:**

- Kubernetes showed the PostgreSQL Pod as `1/1 Running`.
- `/db-health` returned HTTP 500.
- `pg_isready` returned `no response`.
- PostgreSQL's startup process consumed almost 100% CPU.

**Investigation:**

- Inspected Pod status and Kubernetes Service endpoints.
- Checked PostgreSQL processes using `kubectl exec`.
- Inspected Linux kernel logs using `journalctl`.
- Found AppArmor `DENIED` messages involving process signals.
- Identified a suspected compatibility issue involving Ubuntu's kernel, AppArmor, and containerd.

**Temporary workaround:**

Configured the PostgreSQL container with:

```yaml
securityContext:
  appArmorProfile:
    type: Unconfined
```

After updating the Deployment, PostgreSQL began accepting connections.

**Security trade-off:** This disables AppArmor confinement for the PostgreSQL container. It is a temporary workaround for our local development cluster, not a production security configuration. A future improvement is to use a corrected containerd/AppArmor policy and restore confinement.

### Problem 2: Application database was missing

**Symptoms:**

- PostgreSQL accepted connections.
- FastAPI returned `FATAL: database "todo_db" does not exist`.

**Cause:**

The PostgreSQL data directory on the persistent volume had already been initialized without `todo_db`. PostgreSQL's initialization environment variables and SQL scripts only run when initializing an empty data directory.

**Resolution:**

Created `todo_db` using `psql`, then executed the existing `db/init.sql` to create the `todos` table.

**Final verification:**

- `/db-health` returned HTTP 200.
- `POST /todos` successfully created a Todo.
- `GET /todos` returned the saved Todo.

**Lesson learned:** A Kubernetes Pod showing `Running` does not guarantee the application inside it is healthy. Application readiness checks and careful log inspection are essential.

### Finding: Missing FastAPI Kubernetes Security Context

**Discovery:** Trivy configuration scan.

**Before:** 3 HIGH findings:
- KSV-0014: Writable container root filesystem.
- KSV-0118: Missing container security context.
- KSV-0118: Missing Pod security context.

**Risk:** A compromised container could have unnecessary privileges
and potentially modify files in its root filesystem.

**Fix:**
- Enforced non-root execution (UID 10001).
- Disabled privilege escalation.
- Enabled a read-only root filesystem.
- Dropped all Linux capabilities.
- Enabled the RuntimeDefault seccomp profile.

**Verification:**
- Kubernetes Deployment rollout succeeded.
- /health, /db-health, and /metrics returned HTTP 200.
- Trivy HIGH findings decreased from 3 to 0.

**Status:** Fixed and verified.

### Finding: PostgreSQL Pod Missing Security Context

**Discovery:** Trivy configuration scan, KSV-0118 (HIGH).

**Before:** PostgreSQL had no Pod-level security context.

**Risk:** Kubernetes used default security settings without an
explicit seccomp restriction.

**Fix:** Added `seccompProfile: RuntimeDefault` at the Pod level.

**Verification:**

- Kubernetes Deployment rollout succeeded.
- FastAPI `/db-health` confirmed PostgreSQL connectivity.
- Trivy HIGH findings decreased from 2 to 1.
- KSV-0118 was no longer reported.

**Status:** Fixed and verified.

**Remaining risk:** KSV-0014 (writable root filesystem).
Requires further testing before applying read-only restrictions.

### Finding: PostgreSQL Writable Root Filesystem

**Discovery:** Trivy configuration scan reported KSV-0014 (HIGH).

**Risk:** A writable root filesystem allows a compromised container process to modify more files than necessary.

**Initial test:** Enabled `readOnlyRootFilesystem: true` in an isolated PostgreSQL deployment. PostgreSQL crashed because it could not create a lock file in `/var/run/postgresql`.

**Root cause:** PostgreSQL requires writable directories for runtime files, even when its main filesystem is read-only.

**Fix:**

- Enabled `readOnlyRootFilesystem: true`.
- Kept persistent database storage mounted at `/var/lib/postgresql`.
- Added an `emptyDir` volume at `/var/run/postgresql` for runtime files.
- Added an `emptyDir` volume at `/tmp` for temporary files.

**Verification:**

- PostgreSQL Deployment rolled out successfully.
- PostgreSQL and FastAPI Pods were ready.
- Existing database data remained accessible (`SELECT COUNT(*) FROM todos;` returned 1).
- FastAPI `/db-health` returned `{"database":"connected"}`.
- Trivy reported 0 misconfigurations for `postgres-deployment.yaml`.

**Status:** Fixed and verified.

**Remaining limitation:** PostgreSQL retains `appArmorProfile: Unconfined` as a workaround for a local k3s/kernel compatibility issue. This must be revisited before production deployment.

### Finding: PostgreSQL Accessible from Unrelated Kubernetes Pods

**Discovery:** No NetworkPolicy existed in the `secure-cloud-api` namespace. A temporary BusyBox Pod successfully connected to the PostgreSQL Service on TCP port 5432.

**Evidence before fix:** `db (10.43.240.9:5432) open`

**Risk:** Unrelated or compromised Pods could reach PostgreSQL over the cluster network, increasing its attack surface.

**Fix:** Created `k8s/postgres-networkpolicy.yaml` to allow incoming TCP connections on port 5432 only from Pods labeled `app=fastapi` in the same namespace.

**Verification:**

- The unrelated `network-test` Pod's connection attempt failed with exit code 1.
- FastAPI `/db-health` still returned `{"database":"connected"}`.
- The NetworkPolicy was created successfully.

**Status:** Fixed and verified for the tested connection paths.

**Remaining limitation:** Access is controlled using Kubernetes Pod labels, not application authentication. PostgreSQL credentials remain necessary.

### Finding: Missing Kubernetes CPU and Memory Limits

**Discovery:** Inspected the resource configuration of the FastAPI and PostgreSQL Deployments using `kubectl`. Both returned `{}`, indicating that no CPU or memory requests or limits were configured.

**Risk:** Without resource limits, a malfunctioning or compromised container could consume excessive CPU or memory and affect other workloads on the Kubernetes node.

**Fix:**

- FastAPI: CPU request 100m, limit 500m; memory request 128Mi, limit 256Mi.
- PostgreSQL: CPU request 100m, limit 1000m; memory request 256Mi, limit 1Gi.

**Verification:**

- Both Kubernetes Deployments rolled out successfully.
- FastAPI `/db-health` returned `{"database":"connected"}`.
- `kubectl get deployments` confirmed that CPU and memory requests and limits were present.

**Status:** Fixed and verified for configuration and basic functionality.

**Remaining work:** Perform load testing and monitor actual memory usage to confirm that the selected limits are appropriate.

### Finding: Missing HTTP Request Body Size Limit

**Discovery:** A 10 MB JSON request to `POST /todos` returned HTTP 422, showing that field-length validation rejected the input but no HTTP request-body limit was demonstrated.

**Risk:** Excessively large requests may consume unnecessary CPU and memory, especially under concurrent traffic.

**Fix:** Added `RequestSizeLimitMiddleware` to enforce a 1 MiB request-body limit. The middleware checks both the declared `Content-Length` and the bytes actually received.

**Verification:**

- Local health endpoint: HTTP 200.
- Malformed JSON: HTTP 422.
- Oversized request: HTTP 413.
- All 6 automated tests passed, including the streamed-request test.
- GitHub Actions workflow succeeded.
- Kubernetes deployment succeeded.
- Deployed FastAPI health: HTTP 200.
- Deployed database health: HTTP 200.
- Deployed 10 MB request: HTTP 413.

**Status:** Fixed and verified.

### Finding: Missing API Rate Limiting

**Discovery:** Sent 200 sequential requests to `/health`. All 200 returned HTTP 200. No rate limit was triggered. Code review confirmed no rate-limiting mechanism was configured.

**Risk:** Excessive requests can consume server resources and reduce application availability.

**Fix:** Added SlowAPI rate limiting to `GET /todos` and `POST /todos`, configured for 60 requests per minute per client IP address. Health and monitoring endpoints remain unrestricted.

**Verification:**

- All 8 automated tests passed.
- GitHub Actions completed successfully.
- Updated FastAPI image deployed to Kubernetes.
- Sent 65 requests to `GET /todos`.
- Received 60 HTTP 200 responses and 5 HTTP 429 responses.

**Status:** Fixed and verified for the tested endpoint.

**Remaining limitations:** Rate-limit counters are stored in memory and are not shared across multiple replicas. IP-based identification may also require additional proxy configuration in production.

### Finding: Weak PostgreSQL Password

**Discovery:** Inspected Kubernetes Secret metadata using `kubectl describe secret`. The original PostgreSQL password contained only 6 bytes.

**Risk:** Short passwords may be easier to guess through brute-force or credential-guessing attacks.

**Fix:**

- Generated a cryptographically random 48-character password.
- Updated the PostgreSQL `todo_user` account password.
- Updated the existing Kubernetes Secret.
- Restarted FastAPI so it receives the updated credentials.

**Verification:**

- Kubernetes Secret now reports `POSTGRES_PASSWORD: 48 bytes`.
- FastAPI and PostgreSQL Pods are both `1/1 Running`.
- A later user-supplied record of the earlier terminal checks confirms that `GET /db-health` returned `{"database":"connected"}` and `GET /todos` returned both existing records after rotation (responses preserved below).

**Status:** Password rotation, database authentication, and access to existing Todo records verified through earlier interactive testing; the supplied API responses are preserved below. These checks were not rerun during the documentation update.

**Remaining limitation:** Kubernetes Secrets require appropriate RBAC and encryption-at-rest configuration for production use.

### Finding: Mutable Docker Image Tag

**Discovery:** The FastAPI Kubernetes Deployment referenced `ghcr.io/taha-khouildi/secure-cloud-api:latest`.

**Risk:** The `latest` tag can point to different image contents over time. Pod restarts could therefore deploy a different application version without an intentional configuration change.

**Fix:** Replaced the mutable tag with the exact SHA-256 image digest:

`sha256:df533118daac9271dd03e38c9d1489f8aac530a456f0976802d5e726dca4adad`

Set `imagePullPolicy: IfNotPresent` for the pinned image.

**Verification:**

- Kubernetes Deployment successfully updated.
- The running Deployment references the intended image digest.
- FastAPI `/db-health` returned `{"database":"connected"}`.

**Status:** Fixed and verified.

**Operational consideration:** Future application releases require intentionally updating the pinned digest.

### Accepted Risk: PostgreSQL AppArmor Unconfined

**Discovery:** PostgreSQL experienced startup problems with the default AppArmor configuration in the local k3s environment.

**Workaround:** Set `appArmorProfile: Unconfined` in the PostgreSQL container security context.

**Risk:** Disabling AppArmor confinement removes one layer of protection that could otherwise restrict a compromised PostgreSQL process.

**Compensating controls:**

- Read-only container root filesystem.
- Explicit writable volumes for database and runtime files.
- Seccomp `RuntimeDefault` profile.
- NetworkPolicy restricting PostgreSQL access to FastAPI Pods.
- CPU and memory limits.
- Strong PostgreSQL password.

**Status:** Accepted risk for the local development environment.

**Production requirement:** Investigate and resolve the underlying AppArmor compatibility problem, then enable an appropriate AppArmor profile before production deployment.

### Evidence supplement: Todo Records After Password Rotation

**Source:** User-supplied record of earlier terminal verification, incorporated during the documentation restructure. No new runtime checks were performed during this edit.

After password rotation from 6 to 48 bytes, `GET /db-health` returned:

```json
{"database":"connected"}
```

`GET /todos` returned:

```json
[
  {"id":1,"title":"Learned Kubernetes with k3s","completed":false},
  {"id":2,"title":"'; DROP TABLE todos; --","completed":false}
]
```

**Status:** Verified through earlier interactive testing. These supplied responses record successful authentication and access to both existing Todo records after rotation. They are not a newly captured terminal transcript.

### PostgreSQL Startup User and Remaining Hardening Limitation

**Source:** User-reported inspection from an earlier terminal session. The exact process listing and startup-script artifact were not supplied; repeatable verification is recommended.

**Observed:** `kubectl exec` used UID 0 by default, while the main PostgreSQL server process ran as the `postgres` user. The user reported inspecting the official image's root-then-`gosu` privilege-dropping startup behavior.

**Repository configuration:** The PostgreSQL manifest does not enforce `runAsNonRoot` or specify `runAsUser`. The entrypoint script is not stored in this repository.

**Status:** Previously inspected; this does not establish that the PostgreSQL server runs continuously as root. Enforced non-root container startup remains a hardening limitation alongside the accepted AppArmor risk. Compatibility with the image's initialization and mounted-volume permissions requires verification before changing the security context.

## Stage 5 — Earlier Monitoring Observations

**Evidence source:** User report of earlier interactive tests, added during the documentation restructure. No new monitoring checks were performed. Supporting screenshots, timestamped alert logs, and exported Loki query results were not preserved or supplied.

### FastAPIDown Alert Firing and Clearing

The user reported scaling the FastAPI Deployment to zero replicas and observing `FastAPIDown` transition from `PENDING` to `FIRING`. After restoring one replica, the alert returned to `INACTIVE`.

**Status:** Previously observed through interactive testing; supporting artifact not preserved. External alert notification is not verified and remains unimplemented in the documented setup.

### Loki Log Visibility

The user reported viewing logs from both FastAPI and PostgreSQL in Grafana through the Loki data source, with namespace, Pod, and container labels.

**Status:** Previously observed through interactive testing; supporting artifact not preserved. Repeat the query and save evidence for a reproducible record.

### Remaining Verification Work

- Fresh-cluster initialization is not verified; the recorded Kubernetes database setup required manual repair of an existing volume.
- ZAP and broader security testing have not been done; no results are recorded.
- Load testing and resource-limit suitability are not verified.
- The clean-clone Compose setup and full Azure application deployment with the current bootstrap are not verified in these notes.
- No authentication or TLS is implemented in the repository's API deployment.
