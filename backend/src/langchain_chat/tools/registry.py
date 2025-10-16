from langchain_core.tools import BaseTool
from typing import List, Dict, Optional
import importlib
import inspect
import pkgutil
import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Auto-discovering tool registry that scales to hundreds of tools.
    
    Uses ChromaDB for semantic search to avoid context overloading:
    - Semantic search to find relevant tools
    - Category-based filtering
    - Manual tool selection
    
    This prevents performance degradation when you have 100+ tools.
    """
    
    def __init__(self, use_chromadb: bool = True):
        self._tools: Dict[str, BaseTool] = {}
        self._use_chromadb = use_chromadb
        self._chroma_client = None
        self._tool_collection = None
        self._discover_tools()
    
    def _discover_tools(self):
        """Auto-discover all tools from subdirectories."""
        import langchain_chat.tools as tools_package
        
        # Get the tools package path
        package_path = tools_package.__path__
        
        # Walk through all modules in tools package
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=package_path,
            prefix='langchain_chat.tools.'
        ):
            # Skip registry and base modules
            if modname.endswith(('registry', 'base', '__init__')):
                continue
            
            try:
                module = importlib.import_module(modname)
                
                # Find all tool instances in the module
                for name, obj in inspect.getmembers(module):
                    if isinstance(obj, BaseTool):
                        self._tools[obj.name] = obj
                        logger.info(f"Registered tool: {obj.name}")
            
            except Exception as e:
                logger.warning(f"Failed to load tool module {modname}: {e}")
        
        # Initialize semantic search after tools are loaded
        if self._use_chromadb and self._tools:
            self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB for semantic tool search."""
        if not self._tools:
            return
        
        try:
            # Initialize ChromaDB client (in-memory for simplicity)
            self._chroma_client = chromadb.Client(Settings(
                anonymized_telemetry=False,
                allow_reset=True
            ))
            
            # Create or get collection for tools
            try:
                self._tool_collection = self._chroma_client.get_collection("tool_registry")
                logger.info("Using existing tool registry collection")
            except:
                self._tool_collection = self._chroma_client.create_collection(
                    name="tool_registry",
                    metadata={"description": "Tool descriptions for semantic search"}
                )
                logger.info("Created new tool registry collection")
            
            # Index all tools
            tool_ids = []
            tool_documents = []
            tool_metadatas = []
            
            for tool in self._tools.values():
                tool_ids.append(tool.name)
                # Combine name and description for better semantic search
                tool_documents.append(f"{tool.name}: {tool.description}")
                tool_metadatas.append({
                    "name": tool.name,
                    "category": self._get_category(tool)
                })
            
            # Add to ChromaDB (upsert to handle re-initialization)
            self._tool_collection.upsert(
                ids=tool_ids,
                documents=tool_documents,
                metadatas=tool_metadatas
            )
            
            logger.info(f"Indexed {len(tool_ids)} tools in ChromaDB")
        
        except Exception as e:
            logger.warning(f"Failed to initialize ChromaDB: {e}. Falling back to keyword search.")
            self._use_chromadb = False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a single tool by name."""
        return self._tools.get(name)
    
    def get_tools(self, tool_names: Optional[List[str]] = None) -> List[BaseTool]:
        """Get all or specific tools."""
        if tool_names:
            return [self._tools[name] for name in tool_names if name in self._tools]
        return list(self._tools.values())
    
    def get_relevant_tools(
        self, 
        query: str, 
        max_tools: int = 10,
        categories: Optional[List[str]] = None
    ) -> List[BaseTool]:
        """
        Get most relevant tools for a query using ChromaDB semantic search.
        
        This is CRITICAL for performance with 100+ tools.
        Instead of passing all tools to the agent, only pass relevant ones.
        
        Args:
            query: User's question/request
            max_tools: Maximum number of tools to return (default: 10)
            categories: Optional list of categories to filter by
        
        Returns:
            List of most relevant tools
        
        Example:
            >>> registry.get_relevant_tools("What's the weather in London?", max_tools=5)
            [get_weather, get_location, ...]
        """
        if not self._use_chromadb or not self._tool_collection:
            # Fallback: return all tools (or by category)
            if categories:
                return self.get_tools_by_category(categories)
            return list(self._tools.values())[:max_tools]
        
        try:
            # Build where filter for categories if specified
            where_filter = None
            if categories:
                where_filter = {"category": {"$in": categories}}
            
            # Query ChromaDB for similar tools
            results = self._tool_collection.query(
                query_texts=[query],
                n_results=min(max_tools, len(self._tools)),
                where=where_filter
            )
            
            # Extract tool names from results
            tool_names = results['ids'][0] if results['ids'] else []
            
            # Get actual tool objects
            relevant_tools = [
                self._tools[name] for name in tool_names 
                if name in self._tools
            ]
            
            logger.info(f"ChromaDB selected {len(relevant_tools)} relevant tools for query")
            return relevant_tools
        
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            # Fallback to keyword search
            return self.search_tools(query)[:max_tools]
    
    def get_tools_by_category(self, categories: List[str]) -> List[BaseTool]:
        """Get all tools in specified categories."""
        return [
            tool for tool in self._tools.values()
            if self._get_category(tool) in categories
        ]
    
    def list_tools(self) -> List[Dict[str, str]]:
        """List all available tools with metadata."""
        return [
            {
                'name': tool.name,
                'description': tool.description,
                'category': self._get_category(tool)
            }
            for tool in self._tools.values()
        ]
    
    def _get_category(self, tool: BaseTool) -> str:
        """Extract category from tool module path."""
        module = tool.__class__.__module__
        parts = module.split('.')
        if len(parts) > 3:
            return parts[2]  # e.g., 'math' from 'langchain_chat.tools.math.calculator'
        return 'general'
    
    def search_tools(self, query: str) -> List[BaseTool]:
        """Search tools by name or description (keyword-based)."""
        query_lower = query.lower()
        return [
            tool for tool in self._tools.values()
            if query_lower in tool.name.lower() or query_lower in tool.description.lower()
        ]

# Global registry instance
_registry = None

def get_registry() -> ToolRegistry:
    """Get the global tool registry (singleton)."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

def get_tools(tool_names: Optional[List[str]] = None) -> List[BaseTool]:
    """Convenience function to get tools."""
    return get_registry().get_tools(tool_names)
