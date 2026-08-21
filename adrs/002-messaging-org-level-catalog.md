# ADR - Messaging as an Organization-Level Catalog with Ownership

## Context

A topic is consumed by N applications, so messaging needs clear ownership of who may publish and who may consume. Nesting these resources under a single Application makes that hard to see and govern across teams.

The platform already deploys workloads via Jinja templates and Kubernetes. Messaging should reuse that orchestration pattern, with **Crossplane** provisioning SNS/SQS on AWS, while the Tron Portal owns the catalog, ownership rules, and associations.

## Decision

Messaging is a **first-class domain** in Tron — an **organization-level catalog** of Topics, Queues, and consumer associations — with mandatory **owner application** (= sole publisher), explicit **consumer** associations on Topics, and provisioning via **templates → Crossplane → SNS/SQS**.

Tron is the **orchestrator**, not the message broker. Applications publish to SNS and consume from SQS.

## Key Concepts

### Messaging ≠ Application

| Applications (ADR 001) | Messaging |
| --- | --- |
| Webapp, worker, cron — workloads of an app | Queue, Topic, Subscription — integration infra |
| Live under Application / Instance | Live in the **organization catalog** |
| A resource “belongs” to one app | A Topic has **1 publisher (owner)** and **N consumers** |

Application / Instance screens may offer **shortcuts** (create Topic/Queue, Subscribe to Topic) with owner/environment pre-filled, but the resource itself always lives in the Messaging catalog.

### Topic (SNS)

- Catalog resource that provisions an SNS Topic.
- **Owner** is the producing app and the **only publisher**.
- Consumers attach via explicit **consumer associations**, always materialized as **SNS → SQS**.
- **Visibility**: **private** (only owner may create consumer associations) or **global** (other apps in the org may subscribe).
- Unique name: `(organization_id, environment_id, name)`.

### Queue (SQS)

- Catalog resource that provisions an SQS Queue (optional DLQ).
- **Owner-only** produce/consume — no cross-app producer/consumer associations on the Queue itself.
- May be the **SQS destination** of a Topic subscriber (Queue owned by the subscribing app).
- Unique name: `(organization_id, environment_id, name)`.

### Subscription / Association (consumer binding)

- Binds a consumer app to a Topic; Tron materializes SNS Subscription + consumer SQS Queue policies.
- Destination Queue must be owned by the subscriber and share the Topic’s `environment_id`.
- Optional SNS filter policies: prefer **message attributes** (free); payload/body filters supported when needed (paid scan).
### Ownership and MVP product rules

| Principle | Decision |
| --- | --- |
| Scope | Organization catalog (`messaging_topics`, `messaging_queues`, `messaging_associations`) |
| Ownership | Every Topic/Queue has a required **owner application** |
| Publish | Only the owner publishes. No cross-app `publisher` association in the MVP |
| Queue | Owner-only produce/consume; may be the SQS destination of a Topic subscriber |
| Consume | Explicit **consumer** association on a Topic; SQS-only (`queue_uuid`) |
| Isolation | Topic and destination Queue must share `environment_id` |
| Provisioning | Templates → Crossplane Managed Resources. Region and `ClusterProviderConfig` come from the **environment Crossplane config**, not from Topic/Queue settings |

### Crossplane configuration (platform prerequisite)

Before syncing Messaging resources, platform admins configure Crossplane **per environment** (separate from Application deploy and from the Messaging catalog payload):

- Enable Crossplane for the environment and designate a **fixed Kubernetes cluster** for messaging sync (not the workload/least-load cluster).
- Provide **AWS region** and **provider config** as explicit operator inputs (no inference from cluster `api_address`).
- Mark clusters as eligible for messaging sync when appropriate.
- Topic/Queue create payloads do **not** carry `region` / `provider_config`; those are inherited from the environment.

## Consequences

- The Messaging catalog answers **who owns (publishes)** and **who consumes**.
- Multi-publisher Topics and queue-level cross-app produce/consume stay **out of MVP**.
- Application types remain webapp / worker / cron (ADR 001).
- Messaging reuses the platform template pipeline; Crossplane focuses first on SNS/SQS and can later enable other AWS resources (RDS, Redis, S3, etc.).
- UX shortcuts on Application screens preserve discoverability without nesting resources under an Application.

## Alternatives Considered

1. **Keep Queue/Topic as application components**: Rejected. A Topic consumed by N apps becomes “stuck” under one Application and hides ownership.
2. **Organization catalog without strong ownership**: Rejected. Without a mandatory owner (= sole publisher) and explicit consumer associations, publish/consume rights stay opaque.
3. **Region / provider on each Topic or Queue**: Rejected. Crossplane sync uses a fixed cluster and AWS settings per environment to avoid orphaned Managed Resources and inconsistent regions.

## Decision Status

**Accepted**

Messaging is an organization-level catalog with mandatory ownership and consumer associations, provisioned through Tron’s template + Crossplane path to SNS/SQS, while Application types stay as defined in ADR 001.

## Implementation Notes

- Portal: dedicated Messaging domain (Topics, Queues, Associations) plus Application shortcuts for create/subscribe.
- API/DB: org-scoped catalog entities with required owner; Topic consumer associations only; environment isolation and unique names as above.
- Sync: resolve Crossplane context from the environment; render Jinja templates; apply Upbound Managed Resources (`Queue`, `Topic`, `TopicSubscription`) on the environment’s Crossplane cluster.
- Governance: IAM/SNS policies and tags derived from owner (publish) + consumer associations.

---

**Date**: 2026-08-19  
**Authors**: Flavio Andrade  

## References

- ADR 001 — Multi-Environment and Multi-Cluster Application Deployment Architecture
