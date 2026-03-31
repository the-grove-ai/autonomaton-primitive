"""
effectors.py - MCP Effector Layer

External actions are handled via Model Context Protocol (MCP) servers.
Every MCP action is strictly governed by Zone classification.

CRITICAL: The most restrictive zone always wins.

Architecture:
  - ConfigLoader reads mcp.config for zone-per-capability declarations
  - compute_effective_zone() applies most-restrictive-wins rule
  - Pipeline Stage 4 enforces approval before execution reaches here
  - MCPClient is the adapter interface — stub by default, real adapters plug in

To connect a real service, implement a handler in MCPClient.execute()
and register it in the service registry. See mcp.config for governance
declarations.
"""

import yaml
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass

from engine.telemetry import log_event
from engine.profile import get_config_dir


# Zone priority (higher = more restrictive)
ZONE_PRIORITY = {
    "green": 1,
    "yellow": 2,
    "red": 3
}


@dataclass
class MCPActionResult:
    """Result of an MCP action execution."""
    success: bool
    server: str
    capability: str
    payload: dict
    effective_zone: str
    approved: bool
    result: Any = None
    error: Optional[str] = None


class ConfigLoader:
    """
    Loads and caches configuration from YAML files.
    """
    _mcp_config: Optional[dict] = None
    _zones_schema: Optional[dict] = None
    _config_dir: Optional[Path] = None

    @classmethod
    def _get_config_dir(cls) -> Path:
        """Get the config directory for the active profile."""
        if cls._config_dir is None:
            cls._config_dir = get_config_dir()
        return cls._config_dir

    @classmethod
    def load_mcp_config(cls) -> dict:
        """Load MCP server configuration."""
        if cls._mcp_config is None:
            mcp_path = cls._get_config_dir() / "mcp.config"
            if mcp_path.exists():
                with open(mcp_path, "r", encoding="utf-8") as f:
                    cls._mcp_config = yaml.safe_load(f) or {}
            else:
                cls._mcp_config = {}
        return cls._mcp_config

    @classmethod
    def load_zones_schema(cls) -> dict:
        """Load zone governance schema."""
        if cls._zones_schema is None:
            zones_path = cls._get_config_dir() / "zones.schema"
            if zones_path.exists():
                with open(zones_path, "r", encoding="utf-8") as f:
                    cls._zones_schema = yaml.safe_load(f) or {}
            else:
                cls._zones_schema = {}
        return cls._zones_schema

    @classmethod
    def get_server_config(cls, server: str) -> Optional[dict]:
        """Get configuration for a specific MCP server."""
        config = cls.load_mcp_config()
        return config.get("servers", {}).get(server)

    @classmethod
    def get_domain_config(cls, domain: str) -> Optional[dict]:
        """Get configuration for a specific domain."""
        schema = cls.load_zones_schema()
        return schema.get("domains", {}).get(domain)

    @classmethod
    def get_capability_zone(cls, server: str, capability: str) -> str:
        """Get the zone for a specific server capability."""
        server_config = cls.get_server_config(server)
        if not server_config:
            return "red"  # Unknown server = most restrictive

        # Check capability-specific zone first
        governance = server_config.get("governance", {})
        cap_governance = governance.get(capability, {})
        if "zone" in cap_governance:
            return cap_governance["zone"]

        # Fall back to server default zone
        return server_config.get("zone", "yellow")

    @classmethod
    def get_domain_zone(cls, domain: str) -> str:
        """Get the default zone for a domain."""
        domain_config = cls.get_domain_config(domain)
        if not domain_config:
            return "yellow"  # Unknown domain = cautious default
        return domain_config.get("default_zone", "yellow")

    @classmethod
    def get_server_scopes(cls, server: str) -> list:
        """Load OAuth scopes for a server from mcp.config."""
        if cls._mcp_config is None:
            cls.load_mcp_config()
        if cls._mcp_config is None:
            return []
        servers = cls._mcp_config.get("servers", {})
        server_config = servers.get(server, {})
        return server_config.get("auth", {}).get("scopes", [])

    @classmethod
    def get_configured_servers(cls) -> list:
        """Return list of server names from mcp.config."""
        if cls._mcp_config is None:
            cls.load_mcp_config()
        if cls._mcp_config is None:
            return []
        return list(cls._mcp_config.get("servers", {}).keys())

    @classmethod
    def get_server_status(cls, server: str) -> str:
        """Return server status from mcp.config (active/stub/not_implemented)."""
        if cls._mcp_config is None:
            cls.load_mcp_config()
        if cls._mcp_config is None:
            return "unknown"
        servers = cls._mcp_config.get("servers", {})
        return servers.get(server, {}).get("status", "unknown")

    @classmethod
    def reset_cache(cls) -> None:
        """Reset configuration cache (useful when switching profiles)."""
        cls._mcp_config = None
        cls._zones_schema = None
        cls._config_dir = None


# =========================================================================
# Zone Computation
# =========================================================================

def compute_effective_zone(server_zone: str, domain_zone: str) -> str:
    """
    Compute the effective zone by taking the most restrictive.

    Zone priority: red > yellow > green
    """
    server_priority = ZONE_PRIORITY.get(server_zone, 3)
    domain_priority = ZONE_PRIORITY.get(domain_zone, 3)

    # Most restrictive wins
    if server_priority >= domain_priority:
        return server_zone
    return domain_zone


def format_action_description(server: str, capability: str, payload: dict) -> str:
    """
    Format a human-readable action description for Jidoka prompts.
    Uses templates from mcp.config if available.
    """
    server_config = ConfigLoader.get_server_config(server)
    if not server_config:
        return f"Execute {capability} on {server}"

    governance = server_config.get("governance", {})
    cap_governance = governance.get(capability, {})
    template = cap_governance.get("template")

    if template:
        try:
            return template.format(**payload)
        except KeyError:
            pass

    # Fallback to generic description
    server_name = server_config.get("name", server)
    return f"{capability} via {server_name}: {payload}"


# =========================================================================
# MCP Client — Stub Adapter
# =========================================================================

@dataclass
class AuthState:
    """Tracks authentication state for an MCP server."""
    authenticated: bool = False
    auth_url: Optional[str] = None
    requires_user_action: bool = False
    error: Optional[str] = None


class MCPClient:
    """
    MCP client adapter.

    Stub implementation — accepts any server/capability and returns
    structured results. Real adapters (Google Calendar, Gmail, etc.)
    plug into the service registry in execute().

    The governance layer (zone computation, approval gates) lives in
    pipeline Stage 4. This layer handles connection and execution only.
    """

    def __init__(self, server: str):
        self.server = server
        self.config = ConfigLoader.get_server_config(server)
        self.connected = False
        self.auth_state = AuthState()

    def connect(self) -> bool:
        """Connect to the MCP server. Stub: always succeeds if configured."""
        if not self.config:
            return False
        self.connected = True
        self.auth_state = AuthState(authenticated=True)
        return True

    def execute(self, capability: str, payload: dict) -> dict:
        """
        Execute a capability on the MCP server.

        Returns a structured result dict. The stub adapter returns
        success with a marker indicating no real execution occurred.
        Real adapters register in the service registry below.
        """
        if not self.connected:
            return {
                "success": False,
                "error": "Not connected to MCP server"
            }

        # Verify capability is supported
        capabilities = self.config.get("capabilities", [])
        if capability not in capabilities:
            return {
                "success": False,
                "error": f"Capability '{capability}' not supported by {self.server}"
            }

        # Stub: return structured result showing what would execute.
        # To add a real adapter, register a handler method here:
        #
        #   _service_registry = {
        #       "my_service": self._execute_my_service,
        #   }
        #   handler = _service_registry.get(self.server)
        #   if handler:
        #       return handler(capability, payload)

        return {
            "success": True,
            "stub": True,
            "server": self.server,
            "capability": capability,
            "payload": payload,
            "message": f"MCP stub — see mcp.config for governance declarations"
        }

    def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        self.connected = False
        self.auth_state = AuthState()


# Client connection pool
_client_pool: dict[str, MCPClient] = {}


def get_mcp_client(server: str) -> MCPClient:
    """Get or create an MCP client for the given server."""
    if server not in _client_pool:
        _client_pool[server] = MCPClient(server)
    return _client_pool[server]


def execute_mcp_action(
    server: str,
    capability: str,
    payload: dict,
    domain: str
) -> MCPActionResult:
    """
    Execute an MCP action (post-approval).

    Zone governance is handled by pipeline Stage 4 before this is called.
    This function handles:
    1. Connection to the MCP server
    2. Capability execution
    3. Execution telemetry

    Args:
        server: MCP server name (from mcp.config)
        capability: The capability to invoke
        payload: Data to pass to the capability
        domain: The domain context (for telemetry)

    Returns:
        MCPActionResult with execution outcome
    """
    # Compute effective zone for telemetry (NOT for governance)
    server_zone = ConfigLoader.get_capability_zone(server, capability)
    domain_zone = ConfigLoader.get_domain_zone(domain)
    effective_zone = compute_effective_zone(server_zone, domain_zone)

    # Log the execution attempt
    log_event(
        source="effector_execution_start",
        raw_transcript=f"MCP action: {server}.{capability}",
        zone_context=effective_zone,
        inferred={
            "server": server,
            "capability": capability,
            "domain": domain,
            "effective_zone": effective_zone
        }
    )

    # Step 1: Connect to MCP server
    client = get_mcp_client(server)
    if not client.connected:
        if not client.connect():
            log_event(
                source="effector_error",
                raw_transcript=f"Failed to connect to MCP server: {server}",
                zone_context=effective_zone,
                inferred={"server": server, "error": "connection_failed"}
            )
            return MCPActionResult(
                success=False,
                server=server,
                capability=capability,
                payload=payload,
                effective_zone=effective_zone,
                approved=True,
                error=f"Failed to connect to {server}"
            )

    # Step 2: Execute the action
    try:
        execution_result = client.execute(capability, payload)
    except Exception as e:
        log_event(
            source="effector_error",
            raw_transcript=f"MCP execution failed: {server}.{capability}",
            zone_context=effective_zone,
            inferred={
                "server": server,
                "capability": capability,
                "error": str(e)
            }
        )
        return MCPActionResult(
            success=False,
            server=server,
            capability=capability,
            payload=payload,
            effective_zone=effective_zone,
            approved=True,
            error=str(e)
        )

    # Step 3: Log execution outcome
    log_event(
        source="effector_execution",
        raw_transcript=f"Executed MCP action: {server}.{capability}",
        zone_context=effective_zone,
        inferred={
            "server": server,
            "capability": capability,
            "domain": domain,
            "success": execution_result.get("success", False),
            "stub": execution_result.get("stub", False)
        }
    )

    return MCPActionResult(
        success=execution_result.get("success", False),
        server=server,
        capability=capability,
        payload=payload,
        effective_zone=effective_zone,
        approved=True,
        result=execution_result,
        error=execution_result.get("error")
    )


def list_available_servers() -> list[str]:
    """List all configured MCP servers."""
    config = ConfigLoader.load_mcp_config()
    return list(config.get("servers", {}).keys())


def list_server_capabilities(server: str) -> list[str]:
    """List capabilities for a specific MCP server."""
    server_config = ConfigLoader.get_server_config(server)
    if not server_config:
        return []
    return server_config.get("capabilities", [])
