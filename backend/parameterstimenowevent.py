#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class ParametersTimeNowEvent(Event):
    """
    Parameters.time.now event
    """

    EVENT_NAME = "parameters.time.now"
    EVENT_PROPAGATE = False
    EVENT_PARAMS = [
        "timestamp",
        "iso",
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "weekday",
        "weekday_literal",
        "sunset",
        "sunrise",
    ]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
