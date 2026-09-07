from __future__ import annotations

from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler
from typing import Any, Protocol

from aidd.cli.ui_assets import operator_static_asset_for_route
from aidd.cli.ui_http import UiResponse
from aidd.cli.ui_routing import (
    OperatorUiRouter,
    UiGetRoute,
    UiPostRoute,
    handler_for,
)


class UiTransportService(Protocol):
    """Server-side callbacks exposed by :class:`OperatorUiService`.

    The transport owns HTTP composition only.  Endpoint handlers remain on the
    application service so they can use the selected project/work-item context
    and the existing core read/write services.
    """

    def _get_routes(self) -> Mapping[str, UiGetRoute]: ...

    def _post_routes(self) -> Mapping[str, UiPostRoute]: ...

    def _handle_job_get(self, *, path: str, params: dict[str, list[str]]) -> UiResponse: ...

    def _handle_job_post(
        self,
        *,
        path: str,
        payload: dict[str, Any],
    ) -> UiResponse: ...

    def _remote_mutation_error(self, path: str) -> UiResponse | None: ...

    def consume_shutdown_requested(self) -> bool: ...


class OperatorUiTransport:
    """Compose codecs, routing, and the HTTP handler for the operator service.

    JSON payload encoding/decoding stays in ``ui_http`` and generic path/error
    dispatch stays in ``ui_routing``.  This boundary prevents ``ui.py`` from
    assembling transport concerns directly while preserving the existing
    router object for compatibility with characterization tests and callers.
    """

    def __init__(
        self,
        service: UiTransportService,
    ) -> None:
        self._service = service
        self._router = OperatorUiRouter(
            get_routes=service._get_routes(),
            post_routes=service._post_routes(),
            static_route_resolver=operator_static_asset_for_route,
            dynamic_get_route=lambda path, params: service._handle_job_get(
                path=path,
                params=params,
            ),
            dynamic_post_route=lambda path, payload: service._handle_job_post(
                path=path,
                payload=payload,
            ),
            remote_mutation_guard=service._remote_mutation_error,
        )

    @property
    def router(self) -> OperatorUiRouter:
        return self._router

    def handle_get(self, path: str, params: dict[str, list[str]]) -> UiResponse:
        return self._router.handle_get(path, params)

    def handle_post(self, path: str, payload: dict[str, Any]) -> UiResponse:
        return self._router.handle_post(path, payload)

    def handler(self) -> type[BaseHTTPRequestHandler]:
        return handler_for(
            router=self._router,
            shutdown_service=self._service,
        )


__all__ = ["OperatorUiTransport", "UiTransportService"]
