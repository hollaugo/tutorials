"""
Notion MCP Server - Core database and content management tools
Integrates with Notion API to provide database management and content operations
"""
import os
from typing import Optional
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

# Import business logic modules
from functions.notion_client import NotionAPIClient
from functions.context_aggregator import ContextAggregator  
from functions.database_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("NotionMCP")

# Initialize business logic clients
notion_client = NotionAPIClient()
context_aggregator = ContextAggregator(notion_client)
database_manager = DatabaseManager(notion_client)

# --- Helpdesk & Context Aggregation Tools ---

@mcp.tool()
def get_page_context(page_id: str, include_children: bool = True, max_depth: int = 2) -> dict:
    """
    Get comprehensive context for a page including subpages, databases, and blocks
    
    Args:
        page_id: Notion page ID
        include_children: Whether to include child pages and databases
        max_depth: Maximum depth to traverse for nested content
    
    Returns:
        Complete context including page content, children, and related data
    """
    return context_aggregator.get_comprehensive_page_context(page_id, include_children, max_depth)

@mcp.tool()
def search_workspace_context(query: str, context_type: str = "all") -> dict:
    """
    Search across workspace and aggregate context for helpdesk queries
    
    Args:
        query: Search query string
        context_type: Type of context to search ('pages', 'databases', 'all')
    
    Returns:
        Aggregated search results with contextual information
    """
    return context_aggregator.search_and_aggregate_context(query, context_type)

@mcp.tool()
def get_database_insights(database_id: str, include_recent_updates: bool = True) -> dict:
    """
    Get comprehensive database insights including structure, recent activity, and patterns
    
    Args:
        database_id: Notion database ID
        include_recent_updates: Include recently updated pages
    
    Returns:
        Database insights with schema, statistics, and recent activity
    """
    return context_aggregator.get_database_insights(database_id, include_recent_updates)


# --- Database Management Tools ---

@mcp.tool()
def create_database_page(database_id: str, properties: dict, content: str = "") -> dict:
    """
    Create a new page in a Notion database with specified properties and content
    
    Args:
        database_id: Target database ID (string)
        properties: Page properties as key-value pairs (dict)
        content: Optional page content in markdown format (string)
    
    Returns:
        Created page information including page_id, url, and formatted properties
    
    Property Types and Examples:
        - Title: "My Page Title" (use exact property name from database)
        - Status: "In Progress" (predefined status options)
        - Select: "High Priority" (predefined select options)  
        - Multi-select: ["tag1", "tag2"] (array of strings)
        - Checkbox: true/false (boolean)
        - Number: 42 (integer or float)
        - Date: "2024-01-15" (ISO date string)
        - People: ["user_id_1", "user_id_2"] (array of user IDs)
        - Rich Text: "Any text content" (string)
        - URL: "https://example.com" (string)
        - Email: "user@example.com" (string)
        - Phone: "+1-555-123-4567" (string)
    
    Content Markdown Examples:
        Basic formatting:
        "# Heading 1\n## Heading 2\n### Heading 3\n\nRegular paragraph text."
        
        Lists:
        "- Bulleted item 1\n- Bulleted item 2\n* Also bulleted\n\n1. Numbered item 1\n2. Numbered item 2"
        
        Todo Lists (checkboxes):
        "- [ ] Unchecked todo item\n- [x] Checked todo item\n- [ ] Another unchecked item"
        
        Mixed content:
        "## Project Overview\n\nThis is the main description.\n\n### Tasks\n- [ ] Set up development environment\n- [ ] Create database schema\n- [x] Initial planning completed\n\n### Notes\n- Important consideration 1\n- Important consideration 2\n\n> This is a quote or callout\n\n```python\n# Code example\nprint('Hello, World!')\n```"
    
    Complete Usage Examples:
    
        Example 1 - Simple Task:
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6",
            "properties": {
                "Name": "Setup Development Environment",
                "Status": "Not Started",
                "Assign": ["user_id_here"]
            },
            "content": "## Setup Tasks\n\n- [ ] Install Node.js\n- [ ] Install dependencies\n- [ ] Configure environment variables\n- [ ] Test database connection"
        }
        
        Example 2 - Detailed Project Page:
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6",
            "properties": {
                "Name": "User Authentication System",
                "Status": "In Progress",
                "Priority": "High"
            },
            "content": "# User Authentication Implementation\n\n## Overview\nImplement secure user authentication with JWT tokens.\n\n## Requirements\n- [ ] User registration endpoint\n- [ ] Login/logout functionality\n- [ ] Password reset flow\n- [ ] JWT token validation\n- [x] Database user model created\n\n## Technical Notes\n- Use bcrypt for password hashing\n- Implement rate limiting for login attempts\n- Add email verification\n\n## API Endpoints\n1. POST /auth/register\n2. POST /auth/login\n3. POST /auth/logout\n4. POST /auth/reset-password\n\n> **Security Note**: Always validate JWT tokens on protected routes"
        }
        
        Example 3 - Meeting Notes:
        {
            "database_id": "meetings_db_id",
            "properties": {
                "Name": "Sprint Planning Meeting",
                "Date": "2024-01-15",
                "Attendees": ["user1", "user2", "user3"],
                "Status": "Completed"
            },
            "content": "# Sprint Planning - January 15, 2024\n\n## Attendees\n- John Smith (Product Manager)\n- Jane Doe (Developer)\n- Bob Johnson (Designer)\n\n## Agenda Items\n1. Review last sprint\n2. Plan current sprint\n3. Discuss blockers\n\n## Action Items\n- [ ] John: Create user stories for new features\n- [ ] Jane: Set up CI/CD pipeline\n- [ ] Bob: Design mockups for dashboard\n- [x] All: Review and approve sprint goals\n\n## Decisions Made\n- Sprint duration: 2 weeks\n- Daily standups at 9 AM\n- Demo on Friday\n\n## Next Steps\n- Start development on Monday\n- Schedule mid-sprint check-in\n- Prepare demo environment"
        }
    
    Tips:
        - Use get_database_schema() first to see exact property names and types
        - Property names are case-sensitive (use exact names from schema)
        - For todo lists, use "- [ ]" for unchecked and "- [x]" for checked items
        - Use "\\n" for line breaks in JSON strings
        - Status and Select properties must match predefined options in the database
        - People properties require actual Notion user IDs
        - Dates should be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    """
    return database_manager.create_page(database_id, properties, content)

