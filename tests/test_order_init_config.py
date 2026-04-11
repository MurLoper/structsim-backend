from app.constants import ErrorCode
from app.models.config import Project
from app.models.order import Order
from app.services.external_data import project_phase_repository


def test_order_init_project_config_missing_project_id(client, auth_headers):
    response = client.get("/api/v1/orders/init-project-config", headers=auth_headers)
    data = response.get_json()
    assert data["code"] == ErrorCode.VALIDATION_ERROR


def test_order_init_project_config_success(client, db_session, auth_headers, user, monkeypatch):
    project = Project(name="项目A", code="PROJ_INIT", valid=1, sort=1)
    db_session.add(project)
    db_session.commit()

    recent_order = Order(
        order_no="ORD-TEST-001",
        project_id=project.id,
        participant_uids=["tester", "helper"],
        created_by="tester",
        status=0,
        progress=0,
    )
    db_session.add(recent_order)
    db_session.commit()

    monkeypatch.setattr(
        project_phase_repository,
        "get_default_phase_id",
        lambda project_id: 2 if project_id == project.id else None,
    )
    monkeypatch.setattr(
        project_phase_repository,
        "list_project_phases",
        lambda project_id: [{"phaseId": 2, "phaseName": "阶段二"}]
        if project_id == project.id
        else [],
    )

    response = client.get(
        f"/api/v1/orders/init-project-config?projectId={project.id}",
        headers=auth_headers,
    )
    data = response.get_json()

    assert data["code"] == ErrorCode.SUCCESS
    assert data["data"]["projectId"] == project.id
    assert data["data"]["projectName"] == project.name
    assert data["data"]["defaultPhaseId"] == 2
    assert data["data"]["phases"] == [{"phaseId": 2, "phaseName": "阶段二"}]
    assert len(data["data"]["participantCandidates"]) >= 1
    assert data["data"]["participantCandidates"][0]["domainAccount"] == user.domain_account
