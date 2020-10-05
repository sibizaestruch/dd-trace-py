# -*- encoding: utf-8 -*-
from ddtrace.profiling import event
from ddtrace.profiling import recorder
from ddtrace.profiling.collector import stack

import pytest


def test_reset():
    r = recorder.Recorder(event_types={event.Event: 128})
    r.push_event(event.Event())
    assert len(r.events[event.Event]) == 1
    assert len(r.reset()[event.Event]) == 1
    assert len(r.events[event.Event]) == 0
    assert len(r.reset()[event.Event]) == 0
    r.push_event(event.Event())
    assert len(r.events[event.Event]) == 1
    assert len(r.reset()[event.Event]) == 1


def test_push_events_empty():
    r = recorder.Recorder()
    r.push_events([])


def test_limit():
    r = recorder.Recorder(
        event_types={
            stack.StackSampleEvent: 24,
        },
    )
    assert r.events[stack.StackSampleEvent].maxlen == 24


def test_push_unknown_event_type():
    r = recorder.Recorder(
        event_types={
            stack.StackSampleEvent: 24,
        },
    )
    with pytest.raises(recorder.UnknownEvent) as e:
        r.push_event(event.Event)
        assert e.value.event_class == event.Event
