import csv
import io
import json
import sys
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .analyzer import build_analysis
from .logging_config import configure_logging, get_logger
from .parser import parse_chat_logs
from .schemas import AnalyzeRequest, AnalyzeResponse, ExportRequest


def _resolve_frontend_dist() -> Path:
    """frozen(PyInstaller) 환경과 개발 환경 모두에서 frontend/dist를 반환합니다."""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller가 sys._MEIPASS 하위에 datas를 추출합니다
        return Path(sys._MEIPASS) / "frontend" / "dist"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


app = FastAPI(title="chatLog Analyzer API", version="0.1.0")
logger = get_logger(__name__)
FRONTEND_DIST_DIR = _resolve_frontend_dist()


@app.on_event("startup")
def on_startup() -> None:
    configure_logging()
    logger.info("Backend startup complete")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "HTTP %s %s -> %s (%sms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    except Exception:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.exception(
            "HTTP %s %s failed (%sms)",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if (FRONTEND_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")


@app.get("/", include_in_schema=False, response_model=None)
def index() -> FileResponse | dict[str, str]:
    index_path = FRONTEND_DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"status": "ok", "message": "frontend dist not found"}


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api") or full_path == "health":
        raise HTTPException(status_code=404, detail="not_found")

    index_path = FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="frontend_dist_not_found")
    return FileResponse(index_path)


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    logger.info(
        "Analyze request received: vod_id=%s, keywords=%s, bucket=%s",
        payload.source.vod_id,
        payload.keywords,
        payload.options.bucket_size_seconds,
    )
    try:
        messages, parse_errors = parse_chat_logs(payload.source)
    except ValueError as exc:
        logger.warning("Analyze request validation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while parsing chat logs")
        raise HTTPException(status_code=500, detail=f"internal_error: {exc}") from exc

    try:
        summary, volume_series, keyword_series, highlights = build_analysis(
            messages=messages,
            keywords=payload.keywords,
            options=payload.options,
        )
    except Exception as exc:
        logger.exception("Unexpected error while building analysis")
        raise HTTPException(status_code=500, detail=f"internal_error: {exc}") from exc

    logger.info(
        "Analyze result: vod_id=%s, messages=%s, parse_errors=%s, highlights=%s",
        payload.source.vod_id,
        len(messages),
        len(parse_errors),
        len(highlights),
    )

    return AnalyzeResponse(
        summary=summary,
        volume_series=volume_series,
        keyword_series=keyword_series,
        highlights=highlights,
        parse_errors=parse_errors,
        message="ok" if messages else "no_messages",
    )


@app.post("/api/export")
def export_analysis(payload: ExportRequest) -> StreamingResponse:
    logger.info(
        "Export request received: vod_id=%s, format=%s, dataset=%s",
        payload.analysis.source.vod_id,
        payload.format,
        payload.dataset,
    )
    try:
        messages, parse_errors = parse_chat_logs(payload.analysis.source)
    except ValueError as exc:
        logger.warning("Export request validation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error while parsing chat logs for export")
        raise HTTPException(status_code=500, detail=f"internal_error: {exc}") from exc

    try:
        summary, volume_series, keyword_series, highlights = build_analysis(
            messages=messages,
            keywords=payload.analysis.keywords,
            options=payload.analysis.options,
        )
    except Exception as exc:
        logger.exception("Unexpected error while building analysis for export")
        raise HTTPException(status_code=500, detail=f"internal_error: {exc}") from exc

    analyzed = AnalyzeResponse(
        summary=summary,
        volume_series=volume_series,
        keyword_series=keyword_series,
        highlights=highlights,
        parse_errors=parse_errors,
        message="ok" if messages else "no_messages",
    )

    if payload.format == "json":
        logger.info("Export json success: vod_id=%s, dataset=%s", payload.analysis.source.vod_id, payload.dataset)
        return _export_json(analyzed=analyzed, dataset=payload.dataset)

    logger.info("Export csv success: vod_id=%s, dataset=%s", payload.analysis.source.vod_id, payload.dataset)
    return _export_csv(analyzed=analyzed, dataset=payload.dataset)


def _export_json(analyzed: AnalyzeResponse, dataset: str) -> StreamingResponse:
    data = _dataset_payload(analyzed=analyzed, dataset=dataset)
    file_name = f"analysis-{dataset}.json"
    body = json.dumps(data, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.BytesIO(body.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


def _export_csv(analyzed: AnalyzeResponse, dataset: str) -> StreamingResponse:
    if dataset == "all":
        raise HTTPException(status_code=400, detail="csv export는 dataset=all을 지원하지 않습니다.")

    output = io.StringIO()
    writer = csv.writer(output)

    if dataset == "summary":
        writer.writerow(
            [
                "total_messages",
                "unique_users",
                "start_time",
                "end_time",
                "vod_duration_sec",
                "vod_duration_label",
                "avg_messages_per_minute",
            ]
        )
        writer.writerow(
            [
                analyzed.summary.total_messages,
                analyzed.summary.unique_users,
                analyzed.summary.start_time,
                analyzed.summary.end_time,
                analyzed.summary.vod_duration_sec,
                analyzed.summary.vod_duration_label,
                analyzed.summary.avg_messages_per_minute,
            ]
        )
    elif dataset == "highlights":
        writer.writerow(
            [
                "start",
                "start_offset_sec",
                "start_offset_label",
                "end",
                "end_offset_sec",
                "end_offset_label",
                "score",
                "peak_bucket",
                "peak_offset_sec",
                "peak_offset_label",
                "peak_total_messages",
                "representative_keyword",
            ]
        )
        for row in analyzed.highlights:
            writer.writerow(
                [
                    row.start,
                    row.start_offset_sec,
                    row.start_offset_label,
                    row.end,
                    row.end_offset_sec,
                    row.end_offset_label,
                    row.score,
                    row.peak_bucket,
                    row.peak_offset_sec,
                    row.peak_offset_label,
                    row.peak_total_messages,
                    row.representative_keyword,
                ]
            )
    elif dataset == "volume":
        writer.writerow(
            [
                "bucket_start",
                "bucket_start_offset_sec",
                "bucket_start_offset_label",
                "total_messages",
                "unique_users",
            ]
        )
        for row in analyzed.volume_series:
            writer.writerow(
                [
                    row.bucket_start,
                    row.bucket_start_offset_sec,
                    row.bucket_start_offset_label,
                    row.total_messages,
                    row.unique_users,
                ]
            )
    elif dataset == "keywords":
        writer.writerow(
            [
                "bucket_start",
                "bucket_start_offset_sec",
                "bucket_start_offset_label",
                "keyword",
                "count",
            ]
        )
        for row in analyzed.keyword_series:
            writer.writerow(
                [
                    row.bucket_start,
                    row.bucket_start_offset_sec,
                    row.bucket_start_offset_label,
                    row.keyword,
                    row.count,
                ]
            )
    elif dataset == "parse_errors":
        writer.writerow(["file_path", "line_number", "reason", "raw_line"])
        for row in analyzed.parse_errors:
            writer.writerow([row.file_path, row.line_number, row.reason, row.raw_line])
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 dataset입니다.")

    file_name = f"analysis-{dataset}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


def _dataset_payload(analyzed: AnalyzeResponse, dataset: str) -> dict | list:
    model_dump = analyzed.model_dump(mode="json")
    if dataset == "all":
        return model_dump
    if dataset not in model_dump:
        raise HTTPException(status_code=400, detail="지원하지 않는 dataset입니다.")
    return model_dump[dataset]
