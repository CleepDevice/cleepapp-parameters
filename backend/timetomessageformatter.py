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
        profile.message = "%02d:%02d %02d/%02d/%d" % (
            event_params["hour"],
            event_params["minute"],
            event_params["day"],
            event_params["month"],
            event_params["year"],
        )

        return profile
