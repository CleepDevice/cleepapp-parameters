#!/usr/bin/env python
# -*- coding: utf-8 -*-

from raspiot.libs.internals.profileformatter import ProfileFormatter
from raspiot.profiles.soundtexttospeechprofile import SoundTextToSpeechProfile

class SunsetToTextToSpeechFormatter(ProfileFormatter):
    """
    Sunset data to TextToSpeechProfile
    """
    def __init__(self, events_broker):
        """
        Constructor

        Args:
            events_broker (EventsBroker): events broker instance
        """
        ProfileFormatter.__init__(self, events_broker, u'parameters.time.sunset', SoundTextToSpeechProfile())

    def _fill_profile(self, event_values, profile):
        """
        Fill profile with event data

        Args:
            event_values (dict): event values
            profile (Profile): profile instance
        """
        profile.text = u'It\'s sunset!'

        return profile