@mcp.tool()
def update_database_page(page_id: str, properties: dict = {}, content: str = "", content_mode: str = "append") -> dict:
    """
    Update an existing database page's properties and/or content
    
    Args:
        page_id: Page ID to update (string)
        properties: Properties to update (dict, optional - use {} for no updates)
        content: Content to add/replace (string)
        content_mode: How to handle content - "append", "prepend", or "replace" (default: "append")
    
    Returns:
        Updated page information with success status
    
    Content Modes:
        - "append": Adds content after existing content (default behavior)
        - "prepend": Adds content before existing content  
        - "replace": Completely replaces all existing content with new content
    
    Property Examples:
        - Status: "In Progress" (must match existing status options)
        - Name: "Updated Task Name" (title property)
        - Priority: "High" (select property)
        - Assign: ["user_id"] (people property)
        - Completed: true (checkbox property)
        - Due: "2024-01-15" (date property)
    
    Usage Examples:
    
        Content only (append):
        - page_id: "22e88fb3-1348-8016-964d-e16bf62bf78f"
        - content: "New progress update"
        
        Content only (replace):
        - page_id: "22e88fb3-1348-8016-964d-e16bf62bf78f"
        - content: "Completely new content"
        - content_mode: "replace"
        
        Properties only:
        - page_id: "22e88fb3-1348-8016-964d-e16bf62bf78f"
        - properties: {"Status": "Completed"}
        
        Both properties and content:
        - page_id: "22e88fb3-1348-8016-964d-e16bf62bf78f"
        - content: "Task completed successfully"
        - content_mode: "append"
        - properties: {"Status": "Completed", "Name": "Updated Task"}
    
    Tips:
        - Leave properties as {} if you only want to update content
        - Leave content as "" if you only want to update properties
        - Property names must match the database schema exactly
        - Status/Select values must match existing options in the database
    """
    # Convert empty dict to None for the internal function
    props_to_pass = properties if properties else None
    content_to_pass = content if content else None
    
    return database_manager.update_page(page_id, props_to_pass, content_to_pass, content_mode)


