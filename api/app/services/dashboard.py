from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import application as ApplicationModel
from app.models import instance as InstanceModel
from app.models import application_components as ApplicationComponentModel
from app.models import cluster as ClusterModel
from app.models import environment as EnvironmentModel
from app.models import cluster_instance as ClusterInstanceModel
from app.schemas import dashboard as DashboardSchema


class DashboardService:
    @staticmethod
    def get_dashboard_overview(db: Session) -> DashboardSchema.DashboardOverview:
        # Total de aplicações
        applications_count = db.query(func.count(ApplicationModel.Application.id)).scalar() or 0

        # Total de instâncias
        instances_count = db.query(func.count(InstanceModel.Instance.id)).scalar() or 0

        # Estatísticas de componentes
        total_components = db.query(func.count(ApplicationComponentModel.ApplicationComponent.id)).scalar() or 0

        webapp_count = (
            db.query(func.count(ApplicationComponentModel.ApplicationComponent.id))
            .filter(ApplicationComponentModel.ApplicationComponent.type == ApplicationComponentModel.WebappType.webapp)
            .scalar() or 0
        )

        worker_count = (
            db.query(func.count(ApplicationComponentModel.ApplicationComponent.id))
            .filter(ApplicationComponentModel.ApplicationComponent.type == ApplicationComponentModel.WebappType.worker)
            .scalar() or 0
        )

        cron_count = (
            db.query(func.count(ApplicationComponentModel.ApplicationComponent.id))
            .filter(ApplicationComponentModel.ApplicationComponent.type == ApplicationComponentModel.WebappType.cron)
            .scalar() or 0
        )

        enabled_components = (
            db.query(func.count(ApplicationComponentModel.ApplicationComponent.id))
            .filter(ApplicationComponentModel.ApplicationComponent.enabled == True)
            .scalar() or 0
        )

        disabled_components = total_components - enabled_components

        # Total de clusters
        clusters_count = db.query(func.count(ClusterModel.Cluster.id)).scalar() or 0

        # Total de environments
        environments_count = db.query(func.count(EnvironmentModel.Environment.id)).scalar() or 0

        # Componentes por environment
        components_by_environment = {}
        env_components = (
            db.query(
                EnvironmentModel.Environment.name,
                func.count(ApplicationComponentModel.ApplicationComponent.id)
            )
            .join(InstanceModel.Instance, InstanceModel.Instance.environment_id == EnvironmentModel.Environment.id)
            .join(ApplicationComponentModel.ApplicationComponent, ApplicationComponentModel.ApplicationComponent.instance_id == InstanceModel.Instance.id)
            .group_by(EnvironmentModel.Environment.name)
            .all()
        )
        for env_name, count in env_components:
            components_by_environment[env_name] = count

        # Componentes por cluster
        components_by_cluster = {}
        cluster_components = (
            db.query(
                ClusterModel.Cluster.name,
                func.count(ApplicationComponentModel.ApplicationComponent.id)
            )
            .join(ClusterInstanceModel.ClusterInstance, ClusterInstanceModel.ClusterInstance.cluster_id == ClusterModel.Cluster.id)
            .join(ApplicationComponentModel.ApplicationComponent, ApplicationComponentModel.ApplicationComponent.id == ClusterInstanceModel.ClusterInstance.application_component_id)
            .group_by(ClusterModel.Cluster.name)
            .all()
        )
        for cluster_name, count in cluster_components:
            components_by_cluster[cluster_name] = count

        return DashboardSchema.DashboardOverview(
            applications=applications_count,
            instances=instances_count,
            components=DashboardSchema.ComponentStats(
                total=total_components,
                webapp=webapp_count,
                worker=worker_count,
                cron=cron_count,
                enabled=enabled_components,
                disabled=disabled_components,
            ),
            clusters=clusters_count,
            environments=environments_count,
            components_by_environment=components_by_environment,
            components_by_cluster=components_by_cluster,
        )

