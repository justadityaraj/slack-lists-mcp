# Slack Lists MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP Version](https://img.shields.io/badge/MCP-1.2.0%2B-brightgreen.svg)](https://modelcontextprotocol.io/)

**A production-ready Model Context Protocol (MCP) server that provides AI assistants with powerful tools to interact with Slack Lists.**

This server acts as a bridge between AI models and Slack, enabling seamless creation, retrieval, updating, deletion, filtering, and management of Slack List items through a standardized protocol. It empowers AI assistants like Claude Desktop to become powerful productivity tools for managing tasks, projects, and data within Slack.

This project provides a complete package with:
- **Comprehensive Toolset**: Create, query, update, delete, filter, and export list items.
- **Robust Implementation**: Built with Python, FastMCP, and best practices.
- **Easy Deployment**: Simple setup with environment variables.
- **Detailed Documentation**: Full README, tool reference, and examples.
- **Extensible Design**: Easily add new tools and functionality.

Whether you're a developer looking to integrate AI with Slack or a user wanting to supercharge your productivity, this MCP server provides the foundation for powerful, context-aware interactions with your Slack Lists.




## Features

This MCP server provides a rich set of tools for interacting with Slack Lists:

- **Create Single Item**: Add one item to a list with detailed fields.
- **Bulk Create Items**: Add multiple items at once with built-in rate limiting to respect Slack's API.
- **Retrieve Items**: Fetch a list of items with optional metadata.
- **Update Items**: Update any cell on an existing item — check a task off, reassign it, reschedule it, or edit any field (full task management).
- **Delete Items**: Permanently remove an item from a list.
- **Discover Columns**: Infer a list's column IDs, types, and select option IDs from its existing items (Slack exposes no schema API, so this saves you from hunting for IDs in browser dev tools).
- **Filter Items**: Powerful server-side filtering based on any field value (status, assignee, priority, etc.).
- **Export Data**: Export list items to JSON or CSV format for analysis or backup.
- **Subtask Creation**: Create sub-items under a parent item.
- **Full Field Support**: Works with all Slack List field types (text, date, user, select, checkbox, number, email, phone).
- **Error Handling**: Robust error handling and clear feedback for failed operations.




## Getting Started

Follow these steps to get your Slack Lists MCP server up and running.

### Prerequisites

- **Python 3.10+**
- **Slack Workspace**: A Slack workspace where you have permission to install apps.
- **Slack Bot Token**: A bot token with `lists:read` and `lists:write` scopes.

### 1. Create a Slack App

