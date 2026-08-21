from uuid import uuid4, UUID
from typing import List, Any
from app.environments.infra.environment_repository import EnvironmentRepository
from app.environments.infra.environment_model import Environment as EnvironmentModel
from app.environments.infra.environment_settings_model import (
    EnvironmentSettings as EnvironmentSettingsModel,
)
from app.environments.infra.environment_settings_repository import (
    EnvironmentSettingsRepository,
)
from app.environments.core.environment_settings_defaults import (
    DEFAULT_ENVIRONMENT_SETTINGS,
    merge_missing_default_settings,
)
from app.environments.api.environment_dto import (
    EnvironmentCreate,
    Environment,
    EnvironmentWithClusters,
    EnvironmentClusterSummary,
)
from app.environments.core.environment_validators import (
    validate_environment_create_dto,
    validate_environment_can_be_deleted,
)


class EnvironmentService:
    """Business logic for environments. No direct database access."""

    def __init__(
        self,
        repository: EnvironmentRepository,
        settings_repository: EnvironmentSettingsRepository | None = None,
    ):
        self.repository = repository
        self.settings_repository = settings_repository

    def create_environment(
        self, dto: EnvironmentCreate, organization_id: int
    ) -> Environment:
        """Create a new environment within an organization."""
        validate_environment_create_dto(dto)

        environment = self._build_environment_entity(dto, organization_id)
        created = self.repository.create(environment)
        if self.settings_repository:
            settings_row = EnvironmentSettingsModel(
                uuid=uuid4(),
                environment_id=created.id,
                organization_id=organization_id,
                settings=DEFAULT_ENVIRONMENT_SETTINGS,
            )
            self.settings_repository.create(settings_row)
        return created

    def update_environment(
        self, uuid: UUID, dto: EnvironmentCreate, organization_id: int
    ) -> Environment:
        """Update an existing environment within an organization."""
        validate_environment_create_dto(dto)

        environment = self.repository.find_by_uuid_and_organization(
            uuid, organization_id
        )
        if not environment:
            raise ValueError(f"Environment with UUID {uuid} not found in organization")

        environment.name = dto.name

        return self.repository.update(environment)

    def get_environment_id_for_organization(
        self, organization_id: int, environment_uuid: UUID
    ) -> int:
        """Resolve environment UUID to ID. Validates that environment belongs to organization.
        Raises ValueError if not found or does not belong to organization.
        Use this when you need environment_id (e.g. for authorization) from (org_id, env_uuid).
        """
        environment = self.repository.find_by_uuid_and_organization(
            environment_uuid, organization_id
        )
        if not environment:
            raise ValueError(
                f"Environment with UUID {environment_uuid} not found in organization"
            )
        return environment.id

    def get_environment(
        self, uuid: UUID, organization_id: int
    ) -> EnvironmentWithClusters:
        """Get environment by UUID with clusters and settings within an organization."""
        environment = self.repository.find_by_uuid_and_organization(
            uuid, organization_id
        )
        if not environment:
            raise ValueError(f"Environment with UUID {uuid} not found in organization")

        return self._serialize_environment_with_clusters(environment)

    def get_environments(
        self, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[EnvironmentWithClusters]:
        """Get all environments with clusters and settings within an organization."""
        environments = self.repository.find_all(
            organization_id=organization_id, skip=skip, limit=limit
        )
        return [self._serialize_environment_with_clusters(env) for env in environments]

    def delete_environment(self, uuid: UUID, organization_id: int) -> dict:
        """Delete an environment within an organization."""
        environment = self.repository.find_by_uuid_and_organization(
            uuid, organization_id
        )
        if not environment:
            raise ValueError(f"Environment with UUID {uuid} not found in organization")

        validate_environment_can_be_deleted(self.repository, uuid)

        self.repository.delete(environment)

        return {"detail": "Environment deleted successfully"}

    def update_environment_settings(
        self,
        environment_uuid: UUID,
        settings_values: dict[str, Any],
        organization_id: int,
    ) -> List[dict]:
        """
        Update setting values by key (idempotent).
        key, description and type are never changed; only value is updated per key.
        """
        environment = self.repository.find_by_uuid_and_organization(
            environment_uuid, organization_id
        )
        if not environment:
            raise ValueError(
                f"Environment with UUID {environment_uuid} not found in organization"
            )
        if not self.settings_repository:
            raise ValueError("Settings repository not available")
        row = self.settings_repository.find_by_environment_id(environment.id)
        if not row:
            row = EnvironmentSettingsModel(
                uuid=uuid4(),
                environment_id=environment.id,
                organization_id=organization_id,
                settings=[],
            )
            self.settings_repository.create(row)
        current = merge_missing_default_settings(
            list(row.settings) if row.settings else []
        )
        keys_to_value = {
            k: v for k, v in settings_values.items() if k and not k.startswith("_")
        }
        new_settings = []
        for item in current:
            if isinstance(item, dict):
                copied = dict(item)
                if copied.get("key") in keys_to_value:
                    copied["value"] = keys_to_value[copied["key"]]
                new_settings.append(copied)
            else:
                new_settings.append(item)

        row.settings = new_settings
        self.settings_repository.update(row)
        return new_settings

    def reset_environment_settings(
        self, environment_uuid: UUID, organization_id: int
    ) -> List[dict]:
        """Reset settings to default values. Returns the new settings list."""
        environment = self.repository.find_by_uuid_and_organization(
            environment_uuid, organization_id
        )
        if not environment:
            raise ValueError(
                f"Environment with UUID {environment_uuid} not found in organization"
            )
        if not self.settings_repository:
            raise ValueError("Settings repository not available")
        row = self.settings_repository.find_by_environment_id(environment.id)
        if not row:
            row = EnvironmentSettingsModel(
                uuid=uuid4(),
                environment_id=environment.id,
                organization_id=organization_id,
                settings=[],
            )
            self.settings_repository.create(row)
        defaults = [dict(item) for item in DEFAULT_ENVIRONMENT_SETTINGS]
        row.settings = defaults
        self.settings_repository.update(row)
        return defaults

    def _build_environment_entity(
        self, dto: EnvironmentCreate, organization_id: int
    ) -> EnvironmentModel:
        """Build Environment entity from DTO."""
        return EnvironmentModel(
            uuid=uuid4(),
            name=dto.name,
            organization_id=organization_id,
        )

    def _serialize_environment_with_clusters(
        self, environment: EnvironmentModel
    ) -> EnvironmentWithClusters:
        """Serialize environment with clusters and settings."""
        settings_list = []
        if (
            environment.environment_settings
            and environment.environment_settings.settings
        ):
            settings_list = environment.environment_settings.settings
        settings_list = merge_missing_default_settings(settings_list)
        return EnvironmentWithClusters(
            uuid=environment.uuid,
            name=environment.name,
            clusters=[
                EnvironmentClusterSummary(
                    uuid=cluster.uuid,
                    name=cluster.name,
                )
                for cluster in environment.clusters
            ],
            settings=settings_list,
            created_at=environment.created_at.isoformat(),
            updated_at=environment.updated_at.isoformat(),
        )
