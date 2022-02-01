#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class ParametersTimeSunsetEvent(Event):
    """
    Parameters.time.sunset event
    """

    EVENT_NAME = "parameters.time.sunset"
    EVENT_PROPAGATE = False
    EVENT_PARAMS = []

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
