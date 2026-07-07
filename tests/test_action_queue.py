import sqlite3
from retail_ops_control_tower.dashboard.action_queue import init_db, assign_exception, resolve_exception, get_queue

def test_assign_and_resolve():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    assign_exception(conn, "EXC-007", "Marcus Lee", "phone_call")
    queue = get_queue(conn)
    assert len(queue) == 1
    assert queue[0]["status"] == "assigned"
    resolve_exception(conn, "EXC-007", "resolved", "Confirmed via phone")
    queue = get_queue(conn, status="resolved")
    assert len(queue) == 1
    assert queue[0]["status"] == "resolved"
