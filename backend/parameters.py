#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import copy
import re
from datetime import datetime
import reverse_geocode
from timezonefinder import TimezoneFinder
from pytz import timezone
from tzlocal import get_localzone
from cleep.core import CleepModule
from cleep.exception import CommandError, InvalidParameter
from cleep.libs.configs.hostname import Hostname
from cleep.libs.internals.sun import Sun
from cleep.libs.internals.console import Console
from cleep.libs.internals.task import Task

__all__ = [u'Parameters']

class Parameters(CleepModule):
    """
    Parameters application.

    Allow to configure Cleep parameters:

        * system time(current time, sunset, sunrise) according to position
        * system locale

    Useful doc:

        * debian timezone: https://wiki.debian.org/TimeZoneChanges
        * python datetime handling: https://hackernoon.com/avoid-a-bad-date-and-have-a-good-time-423792186f30
    """
    MODULE_AUTHOR = u'Cleep'
    MODULE_VERSION = u'1.1.0'
    MODULE_CATEGORY = u'APPLICATION'
    MODULE_PRICE = 0
    MODULE_DEPS = []
    MODULE_DESCRIPTION = u'Configure generic parameters of your device'
    MODULE_LONGDESCRIPTION = u'Application that helps you to configure generic parameters of your device'
    MODULE_TAGS = [u'configuration', u'date', u'time', u'locale', u'lang']
    MODULE_COUNTRY = None
    MODULE_URLINFO = u'https://github.com/tangb/cleepmod-parameters'
    MODULE_URLHELP = None
    MODULE_URLBUGS = u'https://github.com/tangb/cleepmod-parameters/issues'
    MODULE_URLSITE = None

    MODULE_CONFIG_FILE = u'parameters.conf'
    # default position to raspberry pi foundation
    DEFAULT_CONFIG = {
        u'position': {
            u'latitude': 52.2040,
            u'longitude': 0.1208
        },
        u'country': {
            u'country': u'United Kingdom',
            u'alpha2': u'GB'
        },
        u'timezone': u'Europe/London'
    }

    SYSTEM_ZONEINFO_DIR = u'/usr/share/zoneinfo/'
    SYSTEM_LOCALTIME = u'/etc/localtime'
    SYSTEM_TIMEZONE = u'/etc/timezone'

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled (bool): flag to set debug level to logger
        """
        # init
        CleepModule.__init__(self, bootstrap, debug_enabled)

        # members
        self.hostname = Hostname(self.cleep_filesystem)
        self.sun = Sun()
        self.sunset = None
        self.sunrise = None
        self.suns = {
            u'sunset': 0,
            u'sunset_iso': '',
            u'sunrise': 0,
            u'sunrise_iso': ''
        }
        self.timezonefinder = TimezoneFinder()
        self.timezone_name = None
        self.timezone = None
        self.time_task = None
        self.__clock_uuid = None
        # code from https://stackoverflow.com/a/106223
        self.__hostname_pattern = r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'

        # events
        self.parameters_time_now = self._get_event(u'parameters.time.now')
        self.parameters_time_sunrise = self._get_event(u'parameters.time.sunrise')
        self.parameters_time_sunset = self._get_event(u'parameters.time.sunset')
        self.parameters_hostname_update = self._get_event(u'parameters.hostname.update')
        self.parameters_country_update = self._get_event(u'parameters.country.update')

    def _configure(self):
        """
        Configure module
        """
        # add clock device if not already added
        if self._get_device_count() < 1:
            self.logger.debug(u'Add default devices')
            clock = {
                u'type': u'clock',
                u'name': u'Clock'
            }
            self._add_device(clock)

        # prepare country
        country = self._get_config_field(u'country')
        if not country:
            self.set_country()

        # prepare timezone
        timezone_name = self._get_config_field(u'timezone')
        if timezone_name:
            self.timezone = timezone(timezone_name)
        else:
            self.logger.info(u'No timezone defined, use default one. It will be updated when user sets its position.')
            self.timezone = get_localzone().zone

        # compute sun times
        self.set_sun()

        # store device uuids for events
        # get_module_devices need to have timezone configured !
        devices = self.get_module_devices()
        for uuid in devices:
            if devices[uuid][u'type'] == u'clock':
                self.__clock_uuid = uuid

        # launch time task
        self.time_task = Task(60.0, self._time_task, self.logger)
        self.time_task.start()

    def get_module_config(self):
        """
        Get full module configuration

        Returns:
            dict: module configuration
        """
        config = {}

        config[u'hostname'] = self.get_hostname()
        config[u'position'] = self.get_position()
        config[u'sun'] = self.get_sun()
        config[u'country'] = self.get_country()
        config[u'timezone'] = self.get_timezone()

        return config

    def get_module_devices(self):
        """
        Return clock as parameters device

        Returns:
            dict: module devices
        """
        devices = super(Parameters, self).get_module_devices()

        for uuid in devices:
            if devices[uuid][u'type'] == u'clock':
                data = self.__format_time()
                data.update({
                    u'sunrise': self.suns[u'sunrise'],
                    u'sunset': self.suns[u'sunset']
                })
                devices[uuid].update(data)

        return devices

    def __format_time(self, now=None):
        """
        Return time with different splitted infos

        Args:
            now (int): timestamp to use. If None current timestamp if used

        Returns:
            dict: time data::

                {
                    timestamp (int): current timestamp
                    iso (string): current datetime in iso 8601 format
                    year (int)
                    month (int)
                    day (int)
                    hour (int)
                    minute (int)
                    weekday (int): 0=monday, 1=tuesday... 6=sunday
                    weekday_literal (string): english literal weekday value (monday, tuesday, ...)
                }

        """
        # current time
        if not now:
            now = int(time.time())
        current_dt = datetime.fromtimestamp(now)
        current_dt = self.timezone.localize(current_dt)
        weekday = current_dt.weekday()
        if weekday == 0:
            weekday_literal = u'monday'
        elif weekday == 1:
            weekday_literal = u'tuesday'
        elif weekday == 2:
            weekday_literal = u'wednesday'
        elif weekday == 3:
            weekday_literal = u'thursday'
        elif weekday == 4:
            weekday_literal = u'friday'
        elif weekday == 5:
            weekday_literal = u'saturday'
        elif weekday == 6:
            weekday_literal = u'sunday'

        return {
            u'timestamp': now,
            u'iso': current_dt.isoformat(),
            u'year': current_dt.year,
            u'month': current_dt.month,
            u'day': current_dt.day,
            u'hour': current_dt.hour,
            u'minute': current_dt.minute,
            u'weekday': weekday,
            u'weekday_literal': weekday_literal
        }

    def _time_task(self):
        """
        Time task used to refresh time
        """
        now_formatted = self.__format_time()

        # send now event
        now_event_params = copy.deepcopy(now_formatted)
        now_event_params.update({
            u'sunrise': self.suns[u'sunrise'],
            u'sunset': self.suns[u'sunset']
        })
        self.parameters_time_now.send(params=now_event_params, device_id=self.__clock_uuid)

        # send sunrise event
        if self.sunrise:
            if now_formatted[u'hour'] == self.sunrise.hour and now_formatted[u'minute'] == self.sunrise.minute:
                self.parameters_time_sunrise.send(device_id=self.__clock_uuid)

        # send sunset event
        if self.sunset:
            if now_formatted[u'hour'] == self.sunset.hour and now_formatted[u'minute'] == self.sunset.minute:
                self.parameters_time_sunset.send(device_id=self.__clock_uuid)

        # update sun times after midnight
        if now_formatted[u'hour'] == 0 and now_formatted[u'minute'] == 5:
            self.set_sun()

    def set_hostname(self, hostname):
        """
        Set raspi hostname

        Args:
            hostname (string): hostname

        Returns:
            bool: True if hostname saved successfully, False otherwise

        Raises:
            InvalidParameter: if hostname has invalid format
        """
        # check hostname
        if re.match(self.__hostname_pattern, hostname) is None:
            raise InvalidParameter(u'Hostname is not valid')

        # update hostname
        res = self.hostname.set_hostname(hostname)

        # send event to update hostname on all devices
        if res:
            self.parameters_hostname_update.send(params={u'hostname': hostname})

        return res

    def get_hostname(self):
        """
        Return raspi hostname

        Returns:
            string: raspberry pi hostname
        """
        return self.hostname.get_hostname()

    def set_position(self, latitude, longitude):
        """
        Set device position

        Args:
            latitude (float): latitude
            longitude (float): longitude

        Raises:
            CommandError: if error occured during position saving
        """
        # save new position
        position = {
            u'latitude': latitude,
            u'longitude': longitude
        }

        if not self._set_config_field(u'position', position):
            raise CommandError(u'Unable to save position')

        # and update related stuff
        self.set_timezone()
        self.set_country()
        self.set_sun()

    def get_position(self):
        """
        Return device position

        Returns:
            dict: position coordinates::

                {
                    latitude (float),
                    longitude (float)
                }

        """
        return self._get_config_field(u'position')

    def get_sun(self):
        """
        Compute sun times

        Returns:
            dict: sunset/sunrise timestamps::

                {
                    sunrise (int),
                    sunset (int)
                }

        """
        return self.suns

    def set_sun(self):
        """"
        Compute sun times (sunrise and sunset) according to configured position
        """
        # get position
        position = self._get_config_field(u'position')

        # compute sun times
        self.sunset = None
        self.sunrise = None
        if position[u'latitude'] != 0 and position[u'longitude'] != 0:
            self.sun.set_position(position[u'latitude'], position[u'longitude'])
            self.sunset = self.sun.sunset()
            self.sunrise = self.sun.sunrise()
            self.logger.debug('Found sunrise:%s sunset:%s' % (self.sunrise, self.sunset))

            # save times
            self.suns[u'sunrise'] = int(self.sunrise.strftime('%s'))
            self.suns[u'sunrise_iso'] = self.sunrise.isoformat()
            self.suns[u'sunset'] = int(self.sunset.strftime('%s'))
            self.suns[u'sunset_iso'] = self.sunset.isoformat()

    def set_country(self):
        """
        Compute country (and associated alpha) from current internal position

        Warning:
            This function can take some time to find country info on slow device like raspi 1st generation (~15secs)
        """
        # get position
        position = self._get_config_field(u'position')
        if not position[u'latitude'] and not position[u'longitude']:
            self.logger.debug(u'Unable to set country from unspecified position (%s)' % position)
            return

        # get country from position
        country = {
            u'country': None,
            u'alpha2': None
        }
        try:
            # search country
            coordinates = ((position[u'latitude'], position[u'longitude']), )
            # need a tuple
            geo = reverse_geocode.search(coordinates)
            self.logger.debug('Found country infos from position %s: %s' % (position, geo))
            if geo and len(geo) > 0 and u'country_code' in geo[0] and u'country' in geo[0]:
                country[u'alpha2'] = geo[0][u'country_code']
                country[u'country'] = geo[0][u'country']

            # save new country
            if not self._set_config_field(u'country', country):
                raise CommandError(u'Unable to save country')

            # send event
            self.parameters_country_update.send(params=country)

        except Exception:
            self.logger.exception(u'Unable to find country for position %s:' % position)

    def get_country(self):
        """
        Get country from position

        Returns:
            string: return country name (english)
        """
        return self._get_config_field(u'country')

    def set_timezone(self):
        """
        Set timezone according to coordinates

        Returns:
            bool: True if function succeed, False otherwise

        Raises:
            CommandError: if unable to save timezone
        """
        # get position
        position = self._get_config_field(u'position')
        if not position[u'latitude'] and not position[u'longitude']:
            self.logger.warning(u'Unable to set timezone from unspecified position (%s)' % position)
            return False

        # compute timezone
        current_timezone = None
        try:
            # try to find timezone at position
            current_timezone = self.timezonefinder.timezone_at(lat=position[u'latitude'], lng=position[u'longitude'])
            if current_timezone is None:
                # extend search to closest position
                # TODO increase delta_degree to extend research, careful it use more CPU !
                current_timezone = self.timezonefinder.closest_timezone_at(
                    lat=position[u'latitude'],
                    lng=position[u'longitude']
                )
        except ValueError:
            # the coordinates were out of bounds
            self.logger.exception(u'Coordinates out of bounds')
        except Exception:
            self.logger.exception('Error occured searching timezone at position')
        if not current_timezone:
            self.logger.warning(u'Unable to set device timezone because it was not found')
            return False

        # save timezone value
        self.logger.debug('Save new timezone: %s' % current_timezone)
        if not self._set_config_field(u'timezone', current_timezone):
            raise CommandError(u'Unable to save timezone')

        # configure system timezone
        zoneinfo = os.path.join(self.SYSTEM_ZONEINFO_DIR, current_timezone)
        self.logger.debug(u'Checking zoneinfo file: %s' % zoneinfo)
        if not os.path.exists(zoneinfo):
            raise CommandError('No system file found for "%s" timezone' % current_timezone)
        self.logger.debug(u'zoneinfo file "%s" exists' % zoneinfo)
        self.cleep_filesystem.rm(self.SYSTEM_LOCALTIME)

        self.logger.debug(u'Writing timezone "%s" in "%s"' % (current_timezone, self.SYSTEM_TIMEZONE))
        if not self.cleep_filesystem.write_data(self.SYSTEM_TIMEZONE, u'%s' % current_timezone):
            self.logger.error(u'Unable to write timezone data on "%s". System timezone is not configured!' % self.SYSTEM_TIMEZONE)
            return False

        # launch timezone update in background
        self.logger.debug(u'Updating system timezone')
        command = Console()
        res = command.command(u'/usr/sbin/dpkg-reconfigure -f noninteractive tzdata', timeout=15.0)
        self.logger.debug('Timezone update command result: %s' % res)
        if res['returncode'] != 0:
            self.logger.error('Error reconfiguring system timezone: %s' % res['stderr'])
            return False

        # TODO configure all wpa_supplicant.conf country code

        return True

    def get_timezone(self):
        """
        Return timezone

        Returns:
            string: current timezone name
        """
        return self._get_config_field(u'timezone')

