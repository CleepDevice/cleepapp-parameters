#!/usr/bin/env python
# -*- coding: utf-8 -*-

from raspiot.libs.internals.formatter import Formatter
from raspiot.profiles.soundTextToSpeechProfile import SoundTextToSpeechProfile

class SunriseToTextToSpeechFormatter(Formatter):
    """
    Sunrise data to TextToSpeechProfile
    """
    def __init__(self, events_broker):
        """
        Contructor

        Args:
            events_broker (EventsBroker): events broker instance
        """
        Formatter.__init__(self, events_broker, u'parameters.time.sunrise', SoundTextToSpeechProfile())

    def _fill_profile(self, event_values, profile):
        """
        Fill profile with event data

        Args:
            event_values (dict): event values
            profile (Profile): profile instance
        """
        profile.text = u'It\'s sunrise!'

        return profile

