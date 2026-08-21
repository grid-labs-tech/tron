from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.shared.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


class Environment(Base):
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization", back_populates="environments")
    environment_settings = relationship(
        "EnvironmentSettings",
        back_populates="environment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    crossplane_config = relationship(
        "EnvironmentCrossplaneConfig",
        back_populates="environment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    clusters = relationship("Cluster", back_populates="environment")
    instances = relationship("Instance", back_populates="environment")
    groups = relationship("Group", back_populates="environment")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uix_environment_org_name"),
    )
