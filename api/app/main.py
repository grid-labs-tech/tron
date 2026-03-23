import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html

from app.audit.core.audit_config import get_siem_url, is_audit_enabled
from app.shared.database.database import Base, engine
from app.shared.middleware.audit_middleware import AuditMiddleware

# Also import Base from old database to ensure compatibility
from app.database import Base as OldBase

# Import new structure routers
from app.applications.api.application_handlers import router as applications_router
from app.instances.api.instance_handlers import router as instances_router
from app.environments.api.environment_handlers import router as environments_router
from app.clusters.api.cluster_handlers import (
    router as clusters_router,
    router_env_clusters as clusters_by_environment_router,
)
from app.templates.api.template_handlers import router as templates_router
from app.templates.api.component_template_config_handlers import (
    router as component_template_config_router,
)
from app.users.api.user_handlers import router as users_router
from app.auth.api.auth_handlers import router as auth_router
from app.auth.api.identity_provider_handlers import router as identity_provider_router
from app.organizations.api.group_member_handlers import router as group_members_router
from app.dashboard.api.dashboard_handlers import router as dashboard_router

# Version is injected
from app.webapps.api.webapp_handlers import router as webapps_router
from app.workers.api.worker_handlers import router as workers_router
from app.cron.api.cron_handlers import router as crons_router
from app.setup.api.setup_handlers import router as setup_router
from app.organizations.api.organization_handlers import router as organizations_router
from app.organizations.api.group_handlers import router as groups_router

# Version is injected at build time via APP_VERSION environment variable
APP_VERSION = os.getenv("APP_VERSION", "dev")

# Ensure both Bases are the same instance
assert Base is OldBase, (
    "Base instances must be the same for SQLAlchemy relationships to work"
)

# Import all models to ensure they are registered with SQLAlchemy
# Import order matters for SQLAlchemy relationships
# Models referenced by relationships must be imported before models that reference them
from app.users.infra.user_model import User  # noqa: F401, E402
from app.organizations.infra.organization_model import Organization  # noqa: F401, E402
from app.organizations.infra.organization_member_model import OrganizationMember  # noqa: F401, E402
from app.organizations.infra.group_model import Group  # noqa: F401, E402
from app.organizations.infra.group_member_model import GroupMember  # noqa: F401, E402
from app.environments.infra.environment_model import Environment  # noqa: F401, E402
from app.applications.infra.application_model import Application  # noqa: F401, E402
from app.instances.infra.instance_model import Instance  # noqa: F401, E402
from app.clusters.infra.cluster_model import Cluster  # noqa: F401, E402
from app.templates.infra.template_model import Template  # noqa: F401, E402
from app.templates.infra.component_template_config_model import ComponentTemplateConfig  # noqa: F401, E402
from app.environments.infra.environment_settings_model import EnvironmentSettings  # noqa: F401, E402
from app.auth.infra.token_model import Token  # noqa: F401, E402
from app.auth.infra.identity_provider_model import IdentityProvider  # noqa: F401, E402
from app.auth.infra.user_social_account_model import UserSocialAccount  # noqa: F401, E402
from app.webapps.infra.application_component_model import ApplicationComponent  # noqa: F401, E402
from app.shared.infra.cluster_instance_model import ClusterInstance  # noqa: F401, E402

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tron",
    summary="Platform as a Service built on top of kubernetes",
    version=APP_VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,  # Disable default ReDoc to use custom one with fixed CDN URL
)

# CORS Configuration
# Include common dev origins so preflight (OPTIONS) succeeds from portal
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:80,http://127.0.0.1:3000,http://127.0.0.1:80",
).split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]

CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = os.getenv(
    "CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
).split(",")
CORS_ALLOW_METHODS = [method.strip() for method in CORS_ALLOW_METHODS if method.strip()]

CORS_ALLOW_HEADERS = os.getenv(
    "CORS_ALLOW_HEADERS",
    "Content-Type,Authorization,Accept,Origin,X-Requested-With,x-tron-token",
).split(",")
CORS_ALLOW_HEADERS = [header.strip() for header in CORS_ALLOW_HEADERS if header.strip()]

# Audit logging - only add when enabled and SIEM URL is configured
if is_audit_enabled() and get_siem_url():
    app.add_middleware(AuditMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Include new structure routers
app.include_router(applications_router)
app.include_router(instances_router)
app.include_router(environments_router)
app.include_router(clusters_router)
app.include_router(clusters_by_environment_router)
app.include_router(templates_router)
app.include_router(component_template_config_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(identity_provider_router, prefix="/auth")
app.include_router(dashboard_router)
app.include_router(webapps_router)
app.include_router(workers_router)
app.include_router(crons_router)
app.include_router(setup_router)
app.include_router(organizations_router)
app.include_router(groups_router)
app.include_router(group_members_router)

# Legacy routers removed - all features migrated to new structure


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc endpoint with fixed CDN URL"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy"}
