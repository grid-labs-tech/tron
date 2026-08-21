from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.shared.database.database import Base


class EnvironmentCrossplaneConfig(Base):
    __tablename__ = "environment_crossplane_configs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    environment_id = Column(
        Integer,
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    cluster_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey("clusters.uuid", ondelete="SET NULL"),
        nullable=True,
    )
    aws_region = Column(String, nullable=False, default="", server_default="")
    aws_account_id = Column(String, nullable=False, default="", server_default="")
    provider_config = Column(String, nullable=False, default="", server_default="")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    environment = relationship("Environment", back_populates="crossplane_config")

    __table_args__ = (
        UniqueConstraint("environment_id", name="uq_crossplane_config_environment_id"),
        UniqueConstraint("uuid", name="uq_crossplane_config_uuid"),
    )
