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
        Inicializa o cliente Kubernetes com os parâmetros fornecidos.
        """
        self.configuration = client.Configuration()
        self.configuration.host = url
        self.configuration.verify_ssl = verify_ssl
        self.configuration.api_key = {"authorization": f"Bearer {token}"}
        self.api_client = client.ApiClient(self.configuration)
        self.api_client = client.ApiClient(self.configuration)

    def validate_connection(self):
        """
        Valida a conexão ao Kubernetes tentando listar os namespaces.
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
                error_message = error_body.get("message", str(e.body)) if isinstance(error_body, dict) else str(e.body)
            except (json.JSONDecodeError, AttributeError):
                error_message = str(e.body) if e.body else str(e)
            message = {"status": "error", "message": {"code": str(e.status), "message": error_message}}
            return (False, message)

    def get_namespaces(self):
        """
        Retorna uma lista de namespaces do cluster Kubernetes.
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            return v1.list_namespace().items
        except ApiException as e:
            print(f"Erro ao listar namespaces: {e}")
            return []

    def create_namespace(self, name: str):
        """
        Cria um novo namespace no cluster Kubernetes.
        """
        body = client.V1Namespace(metadata=client.V1ObjectMeta(name=name))
        try:
            v1 = client.CoreV1Api(self.api_client)
            return v1.create_namespace(body=body)
        except ApiException as e:
            print(f"Erro ao criar namespace: {e}")
            return None

    def get_available_cpu(self):
        """
        Retorna a quantidade total de CPU disponível no cluster Kubernetes.
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
            print(f"Erro ao obter a quantidade de CPU disponível: {e}")
            return None

    def get_available_memory(self):
        """
        Obtém a quantidade de memória disponível no cluster Kubernetes.
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
        """Cria o namespace se ele não existir."""
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

    def delete_namespace(self, namespace_name):
        """
        Deleta um namespace do Kubernetes.
        Quando um namespace é deletado, todos os recursos dentro dele são automaticamente deletados.
        """
        v1 = client.CoreV1Api(self.api_client)
        try:
            v1.delete_namespace(name=namespace_name, body=client.V1DeleteOptions())
        except ApiException as e:
            if e.status == 404:
                # Namespace já não existe, não é um erro
                return
            else:
                raise e

    def delete_pod(self, namespace: str, pod_name: str):
        """
        Deleta um pod específico do Kubernetes.

        Args:
            namespace: Nome do namespace
            pod_name: Nome do pod

        Returns:
            True se deletado com sucesso, False caso contrário
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            v1.delete_namespaced_pod(name=pod_name, namespace=namespace, body=client.V1DeleteOptions())
            return True
        except ApiException as e:
            if e.status == 404:
                # Pod já não existe, não é um erro
                return True
            else:
                print(f"Erro ao deletar pod {pod_name}: {e}")
                raise e

    def get_pod_logs(self, namespace: str, pod_name: str, container_name: str = None, tail_lines: int = 100, follow: bool = False):
        """
        Obtém os logs de um pod do Kubernetes.

        Args:
            namespace: Nome do namespace
            pod_name: Nome do pod
            container_name: Nome do container (opcional, se o pod tiver múltiplos containers)
            tail_lines: Número de linhas finais a retornar (padrão: 100)
            follow: Se True, segue os logs em tempo real (padrão: False)

        Returns:
            String com os logs do pod
        """
        try:
            v1 = client.CoreV1Api(self.api_client)
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                tail_lines=tail_lines,
                follow=follow,
                _preload_content=False
            )
            return logs.read().decode('utf-8')
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found")
            else:
                print(f"Erro ao obter logs do pod {pod_name}: {e}")
                raise HTTPException(status_code=e.status, detail=f"Failed to get logs: {str(e)}")

    def exec_pod_command(self, namespace: str, pod_name: str, command: list[str], container_name: str = None):
        """
        Executa um comando em um pod do Kubernetes.

        Args:
            namespace: Nome do namespace
            pod_name: Nome do pod
            command: Lista com o comando e argumentos (ex: ['ls', '-la'])
            container_name: Nome do container (opcional, se o pod tiver múltiplos containers)

        Returns:
            Tupla (stdout, stderr, return_code)
        """
        try:
            v1 = client.CoreV1Api(self.api_client)

            # Executar comando usando stream
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
                _preload_content=False
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
                "return_code": 0 if not stderr else 1
            }
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found")
            else:
                print(f"Erro ao executar comando no pod {pod_name}: {e}")
                raise HTTPException(status_code=e.status, detail=f"Failed to execute command: {str(e)}")
        except Exception as e:
            print(f"Erro ao executar comando no pod {pod_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to execute command: {str(e)}")

    def cleanup_orphaned_gateway_resources(self, namespace: str, component_name: str, expected_resources: list):
        """
        Remove recursos Gateway API (HTTPRoute, TCPRoute, UDPRoute) que não deveriam mais existir.

        Args:
            namespace: Namespace onde os recursos estão
            component_name: Nome do componente
            expected_resources: Lista de dicionários com os recursos esperados (renderizados dos templates)
        """
        # Identificar quais recursos Gateway API deveriam existir
        expected_gateway_kinds = set()
        for resource in expected_resources:
            if resource and isinstance(resource, dict):
                kind = resource.get("kind")
                api_version = resource.get("apiVersion", "")
                # Verificar se é um recurso Gateway API
                if kind in ["HTTPRoute", "TCPRoute", "UDPRoute"] and "gateway.networking.k8s.io" in api_version:
                    expected_gateway_kinds.add(kind)

        # Lista de recursos Gateway API que podem existir
        gateway_resources = [
            ("HTTPRoute", "gateway.networking.k8s.io/v1", "httproutes"),
            ("TCPRoute", "gateway.networking.k8s.io/v1alpha2", "tcproutes"),
            ("UDPRoute", "gateway.networking.k8s.io/v1alpha2", "udproutes"),
        ]

        # Para cada tipo de recurso Gateway API, verificar se deveria existir
        for kind, api_version, resource_name in gateway_resources:
            # Se não está na lista de esperados, tentar deletar se existir
            if kind not in expected_gateway_kinds:
                try:
                    # Tentar deletar o recurso se existir
                    api_parts = api_version.split('/')
                    api_group = api_parts[0]
                    api_version_part = api_parts[1]
                    api_path = f"/apis/{api_group}/{api_version_part}/namespaces/{namespace}/{resource_name}/{component_name}"

                    self.api_client.call_api(
                        api_path,
                        'DELETE',
                        body=client.V1DeleteOptions(),
                        auth_settings=['BearerToken'],
                        response_type='object',
                        _preload_content=True
                    )
                    print(f"Deleted orphaned {kind} '{component_name}' from namespace '{namespace}'")
                except ApiException as e:
                    if e.status == 404:
                        # Recurso não existe, tudo bem
                        pass
                    else:
                        # Log mas não falha - não é crítico
                        print(f"Warning: Could not delete {kind} '{component_name}': {e}")

    def apply_or_delete_yaml_to_k8s(self, yaml_documents, operation="create"):
        # Para operações upsert, limpar recursos Gateway API órfãos antes de aplicar
        if operation == "upsert":
            # Coletar informações dos documentos para identificar namespace e component_name
            namespace = None
            component_name = None

            # Procurar primeiro por recursos Gateway API para obter o nome correto
            for doc in yaml_documents:
                if doc and isinstance(doc, dict):
                    kind = doc.get("kind")
                    api_version = doc.get("apiVersion", "")
                    metadata = doc.get("metadata", {})

                    # Se for um recurso Gateway API, usar esse nome
                    if kind in ["HTTPRoute", "TCPRoute", "UDPRoute"] and "gateway.networking.k8s.io" in api_version:
                        component_name = metadata.get("name")
                        namespace = metadata.get("namespace")
                        if namespace and component_name:
                            break

            # Se não encontrou em recursos Gateway API, procurar em qualquer documento
            if not (namespace and component_name):
                for doc in yaml_documents:
                    if doc and isinstance(doc, dict) and doc.get("metadata"):
                        metadata = doc.get("metadata", {})
                        namespace = metadata.get("namespace")
                        component_name = metadata.get("name")
                        if namespace and component_name:
                            break

            # Se encontrou namespace e component_name, limpar recursos órfãos
            if namespace and component_name:
                try:
                    self.cleanup_orphaned_gateway_resources(namespace, component_name, yaml_documents)
                except Exception as e:
                    # Log mas não falha - não é crítico
                    print(f"Warning: Could not cleanup orphaned Gateway resources: {e}")

        for document in yaml_documents:
            # Pular documentos None ou inválidos (quando template não renderiza nada)
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

            # Se o recurso não está no mapeamento padrão, usar API REST diretamente
            # Isso é necessário para recursos customizados como Gateway API (HTTPRoute, TCPRoute, UDPRoute)
            if not api_mapping:
                # Extrair o grupo e versão da API do apiVersion
                # Formato: grupo/versão (ex: gateway.networking.k8s.io/v1)
                # ou apenas versão para APIs core (ex: v1)
                api_parts = api_version.split('/')
                if len(api_parts) == 2:
                    api_group, api_version_part = api_parts
                else:
                    # API core (ex: v1)
                    api_group = ""
                    api_version_part = api_version

                # Converter o kind para o nome do recurso no path da API
                # Gateway API usa lowercase plural: HTTPRoute -> httproutes, TCPRoute -> tcproutes
                def kind_to_resource_name(kind_str):
                    """Converte um Kind para o nome do recurso no path da API"""
                    # Converter para lowercase
                    lower = kind_str.lower()
                    # Adicionar 's' se não terminar com 's'
                    if not lower.endswith('s'):
                        return lower + 's'
                    return lower

                resource_name = kind_to_resource_name(kind)

                # Determinar o path da API baseado no grupo
                if api_group:
                    # API customizada: /apis/{group}/{version}/namespaces/{namespace}/{resource}/{name}
                    api_path_base = f"/apis/{api_group}/{api_version_part}/namespaces/{namespace}/{resource_name}"
                else:
                    # API core: /api/{version}/namespaces/{namespace}/{resource}/{name}
                    api_path_base = f"/api/{api_version_part}/namespaces/{namespace}/{resource_name}"

                # Aplicar usando API REST diretamente
                try:
                    if operation == "create":
                        # POST para criar
                        self.api_client.call_api(
                            api_path_base,
                            'POST',
                            body=document,
                            auth_settings=['BearerToken'],
                            response_type='object',
                            _preload_content=True
                        )
                    elif operation == "update":
                        # PUT para atualizar - precisa obter resourceVersion primeiro
                        try:
                            # Ler o recurso existente para obter o resourceVersion
                            existing_response = self.api_client.call_api(
                                f"{api_path_base}/{name}",
                                'GET',
                                auth_settings=['BearerToken'],
                                response_type='object',
                                _preload_content=True
                            )
                            existing_resource = existing_response[0] if isinstance(existing_response, tuple) else existing_response

                            # Incluir resourceVersion no documento se existir
                            if existing_resource and 'metadata' in existing_resource:
                                existing_metadata = existing_resource['metadata']
                                if 'resourceVersion' in existing_metadata:
                                    if 'metadata' not in document:
                                        document['metadata'] = {}
                                    document['metadata']['resourceVersion'] = existing_metadata['resourceVersion']
                        except ApiException as read_e:
                            if read_e.status != 404:
                                # Se não conseguir ler e não for 404, relançar o erro
                                raise read_e

                        # PUT para atualizar
                        self.api_client.call_api(
                            f"{api_path_base}/{name}",
                            'PUT',
                            body=document,
                            auth_settings=['BearerToken'],
                            response_type='object',
                            _preload_content=True
                        )
                    elif operation == "upsert":
                        # Tenta atualizar primeiro, se não existir, cria
                        try:
                            # Ler o recurso existente para obter o resourceVersion
                            existing_response = self.api_client.call_api(
                                f"{api_path_base}/{name}",
                                'GET',
                                auth_settings=['BearerToken'],
                                response_type='object',
                                _preload_content=True
                            )
                            existing_resource = existing_response[0] if isinstance(existing_response, tuple) else existing_response

                            # Incluir resourceVersion no documento se existir
                            if existing_resource and 'metadata' in existing_resource:
                                existing_metadata = existing_resource['metadata']
                                if 'resourceVersion' in existing_metadata:
                                    if 'metadata' not in document:
                                        document['metadata'] = {}
                                    document['metadata']['resourceVersion'] = existing_metadata['resourceVersion']

                            # PUT para atualizar
                            self.api_client.call_api(
                                f"{api_path_base}/{name}",
                                'PUT',
                                body=document,
                                auth_settings=['BearerToken'],
                                response_type='object',
                                _preload_content=True
                            )
                        except ApiException as e:
                            if e.status == 404:
                                # Recurso não existe, criar
                                self.api_client.call_api(
                                    api_path_base,
                                    'POST',
                                    body=document,
                                    auth_settings=['BearerToken'],
                                    response_type='object',
                                    _preload_content=True
                                )
                            else:
                                raise e
                    elif operation == "delete":
                        # DELETE para remover
                        try:
                            self.api_client.call_api(
                                f"{api_path_base}/{name}",
                                'DELETE',
                                body=client.V1DeleteOptions(),
                                auth_settings=['BearerToken'],
                                response_type='object',
                                _preload_content=True
                            )
                        except ApiException as e:
                            if e.status == 404:
                                # Recurso já não existe, isso é aceitável
                                pass
                            else:
                                raise e
                except ApiException as e:
                    raise HTTPException(
                        status_code=e.status,
                        detail=f"Failed to {operation} {kind} '{name}': {str(e)}"
                    )
            else:
                # Usar o mapeamento padrão para recursos conhecidos
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
                    # Tenta atualizar primeiro, se não existir, cria
                    try:
                        # Para Deployments, preservar o número de réplicas atual se não especificado
                        if kind == "Deployment" and "spec" in document:
                            try:
                                read_method = getattr(api_instance, "read_namespaced_deployment", None)
                                if read_method:
                                    existing_deployment = read_method(name=name, namespace=namespace)

                                    # Se o novo documento não especifica replicas, preservar o valor atual
                                    # Isso evita que o Kubernetes resete para o valor padrão (1) ou conflite com HPA
                                    if "replicas" not in document.get("spec", {}):
                                        if hasattr(existing_deployment.spec, "replicas") and existing_deployment.spec.replicas is not None:
                                            document["spec"]["replicas"] = existing_deployment.spec.replicas

                                    # Preservar também resourceVersion e outras metadatas necessárias para evitar conflitos
                                    # O resourceVersion é necessário para o replace funcionar corretamente
                                    if hasattr(existing_deployment.metadata, "resource_version") and existing_deployment.metadata.resource_version:
                                        if "metadata" not in document:
                                            document["metadata"] = {}
                                        document["metadata"]["resourceVersion"] = existing_deployment.metadata.resource_version

                                        # Preservar também generation se existir
                                        if hasattr(existing_deployment.metadata, "generation") and existing_deployment.metadata.generation:
                                            document["metadata"]["generation"] = existing_deployment.metadata.generation
                            except ApiException as read_e:
                                # Se não conseguir ler (404 ou outro erro), continua normalmente
                                # Isso significa que o deployment não existe ainda, então criaremos
                                if read_e.status != 404:
                                    # Se for outro erro, loga mas continua
                                    print(f"Warning: Could not read existing deployment to preserve replicas: {read_e}")

                        getattr(api_instance, replace_method)(
                            name=name, namespace=namespace, body=document
                        )
                    except ApiException as e:
                        if e.status == 404:
                            # Recurso não existe, criar
                            getattr(api_instance, create_method)(
                                namespace=namespace, body=document
                            )
                        else:
                            raise e
                elif operation == "delete":
                    try:
                        getattr(api_instance, delete_method)(
                            name=name, namespace=namespace, body=client.V1DeleteOptions()
                        )
                    except ApiException as e:
                        if e.status == 404:
                            # Recurso já não existe no Kubernetes, isso é aceitável
                            # O objetivo é deletar e se já não existe, consideramos sucesso
                            pass
                        else:
                            raise e

        return f"Documents applied successfully"

    def list_pods(self, namespace: str, label_selector: str = None):
        """
        Lista pods de um namespace, opcionalmente filtrados por label selector.

        Args:
            namespace: Nome do namespace
            label_selector: Seletor de labels (ex: "app=myapp")

        Returns:
            Lista de pods com informações formatadas
        """
        try:
            v1 = client.CoreV1Api(self.api_client)

            if label_selector:
                pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector).items
            else:
                pods = v1.list_namespaced_pod(namespace=namespace).items

            # Formatar dados dos pods
            formatted_pods = []
            for pod in pods:
                # Calcular CPU e Memory dos containers
                cpu_requests = 0
                cpu_limits = 0
                memory_requests = 0
                memory_limits = 0

                for container in pod.spec.containers:
                    if container.resources:
                        # Acessar requests (é um dict no Kubernetes Python client)
                        if container.resources.requests:
                            requests = container.resources.requests
                            if 'cpu' in requests:
                                cpu_str = str(requests['cpu'])
                                cpu_requests += self._parse_cpu(cpu_str)
                            if 'memory' in requests:
                                mem_str = str(requests['memory'])
                                memory_requests += self._parse_memory(mem_str)

                        # Acessar limits (é um dict no Kubernetes Python client)
                        if container.resources.limits:
                            limits = container.resources.limits
                            if 'cpu' in limits:
                                cpu_str = str(limits['cpu'])
                                cpu_limits += self._parse_cpu(cpu_str)
                            if 'memory' in limits:
                                mem_str = str(limits['memory'])
                                memory_limits += self._parse_memory(mem_str)

                # Status do pod
                status = "Unknown"
                if pod.status.phase:
                    status = pod.status.phase

                # Restarts
                restarts = 0
                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        if container_status.restart_count:
                            restarts += container_status.restart_count

                # Age (tempo desde a criação)
                age_seconds = 0
                if pod.metadata.creation_timestamp:
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    age_seconds = int((now - pod.metadata.creation_timestamp).total_seconds())

                # Host IP (IP do nó onde o pod está rodando)
                host_ip = pod.status.host_ip if pod.status.host_ip else None

                formatted_pods.append({
                    "name": pod.metadata.name,
                    "status": status,
                    "restarts": restarts,
                    "cpu_requests": cpu_requests,
                    "cpu_limits": cpu_limits,
                    "memory_requests": memory_requests,
                    "memory_limits": memory_limits,
                    "age_seconds": age_seconds,
                    "host_ip": host_ip,
                })

            return formatted_pods
        except ApiException as e:
            print(f"Erro ao listar pods: {e}")
            return []

    def list_jobs(self, namespace: str, label_selector: str = None):
        """
        Lista Jobs de um namespace, opcionalmente filtrados por label selector.
        Usado para listar Jobs criados por CronJobs.

        Args:
            namespace: Nome do namespace
            label_selector: Seletor de labels (ex: "app=myapp")

        Returns:
            Lista de jobs com informações formatadas
        """
        try:
            batch_v1 = client.BatchV1Api(self.api_client)

            if label_selector:
                jobs = batch_v1.list_namespaced_job(namespace=namespace, label_selector=label_selector).items
            else:
                jobs = batch_v1.list_namespaced_job(namespace=namespace).items

            # Formatar dados dos jobs
            formatted_jobs = []
            for job in jobs:
                # Status do job
                status = "Unknown"
                if job.status.succeeded:
                    status = "Succeeded"
                elif job.status.failed:
                    status = "Failed"
                elif job.status.active:
                    status = "Active"
                elif job.status.conditions:
                    # Verificar condições para status mais específico
                    for condition in job.status.conditions:
                        if condition.type == "Complete" and condition.status == "True":
                            status = "Succeeded"
                            break
                        elif condition.type == "Failed" and condition.status == "True":
                            status = "Failed"
                            break

                # Contagem de sucessos e falhas
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

                # Age (tempo desde a criação)
                age_seconds = 0
                if job.metadata.creation_timestamp:
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    age_seconds = int((now - job.metadata.creation_timestamp).total_seconds())

                # Duração (se completado)
                duration_seconds = None
                if start_time and completion_time:
                    from datetime import datetime
                    start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    completion = datetime.fromisoformat(completion_time.replace('Z', '+00:00'))
                    duration_seconds = int((completion - start).total_seconds())

                formatted_jobs.append({
                    "name": job.metadata.name,
                    "status": status,
                    "succeeded": succeeded,
                    "failed": failed,
                    "active": active,
                    "start_time": start_time,
                    "completion_time": completion_time,
                    "age_seconds": age_seconds,
                    "duration_seconds": duration_seconds,
                })

            # Ordenar por criação (mais recente primeiro)
            formatted_jobs.sort(key=lambda x: x["age_seconds"], reverse=False)

            return formatted_jobs
        except ApiException as e:
            print(f"Erro ao listar jobs: {e}")
            return []

    def delete_job(self, namespace: str, job_name: str):
        """
        Deleta um Job específico de um namespace.
        Usado para deletar Jobs criados por CronJobs.

        Args:
            namespace: Nome do namespace
            job_name: Nome do Job a ser deletado

        Returns:
            True se o job foi deletado com sucesso

        Raises:
            HTTPException: Se o job não for encontrado ou houver erro ao deletar
        """
        try:
            batch_v1 = client.BatchV1Api(self.api_client)
            # Deletar o job
            batch_v1.delete_namespaced_job(
                name=job_name,
                namespace=namespace,
                propagation_policy="Background"  # Deleta pods associados também
            )
            return True
        except ApiException as e:
            if e.status == 404:
                raise HTTPException(status_code=404, detail=f"Job '{job_name}' not found")
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting job '{job_name}': {str(e)}"
            )

    def _parse_cpu(self, cpu_str: str) -> float:
        """Converte string de CPU (ex: '500m', '1', '0.5') para float."""
        if not cpu_str:
            return 0.0
        cpu_str = cpu_str.strip()
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)

    def list_events(self, namespace: str, field_selector: str = None):
        """
        Lista eventos de um namespace, opcionalmente filtrados por field selector.

        Args:
            namespace: Nome do namespace
            field_selector: Filtro opcional (ex: "involvedObject.name=pod-name")

        Returns:
            Lista de eventos formatados
        """
        try:
            v1 = client.CoreV1Api(self.api_client)

            if field_selector:
                events = v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector=field_selector
                ).items
            else:
                events = v1.list_namespaced_event(namespace=namespace).items

            # Formatar dados dos eventos
            formatted_events = []
            for event in events:
                # Calcular age (tempo desde a criação)
                age_seconds = 0
                if event.first_timestamp:
                    from datetime import datetime, timezone
                    now = datetime.now(timezone.utc)
                    age_seconds = int((now - event.first_timestamp).total_seconds())

                # Contagem de ocorrências
                count = event.count if event.count else 1

                formatted_events.append({
                    "name": event.metadata.name,
                    "namespace": event.metadata.namespace,
                    "type": event.type,  # Normal, Warning
                    "reason": event.reason or "Unknown",
                    "message": event.message or "",
                    "involved_object": {
                        "kind": event.involved_object.kind if event.involved_object else None,
                        "name": event.involved_object.name if event.involved_object else None,
                        "namespace": event.involved_object.namespace if event.involved_object else None,
                    },
                    "source": {
                        "component": event.source.component if event.source else None,
                        "host": event.source.host if event.source else None,
                    },
                    "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                    "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None,
                    "count": count,
                    "age_seconds": age_seconds,
                })

            # Ordenar por timestamp (mais recente primeiro)
            formatted_events.sort(key=lambda x: x["age_seconds"], reverse=False)

            return formatted_events
        except ApiException as e:
            print(f"Erro ao listar eventos: {e}")
            return []

    def check_api_available(self, api_group: str) -> bool:
        """
        Verifica se uma API group está disponível no cluster Kubernetes.

        Args:
            api_group: Nome do API group (ex: 'gateway.networking.k8s.io')

        Returns:
            True se a API está disponível, False caso contrário
        """
        try:
            # Usar a API REST diretamente para verificar se o grupo existe
            # Fazendo uma requisição GET para /apis/{api_group}
            path = f"/apis/{api_group}"

            try:
                response = self.api_client.call_api(
                    path,
                    'GET',
                    auth_settings=['BearerToken'],
                    response_type='object',
                    _preload_content=False
                )

                # call_api retorna uma tupla: (data, status, headers)
                data, status, headers = response

                # Se a requisição foi bem-sucedida (status 200), o grupo existe
                if status == 200:
                    print(f"API group {api_group} encontrado via API REST")
                    return True
                else:
                    print(f"API group {api_group} retornou status {status}")
                    return False

            except ApiException as api_err:
                # Se der erro 404, o grupo não está disponível
                if api_err.status == 404:
                    print(f"API group {api_group} não encontrado (404)")
                    return False
                else:
                    print(f"Erro ao verificar API group {api_group}: {api_err}")
                    return False

        except ApiException as e:
            print(f"Erro ao verificar API group {api_group}: {e}")
            return False
        except Exception as e:
            print(f"Erro inesperado ao verificar API group {api_group}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_gateway_api_resources(self) -> list[str]:
        """
        Lista os recursos Gateway API disponíveis no cluster usando a API de descoberta.
        Equivalente ao comando 'kubectl api-resources --api-group=gateway.networking.k8s.io'

        Returns:
            Lista de recursos disponíveis (ex: ['HTTPRoute', 'TCPRoute', 'UDPRoute'])
        """
        available_resources = []

        try:
            # Usar a API de descoberta para listar recursos do grupo gateway.networking.k8s.io
            # Isso é equivalente ao comando kubectl api-resources --api-group=gateway.networking.k8s.io
            discovery_api = client.DiscoveryV1Api(self.api_client)

            # Obter todos os recursos da API
            api_resources = discovery_api.get_api_resources(group="gateway.networking.k8s.io")

            # Filtrar apenas os recursos do grupo gateway.networking.k8s.io
            for resource in api_resources.resources:
                # Adicionar o kind do recurso (ex: HTTPRoute, TCPRoute, UDPRoute)
                if resource.kind:
                    available_resources.append(resource.kind)

            # Remover duplicatas e ordenar
            available_resources = sorted(list(set(available_resources)))

        except ApiException as e:
            # Se der erro, tentar método alternativo verificando versões conhecidas
            print(f"Warning: Error getting Gateway API resources via discovery: {e}")
            available_resources = self._fallback_get_gateway_resources()
        except Exception as e:
            # Erro inesperado, tentar método alternativo
            print(f"Warning: Unexpected error getting Gateway API resources: {e}")
            available_resources = self._fallback_get_gateway_resources()

        return available_resources

    def _fallback_get_gateway_resources(self) -> list[str]:
        """
        Método alternativo para verificar recursos Gateway API quando a API de descoberta falha.
        Verifica recursos conhecidos diretamente.

        Returns:
            Lista de recursos disponíveis
        """
        available_resources = []

        # Recursos Gateway API conhecidos e suas versões
        gateway_resources = [
            ("HTTPRoute", "gateway.networking.k8s.io/v1", "httproutes"),
            ("TCPRoute", "gateway.networking.k8s.io/v1alpha2", "tcproutes"),
            ("UDPRoute", "gateway.networking.k8s.io/v1alpha2", "udproutes"),
        ]

        for resource_kind, api_version, resource_name in gateway_resources:
            try:
                # Extrair grupo e versão
                api_parts = api_version.split('/')
                api_group = api_parts[0]
                api_version_part = api_parts[1]

                # Tentar listar o recurso (mesmo que vazio, se a API existir, retornará 200)
                path = f"/apis/{api_group}/{api_version_part}/{resource_name}"

                response = self.api_client.call_api(
                    path,
                    'GET',
                    auth_settings=['BearerToken'],
                    response_type='object',
                    _preload_content=False
                )

                data, status, headers = response

                # Se retornou 200, o recurso está disponível
                if status == 200:
                    available_resources.append(resource_kind)
            except ApiException as e:
                # Se der 404, o recurso não está disponível
                if e.status != 404:
                    # Outro erro, logar mas continuar
                    print(f"Warning: Error checking {resource_kind} availability: {e}")
            except Exception as e:
                # Erro inesperado, logar mas continuar
                print(f"Warning: Unexpected error checking {resource_kind} availability: {e}")

        return available_resources

    def get_gateway_reference(self) -> dict | None:
        """
        Busca o primeiro Gateway disponível no cluster e retorna seu nome e namespace.
        Tenta buscar em namespaces comuns primeiro, depois lista todos os namespaces.

        Returns:
            Dict com 'namespace' e 'name' do Gateway, ou None se não encontrar
        """
        try:
            # Tentar diferentes versões da API Gateway
            api_versions = [
                "gateway.networking.k8s.io/v1",
                "gateway.networking.k8s.io/v1beta1",
            ]

            # Namespaces comuns para tentar primeiro
            common_namespaces = ["kube-system", "default", "gateway-system"]

            for api_version in api_versions:
                try:
                    # Extrair grupo e versão
                    api_parts = api_version.split('/')
                    api_group = api_parts[0]
                    api_version_part = api_parts[1]

                    # Primeiro, tentar buscar em namespaces comuns
                    for namespace in common_namespaces:
                        try:
                            path = f"/apis/{api_group}/{api_version_part}/namespaces/{namespace}/gateways"

                            response = self.api_client.call_api(
                                path,
                                'GET',
                                auth_settings=['BearerToken'],
                                response_type='object',
                                _preload_content=True
                            )

                            data, status, headers = response

                            if status == 200 and isinstance(data, dict):
                                items = data.get('items', [])
                                if items and len(items) > 0:
                                    # Pegar o primeiro Gateway encontrado
                                    gateway = items[0]
                                    metadata = gateway.get('metadata', {})
                                    name = metadata.get('name', '')

                                    if name:
                                        return {
                                            "namespace": namespace,
                                            "name": name
                                        }
                        except ApiException as e:
                            # Se der 404, tentar próximo namespace
                            if e.status == 404:
                                continue
                            # Outro erro, logar mas continuar
                            print(f"Warning: Error getting Gateway from namespace {namespace}: {e}")
                        except Exception as e:
                            # Erro inesperado, logar mas continuar
                            print(f"Warning: Unexpected error getting Gateway from namespace {namespace}: {e}")

                    # Se não encontrou em namespaces comuns, tentar listar todos os Gateways
                    # (algumas versões da API podem suportar isso)
                    try:
                        path = f"/apis/{api_group}/{api_version_part}/gateways"

                        response = self.api_client.call_api(
                            path,
                            'GET',
                            auth_settings=['BearerToken'],
                            response_type='object',
                            _preload_content=True
                        )

                        data, status, headers = response

                        if status == 200 and isinstance(data, dict):
                            items = data.get('items', [])
                            if items and len(items) > 0:
                                # Pegar o primeiro Gateway encontrado
                                gateway = items[0]
                                metadata = gateway.get('metadata', {})
                                name = metadata.get('name', '')
                                namespace = metadata.get('namespace', '')

                                if name and namespace:
                                    return {
                                        "namespace": namespace,
                                        "name": name
                                    }
                    except ApiException as e:
                        # Se der 404 ou 405 (método não permitido), tentar próxima versão
                        if e.status in [404, 405]:
                            continue
                        # Outro erro, logar mas continuar
                        print(f"Warning: Error listing all Gateways via {api_version}: {e}")
                    except Exception as e:
                        # Erro inesperado, logar mas continuar
                        print(f"Warning: Unexpected error listing all Gateways via {api_version}: {e}")

                except Exception as e:
                    # Erro inesperado, logar mas continuar
                    print(f"Warning: Unexpected error getting Gateway via {api_version}: {e}")

            # Se não encontrou em nenhuma versão, retornar None
            return None

        except Exception as e:
            print(f"Error getting Gateway reference: {e}")
            return None

    def _parse_memory(self, memory_str: str) -> int:
        """Converte string de memória (ex: '512Mi', '1Gi', '1000M') para MB."""
        if not memory_str:
            return 0
        memory_str = memory_str.strip()

        # Remover sufixos e converter
        if memory_str.endswith('Ki'):
            return int(memory_str[:-2]) // 1024
        elif memory_str.endswith('Mi'):
            return int(memory_str[:-2])
        elif memory_str.endswith('Gi'):
            return int(memory_str[:-2]) * 1024
        elif memory_str.endswith('Ti'):
            return int(memory_str[:-2]) * 1024 * 1024
        elif memory_str.endswith('K'):
            return int(memory_str[:-1]) // 1000
        elif memory_str.endswith('M'):
            return int(memory_str[:-1])
        elif memory_str.endswith('G'):
            return int(memory_str[:-1]) * 1000
        elif memory_str.endswith('T'):
            return int(memory_str[:-1]) * 1000 * 1000
        else:
            # Assumir bytes
            return int(memory_str) // (1024 * 1024)
