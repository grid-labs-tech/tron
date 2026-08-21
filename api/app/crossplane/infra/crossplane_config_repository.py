from sqlalchemy.orm import Session

from app.crossplane.infra.crossplane_config_model import EnvironmentCrossplaneConfig


class CrossplaneConfigRepository:
    """Persistence for environment Crossplane config. No business logic."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_environment_id(
        self, environment_id: int
    ) -> EnvironmentCrossplaneConfig | None:
        return (
            self.db.query(EnvironmentCrossplaneConfig)
            .filter(EnvironmentCrossplaneConfig.environment_id == environment_id)
            .first()
        )

    def create(self, row: EnvironmentCrossplaneConfig) -> EnvironmentCrossplaneConfig:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: EnvironmentCrossplaneConfig) -> EnvironmentCrossplaneConfig:
        self.db.commit()
        self.db.refresh(row)
        return row
