"""
Unit Tests for Transaction Spatiotemporal Linking (Task T3.4)
Validates:
  - Single person at ATM interaction zone
  - Two queued individuals with proximity
  - Person passing behind outside the ROI
  - Nobody inside the interaction zone
"""
import sys
import os
import pytest

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.linking import compute_transaction_link

# Standard ATM surveillance ROI polygon: rectangle from (400, 300) to (800, 700)
ROI_POLYGON = [
    [400.0, 300.0],
    [800.0, 300.0],
    [800.0, 700.0],
    [400.0, 700.0]
]

def generate_trajectory(start_t: float, end_t: float, step: float, feet_x: float, feet_y: float, box_h: float = 200, box_w: float = 80):
    traj = []
    t = start_t
    while t <= end_t:
        x1 = feet_x - box_w / 2.0
        x2 = feet_x + box_w / 2.0
        y1 = feet_y - box_h
        y2 = feet_y
        traj.append([round(t, 2), int(x1), int(y1), int(x2), int(y2)])
        t += step
    return traj

def test_scenario_single_person():
    """Scenario 1: Exactly one person at the ATM throughout transaction window."""
    tracks = [{
        "track_id": 101,
        # Feet at (600, 550) which is dead-center inside ROI
        "trajectory": generate_trajectory(8.0, 30.0, 0.5, 600.0, 550.0)
    }]

    res = compute_transaction_link(
        txn_id="TXN-001",
        task_id="task_test1",
        start_s=10.0,
        end_s=25.0,
        tracks=tracks,
        roi_polygon=ROI_POLYGON
    )

    print("\n[Scenario 1: Single Person]")
    print(res)
    assert res["track_id"] == 101
    assert res["confidence"] == 1.0
    assert res["ambiguous"] is False
    assert len(res["candidates"]) == 1

def test_scenario_person_passing_behind():
    """Scenario 2: One customer at ATM, one bystander walking behind outside the ROI."""
    tracks = [
        {
            "track_id": 101,
            # Inside ROI
            "trajectory": generate_trajectory(10.0, 25.0, 0.5, 600.0, 550.0)
        },
        {
            "track_id": 102,
            # Feet at (600, 150) -> well outside the ROI (y < 300)
            "trajectory": generate_trajectory(12.0, 20.0, 0.5, 600.0, 150.0)
        }
    ]

    res = compute_transaction_link(
        txn_id="TXN-002",
        task_id="task_test2",
        start_s=10.0,
        end_s=25.0,
        tracks=tracks,
        roi_polygon=ROI_POLYGON
    )

    print("\n[Scenario 2: Person Passing Behind]")
    print(res)
    assert res["track_id"] == 101
    assert res["confidence"] == 1.0
    assert res["ambiguous"] is False
    # Track 102 had 0 dwell inside the ROI
    assert all(c["track_id"] != 102 for c in res["candidates"])

def test_scenario_two_queued_people():
    """Scenario 3: Two people in close proximity; customer has higher dwell, but flagged if tight."""
    tracks = [
        {
            "track_id": 101,
            # Main customer at ATM: 14s in zone
            "trajectory": generate_trajectory(10.0, 24.0, 0.5, 600.0, 550.0)
        },
        {
            "track_id": 102,
            # Person standing close by in zone for 12s
            "trajectory": generate_trajectory(11.0, 23.0, 0.5, 750.0, 650.0)
        }
    ]

    res = compute_transaction_link(
        txn_id="TXN-003",
        task_id="task_test3",
        start_s=10.0,
        end_s=25.0,
        tracks=tracks,
        roi_polygon=ROI_POLYGON
    )

    print("\n[Scenario 3: Two Queued People]")
    print(res)
    assert res["track_id"] == 101
    # Because track 102 had almost equal dwell, it must be flagged ambiguous for human review
    assert res["ambiguous"] is True
    assert len(res["candidates"]) == 2

def test_scenario_nobody_in_zone():
    """Scenario 4: Nobody was inside the ATM interaction polygon during transaction."""
    tracks = [{
        "track_id": 103,
        # Feet outside ROI
        "trajectory": generate_trajectory(10.0, 25.0, 0.5, 200.0, 150.0)
    }]

    res = compute_transaction_link(
        txn_id="TXN-004",
        task_id="task_test4",
        start_s=10.0,
        end_s=25.0,
        tracks=tracks,
        roi_polygon=ROI_POLYGON
    )

    print("\n[Scenario 4: Nobody in Zone]")
    print(res)
    assert res["track_id"] is None
    assert res["confidence"] == 0.0
    assert res["candidates"] == []

if __name__ == "__main__":
    test_scenario_single_person()
    test_scenario_person_passing_behind()
    test_scenario_two_queued_people()
    test_scenario_nobody_in_zone()
    print("\n[PASS] All transaction linking tests successfully verified!")
