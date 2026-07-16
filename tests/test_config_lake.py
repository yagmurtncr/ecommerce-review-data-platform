from config import settings
from lake.lake_io import s3a


def test_s3a_paths_per_layer():
    assert s3a("bronze", "reviews").startswith(f"s3a://{settings.LAKE_BUCKET}/")
    assert "/bronze/reviews" in s3a("bronze", "reviews")
    assert "/silver/reviews" in s3a("silver", "reviews")
    assert "/gold/daily" in s3a("gold", "daily")


def test_connection_string_helpers():
    assert settings.pg_dsn().startswith("postgresql://")
    assert settings.pg_jdbc().startswith("jdbc:postgresql://")
    assert settings.mongo_uri().startswith("mongodb://")
    assert "authSource=admin" in settings.mongo_uri()
