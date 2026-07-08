"""Report endpoints with Excel/PDF/CSV export."""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.services.report import REPORTS, ExportFormat, ReportService

router = APIRouter(prefix="/reports", tags=["Relatorios"])


@router.get("", summary="Listar relatorios disponiveis")
def list_reports(_=Depends(require_permission("report:view"))) -> dict[str, str]:
    return REPORTS


@router.get("/{report}/data", summary="Dados do relatorio (JSON)")
def report_data(
    report: str,
    db: Session = Depends(get_db),
    _=Depends(require_permission("report:view")),
) -> dict:
    ds = ReportService(db).build(report)
    return {"title": ds.title, "headers": ds.headers, "rows": ds.rows}


@router.get("/{report}/export", summary="Exportar relatorio (xlsx | pdf | csv)")
def export_report(
    report: str,
    fmt: ExportFormat = "xlsx",
    db: Session = Depends(get_db),
    _=Depends(require_permission("report:view")),
) -> Response:
    content, media_type, filename = ReportService(db).export(report, fmt)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
