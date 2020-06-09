#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.displayaddorreplacemessageprofile import DisplayAddOrReplaceMessageProfile

class TimeToDisplayAddOrReplaceMessageFormatter(ProfileFormatter):
    """
    Time data to DisplayAddOrReplaceProfile
    """
    def __init__(self, events_broker):
        """
        Constuctor

        Args:
            events_broker (EventsBroker): events broker instance
        """
        ProfileFormatter.__init__(self, events_broker, u'parameters.time.now', DisplayAddOrReplaceMessageProfile())

    def _fill_profile(self, event_values, profile):
        """
        Fill profile with event data
        """
        profile.uuid = u'currenttime'

        #append current time
        profile.message = u':clock: %02d:%02d %02d/%02d/%d' % (event_values[u'hour'], event_values[u'minute'], event_values[u'day'], event_values[u'month'], event_values[u'year'])

        return profile

