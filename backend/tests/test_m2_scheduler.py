"""M2：Fake 全链路、电梯编排、简单互斥、报警与报告。"""

from __future__ import annotations

import time

from tests.conftest import auth_header


def _drain(client, headers):
    response = client.post("/api/v1/scheduler/drain", headers=headers)
    assert response.status_code == 200, response.text


def test_single_robot_sampling_report(client):
    headers = auth_header(client)
    created = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-a", "client_request_id": "job-1"})
    assert created.status_code == 200, created.text
    task_id = created.json()["id"]
    replay = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-a", "client_request_id": "job-1"})
    assert replay.json()["code"] == "IDEMPOTENCY_REPLAY"
    assert replay.json()["id"] == task_id
    _drain(client, headers)
    task = next(item for item in client.get("/api/v1/tasks", headers=headers).json()["items"] if item["id"] == task_id)
    assert task["status"] == "Succeeded"
    measurements = client.get("/api/v1/measurements", headers=headers, params={"task_id": task_id}).json()["items"]
    metrics = {item["metric"] for item in measurements}
    assert "particle.0.5um" in metrics
    assert "temp_c" in metrics
    assert "humidity_rh" in metrics
    assert "air_speed_mps" in metrics
    assert all(item["quality"] == "good" for item in measurements)
    reports = client.get("/api/v1/reports", headers=headers).json()["items"]
    assert any(item["task_ref"] == task_id and item["format"] == "html" for item in reports)
    robots = client.get("/api/v1/robots", headers=headers).json()["items"]
    robot = next(item for item in robots if item["id"] == "robot-01")
    assert robot["status"]["pose"]["x"] == 2
    assert robot["status"]["pose"]["y"] == 3


def test_limit_alarm_ack_close_and_csv(client):
    headers = auth_header(client)
    patched = client.patch(
        "/api/v1/settings/limits",
        headers=headers,
        json={"point_id": "point-a", "limits": {"particle.0.5um": {"max": 10, "unit": "counts"}, "temp_c": {"min": 18, "max": 26}}},
    )
    assert patched.status_code == 200, patched.text
    created = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-a"})
    task_id = created.json()["id"]
    _drain(client, headers)
    alarms = client.get("/api/v1/alarms", headers=headers, params={"state": "open"}).json()["items"]
    assert any(item["rule_id"] == "limit.particle.0.5um" for item in alarms)
    alarm_id = next(item["id"] for item in alarms if item["rule_id"] == "limit.particle.0.5um")
    viewer = auth_header(client, "viewer", "Viewer123!")
    assert client.post(f"/api/v1/alarms/{alarm_id}/close", headers=viewer, json={"note": "no"}).status_code == 403
    assert client.post(f"/api/v1/alarms/{alarm_id}/ack", headers=headers, json={"note": "已知晓"}).status_code == 200
    closed = client.post(f"/api/v1/alarms/{alarm_id}/close", headers=headers, json={"note": "关闭"})
    assert closed.status_code == 200
    assert closed.json()["state"] == "closed"
    exported = client.get("/api/v1/alarms/export", headers=auth_header(client, "operator", "Operator1!"))
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    assert "limit.particle.0.5um" in exported.text
    reports = client.get("/api/v1/reports", headers=headers).json()["items"]
    report = next(item for item in reports if item["task_ref"] == task_id)
    assert report["summary"]["breach_count"] >= 1
    html = client.get(f"/api/v1/reports/{report['id']}", headers=headers).json()["html"]
    assert "particle.0.5um" in html


def test_elevator_transfer_and_mutex(client):
    headers = auth_header(client)
    created = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "robot_id": "robot-01",
            "skills": [
                {"type": "elevator_transfer", "params": {"elevator_id": "elev-01", "to_floor": 2, "enter_point_id": "point-a"}},
                {"type": "sample_particle", "params": {"point_id": "point-a"}},
            ],
        },
    )
    assert created.status_code == 200, created.text
    _drain(client, headers)
    task = client.get("/api/v1/tasks", headers=headers).json()["items"][-1]
    assert task["status"] == "Succeeded"
    elevators = client.get("/api/v1/elevators", headers=headers).json()["items"]
    assert elevators[0]["history"] == ["call:2", "enter", "exit:2"]

    client.patch("/api/v1/settings/features", headers=headers, json={"resource_mutex_on_conflict": "fail"})
    first = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-a"}).json()
    second = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-02", "point_id": "point-a"}).json()
    dispatched = client.post("/api/v1/scheduler/dispatch", headers=headers)
    assert dispatched.status_code == 200
    tasks = {item["id"]: item for item in client.get("/api/v1/tasks", headers=headers).json()["items"]}
    assert tasks[first["id"]]["status"] == "Running"
    assert tasks[second["id"]]["status"] == "Failed"
    assert tasks[second["id"]]["error_code"] == "CONFLICT_MUTEX"


