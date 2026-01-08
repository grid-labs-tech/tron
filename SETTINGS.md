# Settings Documentation

This document describes the available configuration keys that can be managed via the `/settings` endpoint in the API. Each configuration defines certain behaviors within the platform and can affect how the environment or workloads are deployed.

## Available Settings

| Key               | Description                                                       | Type    | Default | Example Value |
|-------------------|-------------------------------------------------------------------|---------|---------|---------------|
| `disable_workload`| Disables the feature workloads which defines hardware type        | boolean | `false` | `true`        |
| `max_replicas`    | Defines the max number of containers                              | boolean | `false` | `true`        |
