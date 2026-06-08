import io

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models.task import Task


def export_tasks_to_excel(tasks: list[Task]) -> io.BytesIO:
    """Compile task list in memory into an Excel spreadsheet binary stream."""
    wb = Workbook()
    ws = wb.active
    ws.title = "TodoSphere Tasks"

    # Headers
    headers = [
        "Task ID",
        "Task Name",
        "Description",
        "Status",
        "Start Time",
        "Expected End Time",
        "Actual End Time",
        "Duration (Seconds)",
    ]
    ws.append(headers)

    # Data Rows
    for task in tasks:
        ws.append(
            [
                str(task.id),
                task.task_name,
                task.description or "",
                task.status.value,
                task.start_time.strftime("%Y-%m-%d %H:%M:%S")
                if task.start_time
                else "",
                task.expected_end_time.strftime("%Y-%m-%d %H:%M:%S")
                if task.expected_end_time
                else "",
                task.actual_end_time.strftime("%Y-%m-%d %H:%M:%S")
                if task.actual_end_time
                else "",
                task.total_time_taken_seconds
                if task.total_time_taken_seconds is not None
                else "",
            ]
        )

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out


def export_tasks_to_pdf(tasks: list[Task]) -> io.BytesIO:
    """Compile task list in memory into a PDF page document stream."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()
    title_style = styles["Title"]

    story.append(Paragraph("TodoSphere Task Export", title_style))
    story.append(Spacer(1, 20))

    # Table data
    data = [["Task Name", "Status", "Start Time", "Expected Deadline"]]
    for task in tasks:
        start_str = (
            task.start_time.strftime("%Y-%m-%d %H:%M") if task.start_time else ""
        )
        end_str = (
            task.expected_end_time.strftime("%Y-%m-%d %H:%M")
            if task.expected_end_time
            else ""
        )
        data.append([task.task_name, task.status.value, start_str, end_str])

    t = Table(data, colWidths=[200, 80, 110, 110])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#f8f9fa"), colors.HexColor("#ffffff")],
                ),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )

    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer
