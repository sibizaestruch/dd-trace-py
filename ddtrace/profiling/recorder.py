# -*- encoding: utf-8 -*-
import collections
import os

from ddtrace.profiling import _nogevent
from ddtrace.profiling.collector import exceptions
from ddtrace.profiling.collector import memalloc
from ddtrace.profiling.collector import memory
from ddtrace.profiling.collector import stack
from ddtrace.profiling.collector import threading
from ddtrace.vendor import attr
from ddtrace.vendor import six


@attr.s
class UnknownEvent(Exception):
    event_type = attr.ib()


def _get_default_event_types():
    return {
        # Allow to store up to 10 threads for 60 seconds at 100 Hz
        stack.StackSampleEvent: 10 * 60 * 100,
        stack.StackExceptionSampleEvent: 10 * 60 * 100,
        # This can generate one event every 0.1s if 100% are taken — though we take 5% by default.
        # = (60 seconds / 0.1 seconds)
        memory.MemorySampleEvent: int(60 / 0.1),
        # (default buffer size / interval) * export interval
        memalloc.MemoryAllocSampleEvent: int((64 / 0.5) * 60),
        exceptions.UncaughtExceptionEvent: 128,
        threading.LockAcquireEvent: 8192,
        threading.LockReleaseEvent: 8192,
    }


@attr.s(slots=True, eq=False)
class Recorder(object):
    """An object that records program activity."""

    event_types = attr.ib(factory=_get_default_event_types, repr=False)
    """A dict of {event_type_class: max events}."""

    events = attr.ib(init=False, repr=False)
    _events_lock = attr.ib(init=False, repr=False, factory=_nogevent.DoubleLock)
    _pid = attr.ib(init=False, repr=False, factory=os.getpid)

    def __attrs_post_init__(self):
        self._reset_events()

    def push_event(self, event):
        """Push an event in the recorder.

        :param event: The `ddtrace.profiling.event.Event` to push.
        """
        return self.push_events([event])

    def push_events(self, events):
        """Push multiple events in the recorder.

        All the events MUST be of the same type.
        There is no sanity check as whether all the events are from the same class for performance reasons.

        :param events: The event list to push.
        """
        # NOTE: do not try to push events if the current PID has changed
        # This means:
        # 1. the process has forked
        # 2. we don't know the state of _events_lock and it might be unusable — we'd deadlock
        if events and os.getpid() == self._pid:
            event_type = events[0].__class__
            with self._events_lock:
                try:
                    q = self.events[event_type]
                except KeyError:
                    raise UnknownEvent(event_type)
                q.extend(events)

    def _reset_events(self):
        self.events = {
            event_class: collections.deque(maxlen=max_events)
            for event_class, max_events in six.iteritems(self.event_types)
        }

    def reset(self):
        """Reset the recorder.

        This is useful when e.g. exporting data. Once the event queue is retrieved, a new one can be created by calling
        the reset method, avoiding iterating on a mutating event list.

        :return: The list of events that has been removed.
        """
        with self._events_lock:
            events = self.events
            self._reset_events()
        return events
