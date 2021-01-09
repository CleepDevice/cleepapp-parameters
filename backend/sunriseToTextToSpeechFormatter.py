#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.soundTextToSpeechProfile import SoundTextToSpeechProfile

class SunriseToTextToSpeechFormatter(ProfileFormatter):
    """
    Sunrise data to TextToSpeechProfile
    """
    def __init__(self, events_broker):
        """
        Contructor

        Args:
            events_broker (EventsBroker): events broker instance
        """
        ProfileFormatter.__init__(self, events_broker, 'parameters.time.sunrise', SoundTextToSpeechProfile())

    def _fill_profile(self, event_params, profile):
        """
        Fill profile with event data

        Args:
            event_params (dict): event parameters
            profile (Profile): profile instance
        """
        profile.text = 'It\'s sunrise!'

        return profile

