from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Dict, List
from urllib.parse import parse_qs, urlparse


@dataclass
class Contact:
    name: str
    phone: str


class PhoneBook:
    def __init__(self) -> None:
        self._contacts: Dict[str, Contact] = {}
        self._lock = Lock()

    def add_contact(self, name: str, phone: str) -> Contact:
        key = name.strip().lower()
        if not key:
            raise ValueError("Name is required.")
        if not phone.strip():
            raise ValueError("Phone number is required.")
        contact = Contact(name=name.strip(), phone=phone.strip())
        with self._lock:
            self._contacts[key] = contact
        return contact

    def delete_contact(self, name: str) -> bool:
        key = name.strip().lower()
        with self._lock:
            return self._contacts.pop(key, None) is not None

    def search(self, query: str) -> List[Contact]:
        q = query.strip().lower()
        with self._lock:
            contacts = list(self._contacts.values())
        if not q:
            return sorted(contacts, key=lambda c: c.name.lower())
        return sorted(
            [contact for contact in contacts if self._matches_query(contact, q)],
            key=lambda c: c.name.lower(),
        )

    @staticmethod
    def _matches_query(contact: Contact, query: str) -> bool:
        return query in contact.name.lower() or query in contact.phone.lower()


class PhoneBookHandler(BaseHTTPRequestHandler):
    book = PhoneBook()
    base_dir = Path(__file__).resolve().parent

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._serve_file(self.base_dir / "templates" / "index.html", "text/html; charset=utf-8")
            return

        if parsed.path == "/static/style.css":
            self._serve_file(self.base_dir / "static" / "style.css", "text/css; charset=utf-8")
            return

        if parsed.path == "/static/script.js":
            self._serve_file(
                self.base_dir / "static" / "script.js",
                "application/javascript; charset=utf-8",
            )
            return

        if parsed.path == "/api/contacts":
            query = parse_qs(parsed.query).get("q", [""])[0]
            contacts = [asdict(contact) for contact in self.book.search(query)]
            self._send_json({"contacts": contacts}, status=HTTPStatus.OK)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:
        if self.path != "/api/contacts":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        payload = self._read_json()
        if payload is None:
            return

        try:
            contact = self.book.add_contact(payload.get("name", ""), payload.get("phone", ""))
            self._send_json({"contact": asdict(contact)}, status=HTTPStatus.CREATED)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def do_DELETE(self) -> None:
        if self.path != "/api/contacts":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        payload = self._read_json()
        if payload is None:
            return

        name = str(payload.get("name", ""))
        if not name.strip():
            self._send_json({"error": "Name is required."}, status=HTTPStatus.BAD_REQUEST)
            return

        deleted = self.book.delete_contact(name)
        self._send_json({"deleted": deleted}, status=HTTPStatus.OK)

    def _serve_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _read_json(self) -> dict | None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json({"error": "Invalid content length."}, status=HTTPStatus.BAD_REQUEST)
            return None

        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON."}, status=HTTPStatus.BAD_REQUEST)
            return None

    def _send_json(self, data: dict, status: HTTPStatus) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), PhoneBookHandler)
    print("Phone Book running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
