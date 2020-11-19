#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event

class ParametersTimeSunsetEvent(Event):
    """
    Parameters.time.sunset event
    """

    EVENT_NAME = 'parameters.time.sunset'
    EVENT_PROPAGATE = False
    EVENT_PARAMS = []

    def __init__(self, bus, formatters_broker):
        """
        Constructor

        Args:
            bus (MessageBus): message bus instance
            formatters_broker (FormattersBroker): formatters broker instance
        """
        Event.__init__(self, bus, formatters_broker)

