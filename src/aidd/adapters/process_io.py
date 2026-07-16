from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import IO


@dataclass(slots=True)
class ManagedStdinWriter:
    _thread: threading.Thread
    _errors: list[BaseException]

    @classmethod
    def start(cls, pipe: IO[str] | None, text: str | None) -> ManagedStdinWriter | None:
        if pipe is None or text is None:
            return None
        errors: list[BaseException] = []

        def _write() -> None:
            try:
                pipe.write(text)
                pipe.close()
            except BrokenPipeError:
                pass
            except BaseException as exc:
                errors.append(exc)
                try:
                    pipe.close()
                except OSError:
                    pass

        thread = threading.Thread(target=_write, daemon=True, name="aidd-stdin-writer")
        writer = cls(_thread=thread, _errors=errors)
        thread.start()
        return writer

    @property
    def error(self) -> BaseException | None:
        return self._errors[0] if self._errors else None

    @property
    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def join(self, *, timeout_seconds: float = 0.5) -> None:
        self._thread.join(timeout=timeout_seconds)


__all__ = ["ManagedStdinWriter"]
