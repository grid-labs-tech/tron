import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock
from app.database import Base

import app.models.namespace as NamespaceModel
import app.models.application_components as WebappDeployModel
import app.models.environment as EnvironmentModel
import app.models.workload as WorkloadModel
import app.models.cluster_instance as InstanceModel
import app.models.cluster as ClusterModel
import app.models.settings as SettingsrModel

@pytest.fixture()
def mock_db():
    engine = create_engine('sqlite:///:memory:')
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = MagicMock()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