def test_estop_offline_low_battery_and_uncertain(client):
    headers = auth_header(client)
    runtime = client.app.state.runtime
    runtime.registry.amr("robot-01").inject(estop=True, fault_msg="急停按钮")
    created = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"robot_id": "robot-01", "skills": [{"type": "navigate_to", "params": {"point_id": "point-b"}}]},
    )
    _drain(client, headers)
    task = next(item for item in client.get("/api/v1/tasks", headers=headers).json()["items"] if item["id"] == created.json()["id"])
    assert task["status"] == "Failed"
    assert task["error_code"] == "ESTOP"
    alarms = client.get("/api/v1/alarms", headers=headers).json()["items"]
    assert any(item["rule_id"] == "device.estop" for item in alarms)

    runtime.registry.amr("robot-01").inject(estop=False, clear_fault=True, online=False)
    client.get("/api/v1/robots", headers=headers)
    alarms = client.get("/api/v1/alarms", headers=headers).json()["items"]
    assert any(item["rule_id"] == "device.offline" for item in alarms)
    runtime.registry.amr("robot-01").inject(online=True, battery_pct=5)
    created = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-b"})
    _drain(client, headers)
    task = next(item for item in client.get("/api/v1/tasks", headers=headers).json()["items"] if item["id"] == created.json()["id"])
    assert task["status"] == "Succeeded"
    assert task["skills"][0]["type"] == "dock_charge"
    assert runtime.registry.amr("robot-01").get_status().battery_pct == 99

    runtime.registry.instrument("pc-02").transient_failures = 2
    created = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-02", "point_id": "point-b"})
    _drain(client, headers)
    measurements = client.get("/api/v1/measurements", headers=headers, params={"task_id": created.json()["id"]}).json()["items"]
    particle = next(item for item in measurements if item["metric"] == "particle.0.5um")
    assert particle["quality"] == "uncertain"


def test_idempotent_ingest_and_websocket(client):
    headers = auth_header(client)
    payload = {
        "device_id": "pc-01",
        "sample_id": "s-1",
        "metric": "temp_c",
        "unit": "C",
        "value": 21.5,
        "client_request_id": "upload-1",
        "point_id": "point-a",
        "robot_id": "robot-01",
        "ts": "2026-09-25T00:00:00+00:00",
    }
    first = client.post("/api/v1/measurements", headers=headers, json=payload)
    second = client.post("/api/v1/measurements", headers=headers, json={**payload, "value": 99})
    assert first.status_code == 200
    assert second.json()["code"] == "IDEMPOTENCY_REPLAY"
    assert second.json()["value"] == 21.5
    assert second.json()["id"] == first.json()["id"]
    token = headers["Authorization"].split()[1]
    with client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
        assert websocket.receive_json()["topic"] == "hello"
        websocket.send_json({"topics": ["measurement"]})
        assert websocket.receive_json()["topic"] == "subscribed"
        event = websocket.receive_json()
        assert event["topic"] == "measurement"


def test_composite_and_cluster_summary(client):
    headers = auth_header(client)
    composite = client.post(
        "/api/v1/composites",
        headers=headers,
        json={
            "name": "两轮",
            "children": [
                {"robot_id": "robot-01", "point_id": "point-a"},
                {"robot_id": "robot-01", "point_id": "point-b", "wait_seconds": 0},
            ],
        },
    )
    assert composite.status_code == 200, composite.text
    cluster = client.post(
        "/api/v1/clusters",
        headers=headers,
        json={
            "name": "双机",
            "items": [
                {"robot_id": "robot-01", "point_id": "point-a"},
                {"robot_id": "robot-02", "point_id": "point-b"},
            ],
        },
    )
    assert cluster.status_code == 200, cluster.text
    _drain(client, headers)
    composites = client.get("/api/v1/composites", headers=headers).json()["items"]
    assert composites[0]["status"] == "Succeeded"
    clusters = client.get("/api/v1/clusters", headers=headers).json()["items"]
    assert clusters[0]["status"] == "Succeeded"
    reports = client.get("/api/v1/reports", headers=headers).json()["items"]
    refs = {item["task_ref"] for item in reports}
    assert composite.json()["id"] in refs
    assert cluster.json()["id"] in refs


