"""Tests for the pure count-diff core (watcher.diff_counts + watcher.Event).

Case table: docs/mvp-plan.md §3. Test 1 is a fully worked example — it is RED
until you implement diff_counts, then green (deliberate TDD starting point).
Tests 2–8 are skeletons: delete the pytest.skip line and write the body from
the pseudocode. Run with: pytest
"""

from collections import Counter

import pytest

from watcher import Event, diff_counts


def test_single_add():
    """Case 1 (worked example): one more bottle appears -> one ADDED event."""
    prev = Counter({"bottle": 1})
    curr = Counter({"bottle": 2})

    events = diff_counts(prev, curr)

    assert len(events) == 1
    ev = events[0]
    assert ev == Event(class_name="bottle", prev=1, new=2)
    assert ev.delta == +1
    assert ev.kind == "ADDED"


def test_no_change():
    """Case 2: identical counts -> no events.

    Pseudocode:
      1. prev = curr = Counter({"cup": 1})   (two separate Counters, same value)
      2. assert diff_counts(prev, curr) == []
    """
    pytest.skip("TODO: implement from pseudocode")


def test_single_remove():
    """Case 3: cup count 2 -> 1 gives one REMOVED event, delta -1.

    Pseudocode:
      1. diff Counter({"cup": 2}) -> Counter({"cup": 1})
      2. one event: class_name "cup", prev 2, new 1
      3. assert delta == -1 and kind == "REMOVED"
    """
    pytest.skip("TODO: implement from pseudocode")


def test_delta_greater_than_one():
    """Case 4: three bottles at once -> ONE event with delta +3 (not three events).

    Pseudocode:
      1. diff Counter({"bottle": 0}) -> Counter({"bottle": 3})
      2. exactly one event, delta == +3, kind == "ADDED"
    """
    pytest.skip("TODO: implement from pseudocode")


def test_simultaneous_add_and_remove():
    """Case 5: cup +1 and book -1 in the same sample -> two events, sorted order.

    Pseudocode:
      1. diff Counter({"cup": 1, "book": 1}) -> Counter({"cup": 2, "book": 0})
      2. exactly two events, in sorted class-name order: book first, then cup
      3. book event: delta -1 REMOVED; cup event: delta +1 ADDED
    """
    pytest.skip("TODO: implement from pseudocode")


def test_class_newly_appears():
    """Case 6: class absent from prev entirely (missing key treated as 0).

    Pseudocode:
      1. diff Counter() -> Counter({"backpack": 1})
      2. one event: prev 0, new 1, ADDED
    """
    pytest.skip("TODO: implement from pseudocode")


def test_class_fully_disappears():
    """Case 7: class present before, absent after (missing key treated as 0).

    Pseudocode:
      1. diff Counter({"backpack": 1}) -> Counter()
      2. one event: prev 1, new 0, delta -1, REMOVED
    """
    pytest.skip("TODO: implement from pseudocode")


def test_empty_to_empty():
    """Case 8: nothing before, nothing after -> no events.

    Pseudocode:
      1. assert diff_counts(Counter(), Counter()) == []
    """
    pytest.skip("TODO: implement from pseudocode")
