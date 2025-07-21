"""
Context Aggregator - Helpdesk and knowledge base functionality
Aggregates context from pages, databases, and blocks for comprehensive Q&A
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class ContextAggregator:
    """Aggregates context from Notion workspace for helpdesk and knowledge queries"""
    
    def __init__(self, notion_client):
        self.client = notion_client
        self.context_cache = {}
        self.cache_ttl = 300  # 5 minutes cache
    
    def get_comprehensive_page_context(self, page_id: str, include_children: bool = True, max_depth: int = 2) -> dict:
        """
        Get comprehensive context for a page including all related content
        
        Args:
            page_id: Notion page ID
            include_children: Whether to include child pages and blocks
            max_depth: Maximum depth to traverse for nested content
        
        Returns:
            Complete context including page content, children, and metadata
        """
        try:
            # Get main page data
            page = self.client.get_page(page_id)
            if "error" in page:
                return page
            
            context = {
                "page": {
                    "id": page_id,
                    "title": self._extract_page_title(page),
                    "url": page.get("url"),
                    "created_time": page.get("created_time"),
                    "last_edited_time": page.get("last_edited_time"),
                    "properties": self.client.format_page_properties(page),
                    "parent": page.get("parent", {})
                },
                "content": [],
                "children": [],
                "related_databases": [],
                "backlinks": [],
                "context_summary": ""
            }
            
            # Get page content (blocks)
            if include_children:
                content_blocks = self._get_page_content_recursive(page_id, max_depth)
                context["content"] = content_blocks
                
                # Extract child pages and databases
                children = self._extract_child_pages_and_databases(content_blocks)
                context["children"] = children
                
                # Find related databases
                related_dbs = self._find_related_databases(page_id, content_blocks)
                context["related_databases"] = related_dbs
                
                # Find backlinks (pages that reference this page)
                backlinks = self._find_backlinks(page_id)
                context["backlinks"] = backlinks
            
            # Generate context summary
            context["context_summary"] = self._generate_context_summary(context)
            
            return context
            
        except Exception as e:
            return {"error": f"Failed to get page context: {str(e)}"}
    
    def search_and_aggregate_context(self, query: str, context_type: str = "all") -> dict:
        """
        Search workspace and aggregate context for comprehensive results
        
        Args:
            query: Search query string
            context_type: Type of context ('pages', 'databases', 'all')
        
        Returns:
            Aggregated search results with enhanced context
        """
        try:
            # Perform initial search
            search_filter = None
            if context_type == "pages":
                search_filter = {"property": "object", "value": "page"}
            elif context_type == "databases":
                search_filter = {"property": "object", "value": "database"}
            
            search_results = self.client.search(query=query, filter_obj=search_filter, page_size=50)
            
            if "error" in search_results:
                return search_results
            
            aggregated_context = {
                "query": query,
                "context_type": context_type,
                "total_results": len(search_results.get("results", [])),
                "results": [],
                "context_summary": "",
                "related_content": [],
                "knowledge_gaps": []
            }
            
            # Process each search result
            for result in search_results.get("results", []):
                if result.get("object") == "page":
                    page_context = self._get_lightweight_page_context(result["id"])
                    aggregated_context["results"].append({
                        "type": "page",
                        "id": result["id"],
                        "title": self._extract_page_title(result),
                        "url": result.get("url"),
                        "relevance_score": self._calculate_relevance_score(query, page_context),
                        "context": page_context,
                        "last_edited": result.get("last_edited_time")
                    })
                elif result.get("object") == "database":
                    db_context = self._get_database_context_summary(result["id"])
                    aggregated_context["results"].append({
                        "type": "database", 
                        "id": result["id"],
                        "title": self._extract_database_title(result),
                        "url": result.get("url"),
                        "context": db_context,
                        "last_edited": result.get("last_edited_time")
                    })
            
            # Sort by relevance
            aggregated_context["results"].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # Find related content
            aggregated_context["related_content"] = self._find_related_content(query, aggregated_context["results"])
            
            # Generate overall context summary
            aggregated_context["context_summary"] = self._generate_search_context_summary(aggregated_context)
            
            return aggregated_context
            
        except Exception as e:
            return {"error": f"Failed to aggregate search context: {str(e)}"}
    
    def get_database_insights(self, database_id: str, include_recent_updates: bool = True) -> dict:
        """
        Get comprehensive database insights including structure and activity
        
        Args:
            database_id: Notion database ID
            include_recent_updates: Include recently updated pages
        
        Returns:
            Database insights with schema, statistics, and activity
        """
        try:
            # Get database schema
            database = self.client.get_database(database_id)
            if "error" in database:
                return database
            
            insights = {
                "database": {
                    "id": database_id,
                    "title": self._extract_database_title(database),
                    "url": database.get("url"),
                    "created_time": database.get("created_time"),
                    "last_edited_time": database.get("last_edited_time")
                },
                "schema": self._analyze_database_schema(database),
                "statistics": {},
                "recent_activity": [],
                "usage_patterns": {},
                "insights_summary": ""
            }
            
            # Get database statistics
            all_pages = self.client.get_all_results(self.client.query_database, database_id)
            if not isinstance(all_pages, list):
                all_pages = []
            
            insights["statistics"] = self._calculate_database_statistics(all_pages, insights["schema"])
            
            # Get recent activity if requested
            if include_recent_updates:
                recent_filter = {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "after": (datetime.now() - timedelta(days=7)).isoformat()
                    }
                }
                recent_pages = self.client.query_database(database_id, filter_obj=recent_filter, page_size=20)
                insights["recent_activity"] = self._format_recent_activity(recent_pages.get("results", []))
            
            # Analyze usage patterns
            insights["usage_patterns"] = self._analyze_usage_patterns(all_pages)
            
            # Generate insights summary
            insights["insights_summary"] = self._generate_database_insights_summary(insights)
            
            return insights
            
        except Exception as e:
            return {"error": f"Failed to get database insights: {str(e)}"}
    
    # --- Helper Methods ---
    
    def _get_page_content_recursive(self, page_id: str, max_depth: int, current_depth: int = 0) -> list:
        """Recursively get page content blocks"""
        if current_depth >= max_depth:
            return []
        
        blocks = self.client.get_all_results(self.client.get_block_children, page_id)
        if not isinstance(blocks, list):
            return []
        
        processed_blocks = []
        for block in blocks:
            processed_block = self._process_block(block)
            
            # Recursively get children if block has them
            if block.get("has_children") and current_depth < max_depth - 1:
                children = self._get_page_content_recursive(block["id"], max_depth, current_depth + 1)
                processed_block["children"] = children
            
            processed_blocks.append(processed_block)
        
        return processed_blocks
    
    def _process_block(self, block: dict) -> dict:
        """Process and extract content from a block"""
        block_type = block.get("type", "unsupported")
        
        processed = {
            "id": block.get("id"),
            "type": block_type,
            "has_children": block.get("has_children", False),
            "content": "",
            "metadata": {}
        }
        
        # Extract content based on block type
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "quote", "callout"]:
            rich_text = block.get(block_type, {}).get("rich_text", [])
            processed["content"] = self.client.extract_plain_text(rich_text)
        elif block_type == "bulleted_list_item" or block_type == "numbered_list_item":
            rich_text = block.get(block_type, {}).get("rich_text", [])
            processed["content"] = self.client.extract_plain_text(rich_text)
        elif block_type == "to_do":
            rich_text = block.get(block_type, {}).get("rich_text", [])
            checked = block.get(block_type, {}).get("checked", False)
            processed["content"] = self.client.extract_plain_text(rich_text)
            processed["metadata"]["checked"] = checked
        elif block_type == "code":
            code_block = block.get(block_type, {})
            processed["content"] = self.client.extract_plain_text(code_block.get("rich_text", []))
            processed["metadata"]["language"] = code_block.get("language")
        elif block_type == "child_database":
            processed["metadata"]["database_id"] = block.get("id")
            processed["content"] = f"Child database: {block.get('child_database', {}).get('title', 'Untitled')}"
        elif block_type == "child_page":
            processed["content"] = f"Child page: {block.get('child_page', {}).get('title', 'Untitled')}"
        
        return processed
    
    def _extract_child_pages_and_databases(self, content_blocks: list) -> list:
        """Extract child pages and databases from content blocks"""
        children = []
        
        def extract_from_blocks(blocks):
            for block in blocks:
                if block["type"] == "child_page":
                    children.append({
                        "type": "page",
                        "id": block["id"],
                        "title": block["content"].replace("Child page: ", "")
                    })
                elif block["type"] == "child_database":
                    children.append({
                        "type": "database", 
                        "id": block["id"],
                        "title": block["content"].replace("Child database: ", "")
                    })
                
                # Process nested children
                if "children" in block:
                    extract_from_blocks(block["children"])
        
        extract_from_blocks(content_blocks)
        return children
    
    def _find_related_databases(self, page_id: str, content_blocks: list) -> list:
        """Find databases related to the page"""
        related_dbs = []
        
        # Find databases mentioned in content
        for block in content_blocks:
            if block["type"] == "child_database":
                db_id = block["metadata"].get("database_id")
                if db_id:
                    db_info = self.client.get_database(db_id)
                    if "error" not in db_info:
                        related_dbs.append({
                            "id": db_id,
                            "title": self._extract_database_title(db_info),
                            "relationship": "child_database"
                        })
        
        return related_dbs
    
    def _find_backlinks(self, page_id: str) -> list:
        """Find pages that link to this page"""
        # This would require a more sophisticated approach in a real implementation
        # For now, return empty list as Notion API doesn't directly support backlink search
        return []
    
    def _generate_context_summary(self, context: dict) -> str:
        """Generate a summary of the page context"""
        page = context["page"]
        content_blocks = len(context["content"])
        children_count = len(context["children"])
        
        summary = f"Page '{page['title']}' contains {content_blocks} content blocks"
        
        if children_count > 0:
            summary += f" and {children_count} child pages/databases"
        
        if context["related_databases"]:
            summary += f", with {len(context['related_databases'])} related databases"
        
        return summary
    
    def _extract_page_title(self, page: dict) -> str:
        """Extract title from page object"""
        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                return self.client.extract_plain_text(prop_data.get("title", []))
        return "Untitled"
    
    def _extract_database_title(self, database: dict) -> str:
        """Extract title from database object"""
        title = database.get("title", [])
        return self.client.extract_plain_text(title)
    
    def _get_lightweight_page_context(self, page_id: str) -> dict:
        """Get lightweight context for search results"""
        page = self.client.get_page(page_id)
        if "error" in page:
            return {}
        
        # Get first few blocks for preview
        blocks = self.client.get_block_children(page_id, page_size=5)
        content_preview = ""
        
        for block in blocks.get("results", []):
            processed = self._process_block(block)
            if processed["content"]:
                content_preview += processed["content"][:200] + " "
                if len(content_preview) > 300:
                    break
        
        return {
            "properties": self.client.format_page_properties(page),
            "content_preview": content_preview.strip()[:300],
            "has_children": any(block.get("has_children") for block in blocks.get("results", []))
        }
    
    def _calculate_relevance_score(self, query: str, context: dict) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = query.lower()
        
        # Check title relevance
        if "properties" in context:
            for prop_value in context["properties"].values():
                if isinstance(prop_value, str) and query_lower in prop_value.lower():
                    score += 2.0
        
        # Check content relevance
        if "content_preview" in context:
            content_lower = context["content_preview"].lower()
            query_words = query_lower.split()
            for word in query_words:
                if word in content_lower:
                    score += 1.0
        
        return min(score, 10.0)  # Cap at 10.0
    
    def _get_database_context_summary(self, database_id: str) -> dict:
        """Get database context summary"""
        try:
            database = self.client.get_database(database_id)
            if "error" in database:
                return {}
            
            # Get sample pages for context
            pages = self.client.query_database(database_id, page_size=5)
            page_count = len(pages.get("results", []))
            
            return {
                "properties": database.get("properties", {}),
                "page_count": page_count,
                "description": database.get("description", [])
            }
        except:
            return {}
    
    def _find_related_content(self, query: str, results: list) -> list:
        """Find related content from search results"""
        # Simple implementation - return pages that share similar titles or content
        related = []
        query_words = set(query.lower().split())
        
        for result in results:
            title_words = set(result["title"].lower().split())
            if query_words.intersection(title_words):
                related.append({
                    "id": result["id"],
                    "title": result["title"],
                    "type": result["type"]
                })
        
        return related[:5]  # Limit to 5 related items
    
    def _generate_search_context_summary(self, aggregated_context: dict) -> str:
        """Generate summary for search context"""
        total = aggregated_context["total_results"]
        query = aggregated_context["query"]
        
        if total == 0:
            return f"No results found for query '{query}'"
        
        page_count = sum(1 for r in aggregated_context["results"] if r["type"] == "page")
        db_count = sum(1 for r in aggregated_context["results"] if r["type"] == "database")
        
        summary = f"Found {total} results for '{query}'"
        if page_count > 0:
            summary += f" ({page_count} pages"
        if db_count > 0:
            summary += f", {db_count} databases)"
        elif page_count > 0:
            summary += ")"
        
        return summary
    
    def _analyze_database_schema(self, database: dict) -> dict:
        """Analyze database schema"""
        properties = database.get("properties", {})
        schema = {
            "property_count": len(properties),
            "property_types": {},
            "required_properties": [],
            "relation_properties": []
        }
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            schema["property_types"][prop_type] = schema["property_types"].get(prop_type, 0) + 1
            
            if prop_data.get("required"):
                schema["required_properties"].append(prop_name)
            
            if prop_type == "relation":
                schema["relation_properties"].append({
                    "name": prop_name,
                    "database_id": prop_data.get("relation", {}).get("database_id")
                })
        
        return schema
    
    def _calculate_database_statistics(self, pages: list, schema: dict) -> dict:
        """Calculate database statistics"""
        return {
            "total_pages": len(pages),
            "properties_analyzed": schema["property_count"],
            "creation_rate": "Not implemented",
            "update_frequency": "Not implemented"
        }
    
    def _format_recent_activity(self, pages: list) -> list:
        """Format recent activity"""
        activity = []
        for page in pages:
            activity.append({
                "page_id": page["id"],
                "title": self._extract_page_title(page),
                "last_edited": page.get("last_edited_time"),
                "url": page.get("url")
            })
        return activity
    
    def _analyze_usage_patterns(self, pages: list) -> dict:
        """Analyze usage patterns"""
        return {
            "total_pages": len(pages),
            "patterns": "Analysis not implemented"
        }
    
    def _generate_database_insights_summary(self, insights: dict) -> str:
        """Generate database insights summary"""
        db_title = insights["database"]["title"]
        stats = insights["statistics"]
        
        return f"Database '{db_title}' contains {stats['total_pages']} pages with {stats['properties_analyzed']} properties"
    
