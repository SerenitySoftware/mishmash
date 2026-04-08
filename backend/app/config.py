from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://mishmash:mishmash_dev@localhost:5432/mishmash"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "mishmash"
    s3_secret_key: str = "mishmash_dev"
    s3_datasets_bucket: str = "mishmash-datasets"
    s3_results_bucket: str = "mishmash-results"

    # App
    app_name: str = "Mishmash"
    debug: bool = True
    secret_key: str = "dev-secret-change-in-production"
    cors_origins: str = "http://localhost:3000"  # comma-separated for multiple

    # Runner
    runner_timeout_seconds: int = 300
    runner_memory_limit: str = "512m"
    runner_cpu_limit: float = 1.0
    max_upload_size_mb: int = 500

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
