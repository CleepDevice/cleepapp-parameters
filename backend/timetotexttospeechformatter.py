#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.soundTextToSpeechProfile import SoundTextToSpeechProfile

class TimeToTextToSpeechFormatter(ProfileFormatter):
    """
    Current time data to TextToSpeechProfile
    """
    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): formatter parameters
        """
        ProfileFormatter.__init__(self, params, 'parameters.time.now', SoundTextToSpeechProfile())

    def _fill_profile(self, event_params, profile):
        """
        Fill profile with event data

        Args:
            event_params (dict): event parameters
            profile (Profile): profile instance

        Note:
            http://www.anglaisfacile.com/exercices/exercice-anglais-2/exercice-anglais-3196.php
        """
        if event_params['hour'] == 0 and event_params['minute'] == 0:
            profile.text = 'It\'s midnight'
        elif event_params['hour'] == 12 and event_params['minute'] == 0:
            profile.text = 'It\'s noon'
        elif event_params['minute'] == 0:
            profile.text = 'It\'s %d o\'clock' % event_params['hour']
        elif event_params['minute'] == 15:
            profile.text = 'It\'s quarter past %d' % event_params['hour']
        elif event_params['minute'] == 45:
            profile.text = 'It\'s quarter to %d' % (event_params['hour']+1)
        elif event_params['minute'] == 30:
            profile.text = 'It\'s half past %d' % event_params['hour']
        elif event_params['minute'] < 30:
            profile.text = 'It\'s %d past %d' % (event_params['minute'], event_params['hour'])
        elif event_params['minute'] > 30:
            profile.text = 'It\'s %d to %d' % (60-event_params['minute'], event_params['hour']+1)

        return profile


