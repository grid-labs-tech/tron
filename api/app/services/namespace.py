from fastapi import HTTPException

import app.models.namespace as NamespaceModel
import app.models.webapp as WebappModel
import app.schemas.namespace as NamespaceSchema

from sqlalchemy.orm import Session
from uuid import uuid4
from uuid import UUID


class NamespaceService:
    def get_namespace(db: Session, namespace_uuid: UUID):
        db_namespace = (
            db.query(NamespaceModel.Namespace)
            .filter(NamespaceModel.Namespace.uuid == namespace_uuid)
            .first()
        )

        if db_namespace is None:
            raise HTTPException(status_code=404, detail="Namespace not found")

        return db_namespace

    def get_namespaces(db: Session, skip: int = 0, limit: int = 100):
        return db.query(NamespaceModel.Namespace).offset(skip).limit(limit).all()

    def delete_namespace(db: Session, namespace_uuid: UUID):

        db_namespace = (
            db.query(NamespaceModel.Namespace)
            .filter(NamespaceModel.Namespace.uuid == namespace_uuid)
            .first()
        )
        if db_namespace is None:
            raise HTTPException(status_code=404, detail="Namespace not found")

        associated_webapps = (
            db.query(WebappModel.Webapp)
            .filter(WebappModel.Webapp.namespace_id == db_namespace.id)
            .all()
        )
        if associated_webapps:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete namespace with associated webapps",
            )

        db.delete(db_namespace)
        db.commit()
        return {"detail": "Namespace deleted successfully"}

    def upsert_namespace(
        db: Session,
        namespace: NamespaceSchema.NamespaceCreate,
        namespace_uuid: UUID = None,
    ):
        if namespace_uuid:
            db_namespace = (
                db.query(NamespaceModel.Namespace)
                .filter(NamespaceModel.Namespace.uuid == namespace_uuid)
                .first()
            )
            if db_namespace:
                db_namespace.name = namespace.name
                db.commit()
                db.refresh(db_namespace)
                return db_namespace

        query_namespace = (
            db.query(NamespaceModel.Namespace)
            .filter(NamespaceModel.Namespace.name == namespace.name)
            .first()
        )

        if  query_namespace:
            raise HTTPException(status_code=400, detail="Namespace name already taken")

        new_namespace = NamespaceModel.Namespace(uuid=uuid4(), name=namespace.name)
        db.add(new_namespace)
        db.commit()
        db.refresh(new_namespace)

        return new_namespace
