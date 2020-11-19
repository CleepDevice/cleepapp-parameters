#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import logging
import sys
sys.path.append('../')
from backend.parameters import Parameters
from cleep.exception import InvalidParameter, MissingParameter, CommandError, Unauthorized
from cleep.libs.tests import session
from mock import patch, MagicMock, Mock
from datetime import datetime
import pytz

class TestParameters(unittest.TestCase):

    def setUp(self):
        self.session = session.TestSession(self)
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')

    def tearDown(self):
        # clean session
        self.session.clean()

    def init_session(self, mock_sun=None,
        mock_hostname=None, set_hostname_return_value=True, get_hostname_return_value='dummy',
        mock_tzfinder=None, tzfinder_timezoneat_side_effect=None, tzfinder_timezoneat_return_value=None, start=True):
        if mock_sun:
            local_tz = pytz.timezone('Europe/London')
            mock_sun.return_value.sunset.return_value = local_tz.localize(datetime.fromtimestamp(1591735300))
            mock_sun.return_value.sunrise.return_value = local_tz.localize(datetime.fromtimestamp(1591735200))

        if mock_hostname:
            mock_hostname.return_value.set_hostname.return_value = set_hostname_return_value
            mock_hostname.return_value.get_hostname.return_value = get_hostname_return_value

        if mock_tzfinder:
            if tzfinder_timezoneat_side_effect:
                mock_tzfinder.return_value.timezone_at.side_effect = tzfinder_timezoneat_side_effect 
            else:
                mock_tzfinder.return_value.timezone_at.return_value = tzfinder_timezoneat_return_value

        self.module = self.session.setup(Parameters)

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

    @patch('backend.parameters.Sun')
    def test_get_module_config_default(self, mock_sun):
        self.init_session(mock_sun=mock_sun)
        conf = self.module.get_module_config()
        logging.debug('Conf: %s' % conf)
        self.assertTrue('sun' in conf)
        self.assertTrue('country' in conf)
        self.assertTrue('position' in conf)
        self.assertTrue('timezone' in conf)
        self.assertTrue('hostname' in conf)

        self.assertTrue('sunset_iso' in conf['sun'])
        self.assertTrue('sunset' in conf['sun'])
        self.assertTrue('sunrise_iso' in conf['sun'])
        self.assertTrue('sunrise' in conf['sun'])

        self.assertTrue('alpha2' in conf['country'])
        self.assertTrue('country' in conf['country'])

        self.assertTrue('latitude' in conf['position'])
        self.assertTrue('longitude' in conf['position'])

    @patch('time.time', MagicMock(return_value=1591818206))
    def test_get_module_devices(self):
        self.init_session()
        devices = self.module.get_module_devices()
        logging.debug('Devices: %s' % devices)

        self.assertEqual(len(devices), 1)
        uid = list(devices.keys())[0]
        self.assertEqual(devices[uid]['name'], 'Clock')
        self.assertTrue('timestamp' in devices[uid])
        self.assertEqual(devices[uid]['iso'], '2020-06-10T21:43:26+01:00')
        self.assertEqual(devices[uid]['year'], 2020)
        self.assertEqual(devices[uid]['month'], 6)
        self.assertEqual(devices[uid]['day'], 10)
        self.assertEqual(devices[uid]['hour'], 21)
        self.assertEqual(devices[uid]['minute'], 43)
        self.assertTrue('sunset' in devices[uid])
        self.assertTrue('sunrise' in devices[uid])
        self.assertEqual(devices[uid]['weekday'], 2)
        self.assertEqual(devices[uid]['weekday_literal'], 'wednesday')
        self.assertEqual(devices[uid]['type'], 'clock')
        self.assertTrue('uuid' in devices[uid])

    @patch('time.time')
    def test_get_module_devices_weekdays(self, mock_time):
        mock_time.return_value = 1591645808
        self.init_session()
        devices = self.module.get_module_devices()
        uid = list(devices.keys())[0]

        self.assertEqual(devices[uid]['weekday'], 0)
        self.assertEqual(devices[uid]['weekday_literal'], 'monday')

        mock_time.return_value = 1591732208
        devices = self.module.get_module_devices()
        self.assertEqual(devices[uid]['weekday'], 1)
        self.assertEqual(devices[uid]['weekday_literal'], 'tuesday')

        mock_time.return_value = 1591818608
        devices = self.module.get_module_devices()
        self.assertEqual(devices[uid]['weekday'], 2)
        self.assertEqual(devices[uid]['weekday_literal'], 'wednesday')

        mock_time.return_value = 1591905008
        devices = self.module.get_module_devices()
        self.assertEqual(devices[uid]['weekday'], 3)
        self.assertEqual(devices[uid]['weekday_literal'], 'thursday')

        mock_time.return_value = 1591991408
        devices = self.module.get_module_devices()
        self.assertEqual(devices[uid]['weekday'], 4)
        self.assertEqual(devices[uid]['weekday_literal'], 'friday')

        mock_time.return_value = 1592077808
        devices = self.module.get_module_devices()
        self.assertEqual(devices[uid]['weekday'], 5)
        self.assertEqual(devices[uid]['weekday_literal'], 'saturday')

        mock_time.return_value = 1592164208
        devices = self.module.get_module_devices()
        self.assertEqual(devices[uid]['weekday'], 6)
        self.assertEqual(devices[uid]['weekday_literal'], 'sunday')

    @patch('time.time')
    def test_time_task_now_event(self, mock_time):
        mock_time.return_value = 1591645808
        self.init_session()

        self.module._time_task()
        self.assertTrue(self.session.event_called_with('parameters.time.now', {
            'hour': 21,
            'day': 8,
            'month': 6,
            'weekday_literal': 'monday',
            'timestamp': 1591645808,
            'weekday': 0,
            'iso': '2020-06-08T21:50:08+01:00',
            'year': 2020,
            'sunset': self.module.suns['sunset'],
            'sunrise': self.module.suns['sunrise'],
            'minute': 50
        }))

    @patch('time.time')
    def test_time_task_sunrise_event(self, mock_time):
        ts = 1591645808
        mock_time.return_value = ts
        self.init_session()
        self.module.sunrise = datetime.fromtimestamp(ts)

        self.module._time_task()
        self.assertTrue(self.session.event_called('parameters.time.sunrise'))

    @patch('time.time')
    def test_time_task_sunset_event(self, mock_time):
        ts = 1591645808
        mock_time.return_value = ts
        self.init_session()
        self.module.sunset = datetime.fromtimestamp(ts)

        self.module._time_task()
        self.assertTrue(self.session.event_called('parameters.time.sunset'))

    @patch('time.time')
    def test_time_task_update_sun_after_midnight(self, mock_time):
        ts = 1591653900 # 00:05
        mock_time.return_value = ts
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
        

#do not remove code below, otherwise test won't run
if __name__ == '__main__':
    # coverage run --omit="*/lib/python*/*","test_*" --concurrency=thread test_parameters.py; coverage report -m -i
    unittest.main()
    
