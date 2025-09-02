from typing import Optional, Literal
from pydantic import SecretStr, Field
from typing import Literal, Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict


class KDBAIConfig(BaseSettings):
    """KDB.AI database connection and search configuration"""

    model_config = SettingsConfigDict(
        env_prefix="KDBAI_",
        frozen=True
    )

    model_config = SettingsConfigDict(
        env_prefix="KDBAI_DB_",
        frozen=True,
        env_file='.env',
        extra="ignore",
    )

    host: str = Field(
        default="127.0.0.1",
        description="KDB.AI server hostname or IP address [env: KDBAI_DB_HOST]"
    )
    port: int = Field(
        default=8082,
        description="KDB.AI server port number [env: KDBAI_DB_PORT]"
    )
    username: str = Field(
        default="",
        description="Username for KDB.AI authentication [env: KDBAI_DB_USERNAME]"
    )
    password: SecretStr = Field(
        default=SecretStr(""),
        description="Password for KDB.AI authentication [env: KDBAI_DB_PASSWORD]"
    )
    mode: Literal["rest", "qipc"] = Field(
        default="qipc",
       description="API mode: 'qipc' (fast binary protocol) or 'rest' (HTTP API) [env: KDBAI_DB_MODE]"
    )
    rest_protocol: Literal["http", "https"] = Field(
        default="http",
        description="Select protocol for REST mode, not considered for QIPC mode [env: KDBAI_DB_REST_PROTOCOL]"
    )
    qipc_tls: bool = Field(
        default=False,
        description="""Enable TLS for QIPC mode, not considered for REST mode.
        When using TLS with QIPC you will need to set the environment variable `KX_SSL_CA_CERT_FILE` that points
        to the certificate on your local filesystem that your TLS proxy is using. For local development and testing
        you can set `KX_SSL_VERIFY_SERVER=NO` to bypass this requirement [env: KDBAI_DB_QIPC_TLS]
        """
    )
    database_name: str = Field(
        default="default",
        description="Default database name to use for operations [env: KDBAI_DB_DATABASE_NAME]"
    )
    retry: int = Field(
        default=2,
        description="Number of connection retry attempts on failure [env: KDBAI_DB_RETRY]"
    )
    k: int = Field(
        default=5,
        description="Default number of results to return from vector searches [env: KDBAI_DB_K]"
    )
    vector_weight: float = Field(
        default=0.7,
        description="Weight for vector similarity in hybrid search (0.0-1.0) [env: KDBAI_DB_VECTOR_WEIGHT]"
    )
    sparse_weight: float = Field(
        default=0.3,
        description="Weight for text similarity in hybrid search (0.0-1.0) [env: KDBAI_DB_SPARSE_WEIGHT]"
    )
    embedding_csv_path: str = Field(
        default = "src/mcp_server/utils/embeddings.csv",
        description = "Path to embeddings csv [env: KDBAI_DB_EMBEDDING_CSV_PATH]"
    )


class ServerConfig(BaseSettings):
    """MCP server configuration and transport settings."""

    model_config = SettingsConfigDict(
        env_prefix="KDBAI_MCP_",
        env_file='.env',
        extra="ignore",
    )

    server_name: str = Field(
        default="KDBAI_MCP_Server",
        description="Name identifier for the MCP server instance [env: KDBAI_MCP_SERVER_NAME]"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging verbosity level [env: KDBAI_MCP_LOG_LEVEL]"
    )
    transport: Literal["stdio", "streamable-http"] = Field(
        default="streamable-http",
        description="Communication protocol: 'stdio' (pipes) or 'streamable-http' (HTTP server) [env: KDBAI_MCP_TRANSPORT]"
    )
    port: int = Field(
        default=7000,
        description="HTTP server port - ignored when using stdio transport [env: KDBAI_MCP_PORT]"
    )
    host: str = Field(
        default="127.0.0.1",
        description="HTTP server bind address - ignored when using stdio transport [env: KDBAI_MCP_HOST]"
    )


class AppSettings(BaseSettings):
    """KDB.AI MCP Server that enables interaction with KDB.AI"""

    mcp: ServerConfig = Field(
        default_factory=ServerConfig,
        description="MCP server configuration and transport settings"
    )
    db: KDBAIConfig = Field(
        default_factory=KDBAIConfig,
        description="KDB.AI database connection and search configuration"
    )
    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_exit_on_error=True,
        cli_avoid_json=True,
        cli_prog_name="mcp-server",
        cli_kebab_case=True,
    )
