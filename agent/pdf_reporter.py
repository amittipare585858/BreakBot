import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph,
    Spacer, Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER


def generate_pdf_report(
    repo_name: str,
    analysis: dict,
    test_results: dict,
    fixes: list,
    username: str,
    output_path: str = None
) -> str:
    """Generate a professional PDF Bug Attack Report."""

    if not output_path:
        os.makedirs("reports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/{repo_name}_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    RED = colors.HexColor('#ff3b3b')
    DARK = colors.HexColor('#0a0a0f')
    GRAY = colors.HexColor('#a0a0b0')
    GREEN = colors.HexColor('#00ff88')
    YELLOW = colors.HexColor('#ffd700')

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=28,
        textColor=RED,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Normal'],
        fontSize=14,
        textColor=RED,
        fontName='Helvetica-Bold',
        spaceBefore=16,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName='Helvetica',
        spaceAfter=6,
        leading=16
    )

    story = []

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("BREAKBOT", title_style))
    story.append(Paragraph(
        "AI Red-Team Bug Attack Report", subtitle_style))
    story.append(HRFlowable(
        width="100%", thickness=2, color=RED))
    story.append(Spacer(1, 0.2*inch))

    meta_data = [
        ["Repository", repo_name],
        ["Scanned By", username],
        ["Generated", datetime.now().strftime(
            "%B %d, %Y at %H:%M")],
        ["Total Tests", str(test_results.get("total", 0))],
        ["Bugs Found", str(test_results.get("failed", 0))],
    ]
    meta_table = Table(meta_data,
        colWidths=[2*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (0,-1), RED),
        ('ROWBACKGROUNDS', (0,0), (-1,-1),
            [colors.HexColor('#f8f8f8'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.3*inch))

    weak_points = analysis.get("weak_points", [])
    bugs_found = test_results.get("failed", 0)
    total_tests = test_results.get("total", 0)

    score = calculate_security_score(
        len(weak_points), bugs_found, total_tests)
    score_color = (
        GREEN if score >= 80
        else YELLOW if score >= 50
        else RED
    )

    story.append(Paragraph(
        "Security Score", heading_style))
    score_data = [[
        Paragraph(f"{score}/100", ParagraphStyle(
            'Score',
            parent=styles['Normal'],
            fontSize=36,
            textColor=score_color,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )),
        Paragraph(
            get_score_label(score), ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=14,
            textColor=score_color,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
    ]]
    score_table = Table(score_data,
        colWidths=[3*inch, 3*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1),
            colors.HexColor('#f0f0f0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 20),
        ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "Attack Summary", heading_style))
    summary_data = [
        ["Metric", "Value", "Status"],
        ["Weak Points Found",
         str(len(weak_points)),
         "REVIEW REQUIRED" if weak_points else "CLEAN"],
        ["Tests Generated",
         str(total_tests), ""],
        ["Tests Passed",
         str(test_results.get("passed", 0)), "GOOD"],
        ["Bugs Detected",
         str(bugs_found),
         "CRITICAL" if bugs_found > 5
         else "WARNING" if bugs_found > 0
         else "CLEAN"],
    ]
    summary_table = Table(summary_data,
        colWidths=[2.5*inch, 1.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), DARK),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1),
            [colors.white, colors.HexColor('#f8f8f8')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (1,0), (2,-1), 'CENTER'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.2*inch))

    if weak_points:
        story.append(Paragraph(
            "Weak Points Identified", heading_style))
        wp_data = [["#", "Description", "Severity"]]
        for i, wp in enumerate(weak_points, 1):
            severity = classify_severity(wp)
            wp_data.append([
                str(i), wp, severity
            ])
        wp_table = Table(wp_data,
            colWidths=[0.4*inch, 4.5*inch, 1.1*inch])

        severity_colors = {
            "CRITICAL": colors.HexColor('#ff0000'),
            "HIGH": RED,
            "MEDIUM": YELLOW,
            "LOW": GREEN,
        }

        style_cmds = [
            ('BACKGROUND', (0,0), (-1,0), DARK),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1),
                [colors.white, colors.HexColor('#f8f8f8')]),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ]
        for i, wp in enumerate(weak_points, 1):
            severity = classify_severity(wp)
            color = severity_colors.get(
                severity, colors.gray)
            style_cmds.append((
                'TEXTCOLOR', (2,i), (2,i), color
            ))
            style_cmds.append((
                'FONTNAME', (2,i), (2,i),
                'Helvetica-Bold'
            ))

        wp_table.setStyle(TableStyle(style_cmds))
        story.append(wp_table)
        story.append(Spacer(1, 0.2*inch))

    failures = test_results.get("failures", [])
    if failures:
        story.append(Paragraph(
            "Bugs Detected", heading_style))
        for i, failure in enumerate(failures, 1):
            story.append(Paragraph(
                f"Bug #{i}: {failure.get('test_name', '')}",
                ParagraphStyle(
                    'BugTitle',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=RED,
                    fontName='Helvetica-Bold',
                    spaceBefore=10
                )
            ))
            story.append(Paragraph(
                f"Error: {failure.get('error', 'Unknown')}",
                body_style
            ))
            if failure.get("fix"):
                story.append(Paragraph(
                    f"Fix: {failure.get('fix', '')}",
                    ParagraphStyle(
                        'Fix',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.HexColor('#006600'),
                        fontName='Helvetica',
                        spaceAfter=6
                    )
                ))

    if fixes:
        story.append(Paragraph(
            "Fix Suggestions", heading_style))
        for i, fix in enumerate(fixes, 1):
            story.append(Paragraph(
                f"Fix #{i}: {fix.get('issue', '')}",
                body_style
            ))
            story.append(Paragraph(
                fix.get("explanation", ""),
                body_style
            ))

    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(
        width="100%", thickness=1, color=GRAY))
    story.append(Paragraph(
        "Generated by BreakBot - AI Red-Team Security Agent",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=GRAY,
            alignment=TA_CENTER,
            spaceBefore=8
        )
    ))

    doc.build(story)
    return output_path


def calculate_security_score(
    weak_points: int,
    bugs: int,
    total_tests: int
) -> int:
    """Calculate security score out of 100."""
    score = 100
    score -= weak_points * 5
    score -= bugs * 10
    if total_tests > 0:
        pass_rate = (total_tests - bugs) / total_tests
        score = int(score * pass_rate)
    return max(0, min(100, score))


def get_score_label(score: int) -> str:
    """Get label for security score."""
    if score >= 80:
        return "SECURE"
    elif score >= 60:
        return "MODERATE"
    elif score >= 40:
        return "VULNERABLE"
    else:
        return "CRITICAL RISK"


def classify_severity(weak_point: str) -> str:
    """Classify severity of a weak point."""
    text = weak_point.lower()
    if any(word in text for word in [
        'sql injection', 'injection', 'password',
        'credential', 'auth', 'overflow'
    ]):
        return "CRITICAL"
    elif any(word in text for word in [
        'division', 'crash', 'null', 'none',
        'error', 'exception', 'unsafe'
    ]):
        return "HIGH"
    elif any(word in text for word in [
        'file', 'resource', 'leak', 'handle',
        'type', 'index', 'boundary'
    ]):
        return "MEDIUM"
    else:
        return "LOW"
