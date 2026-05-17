# FoodByte Restaurant Service

This repository contains the FastAPI application code for the **Restaurant Service** microservice, which manages restaurant data and menu information within the FoodByte platform.

> [!WARNING]
> **DISCLAIMER**: This application is **by no means** a proper industry-standard software application. The application code here exists *strictly* as a vehicle to simulate a production DevOps and Platform Engineering workflow. Please do not evaluate the backend/frontend code for programming best practices; the true focus of this project is the underlying infrastructure, automated testing, GitOps orchestration, and deployment pipelines.

## Architecture & Microservices Context

FoodByte is distributed across several independent Git repositories. They are orchestrated via a declarative GitOps workflow where the **[GitOps Repository](https://github.com/ansuman-satapathy/foodbyte-gitops)** acts as the definitive source of truth for the Kubernetes cluster state.

### Repository Map

- `github.com/ansuman-satapathy/foodbyte-restaurant-service`  ← application code (**this repo**)
- `github.com/ansuman-satapathy/foodbyte-user-service`        ← application code
- `github.com/ansuman-satapathy/foodbyte-order-service`       ← application code
- `github.com/ansuman-satapathy/foodbyte-notification-service` ← application code
- `github.com/ansuman-satapathy/foodbyte-frontend`             ← application code
- `github.com/ansuman-satapathy/foodbyte-gitops`               ← **THE control repo** (Flux watches this)
- `github.com/ansuman-satapathy/foodbyte-helm-charts`          ← Blueprint library
- `github.com/ansuman-satapathy/foodbyte-infra`                ← Infrastructure definition (Terraform)

## GitOps CI/CD Delivery Flow

This microservice does not push deployments to the cluster directly. Deployments are handled asynchronously, powered by the Flux Operator viewing the `foodbyte-gitops` configuration.

The automated delivery flow operates as follows:

1. Code is pushed to the `foodbyte-restaurant-service` repository.
2. GitHub Actions CI triggers a build, test, and push sequence to GHCR.
3. The image tag is updated in the corresponding Helm release within the `foodbyte-gitops` repository.
4. The Flux Operator detects the configuration change in the GitOps repository.
5. Flux reconciles the cluster to match the new state by pulling the latest blueprint from the `foodbyte-helm-charts` repository.
6. The cluster automatically converges to the declarative state without manual intervention.
