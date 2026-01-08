import importlib
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import *
from .database import Base, engine

# Import all models to ensure they are registered with SQLAlchemy
import app.models.cluster
import app.models.environment
import app.models.cluster_instance
import app.models.instance
import app.models.settings
import app.models.template
import app.models.component_template_config
import app.models.application
import app.models.application_components
import app.models.user
import app.models.token

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tron",
    summary="Platform as a Service built on top of kubernetes",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,  # Disable default ReDoc to use custom one with fixed CDN URL
)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:80").split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]

CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
CORS_ALLOW_METHODS = [method.strip() for method in CORS_ALLOW_METHODS if method.strip()]

CORS_ALLOW_HEADERS = os.getenv(
    "CORS_ALLOW_HEADERS",
    "Content-Type,Authorization,Accept,Origin,X-Requested-With,x-tron-token"
).split(",")
CORS_ALLOW_HEADERS = [header.strip() for header in CORS_ALLOW_HEADERS if header.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

ROUTERS_PATH = "./app/routers"


def include_all_routers(app: FastAPI):
    for file in os.listdir(ROUTERS_PATH):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]
            module_path = f"app.routers.{module_name}"

            module = importlib.import_module(module_path)

            if hasattr(module, "router"):
                app.include_router(module.router, tags=[module_name])


include_all_routers(app)

# Fix ReDoc CDN URL - use stable version instead of @next
from fastapi.openapi.docs import get_redoc_html

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc endpoint with fixed CDN URL"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )
