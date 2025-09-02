import sys
import logging
import socket
from mcp.server.fastmcp import FastMCP
from mcp_server.utils.logging import setup_logging
from mcp_server.settings import AppSettings
from mcp_server.tools import register_tools
from mcp_server.prompts import register_prompts
from mcp_server.resources import register_resources


class McpServer:
    def __init__(self, config: AppSettings):
        self.logger = logging.getLogger(__name__)

        self.db_config = config.db
        self.logger.info(f"KDBAIConfig: {self.db_config=}")

        self.mcp_config = config.mcp
        self.logger.info(f"ServerConfig: {self.mcp_config=}")

        # Initialize server
        self.mcp = FastMCP(
            self.mcp_config.server_name,
            port=self.mcp_config.port,
            host=self.mcp_config.host
        )

        self._check_port_availability()
        self._check_kdbai_connection()
        self._register_tools()
        self._register_prompts()
        self._register_resources()

    def _check_port_availability(self):
        """Check if the configured mcp-port is available for HTTP transports."""
        if self.mcp_config.transport in ["streamable-http"]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind((self.mcp_config.host, self.mcp_config.port))
                self.logger.info(
                    f"KDB.AI MCP port availability check: SUCCESS - {self.mcp_config.host}:{self.mcp_config.port} is available"
                )
            except OSError:
                self.logger.error(f"KDB.AI MCP port {self.mcp_config.port} is already in use on {self.mcp_config.host}")
                self.logger.error("Solutions:")
                self.logger.error(f"  - Try a different port: --mcp.port {self.mcp_config.port + 1}")
                self.logger.error(f"  - Stop the service using port {self.mcp_config.port}")
                sys.exit(1)

    def _check_kdbai_connection(self):
        """Check if KDB.AI service is reachable and accessible."""
        try:
            import kdbai_client as kdbai
            from kdbai_client import KDBAIException

            conn_options = {"username":"user", "password":self.db_config.password.get_secret_value()}

            protocol = "http"
            if self.db_config.mode == "rest":
                protocol = self.db_config.rest_protocol
            else: # qipc mode
                if self.db_config.qipc_tls:
                    conn_options["tls"] = True

            endpoint = f"{protocol}://{self.db_config.host}:{self.db_config.port}"
            client = kdbai.Session(endpoint=endpoint, mode=self.db_config.mode, options=conn_options)

            self.logger.info(
                f"KDB.AI connectivity check: SUCCESS - {self.db_config.mode} {endpoint} is accessible"
            )

            client.close()

        except KDBAIException as e:
            self.logger.error(
                f"KDB.AI connectivity check: FAILED - {endpoint} ({e})"
            )
            if self.db_config.mode == 'qipc' and self.db_config.qipc_tls:
                self.logger.error("You are attempting to connect using QIPC with TLS enabled. Ensure you have set the environment variable `KX_SSL_CA_CERT_FILE` that CA certificate on your local filesystem that your TLS proxy is using. For local development and testing you can set `KX_SSL_VERIFY_SERVER=NO`")
            if "authentication error" in str(e).lower():
                self.logger.error("Authentication is enabled on KDB.AI server - you need to set a valid KDBAI_PASSWORD environment variable")
            if "failed to open a session" in str(e).lower():
                self.logger.error(f"Check your KDB.AI Server is running and accepting '{self.db_config.mode}' connections on port '{self.db_config.port}'")
            self.logger.error(
                "KDB.AI MCP server cannot function without connection to a KDB.AI database. Exiting..."
            )
            sys.exit(1)

    def _register_tools(self):
        try:
            registered_tools = register_tools(self.mcp)
            self.logger.info(f"Successfully registered {len(registered_tools)} tools")

            for tool_name in registered_tools:
                self.logger.debug(f"Registered tool: {tool_name}")

        except Exception as e:
            self.logger.error(f"Failed to register tools: {e}")
            raise

    def _register_prompts(self):
        try:
            registered_prompts = register_prompts(self.mcp)
            self.logger.info(f"Successfully registered {len(registered_prompts)} prompts")

            for prompt_name in registered_prompts:
                self.logger.debug(f"Registered prompt: {prompt_name}")

        except Exception as e:
            self.logger.error(f"Failed to register prompts: {e}")
            raise

    def _register_resources(self):
        try:
            registered_resources = register_resources(self.mcp)
            self.logger.info(
                f"Successfully registered {len(registered_resources)} resources"
            )

            for resource_name in registered_resources:
                self.logger.debug(f"Registered resource: {resource_name}")

        except Exception as e:
            self.logger.error(f"Failed to register resources: {e}")
            raise

    def run(self):
        """Start the MCP server."""
        try:
            self.logger.info(f"Starting {self.mcp_config.server_name} MCP Server with {self.mcp_config.transport} transport")
            self.mcp.run(transport=self.mcp_config.transport)
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self.logger.info("Server stopped")


app_settings = AppSettings()

def main():
    """Main entry point for the KDB.AI MCP Server."""

    # Setup logging with configured level
    setup_logging(app_settings.mcp.log_level)


    server = McpServer(app_settings)
    server.run()