1. Go to the [Slack API website](https://api.slack.com/apps) and click **Create New App**.
2. Choose "From scratch", give your app a name (e.g., "Lists MCP Server"), and select your workspace.
3. In the app settings, go to **OAuth & Permissions**.
4. Under **Bot Token Scopes**, add the following scopes:
   - `lists:read`
   - `lists:write`
5. Click **Install to Workspace** at the top of the page and authorize the app.
6. Copy the **Bot User OAuth Token** (it starts with `xoxb-`). This is your `SLACK_BOT_TOKEN`.

### 2. Installation

Clone the repository and install the dependencies:

```bash
# Clone the repository
git clone https://github.com/justadityaraj/slack-lists-mcp.git
cd slack-lists-mcp

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file by copying the example:

```bash
cp .env.example .env
```

Open the `.env` file and set your `SLACK_BOT_TOKEN`:

```dotenv
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
```

### 4. Running the Server

You can run the server directly from the command line:

```bash
python src/slack_lists_server.py
```

The server will start and listen for MCP requests over STDIO.

### 5. Connecting to an MCP Host (e.g., Claude Desktop)

To use the server with an AI assistant, you need to configure your MCP host.

1. Open your MCP host's configuration file (e.g., `mcp_servers.json` for Claude Desktop).
2. Add a new server entry pointing to your `slack_lists_server.py` script.

**Example `mcp_servers.json` configuration:**

```json
{
  "mcpServers": {
    "slack-lists": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["/path/to/slack-lists-mcp-server/src/slack_lists_server.py"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token-here"
      }
    }
  }
}
```

**Important**: Make sure to use the absolute path to your Python executable and the server script.

Once configured, restart your MCP host. The Slack Lists tools should now be available to your AI assistant.




## Tool Reference

This server exposes the following tools to your AI assistant. Each tool is designed to be intuitive and powerful, with clear descriptions and parameters.

--- 

### `create_list_item`

Creates a single new item in a Slack List.

**Description:**
This tool creates one item in the specified Slack List. The item must have at least a title field, and can include additional fields as needed. All field values are validated against the list's schema.

**Parameters:**
- `list_id` (string, required): The ID of the Slack List (e.g., `F1234ABCD`).
- `title` (string, required): The main title/text for the item.
- `title_column_id` (string, optional): Column ID for the title field (defaults to `Col10000000`).
- `additional_fields` (string, optional): JSON string of additional fields. See [Field Formats](#field-formats) for details.
- `parent_item_id` (string, optional): Optional parent item ID to create a subtask.

**Example Prompt:**
> "Create a new task in my project list `F1234ABCD` with the title 'Finish Q4 report' and a due date of 2024-12-20."

--- 

### `create_multiple_list_items`

Creates multiple items in a Slack List with rate limiting.

**Description:**
This tool allows bulk creation of list items. Each item is created individually with proper rate limiting to respect Slack's API limits (~50 requests per minute).

**Parameters:**
- `list_id` (string, required): The ID of the Slack List.
- `items_data` (string, required): JSON array of items to create. See [Bulk Creation Format](#bulk-creation-format) for details.
- `title_column_id` (string, optional): Column ID for the title field.
- `rate_limit_delay` (float, optional): Delay between requests in seconds (default: 1.2s).

**Example Prompt:**
> "Add these three tasks to my list `F1234ABCD`: 1. Design mockups (due 12/10), 2. Write tests (due 12/15), 3. Update documentation (due 12/20)."

--- 

### `get_list_items`

Retrieves items from a Slack List.

**Description:**
This tool fetches items from the specified Slack List with optional metadata. Use this to view current list contents, check item details, or prepare data for filtering.

**Parameters:**
- `list_id` (string, required): The ID of the Slack List.
- `limit` (integer, optional): Maximum number of items to retrieve (default: 50, max: 100).
- `include_metadata` (boolean, optional): Whether to include creation/update metadata (default: True).

**Example Prompt:**
> "Show me the 10 most recent items in my 'Tasks' list `F5678EFGH`."

--- 

### `filter_list_items`

Filters and retrieves items from a Slack List based on field values.

**Description:**
This tool allows you to search and filter list items by specific field values. Useful for finding items with a specific status, assignee, priority, or any other field.

**Parameters:**
- `list_id` (string, required): The ID of the Slack List.
- `filter_column_id` (string, required): Column ID to filter by.
- `filter_value` (string, required): Value to search for.
- `filter_operator` (string, optional): How to match the value. See [Filter Operators](#filter-operators) for options.
- `max_items` (integer, optional): Maximum number of items to process (default: 100).

**Example Prompt:**
> "Find all tasks in list `F1234ABCD` assigned to me that are marked as 'High' priority."

--- 

### `export_list_items`

Exports items from a Slack List to a structured data format.

**Description:**
This tool exports list items to JSON or CSV format, with optional filtering. Useful for backup, analysis, or integration with other systems.

**Parameters:**
- `list_id` (string, required): The ID of the Slack List.
- `export_format` (string, optional): Output format - `json` or `csv` (default: `json`).
- `filter_column_id` (string, optional): Optional column ID to filter by.
- `filter_value` (string, optional): Value to filter for (required if `filter_column_id` is provided).
- `filter_operator` (string, optional): Filter operator.

**Example Prompt:**
> "Export all completed tasks from my project list `F1234ABCD` to a CSV file."

---

### `update_list_item`

Updates one or more cells on an existing Slack List item (row). This is the tool for full task management: check a task off, reassign it, reschedule it, or edit any field — in a single call.

**Description:**
Updates the given columns on the item identified by `row_id`. Find the `row_id` with `get_list_items` or `filter_list_items` (it is each item's `id`, e.g. `Rec1234567`). Find `column_id`s and select option IDs with `discover_list_columns`.

**Parameters:**
- `list_id` (string, required): The ID of the Slack List (e.g., `F1234ABCD`).
- `row_id` (string, required): The ID of the item/row to update (e.g., `Rec1234567`).
- `fields` (string, required): JSON array of cells to update. Each cell is `{"column_id": "...", "type": "...", "value": ...}`. See [Field Formats](#field-formats). Supported types: `text`, `date`, `user`, `select`, `checkbox`, `number`, `email`, `phone`.

**Example Prompt:**
> "Mark task `Rec1234567` in list `F1234ABCD` as done, reassign it to `U1234567`, and move the due date to 2025-09-20."

---

### `delete_list_item`

Permanently deletes an item (row) from a Slack List. This cannot be undone.

**Parameters:**
- `list_id` (string, required): The ID of the Slack List (e.g., `F1234ABCD`).
- `row_id` (string, required): The ID of the item/row to delete (e.g., `Rec1234567`).

**Example Prompt:**
> "Delete item `Rec1234567` from list `F1234ABCD`."

---

### `discover_list_columns`

Discovers a list's columns by inspecting its existing items. Slack exposes no API to read a list's schema directly, so this infers each column's ID, type, a sample value, and (for select columns) the option IDs from the data already in the list. Use it to find the `column_id` and select option IDs needed by `create_list_item` and `update_list_item`.

**Note:** A column is only discoverable if at least one item has a value in it. Empty columns will not appear.

**Parameters:**
- `list_id` (string, required): The ID of the Slack List (e.g., `F1234ABCD`).
- `sample_size` (integer, optional): How many items to scan, 1-1000 (default: 100).

**Example Prompt:**
> "What columns does list `F1234ABCD` have, and what are the status option IDs?"


## Data Formats

### Field Formats

When using `create_list_item` or `create_multiple_list_items`, you need to provide field data in a specific JSON format. The `additional_fields` and `items_data` parameters expect a JSON string.

Each field is an object with `column_id`, `type`, and `value`:

```json
[
  {
    "column_id": "Col10000001",
    "type": "date",
    "value": "2024-12-31"
  },
  {
    "column_id": "Col10000002",
    "type": "select",
    "value": ["OptionID123"]
  },
  {
    "column_id": "Col10000003",
    "type": "user",
    "value": ["U1234567", "U2345678"]
  },
  {
    "column_id": "Col10000004",
    "type": "checkbox",
    "value": true
  }
]
```

**Supported Field Types:**
- `text`: String value.
- `date`: String in `YYYY-MM-DD` format.
- `user`: Array of Slack user IDs (e.g., `["U1234567"]`).
- `select`: Array of select option IDs.
- `checkbox`: Boolean `true` or `false`.
- `number`: Numeric value.
- `email`: String email address.
- `phone`: String phone number.

### Bulk Creation Format

The `items_data` parameter for `create_multiple_list_items` expects a JSON array where each object represents an item to be created.

```json
[
  {
    "title": "First Task",
    "fields": [
      {"column_id": "Col123", "type": "date", "value": "2024-12-15"}
    ]
  },
  {
    "title": "Second Task",
    "fields": [
      {"column_id": "Col123", "type": "date", "value": "2024-12-20"},
      {"column_id": "Col456", "type": "user", "value": ["U1234567"]}
    ]
  }
]
```

### Filter Operators

The `filter_list_items` tool supports the following operators:

- `contains`: Field contains the value (case-insensitive).
- `equals`: Field exactly matches the value (case-insensitive).
- `not_equals`: Field does not match the value.
- `not_contains`: Field does not contain the value.
- `exists`: Field has any non-empty value.
- `not_exists`: Field is empty or missing.




## Troubleshooting

- **`invalid_auth` Error**: Your `SLACK_BOT_TOKEN` is likely incorrect or has been revoked. Generate a new one and update your `.env` file.
- **`missing_scope` Error**: Ensure your Slack app has both `lists:read` and `lists:write` scopes.
- **`list_not_found` Error**: The `list_id` you provided is incorrect. Double-check the ID in Slack.
- **Server Not Responding**: Make sure the server is running and that the path in your MCP host configuration is correct. Check for any errors in the server logs.
- **JSON Errors**: Validate your JSON strings for `additional_fields` and `items_data` using an online validator.

## How to Find List and Column IDs

1. **List ID**: Open the list in Slack. The ID is the last part of the URL (e.g., `https://app.slack.com/client/.../F1234ABCD`).
2. **Column ID**: The easiest way is the `discover_list_columns` tool, which lists every column's ID, type, and select option IDs by inspecting the list's existing items. (You can also inspect browser network requests, or read the raw output of `get_list_items`.)

## Contributing

Contributions are welcome! If you have ideas for new features, bug fixes, or improvements, please open an issue or submit a pull request. See `CONTRIBUTING.md` for more details.

## Verification status

All tools are covered by unit tests and have been exercised against a live Slack workspace: `discover_list_columns`, `create_list_item`, `update_list_item` (text, user, date, and checkbox cells, including a single multi-cell "check off + reassign + reschedule" update), and `delete_list_item` all round-trip correctly.

One field shape differs from the published docs: **checkbox cells take a bare boolean** (`"checkbox": true`), not an array. The docs show `"checkbox": [boolean]`, but the live API rejects the array form with `invalid_arguments` and returns the value as a bare bool, so this server sends a bare bool.

## Credits

This project is derived from [maplehilllabs/mcp-slack-lists](https://github.com/maplehilllabs/mcp-slack-lists) (MIT), extended with `update_list_item`, `delete_list_item`, and `discover_list_columns` plus full field-type support.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

<!-- by [Aditya Raj Singh](https://adityarajsingh.com/) -->


