import json

from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from fastapi import HTTPException


K8S_API_MAPPING = {
    "Deployment": (
        client.AppsV1Api,
        "create_namespaced_deployment",
        "delete_namespaced_deployment",
        "replace_namespaced_deployment",
    ),
    "Service": (
        client.CoreV1Api,
        "create_namespaced_service",
        "delete_namespaced_service",
        "replace_namespaced_service",
    ),
    "ConfigMap": (
        client.CoreV1Api,
        "create_namespaced_config_map",
        "delete_namespaced_config_map",
        "replace_namespaced_config_map",
    ),
    "Secret": (
        client.CoreV1Api,
        "create_namespaced_secret",
        "delete_namespaced_secret",
        "replace_namespaced_secret",
    ),
    "Ingress": (
        client.NetworkingV1Api,
        "create_namespaced_ingress",
        "delete_namespaced_ingress",
        "replace_namespaced_ingress",
    ),
    "HorizontalPodAutoscaler": (
        client.AutoscalingV2Api,
        "create_namespaced_horizontal_pod_autoscaler",
        "delete_namespaced_horizontal_pod_autoscaler",
        "replace_namespaced_horizontal_pod_autoscaler",
    ),
    "CronJob": (
        client.BatchV1Api,
        "create_namespaced_cron_job",
        "delete_namespaced_cron_job",
        "replace_namespaced_cron_job",
    ),
}


