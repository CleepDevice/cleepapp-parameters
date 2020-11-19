#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event

class ParametersTimeNowEvent(Event):
    """
    Parameters.time.now event
    """

    EVENT_NAME = 'parameters.time.now'
    EVENT_PROPAGATE = False
    EVENT_PARAMS = [
        'timestamp',
        'iso',
        'year',
        'month',
        'day',
        'hour',
        'minute',
        'weekday',
        'weekday_literal',
        'sunset',
        'sunrise'
    ]

    def __init__(self, bus, formatters_broker):
        """
        Constructor

        Args:
            bus (MessageBus): message bus instance
            formatters_broker (FormattersBroker): formatters broker instance
        """
        Event.__init__(self, bus, formatters_broker)

