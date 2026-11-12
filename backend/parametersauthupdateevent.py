#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class ParametersAuthUpdateEvent(Event):
    """
    Parameters.auth.update event

    Propagated so peers (CleepDesktop) refresh the device auth flag without
    waiting for a bus reconnect.
    """

    EVENT_NAME = "parameters.auth.update"
    EVENT_PROPAGATE = True
    EVENT_PARAMS = ["enabled"]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
