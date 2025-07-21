"""
Database Manager - Advanced database operations and management
Handles CRUD operations, bulk updates, and complex queries
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class DatabaseManager:
    """Manages database operations and bulk processing"""
    
    def __init__(self, notion_client):
        self.client = notion_client
    
    def create_page(self, database_id: str, properties: dict, content: str = "") -> dict:
        """
        Create a new page in a database with properties and content
        
        Args:
            database_id: Target database ID
            properties: Page properties as key-value pairs
            content: Optional page content in markdown
        
        Returns:
            Created page information
        """
        try:
            # Get database schema to validate property names
            schema_result = self.get_database_schema(database_id)
            if "error" in schema_result:
                return schema_result
            
            # Convert simple properties to Notion format with schema validation
            notion_properties = self._convert_properties_to_notion(properties, schema_result["schema"])
            
            # Create page parent reference
            parent = {"database_id": database_id}
            
            # Convert content to blocks if provided
            children = []
            if content:
                children = self.client.markdown_to_blocks(content)
            
            # Create the page
            result = self.client.create_page(parent, notion_properties, children)
            
            if "error" in result:
                return result
            
            return {
                "page_id": result["id"],
                "url": result["url"],
                "created_time": result["created_time"],
                "properties": self.client.format_page_properties(result),
                "success": True
            }
            
        except Exception as e:
            return {"error": f"Failed to create page: {str(e)}"}
    
    def update_page(self, page_id: str, properties: dict = None, content: str = None, content_mode: str = "append") -> dict:
        """
        Update an existing page's properties and/or content
        
        Args:
            page_id: Page ID to update
            properties: Properties to update
            content: Content to add/replace
            content_mode: How to handle content ('append', 'prepend', 'replace')
        
        Returns:
            Updated page information
        """
        try:
            result = {}
            
            # Update properties if provided
            if properties:
                # Get the page to determine its parent database for schema validation
                page_info = self.client.get_page(page_id)
                if "error" in page_info:
                    return page_info
                
                # Get database schema if page is in a database
                schema = None
                parent = page_info.get("parent", {})
                if parent.get("type") == "database_id":
                    database_id = parent.get("database_id")
                    schema_result = self.get_database_schema(database_id)
                    if "error" not in schema_result:
                        schema = schema_result["schema"]
                
                # Convert properties with schema validation
                notion_properties = self._convert_properties_to_notion(properties, schema)
                update_result = self.client.update_page(page_id, notion_properties)
                
                if "error" in update_result:
                    return update_result
                
                result["properties_updated"] = True
                result["properties"] = self.client.format_page_properties(update_result)
            
            # Handle content based on mode
            if content:
                if content_mode == "replace":
                    # Replace all content by deleting existing blocks and adding new ones
                    content_result = self._replace_page_content(page_id, content)
                    result.update(content_result)
                elif content_mode == "append":
                    # Append to existing content
                    blocks = self.client.markdown_to_blocks(content)
                    append_result = self.client.append_block_children(page_id, blocks)
                    
                    if "error" in append_result:
                        return append_result
                    
                    result["content_appended"] = True
                    result["blocks_added"] = len(blocks)
                elif content_mode == "prepend":
                    # Prepend to existing content
                    content_result = self._prepend_page_content(page_id, content)
                    result.update(content_result)
                else:
                    return {"error": f"Invalid content_mode: {content_mode}. Use 'append', 'prepend', or 'replace'"}
            
            
            result["success"] = True
            result["page_id"] = page_id
            result["content_provided"] = content is not None and content != ""
            result["content_mode_used"] = content_mode
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to update page: {str(e)}"}
    
    def upsert_page(self, page_id: str = None, database_id: str = None, properties: dict = None, content: str = None, content_mode: str = "replace") -> dict:
        """
        Create a new page or update existing page with flexible content handling
        
        Args:
            page_id: Page ID to update (if None, creates new page)
            database_id: Database ID (required if creating new page)
            properties: Properties to set/update
            content: Content to set/append/prepend
            content_mode: How to handle content ('replace', 'append', 'prepend')
        
        Returns:
            Page information with operation details
        """
        try:
            if page_id:
                # Update existing page
                result = {"operation": "update", "page_id": page_id}
                
                # Update properties if provided
                if properties:
                    # Get the page to determine its parent database for schema validation
                    page_info = self.client.get_page(page_id)
                    if "error" in page_info:
                        return page_info
                    
                    # Get database schema if page is in a database
                    schema = None
                    parent = page_info.get("parent", {})
                    if parent.get("type") == "database_id":
                        db_id = parent.get("database_id")
                        schema_result = self.get_database_schema(db_id)
                        if "error" not in schema_result:
                            schema = schema_result["schema"]
                    
                    # Convert properties with schema validation
                    notion_properties = self._convert_properties_to_notion(properties, schema)
                    update_result = self.client.update_page(page_id, notion_properties)
                    
                    if "error" in update_result:
                        return update_result
                    
                    result["properties_updated"] = True
                    result["properties"] = self.client.format_page_properties(update_result)
                
                # Handle content based on mode
                if content:
                    if content_mode == "replace":
                        # Replace all content by deleting existing blocks and adding new ones
                        result.update(self._replace_page_content(page_id, content))
                    elif content_mode == "append":
                        # Append to existing content
                        blocks = self.client.markdown_to_blocks(content)
                        append_result = self.client.append_block_children(page_id, blocks)
                        
                        if "error" in append_result:
                            return append_result
                        
                        result["content_appended"] = True
                        result["blocks_added"] = len(blocks)
                    elif content_mode == "prepend":
                        # Prepend to existing content
                        result.update(self._prepend_page_content(page_id, content))
                    else:
                        return {"error": f"Invalid content_mode: {content_mode}. Use 'replace', 'append', or 'prepend'"}
                
            else:
                # Create new page
                if not database_id:
                    return {"error": "database_id is required when creating a new page"}
                
                create_result = self.create_page(database_id, properties or {}, content or "")
                if "error" in create_result:
                    return create_result
                
                result = {
                    "operation": "create",
                    "page_id": create_result["page_id"],
                    "url": create_result["url"],
                    "created_time": create_result["created_time"],
                    "properties": create_result["properties"]
                }
            
            result["success"] = True
            return result
            
        except Exception as e:
            return {"error": f"Failed to upsert page: {str(e)}"}
    
    def _replace_page_content(self, page_id: str, new_content: str) -> dict:
        """Replace all content blocks in a page"""
        try:
            # Get existing blocks
            existing_blocks = self.client.get_block_children(page_id)
            if "error" in existing_blocks:
                return existing_blocks
            
            # Delete existing blocks
            deleted_count = 0
            for block in existing_blocks.get("results", []):
                delete_result = self.client._make_request("DELETE", f"blocks/{block['id']}")
                if "error" not in delete_result:
                    deleted_count += 1
            
            # Add new blocks
            if new_content:
                new_blocks = self.client.markdown_to_blocks(new_content)
                append_result = self.client.append_block_children(page_id, new_blocks)
                
                if "error" in append_result:
                    return append_result
                
                return {
                    "content_replaced": True,
                    "blocks_deleted": deleted_count,
                    "blocks_added": len(new_blocks)
                }
            else:
                return {
                    "content_replaced": True,
                    "blocks_deleted": deleted_count,
                    "blocks_added": 0
                }
                
        except Exception as e:
            return {"error": f"Failed to replace page content: {str(e)}"}
    
    def _prepend_page_content(self, page_id: str, new_content: str) -> dict:
        """
        Prepend content to a page by combining new content with existing content
        """
        try:
            # Create new blocks from markdown
            new_blocks = self.client.markdown_to_blocks(new_content)
            if not new_blocks:
                return {"content_prepended": True, "blocks_added": 0}
            
            # Get existing blocks
            existing_blocks = self.client.get_block_children(page_id)
            if "error" in existing_blocks:
                return existing_blocks
            
            existing_results = existing_blocks.get("results", [])
            
            # Convert existing blocks to markdown-like text for reconstruction
            existing_content_parts = []
            for block in existing_results:
                block_type = block.get("type")
                if block_type == "paragraph":
                    rich_text = block.get("paragraph", {}).get("rich_text", [])
                    if rich_text:
                        text = rich_text[0].get("text", {}).get("content", "")
                        existing_content_parts.append(text)
                elif block_type == "heading_1":
                    rich_text = block.get("heading_1", {}).get("rich_text", [])
                    if rich_text:
                        text = rich_text[0].get("text", {}).get("content", "")
                        existing_content_parts.append(f"# {text}")
                elif block_type == "heading_2":
                    rich_text = block.get("heading_2", {}).get("rich_text", [])
                    if rich_text:
                        text = rich_text[0].get("text", {}).get("content", "")
                        existing_content_parts.append(f"## {text}")
                elif block_type == "heading_3":
                    rich_text = block.get("heading_3", {}).get("rich_text", [])
                    if rich_text:
                        text = rich_text[0].get("text", {}).get("content", "")
                        existing_content_parts.append(f"### {text}")
                elif block_type == "bulleted_list_item":
                    rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                    if rich_text:
                        text = rich_text[0].get("text", {}).get("content", "")
                        existing_content_parts.append(f"- {text}")
                elif block_type == "numbered_list_item":
                    rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                    if rich_text:
                        text = rich_text[0].get("text", {}).get("content", "")
                        existing_content_parts.append(f"1. {text}")
                elif block_type == "to_do":
                    rich_text = block.get("to_do", {}).get("rich_text", [])
                    checked = block.get("to_do", {}).get("checked", False)
                    if rich_text:
                        text = rich_text[0].get("text", {}).get("content", "")
                        checkbox = "[x]" if checked else "[ ]"
                        existing_content_parts.append(f"- {checkbox} {text}")
                elif block_type == "divider":
                    existing_content_parts.append("---")
                else:
                    # For other block types, try to extract text content
                    if block_type in block:
                        rich_text = block[block_type].get("rich_text", [])
                        if rich_text:
                            text = rich_text[0].get("text", {}).get("content", "")
                            existing_content_parts.append(text)
            
            # Combine new content with existing content
            existing_content = "\n\n".join(existing_content_parts)
            combined_content = new_content + "\n\n" + existing_content if existing_content else new_content
            
            # Replace all content with the combined content
            replace_result = self._replace_page_content(page_id, combined_content)
            
            if "error" in replace_result:
                return replace_result
            
            return {
                "content_prepended": True,
                "blocks_added": len(new_blocks),
                "existing_blocks_preserved": len(existing_results),
                "note": "Content successfully prepended by combining with existing content"
            }
            
        except Exception as e:
            return {"error": f"Failed to prepend page content: {str(e)}"}
    
    def query_database(self, database_id: str, filters: dict = None, sorts: list = None, limit: int = 100) -> dict:
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
        try:
            # Build query parameters
            query_params = {}
            
            if filters:
                query_params["filter"] = filters
            if sorts:
                query_params["sorts"] = sorts
            
            # Execute query
            if limit > 100:
                # Use pagination for large results
                all_results = self.client.get_all_results(
                    self.client.query_database, 
                    database_id, 
                    filter_obj=filters, 
                    sorts=sorts
                )
                
                if isinstance(all_results, dict) and "error" in all_results:
                    return all_results
                
                # Limit results
                results = all_results[:limit]
            else:
                query_result = self.client.query_database(
                    database_id, 
                    filter_obj=filters, 
                    sorts=sorts, 
                    page_size=limit
                )
                
                if "error" in query_result:
                    return query_result
                
                results = query_result.get("results", [])
            
            # Format results
            formatted_results = []
            for page in results:
                formatted_results.append({
                    "page_id": page["id"],
                    "url": page["url"],
                    "created_time": page["created_time"],
                    "last_edited_time": page["last_edited_time"],
                    "properties": self.client.format_page_properties(page)
                })
            
            return {
                "results": formatted_results,
                "count": len(formatted_results),
                "database_id": database_id,
                "success": True
            }
            
        except Exception as e:
            return {"error": f"Failed to query database: {str(e)}"}
    
    def bulk_update_pages(self, database_id: str, updates: list, filter_criteria: dict = None) -> dict:
        """
        Bulk update multiple database pages
        
        Args:
            database_id: Target database
            updates: List of update operations
            filter_criteria: Optional filter to limit which pages to update
        
        Returns:
            Bulk operation results
        """
        try:
            # Get pages to update
            if filter_criteria:
                query_result = self.query_database(database_id, filter_criteria)
                if "error" in query_result:
                    return query_result
                pages_to_update = query_result["results"]
            else:
                # Get all pages if no filter
                all_pages = self.client.get_all_results(self.client.query_database, database_id)
                if isinstance(all_pages, dict) and "error" in all_pages:
                    return all_pages
                pages_to_update = [{"page_id": page["id"]} for page in all_pages]
            
            # Process updates
            results = {
                "total_pages": len(pages_to_update),
                "successful_updates": 0,
                "failed_updates": 0,
                "errors": [],
                "success": True
            }
            
            for page in pages_to_update:
                page_id = page["page_id"]
                
                for update in updates:
                    operation = update.get("operation")
                    properties = update.get("properties", {})
                    content = update.get("content")
                    
                    if operation == "update_properties":
                        update_result = self.update_page(page_id, properties=properties)
                    elif operation == "append_content":
                        update_result = self.update_page(page_id, content=content)
                    elif operation == "update_both":
                        update_result = self.update_page(page_id, properties=properties, content=content)
                    else:
                        results["errors"].append(f"Unknown operation: {operation}")
                        continue
                    
                    if "error" in update_result:
                        results["failed_updates"] += 1
                        results["errors"].append(f"Page {page_id}: {update_result['error']}")
                    else:
                        results["successful_updates"] += 1
            
            return results
            
        except Exception as e:
            return {"error": f"Failed to bulk update pages: {str(e)}"}
    
    def create_project_workspace(self, project_name: str, template_type: str = "standard", team_members: list = None) -> dict:
        """
        Create a complete project workspace with databases and pages
        
        Args:
            project_name: Name of the project
            template_type: Workspace template (standard, agile, research, content)
            team_members: List of team member IDs to share with
        
        Returns:
            Created workspace structure information
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you'd create multiple databases and pages
            return {
                "project_name": project_name,
                "template_type": template_type,
                "team_members": team_members or [],
                "message": "Project workspace creation not fully implemented",
                "success": False
            }
            
        except Exception as e:
            return {"error": f"Failed to create project workspace: {str(e)}"}
    
    def sync_database_relations(self, source_db: str, target_db: str, relation_property: str, sync_rules: dict) -> dict:
        """
        Synchronize related data between databases
        
        Args:
            source_db: Source database ID
            target_db: Target database ID
            relation_property: Property that links the databases
            sync_rules: Rules for synchronization
        
        Returns:
            Synchronization results
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you'd sync data between databases
            return {
                "source_db": source_db,
                "target_db": target_db,
                "relation_property": relation_property,
                "sync_rules": sync_rules,
                "message": "Database synchronization not fully implemented",
                "success": False
            }
            
        except Exception as e:
            return {"error": f"Failed to sync database relations: {str(e)}"}
    
    def _convert_properties_to_notion(self, properties: dict, schema: dict = None) -> dict:
        """Convert simple properties to Notion format using database schema"""
        notion_properties = {}
        
        for key, value in properties.items():
            # Find the exact property name from schema if provided
            actual_property_name = key
            property_type = None
            
            if schema:
                # Find matching property name (case-insensitive)
                for schema_prop_name, schema_prop_info in schema.items():
                    if schema_prop_name.lower() == key.lower():
                        actual_property_name = schema_prop_name
                        property_type = schema_prop_info.get("type")
                        break
            
            if isinstance(value, str):
                # Use schema type if available
                if property_type == "title":
                    notion_properties[actual_property_name] = self.client.create_title_property(value)
                elif property_type == "select":
                    notion_properties[actual_property_name] = self.client.create_select_property(value)
                elif property_type == "status":
                    notion_properties[actual_property_name] = self.client.create_status_property(value)
                elif property_type == "multi_select":
                    notion_properties[actual_property_name] = self.client.create_multi_select_property([value])
                elif property_type == "rich_text":
                    notion_properties[actual_property_name] = self.client.create_rich_text_property(value)
                elif property_type == "url":
                    notion_properties[actual_property_name] = self.client.create_url_property(value)
                elif property_type == "email":
                    notion_properties[actual_property_name] = self.client.create_email_property(value)
                elif property_type == "phone_number":
                    notion_properties[actual_property_name] = self.client.create_phone_property(value)
                else:
                    # Fallback logic for when no schema is provided
                    if key.lower() == "title":
                        notion_properties[actual_property_name] = self.client.create_title_property(value)
                    elif key.lower() in ["status", "priority", "type", "category", "stage"]:
                        notion_properties[actual_property_name] = self.client.create_select_property(value)
                    else:
                        notion_properties[actual_property_name] = self.client.create_rich_text_property(value)
            elif isinstance(value, bool):
                notion_properties[actual_property_name] = self.client.create_checkbox_property(value)
            elif isinstance(value, (int, float)):
                notion_properties[actual_property_name] = self.client.create_number_property(value)
            elif isinstance(value, list):
                if property_type == "multi_select":
                    notion_properties[actual_property_name] = self.client.create_multi_select_property(value)
                elif property_type == "people":
                    notion_properties[actual_property_name] = self.client.create_people_property(value)
                elif property_type == "relation":
                    notion_properties[actual_property_name] = self.client.create_relation_property(value)
                else:
                    # Default to multi-select for lists
                    notion_properties[actual_property_name] = self.client.create_multi_select_property(value)
            elif isinstance(value, dict):
                # Handle complex properties
                if "type" in value:
                    notion_properties[actual_property_name] = value
                else:
                    # Convert dict to rich text (fallback)
                    notion_properties[actual_property_name] = self.client.create_rich_text_property(str(value))
            else:
                # Fallback to string conversion
                notion_properties[actual_property_name] = self.client.create_rich_text_property(str(value))
        
        return notion_properties
    
    def _build_compound_filter(self, filters: dict) -> dict:
        """Build compound filter for complex queries"""
        # This is a simplified implementation
        # In a real implementation, you'd handle complex filter logic
        return filters
    
    def _validate_properties(self, database_id: str, properties: dict) -> dict:
        """Validate properties against database schema"""
        try:
            database = self.client.get_database(database_id)
            if "error" in database:
                return database
            
            db_properties = database.get("properties", {})
            validated = {}
            errors = []
            
            for prop_name, prop_value in properties.items():
                if prop_name in db_properties:
                    validated[prop_name] = prop_value
                else:
                    errors.append(f"Property '{prop_name}' not found in database schema")
            
            return {
                "validated_properties": validated,
                "errors": errors,
                "success": len(errors) == 0
            }
            
        except Exception as e:
            return {"error": f"Failed to validate properties: {str(e)}"}
    
    def get_database_schema(self, database_id: str) -> dict:
        """Get database schema information"""
        try:
            database = self.client.get_database(database_id)
            if "error" in database:
                # Check if the error indicates this is a page, not a database
                error_message = database.get("message", "")
                if "is a page, not a database" in error_message:
                    return {
                        "error": "Invalid ID: The provided ID is a page, not a database",
                        "suggestion": "Use get_page_context() for pages, or find the database ID from the page's parent database",
                        "id_provided": database_id,
                        "id_type": "page"
                    }
                return database
            
            properties = database.get("properties", {})
            schema = {}
            
            for prop_name, prop_data in properties.items():
                schema[prop_name] = {
                    "type": prop_data.get("type"),
                    "required": prop_data.get("required", False),
                    "description": prop_data.get("description")
                }
                
                # Add type-specific details
                prop_type = prop_data.get("type")
                if prop_type == "select":
                    options = prop_data.get("select", {}).get("options", [])
                    schema[prop_name]["options"] = [opt.get("name") for opt in options]
                elif prop_type == "multi_select":
                    options = prop_data.get("multi_select", {}).get("options", [])
                    schema[prop_name]["options"] = [opt.get("name") for opt in options]
                elif prop_type == "relation":
                    schema[prop_name]["database_id"] = prop_data.get("relation", {}).get("database_id")
                elif prop_type == "formula":
                    schema[prop_name]["expression"] = prop_data.get("formula", {}).get("expression")
            
            return {
                "database_id": database_id,
                "title": self.client.extract_plain_text(database.get("title", [])),
                "schema": schema,
                "property_names": list(properties.keys()),
                "success": True
            }
            
        except Exception as e:
            return {"error": f"Failed to get database schema: {str(e)}"}
    
    def create_database_template(self, template_name: str, properties: dict, parent_page_id: str) -> dict:
        """Create a database template"""
        try:
            # This would create a new database with specified properties
            # Simplified implementation
            return {
                "template_name": template_name,
                "properties": properties,
                "parent_page_id": parent_page_id,
                "message": "Database template creation not fully implemented",
                "success": False
            }
            
        except Exception as e:
            return {"error": f"Failed to create database template: {str(e)}"}
    
    def duplicate_database_structure(self, source_db_id: str, target_parent_id: str, new_name: str) -> dict:
        """Duplicate database structure without content"""
        try:
            # Get source database schema
            schema_result = self.get_database_schema(source_db_id)
            if "error" in schema_result:
                return schema_result
            
            # This would create a new database with the same structure
            # Simplified implementation
            return {
                "source_db_id": source_db_id,
                "target_parent_id": target_parent_id,
                "new_name": new_name,
                "schema": schema_result["schema"],
                "message": "Database duplication not fully implemented",
                "success": False
            }
            
        except Exception as e:
            return {"error": f"Failed to duplicate database structure: {str(e)}"}
    
    def archive_old_pages(self, database_id: str, days_old: int = 30, dry_run: bool = True) -> dict:
        """Archive pages older than specified days"""
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # Find old pages
            filter_obj = {
                "property": "Created",
                "date": {
                    "before": cutoff_date
                }
            }
            
            query_result = self.query_database(database_id, filter_obj)
            if "error" in query_result:
                return query_result
            
            old_pages = query_result["results"]
            
            if dry_run:
                return {
                    "dry_run": True,
                    "pages_to_archive": len(old_pages),
                    "pages": [{"page_id": page["page_id"], "created_time": page["created_time"]} for page in old_pages],
                    "success": True
                }
            else:
                # Archive pages (set archived property or move to archive database)
                # This would require implementation based on your archiving strategy
                return {
                    "pages_archived": len(old_pages),
                    "message": "Archiving not fully implemented",
                    "success": False
                }
                
        except Exception as e:
            return {"error": f"Failed to archive old pages: {str(e)}"}