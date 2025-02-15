import unittest
from unittest.mock import MagicMock, Mock, patch

import requests
import asyncio

import config as cfg  # assuming cfg is imported
import utils.iptv as iptv

m3u_obj = iptv.M3U_Parser("https://raw.githubusercontent.com/Divarion-D/xtream_api/master/tests/test.m3u")
epg_obj = iptv.EPG_Parser()

####################### M3U #######################

class TestGetM3uListKey(unittest.TestCase):
    async def test_starts_with_extinf(self):
        expected_output = (1, {'stream_icon': 'http://example.com/logo.png', 'name': 'Channel Name', 'group_title': 'Group Title', 'epg_channel_id': '123'})
        line = "#EXTINF:-1 tvg-logo=\"http://example.com/logo.png\" group-title=\"Group Title\" tvg-id=\"123\" tvg-name=\"Channel Name\",Channel Name"

        result = await m3u_obj._get_m3u_list_key(line, {}, 0)

        self.assertEqual(result, expected_output)

    async def test_starts_with_extgrp(self):
        line = "#EXTGRP:Group Title"
        expected_output = (0, {'group_title': 'Group Title'})

        result = await m3u_obj._get_m3u_list_key(line, {}, 0)

        self.assertEqual(result, expected_output)

    async def test_starts_with_http(self):
        line = "http://example.com/live/channel1.m3u8"
        expected_output = (0, {'url': 'http://example.com/live/channel1.m3u8'})

        result = await m3u_obj._get_m3u_list_key(line, {}, 0)

        self.assertEqual(result, expected_output)

class TestM3uList(unittest.TestCase):

    @patch('requests.get')
    def test_get_m3u_list_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'channel1\nchannel2\nchannel3\n'
        
        result = m3u_obj._get_m3u_list()
        
        self.assertEqual(result, ['channel1', 'channel2', 'channel3'])
    
    @patch('requests.get')
    def test_get_m3u_list_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout
        
        result = m3u_obj._get_m3u_list()
        
        self.assertEqual(result, [])

    @patch('requests.get')
    def test_get_m3u_list_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException('Test error')
        
        result = m3u_obj._get_m3u_list()
        
        self.assertEqual(result, [])

####################### EPG #######################

class TestGetIcon(unittest.TestCase):
    def test_single_icon(self):
        self.assertEqual(epg_obj._get_icon([{"src": "icon1.png"}]), "icon1.png")

    def test_multiple_icons(self):
        self.assertEqual(epg_obj._get_icon([{"src": "icon1.png"}, {"src": "icon2.png"}]), "icon1.png")

    def test_empty_icons(self):
        self.assertEqual(epg_obj._get_icon([]), None)

class TestParseChannel(unittest.TestCase):

    def setUp(self):
        self.channel = {
            "id": "1",
            "display-name": [
              {
                "name": "Channel 1"
              }
            ],
            "icon": [
                {
                    "src": "http://example.com/logo.png"
                }
            ]
        }
        self.channels_db = [
            {
                "name": "Channel 1",
                "id": "1"
            },
            {
                "name": "Channel 2",
                "id": "2"
            }
        ]

    def test_parse_channel(self):
        name, id, channel_db, icon = epg_obj.parse_channel(self.channel, self.channels_db)
        self.assertEqual(name["name"], "Channel 1")
        self.assertEqual(id, "1")
        self.assertEqual(channel_db, {"name": "Channel 1", "id": "1"})
        self.assertEqual(icon, 'http://example.com/logo.png')

    def test_parse_channel_no_match(self):
        channel = {
            "id": "2",
            "display-name": [
              {
                "name": "Channel 3"
              }
            ],
            "icon": {
              "src": "http://example.com/logo.png"
            }
        }
        name, id, channel_db, icon = epg_obj.parse_channel(channel, self.channels_db)
        self.assertIsNone(name)
        self.assertIsNone(id)
        self.assertIsNone(channel_db)
        self.assertIsNone(icon)  

if __name__ == '__main__':
    unittest.main()