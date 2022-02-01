#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class ParametersCountryUpdateEvent(Event):
    """
    Parameters.country.update event
    """

    EVENT_NAME = "parameters.country.update"
    EVENT_PROPAGATE = False
    EVENT_PARAMS = ["country", "alpha2"]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
