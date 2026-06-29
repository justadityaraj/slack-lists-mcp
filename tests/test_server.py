#!/usr/bin/env python3
"""
Basic tests for Slack Lists MCP Server

These tests validate the server functionality without requiring actual Slack API calls.
For full integration testing, you'll need valid Slack credentials and list IDs.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
import sys
import asyncio

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from slack_lists_server import (
    SlackListsClient,
    SlackListsError,
    create_text_field,
    create_date_field,
    create_user_field,
    create_select_field,
    create_checkbox_field,
    create_number_field,
    create_email_field,
    create_phone_field,
    build_field_payload,
    extract_field_value,
    load_dotenv,
)
import slack_lists_server

class TestFieldHelpers:
    """Test field creation helper functions"""
    
    def test_create_text_field(self):
        field = create_text_field("Col123", "Test text")
        assert field["column_id"] == "Col123"
        assert field["rich_text"][0]["elements"][0]["elements"][0]["text"] == "Test text"
    
    def test_create_date_field(self):
        field = create_date_field("Col123", "2024-12-31")
        assert field["column_id"] == "Col123"
        assert field["date"] == ["2024-12-31"]
    
    def test_create_user_field(self):
        field = create_user_field("Col123", ["U1234567"])
        assert field["column_id"] == "Col123"
        assert field["user"] == ["U1234567"]
    
    def test_create_select_field(self):
        field = create_select_field("Col123", ["Option1"])
        assert field["column_id"] == "Col123"
        assert field["select"] == ["Option1"]
    
    def test_create_checkbox_field(self):
        field = create_checkbox_field("Col123", True)
        assert field["column_id"] == "Col123"
        # Checkbox is a bare bool, not an array (verified against the live API)
        assert field["checkbox"] is True

class TestFieldExtraction:
    """Test field value extraction from items"""
    
    def test_extract_text_field(self):
        item = {
            "fields": [
                {"column_id": "Col123", "text": "Test value"}
            ]
        }
        value = extract_field_value(item, "Col123")
        assert value == "Test value"
    
    def test_extract_date_field(self):
        item = {
            "fields": [
                {"column_id": "Col123", "date": ["2024-12-31"]}
            ]
        }
        value = extract_field_value(item, "Col123")
        assert value == "2024-12-31"
    
    def test_extract_user_field(self):
        item = {
            "fields": [
                {"column_id": "Col123", "user": ["U1234567", "U2345678"]}
            ]
        }
        value = extract_field_value(item, "Col123")
        assert value == ["U1234567", "U2345678"]
    
    def test_extract_checkbox_field(self):
        item = {
            "fields": [
                {"column_id": "Col123", "checkbox": True}
            ]
        }
        value = extract_field_value(item, "Col123")
        assert value is True
    
    def test_extract_missing_field(self):
        item = {
            "fields": [
                {"column_id": "Col456", "text": "Other value"}
            ]
        }
        value = extract_field_value(item, "Col123")
        assert value is None

class TestSlackListsClient:
    """Test Slack Lists client functionality"""
    
    def test_client_initialization(self):
        client = SlackListsClient("test-token")
        assert client.token == "test-token"
        assert "Bearer test-token" in client.headers["Authorization"]
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        client = SlackListsClient("test-token")
        
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "data": "test"}
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await client._make_request("GET", "test.endpoint")
            assert result == {"ok": True, "data": "test"}
    
    @pytest.mark.asyncio
    async def test_make_request_slack_error(self):
        client = SlackListsClient("test-token")
        
        mock_response = Mock()
        mock_response.json.return_value = {"ok": False, "error": "invalid_auth"}
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(SlackListsError) as exc_info:
                await client._make_request("GET", "test.endpoint")
            
            assert "invalid_auth" in str(exc_info.value)

class TestEnvironmentValidation:
    """Test environment variable validation"""
    
    def test_missing_token_raises_error(self):
        # Stub the .env loader so it can't pull a real token from the project .env
        with patch.dict(os.environ, {}, clear=True):
            with patch('slack_lists_server.slack_client', None):
                with patch('slack_lists_server.load_dotenv', lambda *a, **k: None):
                    from slack_lists_server import get_slack_client

                    with pytest.raises(SlackListsError) as exc_info:
                        get_slack_client()

                    assert "SLACK_BOT_TOKEN" in str(exc_info.value)
    
    def test_valid_token_creates_client(self):
        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "test-token"}):
            with patch('slack_lists_server.slack_client', None):
                from slack_lists_server import get_slack_client
                
                client = get_slack_client()
                assert client.token == "test-token"

class TestJSONParsing:
    """Test JSON parsing in tool functions"""
    
    def test_valid_json_parsing(self):
        json_str = '[{"column_id": "Col123", "type": "text", "value": "test"}]'
        parsed = json.loads(json_str)
        assert len(parsed) == 1
        assert parsed[0]["column_id"] == "Col123"
    
    def test_invalid_json_handling(self):
        json_str = '{"invalid": json}'
        with pytest.raises(json.JSONDecodeError):
            json.loads(json_str)

class TestLoadDotenv:
    """Test the zero-dependency .env loader"""

    def test_loads_missing_keys(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('SLACK_BOT_TOKEN="xoxb-from-file"\n# comment\nFOO=bar\n')
        with patch.dict(os.environ, {}, clear=True):
            load_dotenv(str(env_file))
            assert os.environ["SLACK_BOT_TOKEN"] == "xoxb-from-file"
            assert os.environ["FOO"] == "bar"

    def test_real_env_wins_over_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SLACK_BOT_TOKEN=xoxb-from-file\n")
        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-real"}, clear=True):
            load_dotenv(str(env_file))
            assert os.environ["SLACK_BOT_TOKEN"] == "xoxb-real"

    def test_missing_file_is_noop(self, tmp_path):
        with patch.dict(os.environ, {}, clear=True):
            load_dotenv(str(tmp_path / "does-not-exist.env"))  # should not raise


class TestNewFieldHelpers:
    """Test the number / email / phone field helpers added for full type support"""

    def test_create_number_field(self):
        field = create_number_field("Col123", 42)
        assert field["column_id"] == "Col123"
        assert field["number"] == [42]

    def test_create_number_field_list_passthrough(self):
        field = create_number_field("Col123", [42])
        assert field["number"] == [42]

    def test_create_email_field(self):
        field = create_email_field("Col123", "user@example.com")
        assert field["email"] == ["user@example.com"]

    def test_create_phone_field(self):
        field = create_phone_field("Col123", "+1-555-123-4567")
        assert field["phone"] == ["+1-555-123-4567"]


class TestBuildFieldPayload:
    """Test the shared field/cell builder used by create and update"""

    def test_text(self):
        field = build_field_payload("Col1", "text", "hello")
        assert field["column_id"] == "Col1"
        assert field["rich_text"][0]["elements"][0]["elements"][0]["text"] == "hello"

    def _text_of(self, field):
        return field["rich_text"][0]["elements"][0]["elements"][0]["text"]

    def test_text_coerces_number_to_string(self):
        field = build_field_payload("Col1", "text", 42)
        assert self._text_of(field) == "42"

    def test_text_unwraps_single_element_list(self):
        field = build_field_payload("Col1", "text", ["hello"])
        assert self._text_of(field) == "hello"

    def test_date_scalar(self):
        assert build_field_payload("Col1", "date", "2025-09-20")["date"] == ["2025-09-20"]

    def test_date_single_element_list(self):
        assert build_field_payload("Col1", "date", ["2025-09-20"])["date"] == ["2025-09-20"]

    def test_user_scalar_is_coerced_to_list(self):
        assert build_field_payload("Col1", "user", "U1")["user"] == ["U1"]

    def test_user_list(self):
        assert build_field_payload("Col1", "user", ["U1", "U2"])["user"] == ["U1", "U2"]

    def test_select_list(self):
        assert build_field_payload("Col1", "select", ["completed"])["select"] == ["completed"]

    def test_checkbox(self):
        assert build_field_payload("Col1", "checkbox", True)["checkbox"] is True

    def test_number(self):
        assert build_field_payload("Col1", "number", 42)["number"] == [42]

    def test_email(self):
        assert build_field_payload("Col1", "email", "a@b.com")["email"] == ["a@b.com"]

    def test_phone(self):
        assert build_field_payload("Col1", "phone", "+1")["phone"] == ["+1"]

    def test_type_is_case_insensitive(self):
        assert build_field_payload("Col1", "DATE", "2025-09-20")["date"] == ["2025-09-20"]

    def test_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            build_field_payload("Col1", "bogus", "x")


class TestUpdateDeleteClient:
    """Test the update/delete client methods build the right endpoint + payload"""

    @pytest.mark.asyncio
    async def test_update_list_item_endpoint_and_payload(self):
        client = SlackListsClient("test-token")
        client._make_request = AsyncMock(return_value={"ok": True})

        cells = [{"column_id": "Col1", "row_id": "Rec1", "select": ["completed"]}]
        await client.update_list_item("F1", cells)

        args, kwargs = client._make_request.call_args
        assert args[0] == "POST"
        assert args[1] == "slackLists.items.update"
        assert kwargs["json"] == {"list_id": "F1", "cells": cells}

    @pytest.mark.asyncio
    async def test_delete_list_item_endpoint_and_payload(self):
        client = SlackListsClient("test-token")
        client._make_request = AsyncMock(return_value={"ok": True})

        await client.delete_list_item("F1", "Rec1")

        args, kwargs = client._make_request.call_args
        assert args[0] == "POST"
        assert args[1] == "slackLists.items.delete"
        assert kwargs["json"] == {"list_id": "F1", "id": "Rec1"}


def _resolve(tool):
    """FastMCP may wrap a tool function in an object exposing .fn; unwrap it."""
    return getattr(tool, "fn", tool)


class TestUpdateDeleteTools:
    """Test the update/delete/discover MCP tools end-to-end with a mocked client"""

    @pytest.mark.asyncio
    async def test_update_tool_injects_row_id_into_every_cell(self, monkeypatch):
        mock_client = AsyncMock()
        mock_client.update_list_item = AsyncMock(return_value={"ok": True})
        monkeypatch.setattr(slack_lists_server, "get_slack_client", lambda: mock_client)

        fields = json.dumps([
            {"column_id": "Col1", "type": "select", "value": ["completed"]},
            {"column_id": "Col2", "type": "user", "value": ["U1"]},
        ])
        result = await _resolve(slack_lists_server.update_list_item)(
            list_id="F1", row_id="Rec1", fields=fields
        )

        assert "Successfully updated" in result
        args, kwargs = mock_client.update_list_item.call_args
        called_list_id = args[0] if args else kwargs.get("list_id")
        cells = args[1] if len(args) > 1 else kwargs.get("cells")
        assert called_list_id == "F1"
        assert all(cell["row_id"] == "Rec1" for cell in cells)
        assert cells[0]["select"] == ["completed"]
        assert cells[1]["user"] == ["U1"]

    @pytest.mark.asyncio
    async def test_update_tool_rejects_bad_json(self, monkeypatch):
        monkeypatch.setattr(slack_lists_server, "get_slack_client", lambda: AsyncMock())
        result = await _resolve(slack_lists_server.update_list_item)(
            list_id="F1", row_id="Rec1", fields="{not json}"
        )
        assert "Error parsing" in result

    @pytest.mark.asyncio
    async def test_update_tool_rejects_unknown_type(self, monkeypatch):
        monkeypatch.setattr(slack_lists_server, "get_slack_client", lambda: AsyncMock())
        fields = json.dumps([{"column_id": "Col1", "type": "bogus", "value": "x"}])
        result = await _resolve(slack_lists_server.update_list_item)(
            list_id="F1", row_id="Rec1", fields=fields
        )
        assert "Unsupported field type" in result

    @pytest.mark.asyncio
    async def test_delete_tool_calls_client(self, monkeypatch):
        mock_client = AsyncMock()
        mock_client.delete_list_item = AsyncMock(return_value={"ok": True})
        monkeypatch.setattr(slack_lists_server, "get_slack_client", lambda: mock_client)

        result = await _resolve(slack_lists_server.delete_list_item)(
            list_id="F1", row_id="Rec1"
        )

        assert "deleted" in result.lower()
        args, kwargs = mock_client.delete_list_item.call_args
        assert (args[0] if args else kwargs.get("list_id")) == "F1"
        assert (args[1] if len(args) > 1 else kwargs.get("item_id")) == "Rec1"

    @pytest.mark.asyncio
    async def test_discover_columns_infers_schema(self, monkeypatch):
        page = {
            "ok": True,
            "items": [
                {"id": "Rec1", "fields": [
                    {"column_id": "Col1", "select": ["completed"], "value": "completed"},
                    {"column_id": "Col2", "user": ["U1"], "value": "U1"},
                ]},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client = AsyncMock()
        mock_client.get_list_items = AsyncMock(return_value=page)
        monkeypatch.setattr(slack_lists_server, "get_slack_client", lambda: mock_client)

        result = await _resolve(slack_lists_server.discover_list_columns)(
            list_id="F1", sample_size=10
        )

        assert "Col1" in result
        assert "Col2" in result
        assert "type: select" in result
        assert "select options: completed" in result

    @pytest.mark.asyncio
    async def test_discover_columns_infers_text_from_value_only_field(self, monkeypatch):
        # A plain-text column can arrive with only the generic "value" (no typed
        # key); it should be reported as text, not unknown.
        page = {
            "ok": True,
            "items": [
                {"id": "Rec1", "fields": [
                    {"column_id": "Col9", "key": "title", "value": "Hello world"},
                ]},
            ],
            "response_metadata": {"next_cursor": ""},
        }
        mock_client = AsyncMock()
        mock_client.get_list_items = AsyncMock(return_value=page)
        monkeypatch.setattr(slack_lists_server, "get_slack_client", lambda: mock_client)

        result = await _resolve(slack_lists_server.discover_list_columns)(
            list_id="F1", sample_size=10
        )

        assert "Col9" in result
        assert "type: text" in result
        assert "unknown" not in result


# Integration test helpers (require actual Slack setup)
class TestIntegrationHelpers:
    """Helper functions for integration testing with real Slack API"""
    
    @staticmethod
    def requires_slack_setup():
        """Decorator to skip tests that require Slack setup"""
        return pytest.mark.skipif(
            not os.getenv("SLACK_BOT_TOKEN") or not os.getenv("TEST_LIST_ID"),
            reason="Requires SLACK_BOT_TOKEN and TEST_LIST_ID environment variables"
        )
    
    @staticmethod
    def get_test_config():
        """Get test configuration from environment"""
        return {
            "token": os.getenv("SLACK_BOT_TOKEN"),
            "list_id": os.getenv("TEST_LIST_ID"),
            "title_column_id": os.getenv("TEST_TITLE_COLUMN_ID", "Col10000000")
        }

# Example integration test (requires setup)
class TestIntegration:
    """Integration tests with real Slack API (requires setup)"""
    
    @TestIntegrationHelpers.requires_slack_setup()
    @pytest.mark.asyncio
    async def test_create_and_retrieve_item(self):
        """Test creating and retrieving an item (requires real Slack setup)"""
        config = TestIntegrationHelpers.get_test_config()
        client = SlackListsClient(config["token"])
        
        # Create a test item
        fields = [create_text_field(config["title_column_id"], "Test Item")]
        result = await client.create_list_item(config["list_id"], fields)
        
        assert result["ok"] is True
        item_id = result["item"]["id"]
        
        # Retrieve items to verify creation
        items_result = await client.get_list_items(config["list_id"], limit=10)
        assert items_result["ok"] is True
        
        # Find our created item
        created_item = None
        for item in items_result["items"]:
            if item["id"] == item_id:
                created_item = item
                break
        
        assert created_item is not None
        title_value = extract_field_value(created_item, config["title_column_id"])
        assert "Test Item" in str(title_value)

if __name__ == "__main__":
    print("Running Slack Lists MCP Server Tests")
    print("=" * 40)
    
    # Run basic tests
    pytest.main([__file__, "-v"])
    
    print("\nTo run integration tests, set these environment variables:")
    print("- SLACK_BOT_TOKEN: Your Slack bot token")
    print("- TEST_LIST_ID: A test list ID (e.g., F1234ABCD)")
    print("- TEST_TITLE_COLUMN_ID: Title column ID (optional, defaults to Col10000000)")
    print("\nThen run: pytest tests/test_server.py -v")

# by Aditya Raj Singh — https://adityarajsingh.com/

