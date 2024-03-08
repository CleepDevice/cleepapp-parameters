#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import copy
import importlib
import re
import datetime
from threading import Timer
import requests
import reverse_geocode
from timezonefinder import TimezoneFinder
from pytz import utc, timezone
from tzlocal import get_localzone
from pycountry_convert import (
    country_alpha2_to_continent_code,
    convert_continent_code_to_continent_name,
)
from cleep.core import CleepModule
from cleep.exception import CommandError, InvalidParameter, MissingParameter
from cleep.libs.configs.hostname import Hostname
from cleep.libs.internals.sun import Sun
from cleep.libs.internals.console import Console
from cleep.libs.internals.task import Task
from cleep.libs.configs.cleepconf import CleepConf

__all__ = ["Parameters"]


class Parameters(CleepModule):
    """
    Parameters application.

    Allow to configure Cleep parameters:

        * system time(current time, sunset, sunrise) according to position
        * system locale
        * auth

    Useful doc:

        * debian timezone: https://wiki.debian.org/TimeZoneChanges
        * python datetime handling: https://hackernoon.com/avoid-a-bad-date-and-have-a-good-time-423792186f30
    """

    MODULE_AUTHOR = "Cleep"
    MODULE_VERSION = "2.2.0"
    MODULE_CATEGORY = "APPLICATION"
    MODULE_DEPS = []
    MODULE_DESCRIPTION = "Configure generic parameters of your device"
    MODULE_LONGDESCRIPTION = (
        "Application that helps you to configure generic parameters of your device"
    )
    MODULE_TAGS = [
        "configuration",
        "date",
        "time",
        "locale",
        "lang",
        "auth",
        "security",
    ]
    MODULE_COUNTRY = None
    MODULE_URLINFO = "https://github.com/CleepDevice/cleepapp-parameters"
    MODULE_URLHELP = None
    MODULE_URLBUGS = "https://github.com/CleepDevice/cleepapp-parameters/issues"
    MODULE_URLSITE = None

    MODULE_CONFIG_FILE = "parameters.conf"
    # default position to raspberry pi foundation
    DEFAULT_CONFIG = {
        "position": {"latitude": 52.2040, "longitude": 0.1208},
        "country": {"country": "United Kingdom", "alpha2": "GB"},
        "timezone": "Europe/London",
        "timestamp": 0,
    }

    SYSTEM_ZONEINFO_DIR = "/usr/share/zoneinfo/"
    SYSTEM_LOCALTIME = "/etc/localtime"
    SYSTEM_TIMEZONE = "/etc/timezone"
    NTP_SYNC_INTERVAL = 60

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
        self.suns = {"sunset": 0, "sunset_iso": "", "sunrise": 0, "sunrise_iso": ""}
        self.timezonefinder = TimezoneFinder()
        self.timezone_name = None
        self.timezone = None
        self.time_task = None
        self.sync_time_task = None
        self.__clock_uuid = None
        self.cleep_conf = CleepConf(self.cleep_filesystem)
        # code from https://stackoverflow.com/a/106223
        self.__hostname_pattern = (
            r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*"
            r"([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        )
        self.rpc_url = bootstrap.get("rpc_config", {}).get("url")

        # events
        self.time_now_event = self._get_event("parameters.time.now")
        self.time_sunrise_event = self._get_event("parameters.time.sunrise")
        self.time_sunset_event = self._get_event("parameters.time.sunset")
        self.hostname_update_event = self._get_event("parameters.hostname.update")
        self.country_update_event = self._get_event("parameters.country.update")

    def _configure(self):
        """
        Configure module
        """
        # add clock device if not already added
        if self._get_device_count() < 1:
            self.logger.debug("Add default devices")
            clock = {"type": "clock", "name": "Clock"}
            self._add_device(clock)

        # prepare country
        country = self._get_config_field("country")
        if not country:
            self.set_country()

        # prepare timezone
        timezone_name = self._get_config_field("timezone")
        self.timezone = timezone(timezone_name or get_localzone().zone)

        # compute sun times
        self.set_sun()

        # store device uuids for events
        devices = self.get_module_devices()
        for device_uuid, device in devices.items():
            if device["type"] == "clock":
                self.__clock_uuid = device_uuid

    def _on_start(self):
        """
        Module starts
        """
        # restore last saved timestamp if system time seems very old (NTP error)
        saved_timestamp = self._get_config_field("timestamp")
        if (int(time.time()) - saved_timestamp) < 0:
            # it seems NTP sync failed, launch timer to regularly try to sync device time
            self.logger.info(
                "Device time seems to be invalid (%s), launch synchronization time task",
                datetime.datetime.utcnow().isoformat(),
            )
            self.sync_time_task = Task(
                Parameters.NTP_SYNC_INTERVAL, self._sync_time_task, self.logger
            )
            self.sync_time_task.start()

        # launch time task (synced to current seconds)
        self.time_task = Task(60.0, self._time_task, self.logger)
        seconds = 60 - (int(time.time()) % 60)
        if seconds == 60:
            self.time_task.start()
        else:
            timer = Timer(seconds, self.time_task.start)
            timer.start()

    def _on_stop(self):
        """
        Module stops
        """
        if self.time_task:
            self.time_task.stop()

    def get_module_config(self):
        """
        Get full module configuration

        Returns:
            dict: module configuration
        """
        config = {}

        config["hostname"] = self.get_hostname()
        config["position"] = self.get_position()
        config["sun"] = self.get_sun()
        config["country"] = self.get_country()
        config["timezone"] = self.get_timezone()

        auth_conf = self.cleep_conf.get_auth()
        config["authenabled"] = auth_conf.get("enabled", False)
        config["authaccounts"] = auth_conf.get("accounts", [])

        return config

    def get_module_devices(self):
        """
        Return clock as parameters device

        Returns:
            dict: module devices
        """
        devices = super().get_module_devices()

        for device in devices.values():
            if device["type"] == "clock":
                data = self.__format_time()
                data.update(
                    {"sunrise": self.suns["sunrise"], "sunset": self.suns["sunset"]}
                )
                device.update(data)

        return devices

    def __format_time(self):
        """
        Return time with different splitted infos

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
        utc_now = utc.localize(datetime.datetime.utcnow())
        local_now = utc_now.astimezone(self.timezone)
        weekday = local_now.weekday()
        if weekday == 0:
            weekday_literal = "monday"
        elif weekday == 1:
            weekday_literal = "tuesday"
        elif weekday == 2:
            weekday_literal = "wednesday"
        elif weekday == 3:
            weekday_literal = "thursday"
        elif weekday == 4:
            weekday_literal = "friday"
        elif weekday == 5:
            weekday_literal = "saturday"
        elif weekday == 6:
            weekday_literal = "sunday"

        return {
            "timestamp": datetime.datetime.timestamp(utc_now),
            "iso": local_now.isoformat(),
            "year": local_now.year,
            "month": local_now.month,
            "day": local_now.day,
            "hour": local_now.hour,
            "minute": local_now.minute,
            "weekday": weekday,
            "weekday_literal": weekday_literal,
        }

    def _sync_time_task(self):
        """
        Sync time task. It is used to try to sync device time using NTP server.

        Note:
            This task is launched only if device time is insane.
        """
        if Parameters.sync_time():
            self.logger.info(
                "Time synchronized with NTP server (%s)",
                datetime.datetime.utcnow().isoformat(),
            )
            self.sync_time_task.stop()
            self.sync_time_task = None

    def _time_task(self):
        """
        Time task used to refresh time
        """
        now_formatted = self.__format_time()
        self.logger.trace("now_formatted: %s", now_formatted)

        # send now event
        now_event_params = copy.deepcopy(now_formatted)
        now_event_params.update(
            {"sunrise": self.suns["sunrise"], "sunset": self.suns["sunset"]}
        )
        self.time_now_event.send(params=now_event_params, device_id=self.__clock_uuid)

        # send sunrise event
        if self.sunrise:
            if (
                now_formatted["hour"] == self.sunrise.hour
                and now_formatted["minute"] == self.sunrise.minute
            ):
                self.time_sunrise_event.send(device_id=self.__clock_uuid)

        # send sunset event
        if self.sunset:
            if (
                now_formatted["hour"] == self.sunset.hour
                and now_formatted["minute"] == self.sunset.minute
            ):
                self.time_sunset_event.send(device_id=self.__clock_uuid)

        # update sun times after midnight
        if now_formatted["hour"] == 0 and now_formatted["minute"] == 5:
            self.set_sun()

        # save last timestamp in config to restore it after a reboot and NTP sync failed (no internet)
        if not self.sync_time_task:
            self._set_config_field("timestamp", now_formatted["timestamp"])

    def get_time(self):
        """
        Return current time

        Returns:
            dict: current time::

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
        return self.__format_time()

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
            raise InvalidParameter("Hostname is not valid")

        # update hostname
        res = self.hostname.set_hostname(hostname)

        # send event to update hostname on all devices
        if res:
            self.hostname_update_event.send(params={"hostname": hostname})

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
        if latitude is None:
            raise MissingParameter('Parameter "latitude" is missing')
        if not isinstance(latitude, float):
            raise InvalidParameter('Parameter "latitude" is invalid')
        if longitude is None:
            raise MissingParameter('Parameter "longitude" is missing')
        if not isinstance(longitude, float):
            raise InvalidParameter('Parameter "longitude" is invalid')

        # save new position
        position = {"latitude": latitude, "longitude": longitude}

        if not self._set_config_field("position", position):
            raise CommandError("Unable to save position")

        # reset python time to take into account last modifications before
        # computing new times
        time.tzset()

        # and update related stuff
        self.set_timezone()
        self.set_country()
        self.set_sun()

        # send now event
        self._time_task()

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
        return self._get_config_field("position")

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
        """ "
        Compute sun times (sunrise and sunset) according to configured position
        """
        # get position
        position = self._get_config_field("position")

        # compute sun times
        self.sunset = None
        self.sunrise = None
        if position["latitude"] != 0 and position["longitude"] != 0:
            self.sun.set_position(position["latitude"], position["longitude"])
            self.sunset = self.sun.sunset().astimezone(self.timezone)
            self.sunrise = self.sun.sunrise().astimezone(self.timezone)
            self.logger.debug("Found sunrise:%s sunset:%s", self.sunrise, self.sunset)

            # save times
            self.suns["sunrise"] = int(self.sunrise.strftime("%s"))
            self.suns["sunrise_iso"] = self.sunrise.isoformat()
            self.suns["sunset"] = int(self.sunset.strftime("%s"))
            self.suns["sunset_iso"] = self.sunset.isoformat()

    def set_country(self):
        """
        Compute country (and associated alpha) from current internal position

        Warning:
            This function can take some time to find country info on slow device like raspi 1st generation (~15secs)
        """
        # get position
        position = self._get_config_field("position")
        if not position["latitude"] and not position["longitude"]:
            self.logger.debug(
                "Unable to set country from unspecified position (%s)", position
            )
            return

        # get country from position
        country = {"country": None, "alpha2": None}
        try:
            # search country
            coordinates = ((position["latitude"], position["longitude"]),)
            # need a tuple
            geo = reverse_geocode.search(coordinates)
            self.logger.debug("Found country infos from position %s: %s", position, geo)
            if (
                geo
                and len(geo) > 0
                and "country_code" in geo[0]
                and "country" in geo[0]
            ):
                country["alpha2"] = geo[0]["country_code"]
                country["country"] = geo[0]["country"]

            # save new country
            if not self._set_config_field("country", country):
                raise CommandError("Unable to save country")

            # send event
            self.country_update_event.send(params=country)

        except CommandError:
            raise

        except Exception:
            self.logger.exception("Unable to find country for position %s:", position)

    def get_country(self):
        """
        Get country from position

        Returns:
            dict: return country infos::

            {
                country (string): country label
                alpha2 (string): country code
            }

        """
        return self._get_config_field("country")

    def set_timezone(self):
        """
        Set timezone according to coordinates

        Returns:
            bool: True if function succeed, False otherwise

        Raises:
            CommandError: if unable to save timezone
        """
        # get position
        position = self._get_config_field("position")
        if not position["latitude"] and not position["longitude"]:
            self.logger.warning(
                "Unable to set timezone from unspecified position (%s)", position
            )
            return False

        # compute timezone
        current_timezone = None
        try:
            # try to find timezone at position
            current_timezone = self.timezonefinder.timezone_at(
                lat=position["latitude"], lng=position["longitude"]
            )
            if current_timezone is None:
                # extend search to closest position
                # TODO increase delta_degree to extend research, careful it use more CPU !
                current_timezone = self.timezonefinder.closest_timezone_at(
                    lat=position["latitude"], lng=position["longitude"]
                )
        except ValueError:
            # the coordinates were out of bounds
            self.logger.exception("Coordinates out of bounds")
        except Exception:
            self.logger.exception("Error occured searching timezone at position")
        if not current_timezone:
            self.logger.warning(
                "Unable to set device timezone because it was not found"
            )
            return False

        # save timezone value
        self.logger.debug("Save new timezone: %s", current_timezone)
        if not self._set_config_field("timezone", current_timezone):
            raise CommandError("Unable to save timezone")

        # configure system timezone
        zoneinfo = os.path.join(self.SYSTEM_ZONEINFO_DIR, current_timezone)
        self.logger.debug("Checking zoneinfo file: %s", zoneinfo)
        if not os.path.exists(zoneinfo):
            raise CommandError(
                f'No system file found for "{current_timezone}" timezone'
            )
        self.logger.debug('zoneinfo file "%s" exists', zoneinfo)
        self.cleep_filesystem.rm(self.SYSTEM_LOCALTIME)

        self.logger.debug(
            'Writing timezone "%s" in "%s"', current_timezone, self.SYSTEM_TIMEZONE
        )
        if not self.cleep_filesystem.write_data(
            self.SYSTEM_TIMEZONE, f"{current_timezone}"
        ):
            self.logger.error(
                'Unable to write timezone data on "%s". System timezone is not configured!',
                self.SYSTEM_TIMEZONE,
            )
            return False

        # launch timezone update in background
        self.logger.debug("Updating system timezone")
        command = Console()
        res = command.command("dpkg-reconfigure -f noninteractive tzdata", timeout=60.0)
        self.logger.debug("Timezone update command result: %s", res)
        if res["returncode"] != 0:
            self.logger.error("Error reconfiguring system timezone: %s", res["stderr"])
            return False

        # propagate changes to cleep
        self.timezone = timezone(current_timezone)
        self._time_task()

        return True

    def get_timezone(self):
        """
        Return timezone

        Returns:
            string: current timezone name
        """
        return self._get_config_field("timezone")

    @staticmethod
    def sync_time():
        """
        Synchronize device time using NTP server

        Note:
            This command may lasts some seconds

        Returns:
            bool: True if NTP sync succeed, False otherwise
        """
        console = Console()
        resp = console.command("/usr/sbin/ntpdate-debian", timeout=60.0)

        return resp["returncode"] == 0

    def get_non_working_days(self, year=None):
        """
        Return non working days of current year

        Args:
            date (int, optional): get non working day for specified year. If not specified use current year. Defaults to None.

        Returns:
            list: list of non working days of the year. List can be empty if error occured::

            [
                {
                    datetime (string): non working day (date in iso format YYYY-MM-DD)
                    label (string): english name of non working day
                },
                ...
            ]

        """
        self._check_parameters(
            [
                {
                    "name": "year",
                    "type": int,
                    "value": year,
                    "none": True,
                }
            ]
        )

        try:
            country = self._get_config_field("country")
            continent_code = country_alpha2_to_continent_code(country["alpha2"])
            continent_name = convert_continent_code_to_continent_name(
                continent_code
            ).lower()
            continent_name = (
                continent_name.lower().replace("south", "").replace("north", "").strip()
            )

            workalendar = importlib.import_module(f"workalendar.{continent_name}")
            fixed_country = "".join(
                [part.capitalize() for part in country["country"].split()]
            )
            _class = getattr(workalendar, fixed_country)
            _instance = _class()
            year = year or datetime.datetime.now().year
            holidays = _instance.holidays(year)
            return [(date.isoformat(), label) for (date, label) in holidays]
        except Exception:
            self.logger.exception("Unable to get non working days:")
            return []

    def is_non_working_day(self, day):
        """
        Check if specified day is non working day according to current locale configuration

        Args:
            day (str): day to check (must be iso format XXXX-MM-DD)
            test (bool): new param

        Returns:
            bool: True if specified day is a non working day, False otherwise
        """
        self._check_parameters(
            [
                {
                    "name": "day",
                    "type": str,
                    "value": day,
                }
            ]
        )

        year = datetime.date.fromisoformat(day).year
        non_working_days = self.get_non_working_days(year=year)
        return any(a_day == day for (a_day, label) in non_working_days)

    def is_today_non_working_day(self):
        """
        Check if today is non working day according to current locale configuration

        Returns:
            bool: True if specified day is a non working day, False otherwise
        """
        today = datetime.date.today()
        return self.is_non_working_day(today.isoformat())

    def get_auth_account(self):
        """
        Return auth accounts

        Returns:
            list: list of account names::

                [
                    account1 (str),
                    account2 (str,
                    ...
                ]

        """
        return self.cleep_conf.get_auth_accounts()

    def add_auth_account(self, account, password):
        """
        Add new auth account

        Args:
            account (bool): account name
            password (str): account password (will be encrypted)
            toto (bool, optional): new param. Defaults to False.

        Raises:
            CommandError: if adding account failed
        """
        self._check_parameters(
            [
                {
                    "name": "account",
                    "type": str,
                    "value": account,
                    "none": False,
                    "empty": False,
                },
                {
                    "name": "password",
                    "type": str,
                    "value": password,
                    "none": False,
                    "empty": False,
                },
            ]
        )

        try:
            self.cleep_conf.add_auth_account(account, password)
            self.__reload_rpcserver_auth()
        except Exception as error:
            raise CommandError(str(error))

    def delete_auth_account(self, account):
        """
        Delete auth account

        Args:
            account (str): account name

        Raises:
            CommandError: if error occured
        """
        self._check_parameters(
            [
                {
                    "name": "account",
                    "type": str,
                    "value": account,
                    "none": False,
                    "empty": False,
                },
            ]
        )

        try:
            self.cleep_conf.delete_auth_account(account)
            self.__reload_rpcserver_auth()
        except Exception as error:
            raise CommandError(str(error))

    def enable_auth(self):
        """
        Enable auth

        Raises:
            CommandError: if error occured
        """
        accounts = self.cleep_conf.get_auth_accounts()
        if not accounts:
            raise CommandError("Please add account before enabling auth")

        self.cleep_conf.enable_auth(True)
        self.__reload_rpcserver_auth()

    def disable_auth(self):
        """
        Disable auth
        """
        self.cleep_conf.enable_auth(enable=False)
        self.__reload_rpcserver_auth()

    def __reload_rpcserver_auth(self):
        """
        Reload RPC server auth configuration
        """
        self.logger.debug("Rpc url=", self.rpc_url)
        try:
            url = f"{self.rpc_url}/reloadauth"
            response = requests.post(url, verify=False)
            response.raise_for_status()
        except Exception:
            self.logger.exception("Unable to reload auth on RPC server")