@mcp.tool()
def query_database_advanced(database_id: str, filters: dict = None, sorts: list = None, limit: int = 100) -> dict:
    """
    Advanced database query with complex filters and sorting
    
    Args:
        database_id: Database to query
        filters: Notion filter object (supports compound filters)
        sorts: List of sort objects
        limit: Maximum results to return
    
    Returns:
        Query results with matched pages
    """
    return database_manager.query_database(database_id, filters, sorts, limit)

@mcp.tool()
def bulk_update_database(database_id: str, updates: list, filter_criteria: dict = None) -> dict:
    """
    Perform bulk operations on multiple database pages based on criteria
    
    Args:
        database_id: Target database ID (string)
        updates: List of update operations (list of dicts)
        filter_criteria: Optional filter to limit which pages to update (dict)
    
    Returns:
        Bulk operation results with success/failure counts and error details
    
    Updates Field Examples:
        
        Update Properties Only:
        [
            {
                "operation": "update_properties",
                "properties": {
                    "Status": "In Progress",
                    "Priority": "High"
                }
            }
        ]
        
        Append Content Only:
        [
            {
                "operation": "append_content", 
                "content": "\n\n## Progress Update\n\n- [x] Task started\n- [ ] Next steps"
            }
        ]
        
        Update Both Properties and Content:
        [
            {
                "operation": "update_both",
                "properties": {
                    "Status": "Completed"
                },
                "content": "\n\n✅ **Task completed on $(date)**"
            }
        ]
    
    Filter Criteria Examples:
        
        Filter by Status:
        {
            "property": "Status",
            "status": {
                "equals": "Not Started"
            }
        }
        
        Filter by Text Contains:
        {
            "property": "Name", 
            "rich_text": {
                "contains": "urgent"
            }
        }
        
        Multiple Conditions (AND):
        {
            "and": [
                {
                    "property": "Status",
                    "status": {"equals": "Not Started"}
                },
                {
                    "property": "Priority",
                    "select": {"equals": "High"}
                }
            ]
        }
        
        Multiple Conditions (OR):
        {
            "or": [
                {
                    "property": "Status", 
                    "status": {"equals": "Not Started"}
                },
                {
                    "property": "Status",
                    "status": {"equals": "In Progress"}
                }
            ]
        }
    
    Complete Usage Examples:
    
        Example 1 - Change all "Not Started" tasks to "In Progress":
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6",
            "updates": [
                {
                    "operation": "update_properties",
                    "properties": {
                        "Status": "In Progress"
                    }
                }
            ],
            "filter_criteria": {
                "property": "Status",
                "status": {
                    "equals": "Not Started"
                }
            }
        }
        
        Example 2 - Add notes to all high priority tasks:
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6", 
            "updates": [
                {
                    "operation": "append_content",
                    "content": "\n\n## High Priority Review\n\n⚠️ This task requires immediate attention."
                }
            ],
            "filter_criteria": {
                "property": "Priority",
                "select": {
                    "equals": "High"
                }
            }
        }
        
        Example 3 - Complete all tasks containing "test":
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6",
            "updates": [
                {
                    "operation": "update_both",
                    "properties": {
                        "Status": "Completed"
                    },
                    "content": "\n\n✅ **Bulk completed - test tasks**"
                }
            ],
            "filter_criteria": {
                "property": "Name",
                "rich_text": {
                    "contains": "test"
                }
            }
        }
        
        Example 4 - Update ALL pages (no filter):
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6",
            "updates": [
                {
                    "operation": "append_content",
                    "content": "\n\n---\n**Bulk Update:** All tasks reviewed on $(date)"
                }
            ]
        }
    
    Common Filter Types:
        - status: equals, does_not_equal, is_empty, is_not_empty
        - select: equals, does_not_equal, is_empty, is_not_empty  
        - rich_text: equals, contains, starts_with, ends_with, is_empty
        - number: equals, greater_than, less_than, is_empty
        - checkbox: equals, does_not_equal
        - date: equals, before, after, this_week, past_month, is_empty
    
    Tips:
        - Omit filter_criteria to update ALL pages in the database
        - Test with a restrictive filter first before bulk operations
        - Multiple updates are applied sequentially to each matching page
        - Check the errors array in the response for any failed updates
    """
    return database_manager.bulk_update_pages(database_id, updates, filter_criteria)

