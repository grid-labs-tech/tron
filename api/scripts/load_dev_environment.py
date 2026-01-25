#!/usr/bin/env python3
"""
Script to load development environment (cluster, environment)
This script is designed for the local Docker development setup.
"""
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the app to ensure all models are loaded
from app.main import app  # noqa - this loads all models properly

from sqlalchemy.orm import Session
from app.shared.database.database import SessionLocal
from app.environments.infra.environment_model import Environment
from app.clusters.infra.cluster_model import Cluster


def get_k3s_token():
    """Get the k3s service account token from environment variable"""
    # The token is set by docker-compose from the tron-admin-token secret
    return os.environ.get('K3S_TOKEN', '')


def load_dev_environment():
    """Load development environment and cluster"""
    db: Session = SessionLocal()

    try:
        # Check if local environment already exists
        existing_env = db.query(Environment).filter(
            Environment.name == 'local'
        ).first()

        if existing_env:
            print("✓ Local environment already exists. Skipping creation.")
            env_id = existing_env.id
        else:
            # Create local environment
            dev_env = Environment(name='local')
            db.add(dev_env)
            db.commit()
            db.refresh(dev_env)
            env_id = dev_env.id
            print("✓ Local environment created successfully!")

        # Check if local cluster already exists
        existing_cluster = db.query(Cluster).filter(
            Cluster.name == 'local-cluster'
        ).first()

        if existing_cluster:
            print("✓ Local cluster already exists. Skipping creation.")
            return

        # Get k3s token - for dev environment we'll use a placeholder
        # The actual token should be set via the Tron UI or API
        k3s_token = get_k3s_token()
        
        if not k3s_token:
            print("⚠ K3s token not found. Creating cluster with placeholder token.")
            print("  Please update the cluster token via the Tron UI.")
            k3s_token = "placeholder-update-via-ui"

        # Create local cluster pointing to k3s-server (port 5443 as configured in docker-compose)
        local_cluster = Cluster(
            name='local-cluster',
            api_address='https://k3s-server:5443',
            token=k3s_token,
            environment_id=env_id
        )

        db.add(local_cluster)
        db.commit()

        print("✓ Local cluster created successfully!")
        print("  Name: local-cluster")
        print("  API Address: https://k3s-server:6443")
        if k3s_token == "placeholder-update-via-ui":
            print("  ⚠ Token: PLACEHOLDER - Update via Tron UI!")

    except Exception as e:
        db.rollback()
        print(f"✗ Error creating local environment: {e}")
        # Don't exit with error - this is optional setup
    finally:
        db.close()


if __name__ == "__main__":
    load_dev_environment()
