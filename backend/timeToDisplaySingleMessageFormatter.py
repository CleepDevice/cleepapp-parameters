#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.displaySingleMessageProfile import DisplaySingleMessageProfile

class TimeToDisplaySingleMessageFormatter(ProfileFormatter):
    """
    Time data to DisplaySingleMessageProfile
    """
    def __init__(self, events_broker):
        """
        Constuctor

        Args:
            events_broker (EventsBroker): events broker instance
        """
        ProfileFormatter.__init__(self, events_broker, 'parameters.time.now', DisplaySingleMessageProfile())

    def _fill_profile(self, event_params, profile):
        """
        Fill profile with event data

        Args:
            event_params (dict): event parameters
            profile (Profile): profile instance
        """
        profile.uuid = 'currenttime'

        # append current time
        profile.message = '%02d:%02d %02d/%02d/%d' % (
            event_params['hour'],
            event_params['minute'],
            event_params['day'],
            event_params['month'],
            event_params['year']
        )

        return profile

