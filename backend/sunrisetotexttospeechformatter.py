#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.soundtexttospeechprofile import SoundTextToSpeechProfile

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
        ProfileFormatter.__init__(self, events_broker, u'parameters.time.sunrise', SoundTextToSpeechProfile())

    def _fill_profile(self, event_values, profile):
        """
        Fill profile with event data

        Args:
            event_values (dict): event values
            profile (Profile): profile instance
        """
        profile.text = u'It\'s sunrise!'

        return profile

