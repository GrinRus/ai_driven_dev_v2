from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any, Protocol
from urllib.parse import parse_qs, urlparse

from aidd.cli.ui_assets import OperatorStaticAssetContent
from aidd.cli.ui_http import (
    UiRequestBodyTooLarge,
    UiResponse,
    _error_response,
    _json_response,
    _read_json_body,
)
from aidd.core.mutation_lease import RunMutationConflict
from aidd.core.runtime_operator import OperatorDecisionConflict

UiGetRoute = Callable[[dict[str, list[str]]], UiResponse]
UiPostRoute = Callable[[dict[str, Any]], UiResponse]
UiStaticRouteResolver = Callable[[str], OperatorStaticAssetContent | None]
UiDynamicGetRoute = Callable[[str, dict[str, list[str]]], UiResponse]
UiDynamicPostRoute = Callable[[str, dict[str, Any]], UiResponse]
UiRemoteMutationGuard = Callable[[str], UiResponse | None]


class UiJobDecisionConflict(RuntimeError):
    """Raised when a terminal UI job can no longer accept a decision."""


class UiShutdownService(Protocol):
    def consume_shutdown_requested(self) -> bool: ...


def _unique_routes[RouteT: (UiGetRoute, UiPostRoute)](
    routes: Mapping[str, RouteT],
    *,
    method: str,
) -> dict[str, RouteT]:
    normalized = dict(routes)
    if len(normalized) != len(routes):
        raise ValueError(f"Duplicate {method} UI route.")
    for path in normalized:
        if not path.startswith("/"):
            raise ValueError(f"{method} UI route must be absolute: {path!r}.")
    return normalized


class OperatorUiRouter:
    def __init__(
        self,
        *,
        get_routes: Mapping[str, UiGetRoute],
        post_routes: Mapping[str, UiPostRoute],
        static_route_resolver: UiStaticRouteResolver,
        dynamic_get_route: UiDynamicGetRoute,
        dynamic_post_route: UiDynamicPostRoute,
        remote_mutation_guard: UiRemoteMutationGuard,
    ) -> None:
        self._get_routes = _unique_routes(get_routes, method="GET")
        self._post_routes = _unique_routes(post_routes, method="POST")
        self._static_route_resolver = static_route_resolver
        self._dynamic_get_route = dynamic_get_route
        self._dynamic_post_route = dynamic_post_route
        self._remote_mutation_guard = remote_mutation_guard

    @property
    def get_paths(self) -> tuple[str, ...]:
        return tuple(self._get_routes)

    @property
    def post_paths(self) -> tuple[str, ...]:
        return tuple(self._post_routes)

    def handle_get(self, path: str, params: dict[str, list[str]]) -> UiResponse:
        try:
            if static_asset := self._static_route_resolver(path):
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type=static_asset.content_type,
                    body=static_asset.text.encode("utf-8"),
                )
            if path == "/favicon.ico":
                return UiResponse(
                    status=int(HTTPStatus.NO_CONTENT),
                    content_type="image/x-icon",
                    body=b"",
                )
            route = self._get_routes.get(path)
            if route is not None:
                return route(params)
            if path == "/api/jobs":
                return _error_response(
                    "job id is required.",
                    status=HTTPStatus.NOT_FOUND,
                )
            if path.startswith("/api/jobs/"):
                return self._dynamic_get_route(path, params)
        except ValueError as exc:
            return _error_response(str(exc))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

    def handle_post(self, path: str, payload: dict[str, Any]) -> UiResponse:
        try:
            remote_mutation_error = self._remote_mutation_guard(path)
            if remote_mutation_error is not None:
                return remote_mutation_error
            if path.startswith("/api/jobs/"):
                return self._dynamic_post_route(path, payload)
            route = self._post_routes.get(path)
            if route is not None:
                return route(payload)
        except FileExistsError as exc:
            return _error_response(str(exc), status=HTTPStatus.CONFLICT)
        except OperatorDecisionConflict as exc:
            return _json_response(
                {
                    "error": str(exc),
                    "winner": exc.winner.to_dict(),
                },
                status=HTTPStatus.CONFLICT,
            )
        except (UiJobDecisionConflict, RunMutationConflict) as exc:
            return _error_response(str(exc), status=HTTPStatus.CONFLICT)
        except ValueError as exc:
            return _error_response(str(exc))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)


def handler_for(
    *,
    router: OperatorUiRouter,
    shutdown_service: UiShutdownService,
) -> type[BaseHTTPRequestHandler]:
    class OperatorUiHandler(BaseHTTPRequestHandler):
        def _send(self, response: UiResponse) -> None:
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            self._send(router.handle_get(parsed.path, parse_qs(parsed.query)))

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = _read_json_body(self)
            except UiRequestBodyTooLarge as exc:
                self._send(
                    _error_response(
                        str(exc),
                        status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    )
                )
                return
            except ValueError as exc:
                self._send(_error_response(str(exc)))
                return
            self._send(router.handle_post(parsed.path, payload))
            if shutdown_service.consume_shutdown_requested():
                threading.Thread(
                    target=self.server.shutdown,
                    name="aidd-ui-server-stop",
                    daemon=True,
                ).start()

        def log_message(self, format: str, *args: object) -> None:
            return

    return OperatorUiHandler


__all__ = [
    "OperatorUiRouter",
    "UiJobDecisionConflict",
    "handler_for",
]
