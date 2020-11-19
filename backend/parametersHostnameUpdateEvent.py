#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event

class ParametersHostnameUpdateEvent(Event):
    """
    Parameters.hostname.update event
    """

    EVENT_NAME = 'parameters.hostname.update'
    EVENT_PROPAGATE = True
    EVENT_PARAMS = ['hostname']

    def __init__(self, bus, formatters_broker):
        """
        Constructor

        Args:
            bus (MessageBus): message bus instance
            formatters_broker (FormattersBroker): formatters broker instance
        """
        Event.__init__(self, bus, formatters_broker)