class K8sClient:
    def __init__(self, url: str, token: str, verify_ssl: bool = False):
        """
        Initialize the Kubernetes client with the provided parameters.
        """
        self.configuration = client.Configuration()
        self.configuration.host = url
        self.configuration.verify_ssl = verify_ssl
        self.configuration.api_key = {"authorization": f"Bearer {token}"}
        self.api_client = client.ApiClient(self.configuration)
        self.api_client = client.ApiClient(self.configuration)

    def validate_connection(self):
        """
        Validate the connection to Kubernetes by attempting to list namespaces.
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            v1.list_namespace()
            message = {"status": "ok", "message": "connected"}
            return (True, message)
        except ApiException as e:
            print(e.body)
            try:
                error_body = json.loads(e.body) if e.body else {}
                error_message = (
                    error_body.get("message", str(e.body))
                    if isinstance(error_body, dict)
                    else str(e.body)
                )
            except (json.JSONDecodeError, AttributeError):
                error_message = str(e.body) if e.body else str(e)
            message = {
                "status": "error",
                "message": {"code": str(e.status), "message": error_message},
            }
            return (False, message)

    def get_namespaces(self):
        """
        Return a list of namespaces from the Kubernetes cluster.
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            return v1.list_namespace().items
        except ApiException as e:
            print(f"Error listing namespaces: {e}")
            return []

    def create_namespace(self, name: str):
        """
        Create a new namespace in the Kubernetes cluster.
        """
        body = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))
        try:
            v1 = client.CoreV1Api(self.api_client)
            return v1.create_namespace(body=body)
        except ApiException as e:
            print(f"Error creating namespace: {e}")
            return None

    def get_available_cpu(self):
        """
        Return the total amount of CPU available in the Kubernetes cluster.
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            nodes = v1.list_node().items

            total_cpu = 0
            for node in nodes:
                cpu_capacity = node.status.capacity["cpu"]
                total_cpu += int(cpu_capacity)

            return total_cpu
        except ApiException as e:
            print(f"Error getting available CPU amount: {e}")
            return None

    def get_available_memory(self):
        """
        Get the amount of memory available in the Kubernetes cluster.
        """
        v1 = client.CoreV1Api(self.api_client)
        nodes = v1.list_node().items

        total_memory = 0
        total_allocated_memory = 0

        for node in nodes:
            node_memory = node.status.allocatable.get("memory")
            if node_memory:
                total_memory += int(node_memory[:-2])
            node_allocated_memory = node.status.capacity.get("memory")
            if node_allocated_memory:
                total_allocated_memory += int(node_allocated_memory[:-2])

        available_memory = total_memory - total_allocated_memory
        return available_memory

    def ensure_namespace_exists(self, namespace_name):
        """
        Create the namespace if it does not exist.

        SECURITY:
        - Protected namespaces (kube-system, etc.) cannot be created
        - This method allows creation of any namespace because:
          1. New apps use tron-ns-* prefix (secure by design)
          2. Legacy apps have their namespace stored in the database
             and are already validated at the application layer
        """
        from app.shared.config import is_namespace_protected, ProtectedNamespaceError

        # Check if namespace is protected - we shouldn't try to create it
        if is_namespace_protected(namespace_name):
            raise ProtectedNamespaceError(namespace_name, "create")

        v1 = client.CoreV1Api(self.api_client)
        try:
            v1.read_namespace(name=namespace_name)
        except ApiException as e:
            if e.status == 404:
                namespace_metadata = client.V1ObjectMeta(name=namespace_name)
                namespace_body = client.V1Namespace(metadata=namespace_metadata)
                v1.create_namespace(body=namespace_body)
            else:
                raise e

    def delete_namespace(self, namespace_name, is_legacy_namespace: bool = False):
        """
        Delete a namespace from Kubernetes.
        When a namespace is deleted, all resources within it are automatically deleted.

        SECURITY: This method has TWO layers of protection:
        1. Protected namespaces (kube-system, etc.) cannot be deleted
        2. Only namespaces with 'tron-ns-' prefix OR legacy namespaces can be deleted

        Args:
            namespace_name: The namespace to delete
            is_legacy_namespace: If True, allows deletion of legacy namespaces
                                 (pre-v0.6 apps that don't have tron-ns- prefix).
                                 This should ONLY be set by the application deletion
                                 service when the namespace is registered in the database.
        """
        from app.shared.config import (
            is_namespace_protected,
            is_tron_managed_namespace,
            ProtectedNamespaceError,
            NotTronManagedNamespaceError,
        )

        # SECURITY CHECK 1: Protected namespaces NEVER can be deleted
        if is_namespace_protected(namespace_name):
            raise ProtectedNamespaceError(namespace_name, "delete")

        # SECURITY CHECK 2: Only Tron-managed namespaces (tron-ns-*) can be deleted
        # Exception: Legacy namespaces (pre-v0.6) can be deleted if explicitly flagged
        if not is_tron_managed_namespace(namespace_name) and not is_legacy_namespace:
            raise NotTronManagedNamespaceError(namespace_name)

        v1 = client.CoreV1Api(self.api_client)
        try:
            v1.delete_namespace(name=namespace_name, body=client.V1DeleteOptions())
        except ApiException as e:
            if e.status == 404:
                # Namespace already does not exist, not an error
                return
            else:
                raise e

    def delete_pod(self, namespace: str, pod_name: str):
        """
        Delete a specific pod from Kubernetes.

        Args:
            namespace: Namespace name
            pod_name: Pod name

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            v1.delete_namespaced_pod(
                name=pod_name, namespace=namespace, body=client.V1DeleteOptions()
            )
            return True
        except ApiException as e:
            if e.status == 404:
                # Pod already does not exist, not an error
                return True
            else:
                print(f"Error deleting pod {pod_name}: {e}")
                raise e

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        container_name: str = None,
        tail_lines: int = 100,
        follow: bool = False,
    ):
        """
        Get logs from a Kubernetes pod.

        Args:
            namespace: Namespace name
            pod_name: Pod name
            container_name: Container name (optional, if pod has multiple containers)
            tail_lines: Number of tail lines to return (default: 100)
            follow: If True, follow logs in real time (default: False)

        Returns:
            String with pod logs
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                tail_lines=tail_lines,
                follow=follow,
                _preload_content=False,
            )
            return logs.read().decode("utf-8")
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found")
            else:
                print(f"Error getting pod logs {pod_name}: {e}")
                raise HTTPException(
                    status_code=e.status, detail=f"Failed to get logs: {str(e)}"
                )

    def exec_pod_command(
        self,
        namespace: str,
        pod_name: str,
        command: list[str],
        container_name: str = None,
    ):
        """
        Execute a command in a Kubernetes pod.

        Args:
            namespace: Namespace name
            pod_name: Pod name
            command: List with command and arguments (e.g., ['ls', '-la'])
            container_name: Container name (optional, if pod has multiple containers)

        Returns:
            Tuple (stdout, stderr, return_code)
        """
        try:
            v1 = client.CoreV1Api(self.api_client)

            # Execute command using stream
            exec_command = stream(
                v1.connect_get_namespaced_pod_exec,
                pod_name,
                namespace,
                command=command,
                container=container_name,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            stdout = ""
            stderr = ""

            while exec_command.is_open():
                exec_command.update(timeout=1)
                if exec_command.peek_stdout():
                    stdout += exec_command.read_stdout()
                if exec_command.peek_stderr():
                    stderr += exec_command.read_stderr()

            exec_command.close()

            return {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": 0 if not stderr else 1,
            }
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found")
            else:
                print(f"Error executing command in pod {pod_name}: {e}")
                raise HTTPException(
                    status_code=e.status, detail=f"Failed to execute command: {str(e)}"
                )
        except Exception as e:
            print(f"Error executing command in pod {pod_name}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to execute command: {str(e)}"
            )

    def cleanup_orphaned_gateway_resources(
        self, namespace: str, component_name: str, expected_resources: list
    ):
        """
        Remove Gateway API resources (HTTPRoute, TCPRoute, UDPRoute) that should no longer exist.

        Args:
            namespace: Namespace where resources are located
            component_name: Component name
            expected_resources: List of dictionaries with expected resources (rendered from templates)
        """
        # Identify which Gateway API resources should exist
        expected_gateway_kinds = set()
        for resource in expected_resources:
            if resource and isinstance(resource, dict):
                kind = resource.get("kind")
                api_version = resource.get("apiVersion", "")
                # Check if it is a Gateway API resource
                if (
                    kind in ["HTTPRoute", "TCPRoute", "UDPRoute"]
                    and "gateway.networking.k8s.io" in api_version
                ):
                    expected_gateway_kinds.add(kind)

        # List of Gateway API resources that may exist
        gateway_resources = [
            ("HTTPRoute", "gateway.networking.k8s.io/v1", "httproutes"),
            ("TCPRoute", "gateway.networking.k8s.io/v1alpha2", "tcproutes"),
            ("UDPRoute", "gateway.networking.k8s.io/v1alpha2", "udproutes"),
        ]

        # For each Gateway API resource type, check if it should exist
        for kind, api_version, resource_name in gateway_resources:
            # If not in expected list, try to delete if it exists
            if kind not in expected_gateway_kinds:
                try:
                    # Try to delete the resource if it exists
                    api_parts = api_version.split("/")
                    api_group = api_parts[0]
                    api_version_part = api_parts[1]
                    api_path = f"/apis/{api_group}/{api_version_part}/namespaces/{namespace}/{resource_name}/{component_name}"

                    self.api_client.call_api(
                        api_path,
                        "DELETE",
                        body=client.V1DeleteOptions(),
                        auth_settings=["BearerToken"],
                        response_type="object",
                        _preload_content=True,
                    )
                    print(
                        f"Deleted orphaned {kind} '{component_name}' from namespace '{namespace}'"
                    )
                except ApiException as e:
                    if e.status == 404:
                        # Resource does not exist, that's fine
                        pass
                    else:
                        # Log but don't fail - not critical
                        print(
                            f"Warning: Could not delete {kind} '{component_name}': {e}"
                        )

    def apply_or_delete_yaml_to_k8s(self, yaml_documents, operation="create"):
        # For upsert operations, clean up orphaned Gateway API resources before applying
        if operation == "upsert":
            # Collect information from documents to identify namespace and component_name
            namespace = None
            component_name = None

            # First search for Gateway API resources to get the correct name
            for doc in yaml_documents:
                if doc and isinstance(doc, dict):
                    kind = doc.get("kind")
                    api_version = doc.get("apiVersion", "")
                    metadata = doc.get("metadata", {})

                    # If it's a Gateway API resource, use that name
                    if (
                        kind in ["HTTPRoute", "TCPRoute", "UDPRoute"]
                        and "gateway.networking.k8s.io" in api_version
                    ):
                        component_name = metadata.get("name")
                        namespace = metadata.get("namespace")
                        if namespace and component_name:
                            break

            # If not found in Gateway API resources, search in any document
            if not (namespace and component_name):
                for doc in yaml_documents:
                    if doc and isinstance(doc, dict) and doc.get("metadata"):
                        metadata = doc.get("metadata", {})
                        namespace = metadata.get("namespace")
                        component_name = metadata.get("name")
                        if namespace and component_name:
                            break

            # If found namespace and component_name, clean up orphaned resources
            if namespace and component_name:
                try:
                    self.cleanup_orphaned_gateway_resources(
                        namespace, component_name, yaml_documents
                    )
                except Exception as e:
                    # Log but don't fail - not critical
                    print(f"Warning: Could not cleanup orphaned Gateway resources: {e}")

        for document in yaml_documents:
            # Skip None or invalid documents (when template doesn't render anything)
            if document is None or not isinstance(document, dict):
                continue

            kind = document.get("kind")
            api_version = document.get("apiVersion")
            metadata = document.get("metadata")

            # Verificar se metadata existe
            if not metadata or not isinstance(metadata, dict):
                continue

            name = metadata.get("name")
            namespace = metadata.get("namespace")

            if not namespace:
                raise ValueError("Namespace not specified in the YAML file")

            try:
                self.ensure_namespace_exists(namespace)
            except Exception as e:
                raise e

            if not kind or not api_version:
                raise ValueError("YAML must include 'kind' and 'apiVersion' fields.")

            api_mapping = K8S_API_MAPPING.get(kind)

            # If resource is not in default mapping, use REST API directly
            # This is necessary for custom resources like Gateway API (HTTPRoute, TCPRoute, UDPRoute)
            if not api_mapping:
                # Extract API group and version from apiVersion
                # Format: group/version (e.g., gateway.networking.k8s.io/v1)
                # or just version for core APIs (e.g., v1)
                api_parts = api_version.split("/")
                if len(api_parts) == 2:
                    api_group, api_version_part = api_parts
                else:
                    # Core API (e.g., v1)
                    api_group = ""
                    api_version_part = api_version

                # Convert kind to resource name in API path
                # Gateway API uses lowercase plural: HTTPRoute -> httproutes, TCPRoute -> tcproutes
                def kind_to_resource_name(kind_str):
                    """Convert a Kind to the resource name in the API path"""
                    # Convert to lowercase
                    lower = kind_str.lower()
                    # Add 's' if it doesn't end with 's'
                    if not lower.endswith("s"):
                        return lower + "s"
                    return lower

                resource_name = kind_to_resource_name(kind)

                # Determine API path based on group
                if api_group:
                    # Custom API: /apis/{group}/{version}/namespaces/{namespace}/{resource}/{name}
                    api_path_base = f"/apis/{api_group}/{api_version_part}/namespaces/{namespace}/{resource_name}"
                else:
                    # Core API: /api/{version}/namespaces/{namespace}/{resource}/{name}
                    api_path_base = f"/api/{api_version_part}/namespaces/{namespace}/{resource_name}"

                # Apply using REST API directly
                try:
                    if operation == "create":
                        # POST to create
                        self.api_client.call_api(
                            api_path_base,
                            "POST",
                            body=document,
                            auth_settings=["BearerToken"],
                            response_type="object",
                            _preload_content=True,
                        )
                    elif operation == "update":
                        # PUT to update - need to get resourceVersion first
                        # Retry up to 3 times for 409 Conflict errors
                        max_retries = 3
                        for retry in range(max_retries):
                            try:
                                # Read existing resource to get resourceVersion
                                existing_response = self.api_client.call_api(
                                    f"{api_path_base}/{name}",
                                    "GET",
                                    auth_settings=["BearerToken"],
                                    response_type="object",
                                    _preload_content=True,
                                )
                                existing_resource = (
                                    existing_response[0]
                                    if isinstance(existing_response, tuple)
                                    else existing_response
                                )

                                # Include resourceVersion in document if it exists
                                if existing_resource and "metadata" in existing_resource:
                                    existing_metadata = existing_resource["metadata"]
                                    if "resourceVersion" in existing_metadata:
                                        if "metadata" not in document:
                                            document["metadata"] = {}
                                        document["metadata"]["resourceVersion"] = (
                                            existing_metadata["resourceVersion"]
                                        )

                                # PUT to update
                                self.api_client.call_api(
                                    f"{api_path_base}/{name}",
                                    "PUT",
                                    body=document,
                                    auth_settings=["BearerToken"],
                                    response_type="object",
                                    _preload_content=True,
                                )
                                break  # Success, exit retry loop
                            except ApiException as e:
                                if e.status == 409 and retry < max_retries - 1:
                                    # Conflict error - resourceVersion changed
                                    # Retry with fresh resourceVersion
                                    import time

                                    time.sleep(0.1 * (retry + 1))  # Backoff
                                    continue
                                elif e.status == 404:
                                    # Resource doesn't exist, can't update
                                    raise e
                                else:
                                    raise e
                    elif operation == "upsert":
                        # Try to update first, if it doesn't exist, create
                        # Retry up to 3 times for 409 Conflict errors (resourceVersion mismatch)
                        max_retries = 3
                        for retry in range(max_retries):
                            try:
                                # Read existing resource to get resourceVersion
                                existing_response = self.api_client.call_api(
                                    f"{api_path_base}/{name}",
                                    "GET",
                                    auth_settings=["BearerToken"],
                                    response_type="object",
                                    _preload_content=True,
                                )
                                existing_resource = (
                                    existing_response[0]
                                    if isinstance(existing_response, tuple)
                                    else existing_response
                                )

                                # Include resourceVersion in document if it exists
                                if existing_resource and "metadata" in existing_resource:
                                    existing_metadata = existing_resource["metadata"]
                                    if "resourceVersion" in existing_metadata:
                                        if "metadata" not in document:
                                            document["metadata"] = {}
                                        document["metadata"]["resourceVersion"] = (
                                            existing_metadata["resourceVersion"]
                                        )

                                # PUT to update
                                self.api_client.call_api(
                                    f"{api_path_base}/{name}",
                                    "PUT",
                                    body=document,
                                    auth_settings=["BearerToken"],
                                    response_type="object",
                                    _preload_content=True,
                                )
                                break  # Success, exit retry loop
                            except ApiException as e:
                                if e.status == 404:
                                    # Resource does not exist, create
                                    self.api_client.call_api(
                                        api_path_base,
                                        "POST",
                                        body=document,
                                        auth_settings=["BearerToken"],
                                        response_type="object",
                                        _preload_content=True,
                                    )
                                    break  # Success, exit retry loop
                                elif e.status == 409 and retry < max_retries - 1:
                                    # Conflict error - resourceVersion changed
                                    # Retry with fresh resourceVersion
                                    import time

                                    time.sleep(0.1 * (retry + 1))  # Backoff
                                    continue
                                else:
                                    raise e
                    elif operation == "delete":
                        # DELETE to remove
                        try:
                            self.api_client.call_api(
                                f"{api_path_base}/{name}",
                                "DELETE",
                                body=client.V1DeleteOptions(),
                                auth_settings=["BearerToken"],
                                response_type="object",
                                _preload_content=True,
                            )
                        except ApiException as e:
                            if e.status == 404:
                                # Resource already does not exist, that's acceptable
                                pass
                            else:
                                raise e
                except ApiException as e:
                    raise HTTPException(
                        status_code=e.status,
                        detail=f"Failed to {operation} {kind} '{name}': {str(e)}",
                    )
            else:
                # Use default mapping for known resources
                api_class, create_method, delete_method, replace_method = api_mapping

                api_instance = api_class(self.api_client)

                if operation == "create":
                    getattr(api_instance, create_method)(
                        namespace=namespace, body=document
                    )
                elif operation == "update":
                    getattr(api_instance, replace_method)(
                        name=name, namespace=namespace, body=document
                    )
                elif operation == "upsert":
                    # Try to update first, if it doesn't exist, create
                    try:
                        # For Deployments, preserve current replica count if not specified
                        if kind == "Deployment" and "spec" in document:
                            try:
                                read_method = getattr(
                                    api_instance, "read_namespaced_deployment", None
                                )
                                if read_method:
                                    existing_deployment = read_method(
                                        name=name, namespace=namespace
                                    )

                                    # If new document doesn't specify replicas, preserve current value
                                    # This prevents Kubernetes from resetting to default (1) or conflicting with HPA
                                    if "replicas" not in document.get("spec", {}):
                                        if (
                                            hasattr(
                                                existing_deployment.spec, "replicas"
                                            )
                                            and existing_deployment.spec.replicas
                                            is not None
                                        ):
                                            document["spec"]["replicas"] = (
                                                existing_deployment.spec.replicas
                                            )

                                    # Also preserve resourceVersion and other necessary metadata to avoid conflicts
                                    # resourceVersion is necessary for replace to work correctly
                                    if (
                                        hasattr(
                                            existing_deployment.metadata,
                                            "resource_version",
                                        )
                                        and existing_deployment.metadata.resource_version
                                    ):
                                        if "metadata" not in document:
                                            document["metadata"] = {}
                                        document["metadata"]["resourceVersion"] = (
                                            existing_deployment.metadata.resource_version
                                        )

                                        # Also preserve generation if it exists
                                        if (
                                            hasattr(
                                                existing_deployment.metadata,
                                                "generation",
                                            )
                                            and existing_deployment.metadata.generation
                                        ):
                                            document["metadata"]["generation"] = (
                                                existing_deployment.metadata.generation
                                            )
                            except ApiException as read_e:
                                # If can't read (404 or other error), continue normally
                                # This means the deployment doesn't exist yet, so we'll create it
                                if read_e.status != 404:
                                    # If it's another error, log but continue
                                    print(
                                        f"Warning: Could not read existing deployment to preserve replicas: {read_e}"
                                    )

                        getattr(api_instance, replace_method)(
                            name=name, namespace=namespace, body=document
                        )
                    except ApiException as e:
                        if e.status == 404:
                            # Resource does not exist, create
                            getattr(api_instance, create_method)(
                                namespace=namespace, body=document
                            )
                        else:
                            raise e
                elif operation == "delete":
                    try:
                        getattr(api_instance, delete_method)(
                            name=name,
                            namespace=namespace,
                            body=client.V1DeleteOptions(),
                        )
                    except ApiException as e:
                        if e.status == 404:
                            # Resource already does not exist in Kubernetes, that's acceptable
                            # The goal is to delete and if it doesn't exist, we consider it success
                            pass
                        else:
                            raise e

        return "Documents applied successfully"

    def list_pods(self, namespace: str, label_selector: str = None):
        """
        List pods from a namespace, optionally filtered by label selector.

        Args:
            namespace: Namespace name
            label_selector: Label selector (e.g., "app=myapp")

        Returns:
            List of pods with formatted information
        """
        try:
            v1 = client.CoreV1Api(self.api_client)

            if label_selector:
                pods = v1.list_namespaced_pod(
                    namespace=namespace, label_selector=label_selector
                ).items
            else:
                pods = v1.list_namespaced_pod(namespace=namespace).items

            # Format pod data
            formatted_pods = []
            for pod in pods:
                # Calculate CPU and Memory from containers
                cpu_requests = 0
                cpu_limits = 0
                memory_requests = 0
                memory_limits = 0

                for container in pod.spec.containers:
                    if container.resources:
                        # Access requests (it's a dict in Kubernetes Python client)
                        if container.resources.requests:
                            requests = container.resources.requests
                            if "cpu" in requests:
                                cpu_str = str(requests["cpu"])
                                cpu_requests += self._parse_cpu(cpu_str)
                            if "memory" in requests:
                                mem_str = str(requests["memory"])
                                memory_requests += self._parse_memory(mem_str)

                        # Access limits (it's a dict in Kubernetes Python client)
                        if container.resources.limits:
                            limits = container.resources.limits
                            if "cpu" in limits:
                                cpu_str = str(limits["cpu"])
                                cpu_limits += self._parse_cpu(cpu_str)
                            if "memory" in limits:
                                mem_str = str(limits["memory"])
                                memory_limits += self._parse_memory(mem_str)

                # Pod status
                status = "Unknown"
                if pod.status.phase:
                    status = pod.status.phase

                # Restarts
                restarts = 0
                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        if container_status.restart_count:
                            restarts += container_status.restart_count

                # Age (time since creation)
                age_seconds = 0
                if pod.metadata.creation_timestamp:
                    from datetime import datetime, timezone

                    now = datetime.now(timezone.utc)
                    age_seconds = int(
                        (now - pod.metadata.creation_timestamp).total_seconds()
                    )

                # Host IP (IP of the node where the pod is running)
                host_ip = pod.status.host_ip if pod.status.host_ip else None

                formatted_pods.append(
                    {
                        "name": pod.metadata.name,
                        "status": status,
                        "restarts": restarts,
                        "cpu_requests": cpu_requests,
                        "cpu_limits": cpu_limits,
                        "memory_requests": memory_requests,
                        "memory_limits": memory_limits,
                        "age_seconds": age_seconds,
                        "host_ip": host_ip,
                    }
                )

            return formatted_pods
        except ApiException as e:
            print(f"Error listing pods: {e}")
            return []

    def list_jobs(self, namespace: str, label_selector: str = None):
        """
        List Jobs from a namespace, optionally filtered by label selector.
        Used to list Jobs created by CronJobs.

        Args:
            namespace: Namespace name
            label_selector: Label selector (e.g., "app=myapp")

        Returns:
            List of jobs with formatted information
        """
        try:
            batch_v1 = client.BatchV1Api(self.api_client)

            if label_selector:
                jobs = batch_v1.list_namespaced_job(
                    namespace=namespace, label_selector=label_selector
                ).items
            else:
                jobs = batch_v1.list_namespaced_job(namespace=namespace).items

            # Format job data
            formatted_jobs = []
            for job in jobs:
                # Job status
                status = "Unknown"
                if job.status.succeeded:
                    status = "Succeeded"
                elif job.status.failed:
                    status = "Failed"
                elif job.status.active:
                    status = "Active"
                elif job.status.conditions:
                    # Check conditions for more specific status
                    for condition in job.status.conditions:
                        if condition.type == "Complete" and condition.status == "True":
                            status = "Succeeded"
                            break
                        elif condition.type == "Failed" and condition.status == "True":
                            status = "Failed"
                            break

                # Count of successes and failures
                succeeded = job.status.succeeded if job.status.succeeded else 0
                failed = job.status.failed if job.status.failed else 0
                active = job.status.active if job.status.active else 0

                # Start time
                start_time = None
                if job.status.start_time:
                    start_time = job.status.start_time.isoformat()

                # Completion time
                completion_time = None
                if job.status.completion_time:
                    completion_time = job.status.completion_time.isoformat()

                # Age (time since creation)
                age_seconds = 0
                if job.metadata.creation_timestamp:
                    from datetime import datetime, timezone

                    now = datetime.now(timezone.utc)
                    age_seconds = int(
                        (now - job.metadata.creation_timestamp).total_seconds()
                    )

                # Duration (if completed)
                duration_seconds = None
                if start_time and completion_time:
                    from datetime import datetime

                    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    completion = datetime.fromisoformat(
                        completion_time.replace("Z", "+00:00")
                    )
                    duration_seconds = int((completion - start).total_seconds())

                formatted_jobs.append(
                    {
                        "name": job.metadata.name,
                        "status": status,
                        "succeeded": succeeded,
                        "failed": failed,
                        "active": active,
                        "start_time": start_time,
                        "completion_time": completion_time,
                        "age_seconds": age_seconds,
                        "duration_seconds": duration_seconds,
                    }
                )

            # Sort by creation (most recent first)
            formatted_jobs.sort(key=lambda x: x["age_seconds"], reverse=False)

            return formatted_jobs
        except ApiException as e:
            print(f"Error listing jobs: {e}")
            return []

    def delete_job(self, namespace: str, job_name: str):
        """
        Delete a specific Job from a namespace.
        Used to delete Jobs created by CronJobs.

        Args:
            namespace: Namespace name
            job_name: Name of the Job to be deleted

        Returns:
            True if the job was deleted successfully

        Raises:
            HTTPException: If the job is not found or there's an error deleting
        """
        try:
            batch_v1 = client.BatchV1Api(self.api_client)
            # Delete the job
            batch_v1.delete_namespaced_job(
                name=job_name,
                namespace=namespace,
                propagation_policy="Background",  # Also deletes associated pods
            )
            return True
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(
                    status_code=404, detail=f"Job '{job_name}' not found"
                )
            raise HTTPException(
                status_code=500, detail=f"Error deleting job '{job_name}': {str(e)}"
            )

    def _parse_cpu(self, cpu_str: str) -> float:
        """Convert CPU string (e.g., '500m', '1', '0.5') to float."""
        if not cpu_str:
            return 0.0
        cpu_str = cpu_str.strip()
        if cpu_str.endswith("m"):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)

    def list_events(self, namespace: str, field_selector: str = None):
        """
        List events from a namespace, optionally filtered by field selector.

        Args:
            namespace: Namespace name
            field_selector: Optional filter (e.g., "involvedObject.name=pod-name")

        Returns:
            List of formatted events
        """
        try:
            v1 = client.CoreV1Api(self.api_client)

            if field_selector:
                events = v1.list_namespaced_event(
                    namespace=namespace, field_selector=field_selector
                ).items
            else:
                events = v1.list_namespaced_event(namespace=namespace).items

            # Format event data
            formatted_events = []
            for event in events:
                # Calculate age (time since creation)
                age_seconds = 0
                if event.first_timestamp:
                    from datetime import datetime, timezone

                    now = datetime.now(timezone.utc)
                    age_seconds = int((now - event.first_timestamp).total_seconds())

                # Count of occurrences
                count = event.count if event.count else 1

                formatted_events.append(
                    {
                        "name": event.metadata.name,
                        "namespace": event.metadata.namespace,
                        "type": event.type,  # Normal, Warning
                        "reason": event.reason or "Unknown",
                        "message": event.message or "",
                        "involved_object": {
                            "kind": event.involved_object.kind
                            if event.involved_object
                            else None,
                            "name": event.involved_object.name
                            if event.involved_object
                            else None,
                            "namespace": event.involved_object.namespace
                            if event.involved_object
                            else None,
                        },
                        "source": {
                            "component": event.source.component
                            if event.source
                            else None,
                            "host": event.source.host if event.source else None,
                        },
                        "first_timestamp": event.first_timestamp.isoformat()
                        if event.first_timestamp
                        else None,
                        "last_timestamp": event.last_timestamp.isoformat()
                        if event.last_timestamp
                        else None,
                        "count": count,
                        "age_seconds": age_seconds,
                    }
                )

            # Sort by timestamp (most recent first)
            formatted_events.sort(key=lambda x: x["age_seconds"], reverse=False)

            return formatted_events
        except ApiException as e:
            print(f"Error listing events: {e}")
            return []

    def check_api_available(self, api_group: str) -> bool:
        """
        Check if an API group is available in the Kubernetes cluster.

        Args:
            api_group: API group name (e.g., 'gateway.networking.k8s.io')

        Returns:
            True if the API is available, False otherwise
        """
        try:
            # Use REST API directly to check if the group exists
            # Making a GET request to /apis/{api_group}
            path = f"/apis/{api_group}"

            try:
                response = self.api_client.call_api(
                    path,
                    "GET",
                    auth_settings=["BearerToken"],
                    response_type="object",
                    _preload_content=False,
                )

                # call_api returns a tuple: (data, status, headers)
                data, status, headers = response

                # If the request was successful (status 200), the group exists
                if status == 200:
                    print(f"API group {api_group} found via REST API")
                    return True
                else:
                    print(f"API group {api_group} returned status {status}")
                    return False

            except ApiException as api_err:
                # If error 404, the group is not available
                if api_err.status == 404:
                    print(f"API group {api_group} not found (404)")
                    return False
                else:
                    print(f"Error checking API group {api_group}: {api_err}")
                    return False

        except ApiException as e:
            print(f"Error checking API group {api_group}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error checking API group {api_group}: {e}")
            import traceback

            traceback.print_exc()
            return False

    def get_gateway_api_resources(self) -> list[str]:
        """
        List Gateway API resources available in the cluster using the discovery API.
        Equivalent to the command 'kubectl api-resources --api-group=gateway.networking.k8s.io'

        Returns:
            List of available resources (e.g., ['HTTPRoute', 'TCPRoute', 'UDPRoute'])
        """
        available_resources = []

        try:
            # Use discovery API to list resources from gateway.networking.k8s.io group
            # This is equivalent to the command kubectl api-resources --api-group=gateway.networking.k8s.io
            discovery_api = client.DiscoveryV1Api(self.api_client)

            # Get all API resources
            api_resources = discovery_api.get_api_resources(
                group="gateway.networking.k8s.io"
            )

            # Filter only resources from gateway.networking.k8s.io group
            for resource in api_resources.resources:
                # Add the resource kind (e.g., HTTPRoute, TCPRoute, UDPRoute)
                if resource.kind:
                    available_resources.append(resource.kind)

            # Remove duplicates and sort
            available_resources = sorted(list(set(available_resources)))

        except ApiException as e:
            # If error, try alternative method checking known versions
            print(f"Warning: Error getting Gateway API resources via discovery: {e}")
            available_resources = self._fallback_get_gateway_resources()
        except Exception as e:
            # Unexpected error, try alternative method
            print(f"Warning: Unexpected error getting Gateway API resources: {e}")
            available_resources = self._fallback_get_gateway_resources()

        return available_resources

    def _fallback_get_gateway_resources(self) -> list[str]:
        """
        Alternative method to check Gateway API resources when discovery API fails.
        Checks known resources directly.

        Returns:
            List of available resources
        """
        available_resources = []

        # Known Gateway API resources and their versions
        gateway_resources = [
            ("HTTPRoute", "gateway.networking.k8s.io/v1", "httproutes"),
            ("TCPRoute", "gateway.networking.k8s.io/v1alpha2", "tcproutes"),
            ("UDPRoute", "gateway.networking.k8s.io/v1alpha2", "udproutes"),
        ]

        for resource_kind, api_version, resource_name in gateway_resources:
            try:
                # Extract group and version
                api_parts = api_version.split("/")
                api_group = api_parts[0]
                api_version_part = api_parts[1]

                # Try to list the resource (even if empty, if the API exists, it will return 200)
                path = f"/apis/{api_group}/{api_version_part}/{resource_name}"

                response = self.api_client.call_api(
                    path,
                    "GET",
                    auth_settings=["BearerToken"],
                    response_type="object",
                    _preload_content=False,
                )

                data, status, headers = response

                # If returned 200, the resource is available
                if status == 200:
                    available_resources.append(resource_kind)
            except ApiException as e:
                # If error 404, the resource is not available
                if e.status != 404:
                    # Other error, log but continue
                    print(f"Warning: Error checking {resource_kind} availability: {e}")
            except Exception as e:
                # Unexpected error, log but continue
                print(
                    f"Warning: Unexpected error checking {resource_kind} availability: {e}"
                )

        return available_resources

    def get_gateway_reference(self) -> dict | None:
        """
        Search for the first available Gateway in the cluster and return its name and namespace.
        Tries to search in common namespaces first, then lists all namespaces.

        Returns:
            Dict with Gateway 'namespace' and 'name', or None if not found
        """
        try:
            # Try different Gateway API versions
            api_versions = [
                "gateway.networking.k8s.io/v1",
                "gateway.networking.k8s.io/v1beta1",
            ]

            # Common namespaces to try first
            common_namespaces = ["kube-system", "default", "gateway-system"]

            for api_version in api_versions:
                try:
                    # Extract group and version
                    api_parts = api_version.split("/")
                    api_group = api_parts[0]
                    api_version_part = api_parts[1]

                    # First, try to search in common namespaces
                    for namespace in common_namespaces:
                        try:
                            path = f"/apis/{api_group}/{api_version_part}/namespaces/{namespace}/gateways"

                            response = self.api_client.call_api(
                                path,
                                "GET",
                                auth_settings=["BearerToken"],
                                response_type="object",
                                _preload_content=True,
                            )

                            data, status, headers = response

                            if status == 200 and isinstance(data, dict):
                                items = data.get("items", [])
                                if items and len(items) > 0:
                                    # Get the first Gateway found
                                    gateway = items[0]
                                    metadata = gateway.get("metadata", {})
                                    name = metadata.get("name", "")

                                    if name:
                                        return {"namespace": namespace, "name": name}
                        except ApiException as e:
                            # If error 404, try next namespace
                            if e.status == 404:
                                continue
                            # Other error, log but continue
                            print(
                                f"Warning: Error getting Gateway from namespace {namespace}: {e}"
                            )
                        except Exception as e:
                            # Unexpected error, log but continue
                            print(
                                f"Warning: Unexpected error getting Gateway from namespace {namespace}: {e}"
                            )

                    # If not found in common namespaces, try to list all Gateways
                    # (some API versions may support this)
                    try:
                        path = f"/apis/{api_group}/{api_version_part}/gateways"

                        response = self.api_client.call_api(
                            path,
                            "GET",
                            auth_settings=["BearerToken"],
                            response_type="object",
                            _preload_content=True,
                        )

                        data, status, headers = response

                        if status == 200 and isinstance(data, dict):
                            items = data.get("items", [])
                            if items and len(items) > 0:
                                # Get the first Gateway found
                                gateway = items[0]
                                metadata = gateway.get("metadata", {})
                                name = metadata.get("name", "")
                                namespace = metadata.get("namespace", "")

                                if name and namespace:
                                    return {"namespace": namespace, "name": name}
                    except ApiException as e:
                        # If error 404 or 405 (method not allowed), try next version
                        if e.status in [404, 405]:
                            continue
                        # Other error, log but continue
                        print(
                            f"Warning: Error listing all Gateways via {api_version}: {e}"
                        )
                    except Exception as e:
                        # Unexpected error, log but continue
                        print(
                            f"Warning: Unexpected error listing all Gateways via {api_version}: {e}"
                        )

                except Exception as e:
                    # Unexpected error, log but continue
                    print(
                        f"Warning: Unexpected error getting Gateway via {api_version}: {e}"
                    )

            # If not found in any version, return None
            return None

        except Exception as e:
            print(f"Error getting Gateway reference: {e}")
            return None

    def _parse_memory(self, memory_str: str) -> int:
        """Convert memory string (e.g., '512Mi', '1Gi', '1000M') to MB."""
        if not memory_str:
            return 0
        memory_str = memory_str.strip()

        # Remove suffixes and convert
        if memory_str.endswith("Ki"):
            return int(memory_str[:-2]) // 1024
        elif memory_str.endswith("Mi"):
            return int(memory_str[:-2])
        elif memory_str.endswith("Gi"):
            return int(memory_str[:-2]) * 1024
        elif memory_str.endswith("Ti"):
            return int(memory_str[:-2]) * 1024 * 1024
        elif memory_str.endswith("K"):
            return int(memory_str[:-1]) // 1000
        elif memory_str.endswith("M"):
            return int(memory_str[:-1])
        elif memory_str.endswith("G"):
            return int(memory_str[:-1]) * 1000
        elif memory_str.endswith("T"):
            return int(memory_str[:-1]) * 1000 * 1000
        else:
            # Assume bytes
            return int(memory_str) // (1024 * 1024)
