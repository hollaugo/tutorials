"""
Notion API Client - Core client for interacting with Notion API
Handles authentication, requests, and common operations
"""
import os
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class NotionAPIClient:
    """Core client for Notion API operations"""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv("NOTION_TOKEN")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        if not self.token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN environment variable.")
    
    def _make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Make authenticated request to Notion API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def get_page(self, page_id: str) -> dict:
        """Get a page by ID"""
        return self._make_request("GET", f"pages/{page_id}")
    
    def get_database(self, database_id: str) -> dict:
        """Get a database by ID"""
        return self._make_request("GET", f"databases/{database_id}")
    
    def query_database(self, database_id: str, filter_obj: dict = None, sorts: list = None, page_size: int = 100) -> dict:
        """Query a database with optional filters and sorting"""
        data = {
            "page_size": page_size
        }
        
        if filter_obj:
            data["filter"] = filter_obj
        if sorts:
            data["sorts"] = sorts
            
        return self._make_request("POST", f"databases/{database_id}/query", data)
    
    def create_page(self, parent: dict, properties: dict, children: list = None) -> dict:
        """Create a new page"""
        data = {
            "parent": parent,
            "properties": properties
        }
        
        if children:
            data["children"] = children
            
        return self._make_request("POST", "pages", data)
    
    def update_page(self, page_id: str, properties: dict) -> dict:
        """Update a page's properties"""
        data = {"properties": properties}
        return self._make_request("PATCH", f"pages/{page_id}", data)
    
    def get_block_children(self, block_id: str, page_size: int = 100) -> dict:
        """Get children of a block"""
        params = {"page_size": page_size}
        return self._make_request("GET", f"blocks/{block_id}/children", params=params)
    
    def append_block_children(self, block_id: str, children: list) -> dict:
        """Append children to a block"""
        data = {"children": children}
        return self._make_request("PATCH", f"blocks/{block_id}/children", data)
    
    def search(self, query: str = None, filter_obj: dict = None, sorts: list = None, page_size: int = 100) -> dict:
        """Search across workspace"""
        data = {
            "page_size": page_size
        }
        
        if query:
            data["query"] = query
        if filter_obj:
            data["filter"] = filter_obj
        if sorts:
            data["sorts"] = sorts
            
        return self._make_request("POST", "search", data)
    
    def get_all_results(self, method_func, *args, **kwargs) -> list:
        """Get all results from a paginated endpoint"""
        all_results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            if next_cursor:
                kwargs['start_cursor'] = next_cursor
                
            response = method_func(*args, **kwargs)
            
            if "error" in response:
                return response
                
            results = response.get("results", [])
            all_results.extend(results)
            
            has_more = response.get("has_more", False)
            next_cursor = response.get("next_cursor")
            
        return all_results
    
    def extract_plain_text(self, rich_text: list) -> str:
        """Extract plain text from rich text array"""
        if not rich_text:
            return ""
        
        text_parts = []
        for text_obj in rich_text:
            if isinstance(text_obj, dict) and "text" in text_obj:
                text_parts.append(text_obj["text"].get("content", ""))
            elif isinstance(text_obj, dict) and "plain_text" in text_obj:
                text_parts.append(text_obj["plain_text"])
                
        return "".join(text_parts)
    
    def format_page_properties(self, page: dict) -> dict:
        """Format page properties for easier access"""
        properties = page.get("properties", {})
        formatted = {}
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type")
            
            if prop_type == "title":
                formatted[prop_name] = self.extract_plain_text(prop_data.get("title", []))
            elif prop_type == "rich_text":
                formatted[prop_name] = self.extract_plain_text(prop_data.get("rich_text", []))
            elif prop_type == "number":
                formatted[prop_name] = prop_data.get("number")
            elif prop_type == "select":
                select_obj = prop_data.get("select")
                formatted[prop_name] = select_obj.get("name") if select_obj else None
            elif prop_type == "status":
                status_obj = prop_data.get("status")
                formatted[prop_name] = status_obj.get("name") if status_obj else None
            elif prop_type == "multi_select":
                multi_select = prop_data.get("multi_select", [])
                formatted[prop_name] = [option.get("name") for option in multi_select]
            elif prop_type == "date":
                date_obj = prop_data.get("date")
                formatted[prop_name] = date_obj.get("start") if date_obj else None
            elif prop_type == "checkbox":
                formatted[prop_name] = prop_data.get("checkbox", False)
            elif prop_type == "url":
                formatted[prop_name] = prop_data.get("url")
            elif prop_type == "email":
                formatted[prop_name] = prop_data.get("email")
            elif prop_type == "phone_number":
                formatted[prop_name] = prop_data.get("phone_number")
            elif prop_type == "people":
                people = prop_data.get("people", [])
                formatted[prop_name] = [person.get("name", person.get("id")) for person in people]
            elif prop_type == "files":
                files = prop_data.get("files", [])
                formatted[prop_name] = [file.get("name") for file in files]
            elif prop_type == "relation":
                relations = prop_data.get("relation", [])
                formatted[prop_name] = [rel.get("id") for rel in relations]
            elif prop_type == "formula":
                formula = prop_data.get("formula", {})
                formatted[prop_name] = formula.get("string") or formula.get("number") or formula.get("boolean")
            elif prop_type == "rollup":
                rollup = prop_data.get("rollup", {})
                formatted[prop_name] = rollup.get("array") or rollup.get("number") or rollup.get("date")
            else:
                formatted[prop_name] = prop_data.get(prop_type)
                
        return formatted
    
    def create_rich_text(self, text: str) -> list:
        """Create rich text array from plain text"""
        return [{"text": {"content": text}}]
    
    def create_title_property(self, text: str) -> dict:
        """Create title property"""
        return {"title": self.create_rich_text(text)}
    
    def create_rich_text_property(self, text: str) -> dict:
        """Create rich text property"""
        return {"rich_text": self.create_rich_text(text)}
    
    def create_select_property(self, option_name: str) -> dict:
        """Create select property"""
        return {"select": {"name": option_name}}
    
    def create_status_property(self, status_name: str) -> dict:
        """Create status property"""
        return {"status": {"name": status_name}}
    
    def create_multi_select_property(self, options: list) -> dict:
        """Create multi-select property"""
        return {"multi_select": [{"name": option} for option in options]}
    
    def create_date_property(self, start_date: str, end_date: str = None) -> dict:
        """Create date property"""
        date_obj = {"start": start_date}
        if end_date:
            date_obj["end"] = end_date
        return {"date": date_obj}
    
    def create_checkbox_property(self, checked: bool) -> dict:
        """Create checkbox property"""
        return {"checkbox": checked}
    
    def create_number_property(self, number: float) -> dict:
        """Create number property"""
        return {"number": number}
    
    def create_url_property(self, url: str) -> dict:
        """Create URL property"""
        return {"url": url}
    
    def create_email_property(self, email: str) -> dict:
        """Create email property"""
        return {"email": email}
    
    def create_phone_property(self, phone: str) -> dict:
        """Create phone number property"""
        return {"phone_number": phone}
    
    def create_people_property(self, user_ids: list) -> dict:
        """Create people property"""
        return {"people": [{"id": user_id} for user_id in user_ids]}
    
    def create_relation_property(self, page_ids: list) -> dict:
        """Create relation property"""
        return {"relation": [{"id": page_id} for page_id in page_ids]}
    
    def create_paragraph_block(self, text: str) -> dict:
        """Create paragraph block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self.create_rich_text(text)
            }
        }
    
    def create_heading_block(self, text: str, level: int = 1) -> dict:
        """Create heading block"""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self.create_rich_text(text)
            }
        }
    
    def create_bulleted_list_block(self, text: str) -> dict:
        """Create bulleted list item block"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self.create_rich_text(text)
            }
        }
    
    def create_numbered_list_block(self, text: str) -> dict:
        """Create numbered list item block"""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self.create_rich_text(text)
            }
        }
    
    def create_to_do_block(self, text: str, checked: bool = False) -> dict:
        """Create to-do block"""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": self.create_rich_text(text),
                "checked": checked
            }
        }
    
    def create_code_block(self, text: str, language: str = "plain text") -> dict:
        """Create code block"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": self.create_rich_text(text),
                "language": language
            }
        }
    
    def create_quote_block(self, text: str) -> dict:
        """Create quote block"""
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": self.create_rich_text(text)
            }
        }
    
    def create_callout_block(self, text: str, icon: str = "💡") -> dict:
        """Create callout block"""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": self.create_rich_text(text),
                "icon": {"emoji": icon}
            }
        }
    
    def markdown_to_blocks(self, markdown_text: str) -> list:
        """Convert markdown text to Notion blocks (basic implementation)"""
        blocks = []
        
        # Handle escaped newlines first
        if '\\n' in markdown_text:
            markdown_text = markdown_text.replace('\\n', '\n')
        
        lines = markdown_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('# '):
                blocks.append(self.create_heading_block(line[2:], 1))
            elif line.startswith('## '):
                blocks.append(self.create_heading_block(line[3:], 2))
            elif line.startswith('### '):
                blocks.append(self.create_heading_block(line[4:], 3))
            elif line.startswith('- [ ] '):
                # Unchecked todo item
                blocks.append(self.create_to_do_block(line[6:], False))
            elif line.startswith('- [x] '):
                # Checked todo item
                blocks.append(self.create_to_do_block(line[6:], True))
            elif line.startswith('- '):
                blocks.append(self.create_bulleted_list_block(line[2:]))
            elif line.startswith('* '):
                blocks.append(self.create_bulleted_list_block(line[2:]))
            elif line.startswith('1. '):
                blocks.append(self.create_numbered_list_block(line[3:]))
            elif line.startswith('> '):
                blocks.append(self.create_quote_block(line[2:]))
            elif line.startswith('```') and line.endswith('```'):
                # Simple code block handling
                code_text = line[3:-3]
                blocks.append(self.create_code_block(code_text))
            else:
                blocks.append(self.create_paragraph_block(line))
                
        return blocks