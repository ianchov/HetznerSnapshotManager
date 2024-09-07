import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import hetzner_vm_snapshot as hvs

class TestHetznerVMSnapshot(unittest.TestCase):

    @patch('hetzner_vm_snapshot.requests.request')
    def test_make_api_request_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.text = '{"success": true}'
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        result = hvs.make_api_request("https://api.example.com")
        self.assertEqual(result, {"success": True})

    @patch('hetzner_vm_snapshot.requests.request')
    def test_make_api_request_error(self, mock_request):
        mock_response = MagicMock()
        mock_response.text = '{"error": {"message": "API Error"}}'
        mock_response.json.return_value = {"error": {"message": "API Error"}}
        mock_request.return_value = mock_response

        with self.assertRaises(SystemExit):
            hvs.make_api_request("https://api.example.com")

    @patch('hetzner_vm_snapshot.make_api_request')
    def test_get_servers(self, mock_make_api_request):
        mock_make_api_request.return_value = {
            "servers": [
                {"name": "server2", "id": 2},
                {"name": "server1", "id": 1},
            ]
        }
        result = hvs.get_servers()
        self.assertEqual(result, [
            {"name": "server1", "id": 1},
            {"name": "server2", "id": 2},
        ])

    @patch('hetzner_vm_snapshot.make_api_request')
    def test_get_snapshots(self, mock_make_api_request):
        mock_make_api_request.side_effect = [
            {
                "images": [
                    {"id": 1, "bound_to": 100, "description": "Snapshot 1", "created": "2023-01-01T00:00:00+00:00"},
                    {"id": 2, "created_from": {"id": 100}, "description": "Snapshot 2", "created": "2023-01-02T00:00:00+00:00"},
                    {"id": 3, "description": "Snapshot for server 100", "created": "2023-01-03T00:00:00+00:00"},
                    {"id": 4, "description": "Unrelated snapshot", "created": "2023-01-04T00:00:00+00:00"},
                ],
                "meta": {"pagination": {"last_page": 1}}
            }
        ]
        result = hvs.get_snapshots(100, "test-server")
        self.assertEqual(len(result), 3)
        self.assertEqual([s["id"] for s in result], [3, 2, 1])  # Reversed order due to sorting

    @patch('builtins.input', return_value='q')
    @patch('hetzner_vm_snapshot.get_servers')
    def test_main_menu_quit(self, mock_get_servers, mock_input):
        mock_get_servers.return_value = [{"name": "server1", "id": 1}]
        with self.assertRaises(SystemExit):
            hvs.main_menu()

if __name__ == '__main__':
    unittest.main()
