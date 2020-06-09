#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event

class ParametersTimeNowEvent(Event):
    """
    Parameters.time.now event
    """

    EVENT_NAME = u'parameters.time.now'
    EVENT_SYSTEM = False
    EVENT_PARAMS = [
        u'timestamp',
        u'iso',
        u'year',
        u'month',
        u'day',
        u'hour',
        u'minute',
        u'weekday',
        u'weekday_literal',
        u'sunset',
        u'sunrise'
    ]

    def __init__(self, bus, formatters_broker):
        """
        Constructor

        Args:
            bus (MessageBus): message bus instance
            formatters_broker (FormattersBroker): formatters broker instance
        """
        Event.__init__(self, bus, formatters_broker)

