# Secure Cloud API — Development Notes

## Project Overview

**Project:** Secure Cloud API — DevSecOps Portfolio Project  
**Current stage:** Stage 1 — FastAPI + PostgreSQL + Docker Compose  
**Status:** Development environment ready; application not yet implemented.

### Project Goal

Build a small Todo REST API backed by PostgreSQL, then progressively deploy, automate, monitor, and secure it using Docker, Terraform, AWS, GitHub Actions, k3s, and security testing tools.

The project's main purpose is to demonstrate practical Cloud, DevOps, and Security engineering skills rather than complex application development.

### Completion Criteria for Stage 1

The application and PostgreSQL database must start successfully using `docker compose up` from a fresh Git clone, with setup instructions documented in `README.md`.

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

Later, GitHub will host the repository and GitHub Actions will automate testing and deployment.

---

## 4. Docker Installation

### Why Docker?

Docker packages an application with its dependencies into an image.

Containers created from that image can run in compatible environments without manually installing the application's dependencies on each machine.

For this project, Docker will run two separate services:

- FastAPI application.
- PostgreSQL database.

Docker Compose will manage them together.

### Installation Method

Chose Docker Engine from Docker's official APT repository instead of Snap or Ubuntu's `docker.io` package.

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

The repository must identify the correct Ubuntu codename:

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

### Completed

- [x] Installed Ubuntu alongside Windows
- [x] Verified CPU-independent system basics, RAM, and storage
- [x] Updated Ubuntu package information
- [x] Installed Git
- [x] Installed Docker Engine
- [x] Installed Docker Compose
- [x] Successfully executed `hello-world`
- [x] Diagnosed and fixed a Docker repository configuration error

### Not Yet Confirmed

- [ ] Configure Git author name and email
- [ ] Complete the Docker daemon failure experiment
- [ ] Initialize the project Git repository
- [ ] Create the initial FastAPI endpoint
- [ ] Connect FastAPI to PostgreSQL
- [ ] Create Dockerfile and Compose configuration
- [ ] Verify `docker compose up` from a fresh clone

---

## 9. Next Task

Create the project repository:

```bash
mkdir -p ~/projects/secure-cloud-api
cd ~/projects/secure-cloud-api
git init -b main
```

Create the initial structure:

```text
secure-cloud-api/
├── app/
│   └── main.py
├── README.md
├── notes.md
└── .gitignore
```

Then implement a minimal `/health` endpoint in FastAPI.

**Important:** Do not proceed to Terraform or AWS until Stage 1's reproducibility requirement has been satisfied.

---

## 10. References

- Docker Engine installation: https://docs.docker.com/engine/install/ubuntu/
- Docker overview: https://docs.docker.com/get-started/docker-overview/
- Docker Compose: https://docs.docker.com/compose/
- Git documentation: https://git-scm.com/docs
- FastAPI documentation: https://fastapi.tiangolo.com/
