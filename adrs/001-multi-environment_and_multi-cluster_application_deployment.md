# ADR - Multi-Environment and Multi-Cluster Application Deployment Architecture

## Context

This architecture is designed to manage and deploy applications across multiple environments and Kubernetes clusters. The system supports three types of applications: Webapp, Worker, and Cronjob. Each with distinct deployment requirements. The platform operates as a multi-cluster system, where each Kubernetes cluster is associated with a single logical environment, allowing for organized, environment-specific deployments.

## Decision

The decision is to create an architecture that defines "environments" as logical units associated with Kubernetes clusters for deploying resources. Each deployment (representing an application in a particular environment) may have multiple instances across clusters within that environment.

## Key Concepts

### Environment
- An environment is a logical unit defining where resources will be deployed.
- Environments align with clusters, meaning each Kubernetes cluster is associated with a single, unique environment.

### Application Types
Applications on the platform can be of the following types:
- **Webapp**: Applications that are accessed primarily via web interfaces.
- **Worker**: Applications that perform background processing tasks.
- **Cronjob**: Applications that run scheduled tasks.

### Deploy
- Each application has a corresponding deploy for each environment.
- A deploy comprises the set of definitions and configurations required for that specific environment.

> Do not confuse the concept of platform deploy with Kubernetes deployment

### Multi-Cluster Platform
- The platform supports multiple clusters, each linked to an environment.
- Each deploy can have one or more "instances," representing the concrete instantiation of a deploy within a cluster.

## Consequences

- **Environment-specific Deployments**: The clear separation of environments ensures that each deploy is isolated to its designated environment, enhancing operational clarity and resource organization.
- **Multi-Cluster Flexibility**: The multi-cluster structure allows application to scale across clusters, providing redundancy and load distribution.
- **Application-Type Specific Configuration**: By defining applications as Webapp, Worker, or Cronjob, each application type can follow optimized deploy configurations, ensuring better performance and maintainability.

## Alternatives Considered

1. **Single-Cluster Per Application Type**: This option was rejected as it limits scalability and does not offer enough isolation between environments.
2. **Environment-Agnostic Deploy**: This was dismissed since environment-specific configurations are critical for ensuring that applications behave correctly under different conditions and that resources are optimized.

## Decision Status

**Accepted**

This architecture provides a scalable, organized, and manageable deployment strategy across multiple environments and clusters, accommodating diverse application types with specific operational requirements.

## Implementation Notes

- Each application will be assigned to an environment and deployed to its corresponding Kubernetes cluster(s).
- Instances of deployments will be managed and monitored per cluster, ensuring alignment with environment-specific requirements.
- Further documentation on Kubernetes configurations and deployment strategies per application type will be provided as the system is implemented.

---

**Date**: 2024-11-02
**Authors**: Diogo Munhoz Fraga
