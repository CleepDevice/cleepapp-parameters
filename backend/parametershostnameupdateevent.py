#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class ParametersHostnameUpdateEvent(Event):
    """
    Parameters.hostname.update event
    """

    EVENT_NAME = "parameters.hostname.update"
    EVENT_PROPAGATE = True
    EVENT_PARAMS = ["hostname"]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
