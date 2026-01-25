#!/usr/bin/env python3
"""
Script to update local cluster token from k3s.
This script reads the token from the tron-admin-token secret in k3s
and updates the local-cluster in the database.
"""
import sys
import os
import subprocess
import time

# Add root directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the app to ensure all models are loaded
from app.main import app  # noqa - this loads all models properly

from sqlalchemy.orm import Session
from app.shared.database.database import SessionLocal
from app.clusters.infra.cluster_model import Cluster


def get_k3s_token_from_secret():
    """Get the k3s token from the tron-admin-token secret"""
    max_retries = 30
    
    for i in range(max_retries):
        try:
            # Use kubectl to get the token from the secret
            result = subprocess.run(
                [
                    'kubectl', '--kubeconfig=/output/kubeconfig.yaml',
                    'get', 'secret', 'tron-admin-token',
                    '-n', 'kube-system',
                    '-o', 'jsonpath={.data.token}'
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                import base64
                token = base64.b64decode(result.stdout).decode('utf-8')
                return token
                
        except Exception as e:
            pass
        
        if i < max_retries - 1:
            print(f"  Waiting for k3s token... ({i + 1}/{max_retries})")
            time.sleep(2)
    
    return None


def update_cluster_token():
    """Update the local cluster token"""
    print("🔧 Updating local cluster token...")
    
    # Get token from k3s
    token = get_k3s_token_from_secret()
    
    if not token:
        print("⚠ Could not get k3s token. Cluster token not updated.")
        print("  You can update it later via the Tron UI.")
        return
    
    db: Session = SessionLocal()
    
    try:
        # Find local cluster
        cluster = db.query(Cluster).filter(
            Cluster.name == 'local-cluster'
        ).first()
        
        if not cluster:
            print("⚠ Local cluster not found. Skipping token update.")
            return
        
        # Update token
        cluster.token = token
        db.commit()
        
        print("✓ Local cluster token updated successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error updating cluster token: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    update_cluster_token()
