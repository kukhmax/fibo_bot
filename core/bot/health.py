from dataclasses import asdict
from dataclasses import dataclass
import socket
from urllib.parse import urlparse

from core.config import load_environment_config
from core.config import load_runtime_secrets


@dataclass(frozen=True)
class DependencyHealth:
    name: str
    host: str
    port: int
    healthy: bool


@dataclass(frozen=True)
class AppHealth:
    app: str
    environment: str
    mode: str
    telegram_token_configured: bool
    dependencies: list[DependencyHealth]
    healthy: bool


def build_health_snapshot() -> AppHealth:
    secrets = load_runtime_secrets()
    config = load_environment_config(secrets.environment)

    redis_host, redis_port = _extract_host_port("REDIS_URL", "redis://redis:6379/0", 6379)
    postgres_host, postgres_port = _extract_host_port(
        "DATABASE_URL", "postgresql://fib_bot:fib_bot@postgres:5432/fib_bot", 5432
    )

    dependencies = [
        DependencyHealth(
            name="redis",
            host=redis_host,
            port=redis_port,
            healthy=_check_tcp_dependency(redis_host, redis_port),
        ),
        DependencyHealth(
            name="postgres",
            host=postgres_host,
            port=postgres_port,
            healthy=_check_tcp_dependency(postgres_host, postgres_port),
        ),
    ]
    all_healthy = all(dep.healthy for dep in dependencies)

    return AppHealth(
        app="fib_bot",
        environment=config.environment,
        mode=config.bot.mode,
        telegram_token_configured=bool(secrets.telegram_bot_token),
        dependencies=dependencies,
        healthy=all_healthy,
    )


def health_snapshot_dict() -> dict:
    snapshot = build_health_snapshot()
    payload = asdict(snapshot)
    payload["dependencies"] = [asdict(item) for item in snapshot.dependencies]
    return payload


def _extract_host_port(env_key: str, default_url: str, default_port: int) -> tuple[str, int]:
    from os import getenv

    raw_url = getenv(env_key, default_url)
    parsed = urlparse(raw_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or default_port
    return host, port


def _check_tcp_dependency(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
