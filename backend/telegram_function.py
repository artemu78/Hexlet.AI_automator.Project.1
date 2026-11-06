"""Yandex Cloud Functions entry point: telegram_function.handler.

Environment: BOT_TOKEN, ADMIN_CHAT_ID.
GET / sends a default message; GET /?text=Hello sends the supplied text.
GET /?version returns the handler version without sending a message.
Uses only the Python standard library.
"""

import errno
import json
import socket
import ssl
import time
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


FUNCTION_VERSION = "1.0.2"
PROXY_HOST = "jkvsndafl2.execute-api.us-east-1.amazonaws.com"
PROXY_BASE_URL = f"https://{PROXY_HOST}"


def send_message(text):
    """Send text to the configured administrator and return Telegram's result."""
    token = os.environ["BOT_TOKEN"].strip()
    chat_id = os.environ["ADMIN_CHAT_ID"].strip()
    if not token or not chat_id:
        raise ValueError("Missing configuration")

    request = Request(
        f"{PROXY_BASE_URL}/bot{token}/sendMessage?destination=telegram",
        data=json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise ValueError("Telegram rejected the message")
    return result["result"]


def network_diagnostics(error, elapsed):
    """Describe failures without exposing exception strings containing secret URLs."""
    reason = error.reason if isinstance(error, URLError) else error
    code = getattr(reason, "errno", None)
    if isinstance(reason, socket.gaierror):
        category, detail = "dns_error", "Could not resolve the API hostname."
    elif isinstance(reason, ssl.SSLCertVerificationError):
        category, detail = "tls_certificate_error", "TLS certificate verification failed."
    elif isinstance(reason, ssl.SSLError):
        category, detail = "tls_error", "TLS negotiation or TLS data transfer failed."
    elif isinstance(reason, TimeoutError) or code == errno.ETIMEDOUT:
        category, detail = "timeout", "A socket operation timed out; connection, TLS handshake, or response reading may be responsible."
    elif code == errno.ECONNREFUSED:
        category, detail = "connection_refused", "The connection was refused."
    elif code == errno.ECONNRESET:
        category, detail = "connection_reset", "The connection was reset."
    elif code in (errno.ENETUNREACH, errno.EHOSTUNREACH):
        category, detail = "network_unreachable", "No route to the network or host was available."
    else:
        category, detail = "network_error", "The HTTPS request failed before a usable HTTP response was received."
    return {
        "category": category,
        "detail": detail,
        "host": PROXY_HOST,
        "upstream_host": "api.telegram.org",
        "route": "aws-proxy",
        "port": 443,
        "errno": code if isinstance(code, int) else None,
        "elapsed_ms": round(elapsed * 1000),
        "socket_timeout_seconds": 10,
        "restriction_assessment": "inconclusive",
        "interpretation": "This error alone cannot establish blocking or its cause. This request uses the AWS proxy. Check Yandex-to-AWS connectivity and AWS proxy logs; the proxy-to-Telegram hop is separate.",
        "delivery_status": "unknown; a failed response does not guarantee the message was not sent",
    }


def handler(event, context):
    """Accept a GET request using Yandex's standard HTTP integration."""
    def response(status, payload):
        return {
            "statusCode": status,
            "headers": {
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-store",
            },
            "isBase64Encoded": False,
            "body": json.dumps(payload, ensure_ascii=False),
        }

    if event.get("httpMethod") != "GET":
        result = response(405, {"ok": False, "error": "Use GET"})
        result["headers"]["Allow"] = "GET"
        return result

    params = event.get("queryStringParameters") or {}
    if "version" in params:
        return response(200, {"service": "telegram-function", "version": FUNCTION_VERSION})

    text = params.get("text", "Привет из Yandex Cloud Functions!")
    if not isinstance(text, str) or not text.strip() or len(text) > 4096:
        return response(400, {"ok": False, "error": "Text must contain 1–4096 characters"})

    if not os.environ.get("BOT_TOKEN", "").strip() or not os.environ.get("ADMIN_CHAT_ID", "").strip():
        return response(500, {"ok": False, "error": "Set BOT_TOKEN and ADMIN_CHAT_ID"})

    started = time.monotonic()
    try:
        message = send_message(text)
    except HTTPError as error:
        return response(502, {
            "ok": False,
            "error": "The HTTPS endpoint returned an HTTP error",
            "diagnostics": {
                "category": "http_error",
                "upstream_http_status": error.code,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "interpretation": "An HTTP response was received; this was not a connection timeout. The AWS proxy returned an HTTP error. Check its status and logs; it may have relayed a Telegram error or generated its own failure.",
            },
        })
    except (URLError, OSError) as error:
        diagnostics = network_diagnostics(error, time.monotonic() - started)
        return response(504 if diagnostics["category"] == "timeout" else 502, {
            "ok": False, "error": diagnostics["detail"], "diagnostics": diagnostics,
        })
    except (ValueError, KeyError):
        return response(502, {"ok": False, "error": "Invalid response from Telegram"})

    return response(200, {"ok": True, "message_id": message["message_id"]})
