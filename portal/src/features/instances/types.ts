import type { Application } from '../applications/types'
import type { Environment } from '../environments/types'

export interface InstanceComponent {
  uuid: string
  name: string
  type: string
  settings: Record<string, any> | null
  url: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface Instance {
  uuid: string
  application: Application
  environment: Environment
  components: InstanceComponent[]
  image: string
  version: string
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface InstanceCreate {
  application_uuid: string
  environment_uuid: string
  image: string
  version: string
  enabled?: boolean
}

export interface KubernetesEventInvolvedObject {
  kind: string | null
  name: string | null
  namespace: string | null
}

export interface KubernetesEventSource {
  component: string | null
  host: string | null
}

export interface KubernetesEvent {
  name: string
  namespace: string
  type: string // Normal, Warning
  reason: string
  message: string
  involved_object: KubernetesEventInvolvedObject
  source: KubernetesEventSource
  first_timestamp: string | null
  last_timestamp: string | null
  count: number
  age_seconds: number
}
