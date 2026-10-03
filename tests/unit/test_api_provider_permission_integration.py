from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
)
from core.research.acquisition_pipeline import (
    ResearchAcquisitionPipeline,
)
from core.research.api_provider import (
    RESTJSONProviderConfig,
    RESTJSONResearchProvider,
)


class CountingAPIHandler(BaseHTTPRequestHandler):
    calls = 0

    def do_GET(self) -> None:
        type(self).calls += 1

        payload = {
            "results": [
                {
                    "title": "SAHIBEX API Integration",
                    "url": (
                        "https://example.com/"
                        "sahibex-api"
                    ),
                    "content": (
                        "Deterministic REST/JSON "
                        "API integration result."
                    ),
                },
                {
                    "title": "SAHIBEX API Research",
                    "url": (
                        "https://example.org/"
                        "sahibex-api-research"
                    ),
                    "content": (
                        "Second deterministic API "
                        "result for pipeline testing."
                    ),
                },
            ]
        }

        body = json.dumps(
            payload
        ).encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(body)

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        return


class LocalAPIServer:
    def __init__(self) -> None:
        self.server = HTTPServer(
            ("127.0.0.1", 0),
            CountingAPIHandler,
        )

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        return (
            f"http://{host}:{port}/api"
        )

    def start(self) -> None:
        CountingAPIHandler.calls = 0
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def make_pipeline(tmp_path: Path):
    database_path = tmp_path / "research.db"

    server = LocalAPIServer()
    server.start()

    provider = RESTJSONResearchProvider(
        RESTJSONProviderConfig(
            allow_private_hosts=True,
        )
    )

    acquisition_engine = ResearchAcquisitionEngine()

    acquisition_engine.register_provider(
        provider
    )

    pipeline = ResearchAcquisitionPipeline(
        database_path=str(database_path),
        acquisition_engine=acquisition_engine,
    )

    return (
        pipeline,
        provider,
        server,
    )


def make_request(
    server: LocalAPIServer,
) -> AcquisitionRequest:
    return AcquisitionRequest(
        query="SAHIBEX API permission test",
        source_type="api",
        max_sources=2,
        metadata={
            "url": server.url,
            "results_path": "results",
        },
    )


def test_api_blocked_without_confirmation():
    with TemporaryDirectory() as temp_dir:
        (
            pipeline,
            provider,
            server,
        ) = make_pipeline(
            Path(temp_dir)
        )

        try:
            request = make_request(
                server
            )

            blocked = False

            try:
                pipeline.acquire_and_ingest(
                    request,
                    provider_name=(
                        "rest_json_api"
                    ),
                    confirmation=False,
                )
            except PermissionError:
                blocked = True

            assert blocked is True

            # Critical security assertion:
            # API network request must never
            # execute before NETWORK_ACCESS
            # permission is granted.
            assert (
                CountingAPIHandler.calls
                == 0
            )

            print(
                "[PASS] API blocked "
                "without confirmation"
            )

            print(
                "[PASS] API endpoint was "
                "never executed"
            )

        finally:
            pipeline.close()
            server.stop()


def test_api_executes_after_confirmation():
    with TemporaryDirectory() as temp_dir:
        (
            pipeline,
            provider,
            server,
        ) = make_pipeline(
            Path(temp_dir)
        )

        try:
            request = make_request(
                server
            )

            result = pipeline.acquire_and_ingest(
                request,
                provider_name=(
                    "rest_json_api"
                ),
                confirmation=True,
            )

            assert result is not None

            assert (
                CountingAPIHandler.calls
                == 1
            )

            assert (
                result.stored_count
                == 2
            )

            assert (
                result.duplicate_count
                == 0
            )

            assert (
                len(result.ingested)
                == 2
            )

            print(
                "[PASS] confirmed API "
                "execution"
            )

            print(
                "[PASS] API endpoint executed "
                "exactly once"
            )

            print(
                "[PASS] API results entered "
                "ingestion pipeline"
            )

            print(
                "[PASS] API results were stored"
            )

        finally:
            pipeline.close()
            server.stop()


def test_api_results_preserve_metadata():
    with TemporaryDirectory() as temp_dir:
        (
            pipeline,
            provider,
            server,
        ) = make_pipeline(
            Path(temp_dir)
        )

        try:
            request = make_request(
                server
            )

            result = pipeline.acquire_and_ingest(
                request,
                provider_name=(
                    "rest_json_api"
                ),
                confirmation=True,
            )

            assert result.stored_count == 2

            acquisition = result.acquisition

            assert (
                acquisition.completed
                is True
            )

            assert (
                acquisition.status
                == "completed"
            )

            assert (
                len(acquisition.sources)
                == 2
            )

            first = acquisition.sources[0]

            assert (
                first.source_type
                == "api"
            )

            assert (
                first.metadata[
                    "provider_name"
                ]
                == "rest_json_api"
            )

            assert (
                first.metadata[
                    "content_is_api_result"
                ]
                is True
            )

            assert (
                first.metadata[
                    "discovery_only"
                ]
                is True
            )

            print(
                "[PASS] API metadata "
                "preserved through pipeline"
            )

        finally:
            pipeline.close()
            server.stop()


if __name__ == "__main__":
    test_api_blocked_without_confirmation()
    test_api_executes_after_confirmation()
    test_api_results_preserve_metadata()

    print(
        "\nSAHIBEX REST/JSON API "
        "PERMISSION INTEGRATION TEST: PASS"
    )
