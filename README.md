# FoodByte Restaurant Service

This repository contains the FastAPI application code for the **Restaurant Service** microservice, which serves as a core backend component of the broader FoodByte platform.

> [!WARNING]
> **DISCLAIMER**: This application is **by no means** a proper industry-standard software application. The application code here exists *strictly* as a vehicle to simulate a production DevOps and Platform Engineering workflow. Please do not evaluate the backend/frontend code for programming best practices; the true focus of this project is the underlying infrastructure, automated testing, GitOps orchestration, and deployment pipelines.

## Architecture & Microservices Context

FoodByte is distributed across several completely independent Git repositories. There is no hard link between them at the Git level. Instead, they are orchestrated via a declarative GitOps workflow where the central **[Helm Charts Repository](https://github.com/ansuman-satapathy/foodbyte-helm-charts)** acts as the definitive source of truth (the control plane) for the Kubernetes cluster state.

### Repository Map

- `github.com/ansuman-satapathy/foodbyte-user-service`       ← application code
- `github.com/ansuman-satapathy/foodbyte-restaurant-service` ← application code (**this repo**)
- `github.com/ansuman-satapathy/foodbyte-order-service`       ← application code
- `github.com/ansuman-satapathy/foodbyte-notification-service`← application code
- `github.com/ansuman-satapathy/foodbyte-frontend`            ← application code
- `github.com/ansuman-satapathy/foodbyte-helm-charts`         ← **THE control repo** (Flux watches this)
- `github.com/ansuman-satapathy/foodbyte-infra`               ← Infrastructure definition

## GitOps CI/CD Delivery Flow

This microservice does **not** push deployments to the cluster directly. Deployments are handled asynchronously, powered by Flux CD viewing the `foodbyte-helm-charts` configuration.

The fully automated delivery flow operates as follows:

1. You push new code to the `foodbyte-restaurant-service` repository.
2. GitHub Actions CI automatically triggers — it lints, tests, builds the new Docker image, and pushes it to your GHCR registry with the image tag set as the `git commit SHA`.
3. The CI pipeline then opens a PR (or auto-commits) on `foodbyte-helm-charts`, updating the specific `image.tag` contained in the `values.yaml` for the Restaurant Service.
4. **Flux CD** detects the configuration change in the `helm-charts` repository.
5. Flux applies the newly specified Helm release securely into the Kubernetes cluster.
6. **Done.** There are absolutely no manual steps required and no manual `kubectl apply` commands needed. The cluster automatically converges to the declarative state mapped in the Helm charts.
