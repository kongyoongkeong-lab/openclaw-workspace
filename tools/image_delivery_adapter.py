#!/usr/bin/env python3
"""
Image delivery adapter boundary.

Local CLI tests use MockImageDeliveryAdapter. OpenClaw runtime may inject an
adapter/function backed by the first-class message tool. This module does not
import OpenClaw tool modules directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class ImageDeliverySender(Protocol):
    """Callable boundary for runtime-injected delivery."""

    def __call__(self, *, channel: str, target: str, media: str, mime: str | None = None, caption: str | None = None) -> dict[str, Any]:
        ...


@dataclass
class ImageDeliveryRequest:
    image_path: str
    target_chat_id: str
    caption: str | None = None
    mime_type: str | None = None
    channel: str = "telegram"


@dataclass
class MockImageDeliveryAdapter:
    """Test adapter that records requests without network/tool delivery."""

    calls: list[ImageDeliveryRequest] = field(default_factory=list)

    def send_image(self, request: ImageDeliveryRequest) -> dict[str, Any]:
        self.calls.append(request)
        return {
            "success": True,
            "mock": True,
            "channel": request.channel,
            "target": request.target_chat_id,
            "media": request.image_path,
            "mime": request.mime_type,
            "caption": request.caption,
        }


@dataclass
class InjectedImageDeliveryAdapter:
    """Runtime adapter using an injected sender callable, not an import."""

    sender: ImageDeliverySender

    def send_image(self, request: ImageDeliveryRequest) -> dict[str, Any]:
        response = self.sender(
            channel=request.channel,
            target=request.target_chat_id,
            media=request.image_path,
            mime=request.mime_type,
            caption=request.caption,
        )
        return response if isinstance(response, dict) else {"success": False, "response": response}


def send_image_with_adapter(
    image_path: str,
    target_chat_id: str,
    caption: str | None = None,
    mime_type: str | None = None,
    adapter: MockImageDeliveryAdapter | InjectedImageDeliveryAdapter | None = None,
) -> dict[str, Any]:
    """Send image through an explicit adapter boundary.

    If no adapter is supplied, return a dry-run result. This keeps CLI tests
    local and prevents accidental production delivery.
    """

    request = ImageDeliveryRequest(
        image_path=image_path,
        target_chat_id=target_chat_id,
        caption=caption,
        mime_type=mime_type,
    )

    if adapter is None:
        return {
            "success": False,
            "dry_run": True,
            "reason": "No delivery adapter injected",
            "request": request.__dict__,
        }

    return adapter.send_image(request)
