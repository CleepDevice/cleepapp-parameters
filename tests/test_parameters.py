#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import logging
import sys
sys.path.append('../')
from backend.parameters import Parameters
from backend.parameterscountryupdateevent import ParametersCountryUpdateEvent
from backend.parametershostnameupdateevent import ParametersHostnameUpdateEvent
from backend.parameterstimenowevent import ParametersTimeNowEvent
from backend.parameterstimesunriseevent import ParametersTimeSunriseEvent
from backend.parameterstimesunsetevent import ParametersTimeSunsetEvent
from backend.timetomessageformatter import TimeToMessageFormatter
from backend.timetoidentifiedmessageformatter import TimeToIdentifiedMessageFormatter
from cleep.exception import InvalidParameter, MissingParameter, CommandError, Unauthorized
from cleep.libs.tests import session
from unittest.mock import patch, MagicMock, Mock, ANY
from cleep.libs.tests.mockdatetime import mock_datetime
import datetime
import pytz
import time

class TestsParameters(unittest.TestCase):

    def setUp(self):
        self.session = session.TestSession(self)
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')

    def tearDown(self):
        self.session.clean()

    def init_session(self, mock_sun=None, mock_cleepconf=None,
        mock_hostname=None, set_hostname_return_value=True, get_hostname_return_value='dummy',
        mock_tzfinder=None, tzfinder_timezoneat_side_effect=None, tzfinder_timezoneat_return_value=None, start=True):
        if mock_sun:
            local_tz = pytz.timezone('Europe/London')
            mock_sun.return_value.sunset.return_value = local_tz.localize(datetime.datetime.fromtimestamp(1591735300))
            mock_sun.return_value.sunrise.return_value = local_tz.localize(datetime.datetime.fromtimestamp(1591735200))

        if mock_hostname:
            mock_hostname.return_value.set_hostname.return_value = set_hostname_return_value
            mock_hostname.return_value.get_hostname.return_value = get_hostname_return_value

        if mock_tzfinder:
            if tzfinder_timezoneat_side_effect:
                mock_tzfinder.return_value.timezone_at.side_effect = tzfinder_timezoneat_side_effect 
            else:
                mock_tzfinder.return_value.timezone_at.return_value = tzfinder_timezoneat_return_value

        if mock_cleepconf:
            get_auth_get_mock = Mock()
            get_auth_get_mock.get = Mock(side_effect=[True, ['account1']])
            mock_cleepconf.return_value.get_auth.return_value = get_auth_get_mock

        self.module = self.session.setup(Parameters, mock_on_start=False, mock_on_stop=False)

        if start:
            self.session.start_module(self.module)

    def test_configure(self):
        self.init_session(start=False)
        self.module._add_device = Mock()
        self.module._get_device_count = Mock(return_value=0)
        self.module._get_config_field = Mock(return_value=None)
        self.module.set_country = Mock()
        self.module.set_sun = Mock()

        self.session.start_module(self.module)

        self.module._add_device.assert_called_with({
            'type': 'clock',
            'name': 'Clock'
        })
        self.module.set_country.assert_called()
        self.module.set_sun.assert_called()

    @patch('backend.parameters.time.time', Mock(return_value=1607538850))
    @patch('backend.parameters.Timer')
    @patch('backend.parameters.Task')
    def test_on_start_launch_time_task(self, mock_task, mock_timer):
        self.init_session()

        # mocked time = 9/12/2020 à 18:34:10, so cleep seconds synchronized with system, it must delay of 50 seconds
        mock_timer.assert_called_with(50, mock_task.return_value.start)
        self.assertTrue(mock_timer.return_value.start.called)

    @patch('backend.parameters.time.time', Mock(return_value=1607538850))
    @patch('backend.parameters.Task')
    def test_on_start_sync_time_first_launch(self, mock_task):
        self.init_session()

        self.assertEqual(mock_task.call_count, 1)

    @patch('backend.parameters.time.time', Mock(return_value=1575916450))
    @patch('backend.parameters.Task')
    def test_on_start_sync_time_already_launched_invalid_time(self, mock_task):
        self.init_session(start=False)
        self.module._get_config_field = Mock(side_effect=[{}, {}, 'france', 'Europe/Paris', {'latitude': 52.2040, 'longitude': 0.1208}, 1607538850])

        self.session.start_module(self.module)

        logging.debug(self.module._get_config_field.call_args_list)
        self.assertEqual(mock_task.call_count, 2)
        mock_task.assert_any_call(Parameters.NTP_SYNC_INTERVAL, self.module._sync_time_task, ANY)
        self.assertTrue(mock_task.return_value.start.called)

    @patch('backend.parameters.time.time', Mock(return_value=1607538850))
    @patch('backend.parameters.Task')
    def test_on_start_sync_time_already_launched_valid_time(self, mock_task):
        self.init_session(start=False)
        self.module._get_config_field = Mock(side_effect=[{}, {}, 'france', 'Europe/Paris', {'latitude': 52.2040, 'longitude': 0.1208}, 1607538150])

        self.session.start_module(self.module)

        logging.debug(mock_task.call_args_list)
        self.assertEqual(mock_task.call_count, 1)
        self.assertFalse(mock_task.return_value.start.called)

    @patch('backend.parameters.Sun')
    @patch('backend.parameters.CleepConf')
    def test_get_module_config_default(self, mock_cleepconf, mock_sun):
        self.init_session(mock_sun=mock_sun, mock_cleepconf=mock_cleepconf)

        conf = self.module.get_module_config()
        logging.debug('Conf: %s' % conf)

        self.assertTrue('sun' in conf)
        self.assertTrue('country' in conf)
        self.assertTrue('position' in conf)
        self.assertTrue('timezone' in conf)
        self.assertTrue('hostname' in conf)
        self.assertTrue('authenabled' in conf)
        self.assertTrue('authaccounts' in conf)

        self.assertTrue('sunset_iso' in conf['sun'])
        self.assertTrue('sunset' in conf['sun'])
        self.assertTrue('sunrise_iso' in conf['sun'])
        self.assertTrue('sunrise' in conf['sun'])

        self.assertTrue('alpha2' in conf['country'])
        self.assertTrue('country' in conf['country'])

        self.assertTrue('latitude' in conf['position'])
        self.assertTrue('longitude' in conf['position'])

        self.assertEqual(conf['authenabled'], True)
        self.assertEqual(conf['authaccounts'], ['account1'])

    @patch('time.time', MagicMock(return_value=1591818206))
    def test_get_module_devices(self):
        utc_now = datetime.datetime(2020, 6, 8, 19, 50, 8, 0) # 1591645808
        with mock_datetime(utc_now, datetime):
            self.init_session()
            devices = self.module.get_module_devices()
            logging.debug('Devices: %s' % devices)

            self.assertEqual(len(devices), 1)
            uid = list(devices.keys())[0]
            self.assertEqual(devices[uid]['name'], 'Clock')
            self.assertTrue('timestamp' in devices[uid])
            self.assertEqual(devices[uid]['iso'], '2020-06-08T20:50:08+01:00')
            self.assertEqual(devices[uid]['year'], 2020)
            self.assertEqual(devices[uid]['month'], 6)
            self.assertEqual(devices[uid]['day'], 8)
            self.assertEqual(devices[uid]['hour'], 20)
            self.assertEqual(devices[uid]['minute'], 50)
            self.assertTrue('sunset' in devices[uid])
            self.assertTrue('sunrise' in devices[uid])
            self.assertEqual(devices[uid]['weekday'], 0)
            self.assertEqual(devices[uid]['weekday_literal'], 'monday')
            self.assertEqual(devices[uid]['type'], 'clock')
            self.assertTrue('uuid' in devices[uid])

    def test_get_module_devices_weekdays(self):
        utc_now = datetime.datetime(2020, 6, 8, 19, 50, 8, 0) # 1591645808
        uid = None
        with mock_datetime(utc_now, datetime):
            self.init_session()
            devices = self.module.get_module_devices()
            uid = list(devices.keys())[0]

            self.assertEqual(devices[uid]['weekday'], 0)
            self.assertEqual(devices[uid]['weekday_literal'], 'monday')

        utc_now = datetime.datetime(2020, 6, 9, 19, 50, 8, 0) # 1591732208
        with mock_datetime(utc_now, datetime):
            devices = self.module.get_module_devices()
            self.assertEqual(devices[uid]['weekday'], 1)
            self.assertEqual(devices[uid]['weekday_literal'], 'tuesday')

        utc_now = datetime.datetime(2020, 6, 10, 19, 50, 8, 0) # 1591818608
        with mock_datetime(utc_now, datetime):
            devices = self.module.get_module_devices()
            self.assertEqual(devices[uid]['weekday'], 2)
            self.assertEqual(devices[uid]['weekday_literal'], 'wednesday')

        utc_now = datetime.datetime(2020, 6, 11, 19, 50, 8, 0) # 1591905008
        with mock_datetime(utc_now, datetime):
            devices = self.module.get_module_devices()
            self.assertEqual(devices[uid]['weekday'], 3)
            self.assertEqual(devices[uid]['weekday_literal'], 'thursday')

        utc_now = datetime.datetime(2020, 6, 12, 19, 50, 8, 0) # 1591991408
        with mock_datetime(utc_now, datetime):
            devices = self.module.get_module_devices()
            self.assertEqual(devices[uid]['weekday'], 4)
            self.assertEqual(devices[uid]['weekday_literal'], 'friday')

        utc_now = datetime.datetime(2020, 6, 13, 19, 50, 8, 0) # 1592077808
        with mock_datetime(utc_now, datetime):
            devices = self.module.get_module_devices()
            self.assertEqual(devices[uid]['weekday'], 5)
            self.assertEqual(devices[uid]['weekday_literal'], 'saturday')

        utc_now = datetime.datetime(2020, 6, 14, 19, 50, 8, 0) # 1592164208
        with mock_datetime(utc_now, datetime):
            devices = self.module.get_module_devices()
            self.assertEqual(devices[uid]['weekday'], 6)
            self.assertEqual(devices[uid]['weekday_literal'], 'sunday')

    @patch('backend.parameters.Parameters.sync_time')
    def test_sync_time_task_sync_ok(self, sync_time_mock):
        self.init_session()
        sync_time_mock.return_value = True
        self.module.sync_time_task = Mock()

        self.module._sync_time_task()
        
        self.assertIsNone(self.module.sync_time_task)

    def test_sync_time_task_sync_ko(self):
        self.init_session()
        self.module.sync_time = Mock(return_value=False)
        self.module.sync_time_task = Mock()

        self.module._sync_time_task()
        
        self.assertFalse(self.module.sync_time_task.stop.called)

    def test_time_task_now_event(self):
        utc_now = datetime.datetime(2020, 6, 8, 19, 50, 8, 0) # 1591645808
        with mock_datetime(utc_now, datetime):
            self.init_session()
            self.module.timezone = pytz.timezone('Europe/London')
            self.module._set_config_field = Mock()

            self.module._time_task()

            self.assertTrue(self.session.event_called_with('parameters.time.now', {
                'hour': 20,
                'day': 8,
                'month': 6,
                'weekday_literal': 'monday',
                'timestamp': 1591645808,
                'weekday': 0,
                'iso': '2020-06-08T20:50:08+01:00',
                'year': 2020,
                'sunset': self.module.suns['sunset'],
                'sunrise': self.module.suns['sunrise'],
                'minute': 50
            }))
            self.module._set_config_field.assert_called_with('timestamp', 1591645808)

    def test_time_task_sunrise_event(self):
        utc_now = datetime.datetime(2020, 6, 8, 8, 15, 8, 0)
        with mock_datetime(utc_now, datetime):
            self.init_session()
            self.module.sunrise = pytz.utc.localize(utc_now).astimezone(self.module.timezone)

            self.module._time_task()
            self.assertTrue(self.session.event_called('parameters.time.sunrise'))

    def test_time_task_sunset_event(self):
        utc_now = datetime.datetime(2020, 6, 8, 20, 5, 8, 0)
        with mock_datetime(utc_now, datetime):
            self.init_session()
            self.module.sunset = pytz.utc.localize(utc_now).astimezone(self.module.timezone)

            self.module._time_task()
            self.assertTrue(self.session.event_called('parameters.time.sunset'))

    def test_time_task_update_sun_after_midnight(self):
        utc_now = datetime.datetime(2020, 6, 8, 23, 5, 8, 0)
        with mock_datetime(utc_now, datetime):
            self.init_session()
            self.module.set_sun = MagicMock()

            self.module._time_task()

            self.assertTrue(self.module.set_sun.called)

    @patch('cleep.libs.configs.hostname.Hostname')
    def test_set_hostname_succeed(self, mock_hostname):
        self.init_session(mock_hostname=mock_hostname)
        
        self.assertTrue(self.module.set_hostname('dummy'))
        self.assertTrue(self.session.event_called_with('parameters.hostname.update', {
            'hostname': 'dummy'
        }))

    @patch('backend.parameters.Hostname')
    def test_set_hostname_failed(self, mock_hostname):
        self.init_session(mock_hostname=mock_hostname, set_hostname_return_value=False)
        
        self.assertFalse(self.module.set_hostname('dummy'))
        self.assertFalse(self.session.event_called('parameters.hostname.update'))

    def test_set_hostname_invalid_name(self):
        self.init_session()

        with self.assertRaises(InvalidParameter):
            self.module.set_hostname('dummy?')
        with self.assertRaises(InvalidParameter):
            self.module.set_hostname('dummy-')
        with self.assertRaises(InvalidParameter):
            self.module.set_hostname('dum!my')
        with self.assertRaises(InvalidParameter):
            self.module.set_hostname('dummy.')

    @patch('backend.parameters.Hostname')
    def test_get_hostname(self, mock_hostname):
        self.init_session(mock_hostname=mock_hostname, get_hostname_return_value='hello')

        self.assertEqual(self.module.get_hostname(), 'hello')

    def test_get_position(self):
        self.init_session()
        position = self.module.get_position()
        self.assertTrue('latitude' in position)
        self.assertTrue('longitude' in position)

    def test_set_position(self):
        self.init_session()
        self.module.set_timezone = MagicMock()
        self.module.set_country = MagicMock()
        self.module.set_sun = MagicMock()

        self.module.set_position(48.8591554, 2.2907284)
        self.assertTrue(self.module.set_timezone.called)
        self.assertTrue(self.module.set_country.called)
        self.assertTrue(self.module.set_sun.called)

        position = self.module.get_position()
        self.assertEqual(position['latitude'], 48.8591554)
        self.assertEqual(position['longitude'], 2.2907284)

    def test_set_position_exception(self):
        self.init_session()

        with self.assertRaises(MissingParameter) as cm:
            self.module.set_position(None, 2.2907284)
        self.assertEqual(str(cm.exception), 'Parameter "latitude" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.set_position(48, 2.2907284)
        self.assertEqual(str(cm.exception), 'Parameter "latitude" is invalid')

        with self.assertRaises(MissingParameter) as cm:
            self.module.set_position(48.8591554, None)
        self.assertEqual(str(cm.exception), 'Parameter "longitude" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.set_position(48.8591554, 2)
        self.assertEqual(str(cm.exception), 'Parameter "longitude" is invalid')

        self.module._set_config_field = Mock(return_value=False)
        with self.assertRaises(CommandError) as cm:
            self.module.set_position(48.8591554, 2.2907284)
        self.assertEqual(str(cm.exception), 'Unable to save position')

    def test_get_country(self):
        self.init_session()
        country = self.module.get_country()
        self.assertEqual(country['alpha2'], 'GB')
        self.assertEqual(country['country'], 'United Kingdom')

    def test_set_country(self):
        self.init_session()
        original_set_country = self.module.set_country
        self.module.set_timezone = MagicMock()
        self.module.set_country = MagicMock()
        self.module.set_sun = MagicMock()
        self.module.set_position(48.8591554, 2.2907284)
        self.module.set_country = original_set_country

        self.module.set_country()
        country = self.module.get_country()
        self.assertEqual(country['alpha2'], 'FR')
        self.assertEqual(country['country'], 'France')

        self.assertTrue(self.session.event_called_with('parameters.country.update', {
            'alpha2': 'FR',
            'country': 'France',
        }))

    @patch('backend.parameters.reverse_geocode')
    def test_set_country_geocode_exception(self, mock_reverse_geo):
        mock_reverse_geo.search.side_effect = Exception('Test exception')
        self.init_session()

        self.module.set_country()

        self.assertFalse(self.session.event_called('parameters.country.update'))

    def test_set_country_commanderror(self):
        self.init_session()
        original_set_country = self.module.set_country
        self.module.set_timezone = MagicMock()
        self.module.set_country = MagicMock()
        self.module.set_sun = MagicMock()
        self.module.set_position(48.8591554, 2.2907284)
        self.module.set_country = original_set_country
        self.module._set_config_field = Mock(return_value=False)

        with self.assertRaises(CommandError) as cm:
            self.module.set_country()
        self.assertEqual(str(cm.exception), 'Unable to save country')

    def test_set_country_no_position(self):
        self.init_session()
        self.module._set_config_field('position', {
            'latitude': 0,
            'longitude': 0
        })

        self.module.set_country()

    def test_set_timezone(self):
        self.init_session()
        original_set_timezone = self.module.set_timezone
        self.module.set_timezone = MagicMock()
        self.module.set_country = MagicMock()
        self.module.set_sun = MagicMock()
        self.module.set_position(48.8591554, 2.2907284)
        self.module.set_timezone = original_set_timezone

        self.assertTrue(self.module.set_timezone())

    def test_set_timezone_no_position(self):
        self.init_session()
        self.module._set_config_field('position', {
            'latitude': 0,
            'longitude': 0
        })

        self.assertFalse(self.module.set_timezone())

    @patch('backend.parameters.TimezoneFinder')
    def test_set_timezone_timezonefinder_exception(self, mock_tzfinder):
        self.init_session(mock_tzfinder=mock_tzfinder, tzfinder_timezoneat_side_effect=Exception('Test exception'))

        self.assertFalse(self.module.set_timezone())

    @patch('backend.parameters.TimezoneFinder')
    def test_set_timezone_timezonefinder_valueerror(self, mock_tzfinder):
        self.init_session(mock_tzfinder=mock_tzfinder, tzfinder_timezoneat_side_effect=ValueError('Test exception'))

        self.assertFalse(self.module.set_timezone())

    @patch('backend.parameters.TimezoneFinder')
    def test_set_timezone_unable_set_config(self, mock_tzfinder):
        self.init_session(mock_tzfinder=mock_tzfinder, tzfinder_timezoneat_return_value='Europe/Paris')

        self.module._set_config_field = Mock(return_value=False)
        with self.assertRaises(CommandError) as cm:
            self.module.set_timezone()
        self.assertEqual(str(cm.exception), 'Unable to save timezone')

    @patch('backend.parameters.TimezoneFinder')
    def test_set_timezone_invalid_timezone(self, mock_tzfinder):
        self.init_session(mock_tzfinder=mock_tzfinder, tzfinder_timezoneat_return_value='Europe/Dummy')

        with self.assertRaises(CommandError) as cm:
            self.module.set_timezone()
        self.assertEqual(str(cm.exception), 'No system file found for "Europe/Dummy" timezone')

    def test_set_timezone_unable_write_system_file(self):
        self.init_session()

        self.module.cleep_filesystem.write_data = Mock(return_value=False)
        self.assertFalse(self.module.set_timezone())

    @patch('backend.parameters.Console')
    def test_set_timezone_command_failed(self, mock_console):
        self.init_session()

        mock_console.return_value.command.return_value = {'returncode': 1, 'stderr': 'Test error'}
        self.assertFalse(self.module.set_timezone())

    @patch('backend.parameters.TimezoneFinder')
    def test_set_timezone_timezonefinder_extend_timezone_search(self, mock_tzfinder):
        mock_tzfinder.return_value.closest_timezone_at = Mock(return_value='Europe/Paris')
        self.init_session(mock_tzfinder=mock_tzfinder, tzfinder_timezoneat_return_value=None)
        self.module._get_config_field = Mock(return_value={
            'latitude': 52.204,
            'longitude': 0.1208,
        })

        self.assertTrue(self.module.set_timezone())
        mock_tzfinder.return_value.closest_timezone_at.assert_called_with(lat=52.204, lng=0.1208)

    @patch('backend.parameters.Console')
    def test_sync_time(self, mock_console):
        self.init_session()

        self.module.sync_time()

        mock_console.return_value.command.assert_called_with('/usr/sbin/ntpdate-debian', timeout=60.0)

    def test_get_non_working_days(self):
        self.init_session()

        holidays = self.module.get_non_working_days(2021)
        logging.debug('Holidays: %s', holidays)

        self.assertListEqual(holidays, [
            ('2021-01-01', 'New year'),
            ('2021-04-02', 'Good Friday'),
            ('2021-04-04', 'Easter Sunday'),
            ('2021-04-05', 'Easter Monday'),
            ('2021-05-03', 'Early May Bank Holiday'),
            ('2021-05-31', 'Spring Bank Holiday'),
            ('2021-08-30', 'Late Summer Bank Holiday'),
            ('2021-12-25', 'Christmas Day'),
            ('2021-12-26', 'Boxing Day'),
            ('2021-12-27', 'Christmas Shift'),
            ('2021-12-28', 'Boxing Day Shift')
        ])

    def test_get_non_working_day_unknown_country(self):
        self.init_session()
        self.module._get_config_field = Mock(return_value={"country": "country", "alpha2": "CO"})

        holidays = self.module.get_non_working_days(2021)
        logging.debug('Holidays: %s', holidays)

        self.assertListEqual(holidays, [])

    def test_is_non_working_day(self):
        self.init_session()

        self.assertTrue(self.module.is_non_working_day('2021-01-01'))
        self.assertFalse(self.module.is_non_working_day('2021-01-02'))

    def test_is_today_non_working_day(self):
        self.init_session()

        with patch('backend.parameters.datetime') as datetime_mock:
            datetime_mock.date.today.return_value = datetime.date.fromisoformat('2021-01-01')
            self.module.is_non_working_day = Mock()
            self.assertTrue(self.module.is_today_non_working_day())
            self.module.is_non_working_day.assert_called_with('2021-01-01')





class TestsParametersCountryUpdateEvent(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        params = { 
            'internal_bus': Mock(),
            'formatters_broker': Mock(),
            'get_external_bus_name': None,
        }   
        self.event = ParametersCountryUpdateEvent(params)

    def test_event_params(self):
        self.assertEqual(self.event.EVENT_PARAMS, ['country', 'alpha2'])





class TestsParametersHostnameUpdateEvent(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        params = { 
            'internal_bus': Mock(),
            'formatters_broker': Mock(),
            'get_external_bus_name': None,
        }   
        self.event = ParametersHostnameUpdateEvent(params)

    def test_event_params(self):
        self.assertEqual(self.event.EVENT_PARAMS, ['hostname'])





class TestsParametersTimeNowEvent(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        params = { 
            'internal_bus': Mock(),
            'formatters_broker': Mock(),
            'get_external_bus_name': None,
        }   
        self.event = ParametersTimeNowEvent(params)

    def test_event_params(self):
        self.assertEqual(self.event.EVENT_PARAMS, ['timestamp', 'iso', 'year', 'month', 'day', 'hour', 'minute', 'weekday', 'weekday_literal', 'sunset', 'sunrise'])





class TestsParametersTimeSunriseEvent(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        params = { 
            'internal_bus': Mock(),
            'formatters_broker': Mock(),
            'get_external_bus_name': None,
        }   
        self.event = ParametersTimeSunriseEvent(params)

    def test_event_params(self):
        self.assertEqual(self.event.EVENT_PARAMS, [])





class TestsParametersTimeSunsetEvent(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        params = { 
            'internal_bus': Mock(),
            'formatters_broker': Mock(),
            'get_external_bus_name': None,
        }   
        self.event = ParametersTimeSunsetEvent(params)

    def test_event_params(self):
        self.assertEqual(self.event.EVENT_PARAMS, [])





class TestsTimeToMessageFormatter(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        events_broker = Mock()
        self.formatter = TimeToMessageFormatter({'events_broker': events_broker})

    def test_fill_profile(self):
        event_params = {
            'timestamp': 1618220940,
            'iso': '1970-01-19T18:30:20+01:00',
            'year': 2021,
            'month': 4,
            'day': 12,
            'hour': 9,
            'minute': 49,
            'weekday': 0,
            'weekday_literal': 'monday',
            'sunset': 1618259400,
            'sunrise': 1618216200,
        }
        profile = Mock()
        profile = self.formatter._fill_profile(event_params, profile)
        
        self.assertEqual(profile.message, '09:49 12/04/2021')



class TestsTimeToIdentifiedMessageFormatter(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        events_broker = Mock()
        self.formatter = TimeToIdentifiedMessageFormatter({'events_broker': events_broker})

    def test_fill_profile(self):
        event_params = {
            'timestamp': 1618220940,
            'iso': '1970-01-19T18:30:20+01:00',
            'year': 2021,
            'month': 4,
            'day': 12,
            'hour': 9,
            'minute': 49,
            'weekday': 0,
            'weekday_literal': 'monday',
            'sunset': 1618259400,
            'sunrise': 1618216200,
        }
        profile = Mock()
        profile = self.formatter._fill_profile(event_params, profile)
        
        self.assertEqual(profile.id, 'currenttime')
        self.assertEqual(profile.message, '09:49 12/04/2021')



if __name__ == '__main__':
    # coverage run --omit="*/lib/python*/*","test_*" --concurrency=thread test_parameters.py; coverage report -m -i
    unittest.main()
    
