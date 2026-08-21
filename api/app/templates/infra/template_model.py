from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.shared.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.shared.database.types import JSONBCompat


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False, index=True)  # webapp, cron, worker, etc.
    content = Column(Text, nullable=False)  # Jinja2 template content
    variables_schema = Column(
        Text, nullable=True
    )  # JSON with schema of available variables
    template_settings = Column(JSONBCompat, nullable=False, default=list)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "slug", name="uix_templates_organization_slug"
        ),
    )

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization", back_populates="templates")
    component_configs = relationship(
        "ComponentTemplateConfig", back_populates="template", lazy="select"
    )
