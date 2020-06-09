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

    def _fill_profile(self, event_params, profile):
        """
        Fill profile with event data

        Args:
            event_params (dict): event parameters
            profile (Profile): profile instance
        """
        profile.uuid = u'currenttime'

        # append current time
        profile.message = u':clock: %02d:%02d %02d/%02d/%d' % (
            event_params[u'hour'],
            event_params[u'minute'],
            event_params[u'day'],
            event_params[u'month'],
            event_params[u'year']
        )

        return profile