def test_cancel_releases_and_point_guard(client):
    headers = auth_header(client)
    created = client.post("/api/v1/tasks", headers=headers, json={"robot_id": "robot-01", "point_id": "point-a"})
    client.post("/api/v1/scheduler/dispatch", headers=headers)
    cancelled = client.post(f"/api/v1/tasks/{created.json()['id']}/cancel", headers=headers)
    assert cancelled.json()["status"] == "Cancelled"
    assert client.app.state.runtime.registry.amr("robot-01").cancel_count >= 1
    denied = client.delete("/api/v1/points/point-a", headers=headers)
    assert denied.status_code == 422
    created_point = client.post(
        "/api/v1/points",
        headers=headers,
        json={"id": "point-c", "map_id": "map-demo", "name": "C", "pose": {"x": 1, "y": 1, "theta": 0}, "limits": {}},
    )
    assert created_point.status_code == 200
    assert client.delete("/api/v1/points/point-c", headers=headers).status_code == 200


def test_queue_mutex_and_fault_disconnect_wait(client):
    headers = auth_header(client)
    created = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"robot_id": "robot-01", "skills": [{"type": "navigate_to", "params": {"point_id": "point-a"}}]},
    )
    assert created.json()["status"] == "Queued"
    first = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"robot_id": "robot-01", "skills": [{"type": "navigate_to", "params": {"point_id": "point-b"}}]},
    ).json()
    second = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"robot_id": "robot-02", "skills": [{"type": "navigate_to", "params": {"point_id": "point-b"}}]},
    ).json()
    _drain(client, headers)
    tasks = {item["id"]: item for item in client.get("/api/v1/tasks", headers=headers).json()["items"]}
    assert tasks[first["id"]]["status"] == "Succeeded"
    assert tasks[second["id"]]["status"] == "Succeeded"

    runtime = client.app.state.runtime
    runtime.registry.amr("robot-01").inject(fault_code="E1", fault_msg="驱动故障")
    faulted = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"robot_id": "robot-01", "skills": [{"type": "navigate_to", "params": {"point_id": "point-a"}}]},
    ).json()
    _drain(client, headers)
    fault_task = next(item for item in client.get("/api/v1/tasks", headers=headers).json()["items"] if item["id"] == faulted["id"])
    assert fault_task["error_code"] == "FAULT"
    assert any(item["rule_id"] == "device.fault" for item in client.get("/api/v1/alarms", headers=headers).json()["items"])
    runtime.registry.amr("robot-01").inject(clear_fault=True, online=True)

    running = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"robot_id": "robot-02", "skills": [{"type": "navigate_to", "params": {"point_id": "point-a"}}]},
    ).json()
    assert client.post("/api/v1/scheduler/dispatch", headers=headers).status_code == 200
    runtime.registry.amr("robot-02").inject(online=False)
    client.get("/api/v1/robots", headers=headers)
    offline = next(item for item in client.get("/api/v1/tasks", headers=headers).json()["items"] if item["id"] == running["id"])
    assert offline["status"] == "Failed"
    assert offline["error_code"] == "DEVICE_OFFLINE"
    runtime.registry.amr("robot-02").inject(online=True)

    started = time.monotonic()
    waited = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "robot_id": "robot-01",
            "skills": [
                {"type": "wait", "params": {"seconds": 0.05}},
                {"type": "navigate_to", "params": {"point_id": "point-a"}},
            ],
        },
    ).json()
    _drain(client, headers)
    assert time.monotonic() - started >= 0.05
    done = next(item for item in client.get("/api/v1/tasks", headers=headers).json()["items"] if item["id"] == waited["id"])
    assert done["status"] == "Succeeded"


def test_ingested_measurement_raises_limit_alarm(client):
    headers = auth_header(client)
    created = client.post(
        "/api/v1/measurements",
        headers=headers,
        json={
            "device_id": "th-01",
            "sample_id": "hot",
            "metric": "temp_c",
            "unit": "C",
            "value": 40,
            "point_id": "point-a",
            "robot_id": "robot-01",
            "client_request_id": "hot-1",
        },
    )
    assert created.status_code == 200, created.text
    alarms = client.get("/api/v1/alarms", headers=headers).json()["items"]
    assert any(item["rule_id"] == "limit.temp_c" and item["object_ref"] == created.json()["id"] for item in alarms)