@mcp.tool()
def update_page(page_id: str, title: str = "", content: str = "", content_mode: str = "append") -> dict:
    """
    Update any Notion page (database or regular page) with content
    
    Args:
        page_id: Page ID to update (string)
        title: New title for the page (optional, only works for regular pages)
        content: Content to add/replace (string)
        content_mode: How to handle content - "append", "prepend", or "replace" (default: "append")
    
    Returns:
        Updated page information with success status
    
    Content Modes:
        - "append": Adds content after existing content (default behavior)
        - "prepend": Adds content before existing content  
        - "replace": Completely replaces all existing content with new content
    
    Usage Examples:
    
        Regular page content update:
        - page_id: "22e88fb3-1348-8016-964d-e16bf62bf78f"
        - title: "Updated Page Title"
        - content: "New content to add"
        - content_mode: "append"
        
        Database page content update:
        - page_id: "22e88fb3-1348-8016-964d-e16bf62bf78f"
        - content: "Progress update"
        - content_mode: "prepend"
    
    Note: 
        - For database pages, use update_database_page to update properties
        - This tool focuses on content and title updates for any page type
        - Title updates only work for regular pages, not database pages
    """
    try:
        # Get page info to determine if it's a database page
        page_info = notion_client.get_page(page_id)
        if "error" in page_info:
            return page_info
        
        result = {"page_id": page_id, "success": True}
        
        # Update title if provided (only for regular pages)
        if title:
            parent = page_info.get("parent", {})
            if parent.get("type") != "database_id":
                # This is a regular page, we can update the title
                title_update = notion_client.update_page(
                    page_id, 
                    {"title": notion_client.create_title_property(title)}
                )
                if "error" in title_update:
                    return title_update
                result["title_updated"] = True
            else:
                result["title_skipped"] = "Cannot update title of database page - use update_database_page instead"
        
        # Update content if provided
        if content:
            if content_mode == "replace":
                # Replace all content
                content_result = database_manager._replace_page_content(page_id, content)
                result.update(content_result)
            elif content_mode == "append":
                # Append content
                blocks = notion_client.markdown_to_blocks(content)
                append_result = notion_client.append_block_children(page_id, blocks)
                
                if "error" in append_result:
                    return append_result
                
                result["content_appended"] = True
                result["blocks_added"] = len(blocks)
            elif content_mode == "prepend":
                # Prepend content
                content_result = database_manager._prepend_page_content(page_id, content)
                result.update(content_result)
            else:
                return {"error": f"Invalid content_mode: {content_mode}. Use 'append', 'prepend', or 'replace'"}
        
        result["content_mode_used"] = content_mode
        return result
        
    except Exception as e:
        return {"error": f"Failed to update page: {str(e)}"}

@mcp.tool()
def get_database_schema(database_id: str) -> dict:
    """
    Get detailed database schema including property names, types, and configuration
    
    Args:
        database_id: Notion database ID (string) - NOT a page ID
    
    Returns:
        Database schema with exact property names, types, and configuration
    
    Important Notes:
        - This tool requires a DATABASE ID, not a page ID
        - Database IDs typically look like: "22e88fb3-1348-80ba-bb35-d762e7b9b8e6"
        - Page IDs will return an error - use get_page_context() for pages instead
        - To find a database ID: look at the URL when viewing the database in Notion
        - Database URLs look like: https://notion.so/databasename-DATABASEID
        - Page URLs look like: https://notion.so/pagename-PAGEID
    
    Example Usage:
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6"
        }
    
    Example Response:
        {
            "database_id": "22e88fb3-1348-80ba-bb35-d762e7b9b8e6",
            "title": "Project Tasks Database",
            "schema": {
                "Name": {"type": "title", "required": false},
                "Status": {"type": "status", "required": false},
                "Assign": {"type": "people", "required": false}
            },
            "property_names": ["Name", "Status", "Assign"],
            "success": true
        }
    
    Error Handling:
        - If you provide a page ID instead of database ID, you'll get a helpful error
        - Use get_page_context() to get information about individual pages
        - Use search_workspace_context() to find databases by name
    """
    return database_manager.get_database_schema(database_id)





