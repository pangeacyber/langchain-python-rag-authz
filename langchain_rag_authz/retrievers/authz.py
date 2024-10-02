from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Any

from langchain_core.vectorstores import VectorStore, VectorStoreRetriever
from pangea import PangeaConfig
from pangea.services import AuthZ
from pangea.services.authz import Resource, Subject
from pydantic import SecretStr


class AuthzRetriever(VectorStoreRetriever):
    """A retriever backed by a vector store with AuthZ filtering."""

    _client: AuthZ
    _subject: Subject
    _cached_filter_category: Callable[[str], bool]

    def __init__(
        self,
        vectorstore: VectorStore,
        username: str,
        token: SecretStr,
        domain: str = "aws.us.pangea.cloud",
        **kwargs,
    ):
        """
        Args:
            vectorstore: Vector store to use for retrieval.
            username: Unique username to filter documents for.
            token: Pangea AuthZ API token.
            domain: Pangea API domain.
        """

        tags = kwargs.pop("tags", None) or vectorstore._get_retriever_tags()
        super().__init__(vectorstore=vectorstore, tags=tags, **kwargs)
        self._client = AuthZ(token=token.get_secret_value(), config=PangeaConfig(domain=domain))
        self._subject = Subject(type="user", id=username)
        self._cached_filter_category = lru_cache()(self._filter_category)
        self.search_kwargs["filter"] = self._filter

    def _filter_category(self, category: str) -> bool:
        """Check if the subject has read permissions for the given category."""

        response = self._client.check(resource=Resource(type=category), action="read", subject=self._subject)
        return response.result is not None and response.result.allowed

    def _filter(self, metadata: dict[str, Any]) -> bool:
        """Filter documents based on the subject's permissions in AuthZ."""

        category: str | None = metadata.get("category")

        # Assume un-categorized documents may be read by anyone.
        if not category or len(category) == 0:
            return True

        return self._cached_filter_category(category)
