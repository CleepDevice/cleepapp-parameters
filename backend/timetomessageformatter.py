#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.messageprofile import MessageProfile


class TimeToMessageFormatter(ProfileFormatter):
    """
    Time data to MessageProfile
    """

    def __init__(self, params):
        """
        Constuctor

        Args:
            params (dict): formatter parameters
        """
        ProfileFormatter.__init__(self, params, "parameters.time.now", MessageProfile())

    def _fill_profile(self, event_params, profile):
        """
        Fill profile with event data

        Args:
            event_params (dict): event parameters
            profile (Profile): profile instance
        """
        # append current time
        profile.message = f"{event_params['hour']:02d}:{event_params['minute']:02d} {event_params['day']:02d}/{event_params['month']:02d}/{event_params['year']}"

        return profile