# --- Analysis Prompts ---



@mcp.prompt()
def helpdesk_resolution_prompt(user_query: str) -> str:
    """Helpdesk query resolution prompt with context aggregation"""
    return f"""Resolve the following helpdesk query using comprehensive workspace context: "{user_query}"

Follow this systematic approach:

1. **Context Gathering**:
   - Use search_workspace_context to find relevant pages and databases
   - If specific pages/databases are mentioned, use get_page_context or get_database_insights

2. **Information Analysis**:
   - Analyze the gathered context for relevant information
   - Identify any gaps in information that need additional searches
   - Cross-reference information from multiple sources

3. **Solution Development**:
   - Provide step-by-step solutions based on the gathered context
   - Include specific page/database references with URLs when possible
   - Suggest related tools or workflows that might be helpful

4. **Follow-up Actions**:
   - Recommend specific Notion actions the user can take
   - Suggest process improvements to prevent similar queries
   - Offer to create documentation or procedures if needed

Structure your response as:
- **Quick Answer**: Direct response to the query
- **Detailed Context**: Relevant information found in the workspace
- **Step-by-Step Solution**: Actionable instructions
- **Related Resources**: Links to relevant pages/databases
- **Recommended Actions**: Next steps or improvements"""


# --- API Endpoints ---

from fastapi import Request
# from slack_client import handler  # Commented out - handler not available

# Example of exposing Slack endpoint using FastMCP custom route
@mcp.custom_route("/slack/events", methods=["POST"])
async def slack_events_endpoint(req: Request):
    """Expose Slack events endpoint for Slack event handling."""
    try:
        # Get the request body
        body = await req.json()
        
        # Handle URL verification challenge
        if body.get("type") == "url_verification":
            challenge = body.get("challenge")
            if challenge:
                return JSONResponse({
                    "challenge": challenge
                })
            else:
                return JSONResponse({
                    "error": "challenge_failed",
                    "message": "No challenge provided"
                }, status_code=400)
        
        # Handle other Slack events
        return JSONResponse({
            "status": "success",
            "message": "Slack event received",
            "event_type": body.get("type", "unknown")
        })
        
    except Exception as e:
        return JSONResponse({
            "error": "challenge_failed",
            "message": f"Error processing request: {str(e)}"
        }, status_code=500)

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint"""
    return PlainTextResponse("OK")

@mcp.custom_route("/info", methods=["GET"])
async def mcp_info(request):
    """Return MCP server info including tool and prompt counts"""
    
    tools = [
        # Context & Helpdesk
        "get_page_context", "search_workspace_context", "get_database_insights",
        # Database Management  
        "create_database_page", "update_database_page", "query_database_advanced", "bulk_update_database", "get_database_schema",
        # General Page Management
        "update_page"
    ]
    
    prompts = [
        "workspace_analysis_prompt", "helpdesk_resolution_prompt"
    ]
    
    return JSONResponse({
        "name": "NotionMCP",
        "description": "Core Notion database and content management tools",
        "version": "1.0.0",
        "features": {
            "helpdesk_support": "AI-powered context aggregation and query resolution",
            "database_management": "Advanced CRUD operations with flexible content handling",
            "content_operations": "Create, update, and upsert pages with markdown support",
            "schema_management": "Database schema analysis and property validation"
        },
        "tools": {
            "count": len(tools),
            "list": tools,
            "categories": {
                "helpdesk": 3,
                "database": 5,
                "general": 1
            }
        },
        "prompts": {
            "count": len(prompts),
            "list": prompts
        },
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/mcp"
        }
    })

# Create CORS middleware
cors_middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
]

# Create HTTP app with CORS middleware
mcp_app = mcp.http_app(path='/mcp', middleware=cors_middleware)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        # Run in stdio mode for Claude Desktop
        mcp.run()
    elif len(sys.argv) > 1 and sys.argv[1] == "--http":
        # Run in streamable HTTP mode for MCP Inspector
        mcp.run(
            transport="http",
            host="127.0.0.1", 
            port=8080,
            path="/mcp"
        )
    else:
        # Run HTTP server for development
        import uvicorn
        port = int(os.environ.get("PORT", 8080))
        uvicorn.run(mcp_app, host="0.0.0.0", port=port)