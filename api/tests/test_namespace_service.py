import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from unittest.mock import ANY
from fastapi import HTTPException
from app.services.namespace import NamespaceService
from app.schemas.namespace import NamespaceCreate
from app.models.namespace import Namespace as NamespaceModel


def test_create_namespace_success(mocker):
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = None

    namespace_data = NamespaceCreate(name="test-namespace")

    mock_namespace_model = MagicMock(spec=NamespaceModel)
    mock_namespace_model.name = namespace_data.name
    mock_namespace_model.uuid = uuid4()

    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = mock_namespace_model

    result = NamespaceService.upsert_namespace(mock_db, namespace=namespace_data)

    assert result.name == "test-namespace"
    assert isinstance(result.uuid, uuid4().__class__)

    mock_query.filter.assert_called_once_with(ANY)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_get_namespace_success(mocker):

    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_namespace = NamespaceModel(name="test-namespace", uuid=uuid4())
    mock_query.filter.return_value.first.return_value = mock_namespace

    result = NamespaceService.get_namespace(mock_db, mock_namespace.uuid)

    assert result == mock_namespace


def test_get_namespace_not_found(mocker):

    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_query.filter.return_value.first.return_value = None

    namespace_uuid = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        NamespaceService.get_namespace(mock_db, namespace_uuid)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Namespace not found"


def test_delete_namespace_success(mock_db):

    namespace_uuid = uuid4()

    mock_namespace = MagicMock(spec=NamespaceModel)
    mock_namespace.id = 1
    mock_namespace.uuid = namespace_uuid
    mock_db.query.return_value.filter.return_value.first.return_value = mock_namespace

    mock_db.query.return_value.filter.return_value.all.return_value = []

    result = NamespaceService.delete_namespace(mock_db, namespace_uuid)

    assert result == {"detail": "Namespace deleted successfully"}


def test_delete_namespace_not_found(mock_db):

    namespace_uuid = uuid4()

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        NamespaceService.delete_namespace(mock_db, namespace_uuid)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Namespace not found"


def test_delete_namespace_with_associated_webapps(mock_db):

    namespace_uuid = uuid4()

    mock_namespace = MagicMock(spec=NamespaceModel)
    mock_namespace.id = 1
    mock_namespace.uuid = namespace_uuid
    mock_db.query.return_value.filter.return_value.first.return_value = mock_namespace

    mock_db.query.return_value.filter.return_value.all.return_value = [MagicMock()]

    with pytest.raises(HTTPException) as exc_info:
        NamespaceService.delete_namespace(mock_db, namespace_uuid)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Cannot delete namespace with associated webapps"


def test_get_namespaces_success(mock_db):
    mock_namespace_1 = MagicMock(spec=NamespaceModel)
    mock_namespace_1.uuid = uuid4()
    mock_namespace_2 = MagicMock(spec=NamespaceModel)
    mock_namespace_2.uuid = uuid4()

    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [
        mock_namespace_1,
        mock_namespace_2,
    ]

    result = NamespaceService.get_namespaces(mock_db, skip=0, limit=2)

    assert len(result) == 2
    assert result[0] == mock_namespace_1
    assert result[1] == mock_namespace_2

    mock_db.query.return_value.offset.assert_called_once_with(0)
    mock_db.query.return_value.offset.return_value.limit.assert_called_once_with(2)


def test_get_namespaces_empty(mock_db):

    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = (
        []
    )

    result = NamespaceService.get_namespaces(mock_db, skip=0, limit=2)

    assert result == []

    mock_db.query.return_value.offset.assert_called_once_with(0)
    mock_db.query.return_value.offset.return_value.limit.assert_called_once_with(2)
