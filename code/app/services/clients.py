from app.services.opensource import OpenSourceClient
from app.services.snyk import SnykClient


def get_snyk_client() -> SnykClient:
	return SnykClient()


def get_opensource_client() -> OpenSourceClient:
	return OpenSourceClient()
