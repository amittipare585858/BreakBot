import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet, ParagraphStyle)
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, 
    Table, TableStyle, HRFlowable, 
    KeepTogether, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import ListFlowable, ListItem


def generate_pdf_report(
    repo_name: str,
    analysis: dict,
    test_results: dict,
    fixes: list,
    username: str,
    output_path: str = None
) -> str:
    """Generate a clean professional PDF report."""
    
    if not output_path:
        os.makedirs("reports", exist_ok=True)
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S")
        output_path = (
            f"reports/{repo_name}_{timestamp}.pdf")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
        title="BreakBot Bug Attack Report"
    )
    
    # Colors
    RED = colors.HexColor('#ff3b3b')
    DARK = colors.HexColor('#1a1a2e')
    LIGHT_GRAY = colors.HexColor('#f8f8fc')
    MID_GRAY = colors.HexColor('#9999bb')
    WHITE = colors.white
    GREEN = colors.HexColor('#00aa66')
    YELLOW = colors.HexColor('#cc8800')
    
    styles = getSampleStyleSheet()
    
    # Define styles
    def make_style(name, **kwargs):
        return ParagraphStyle(name, **kwargs)
    
    title_s = make_style('BBTitle',
        fontSize=26,
        textColor=RED,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=16,
        spaceBefore=8)
    
    subtitle_s = make_style('BBSub',
        fontSize=11,
        textColor=MID_GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=20,
        spaceBefore=0)
    
    heading_s = make_style('BBHead',
        fontSize=13, textColor=RED,
        fontName='Helvetica-Bold',
        spaceBefore=20, spaceAfter=8)
    
    body_s = make_style('BBBody',
        fontSize=9, textColor=DARK,
        fontName='Helvetica',
        spaceAfter=4, leading=14,
        wordWrap='CJK')
    
    small_s = make_style('BBSmall',
        fontSize=8, textColor=MID_GRAY,
        fontName='Helvetica',
        spaceAfter=2)
    
    footer_s = make_style('BBFooter',
        fontSize=8, textColor=MID_GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER)
    
    story = []
    
    # -- HEADER ----------------------------------
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("BREAKBOT", title_s))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "AI Red-Team Bug Attack Report", subtitle_s))
    story.append(Spacer(1, 0.15*inch))
    story.append(HRFlowable(
        width="100%", thickness=2,
        color=RED, spaceAfter=20))
    story.append(Spacer(1, 0.1*inch))
    
    # -- METADATA TABLE ---------------------------
    weak_points = analysis.get("weak_points", [])
    bugs_found = test_results.get("failed", 0)
    total_tests = test_results.get("total", 0)
    passed = test_results.get("passed", 0)
    score = calculate_security_score(
        len(weak_points), bugs_found, total_tests)
    
    meta = [
        ["Repository:", repo_name or "pasted_code"],
        ["Scanned By:", username],
        ["Generated:", datetime.now().strftime(
            "%B %d, %Y at %H:%M")],
        ["Security Score:", f"{score}/100 - "
         f"{get_score_label(score)}"],
    ]
    
    meta_table = Table(meta,
        colWidths=[1.5*inch, 4.5*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1),
         'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), RED),
        ('TEXTCOLOR', (1,0), (1,-1), DARK),
        ('ROWBACKGROUNDS', (0,0), (-1,-1),
         [LIGHT_GRAY, WHITE]),
        ('GRID', (0,0), (-1,-1), 0.3,
         colors.HexColor('#e8e8f0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.2*inch))
    
    # -- ATTACK SUMMARY ---------------------------
    story.append(Paragraph(
        "Attack Summary", heading_s))
    
    summary = [
        ["Metric", "Count", "Status"],
        ["Weak Points Found",
         str(len(weak_points)),
         "REVIEW REQUIRED" if weak_points else "CLEAN"],
        ["Tests Generated",
         str(total_tests), "-"],
        ["Tests Passed",
         str(passed), "GOOD" if passed > 0 else "-"],
        ["Bugs Detected",
         str(bugs_found),
         "CRITICAL" if bugs_found > 5
         else "WARNING" if bugs_found > 0
         else "CLEAN"],
    ]
    
    summary_table = Table(summary,
        colWidths=[3*inch, 1*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), DARK),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0),
         'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1),
         [WHITE, LIGHT_GRAY]),
        ('GRID', (0,0), (-1,-1), 0.3,
         colors.HexColor('#e8e8f0')),
        ('PADDING', (0,0), (-1,-1), 7),
        ('ALIGN', (1,0), (2,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    
    # -- WEAK POINTS ------------------------------
    if weak_points:
        story.append(Paragraph(
            "Weak Points Identified", heading_s))
        
        wp_data = [["#", "Description", "Severity"]]
        for i, wp in enumerate(weak_points, 1):
            severity = classify_severity(wp)
            # Wrap long text in Paragraph for auto-wrap
            wp_data.append([
                str(i),
                Paragraph(wp[:300], body_s),
                severity
            ])
        
        sev_colors = {
            "CRITICAL": colors.HexColor('#ff0000'),
            "HIGH": RED,
            "MEDIUM": YELLOW,
            "LOW": GREEN,
        }
        
        wp_table = Table(wp_data,
            colWidths=[
                0.3*inch, 4.5*inch, 0.8*inch],
            repeatRows=1)
        
        style_cmds = [
            ('BACKGROUND', (0,0), (-1,0), DARK),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0),
             'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.3,
             colors.HexColor('#e8e8f0')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1),
             [WHITE, LIGHT_GRAY]),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (2,0), (2,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]
        for i, wp in enumerate(weak_points, 1):
            severity = classify_severity(wp)
            c = sev_colors.get(severity, MID_GRAY)
            style_cmds.append((
                'TEXTCOLOR', (2,i), (2,i), c))
            style_cmds.append((
                'FONTNAME', (2,i), (2,i),
                'Helvetica-Bold'))
        
        wp_table.setStyle(TableStyle(style_cmds))
        story.append(wp_table)
    
    # -- BUGS DETECTED ----------------------------
    failures = test_results.get("failures", [])
    if failures:
        story.append(Paragraph(
            "Bugs Detected", heading_s))
        for i, failure in enumerate(failures, 1):
            bug_data = [
                [Paragraph(
                    f"Bug #{i}: "
                    f"{failure.get('test_name','Unknown')}",
                    make_style(f'BT{i}',
                        fontSize=9,
                        textColor=RED,
                        fontName='Helvetica-Bold')
                )],
                [Paragraph(
                    f"Error: "
                    f"{failure.get('error','')[:300]}",
                    body_s
                )],
            ]
            bug_table = Table(bug_data,
                colWidths=[5.5*inch])
            bug_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1),
                 colors.HexColor('#fff5f5')),
                ('BOX', (0,0), (-1,-1), 1,
                 colors.HexColor('#ffdddd')),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(bug_table)
            story.append(Spacer(1, 6))
    
    # -- FIX SUGGESTIONS --------------------------
    if fixes:
        story.append(Paragraph(
            "Fix Suggestions", heading_s))
        for i, fix in enumerate(fixes, 1):
            items = [
                Paragraph(
                    f"Fix #{i}: "
                    f"{fix.get('weak_point','')[:100]}",
                    make_style(f'FT{i}',
                        fontSize=9,
                        textColor=RED,
                        fontName='Helvetica-Bold',
                        spaceAfter=4)
                ),
                Paragraph(
                    f"Issue: {fix.get('issue','')}",
                    body_s),
                Paragraph(
                    f"Explanation: "
                    f"{fix.get('explanation','')}",
                    body_s),
            ]
            fix_code = fix.get('fix_code','')
            if fix_code and len(fix_code) > 10:
                items.append(Paragraph(
                    f"Fix: {fix_code[:400]}",
                    make_style(f'FC{i}',
                        fontSize=8,
                        textColor=DARK,
                        fontName='Courier',
                        spaceAfter=4,
                        backColor=LIGHT_GRAY,
                        leading=12)
                ))
            
            fix_content = [[item] for item in items]
            fix_table = Table(
                fix_content,
                colWidths=[5.5*inch])
            fix_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1),
                 colors.HexColor('#f8f8fc')),
                ('BOX', (0,0), (-1,-1), 0.5,
                 colors.HexColor('#e8e8f0')),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(fix_table)
            story.append(Spacer(1, 8))
    
    # -- FOOTER -----------------------------------
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor('#e8e8f0')))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Generated by BreakBot - "
        "AI Red-Team Security Agent | "
        f"{datetime.now().strftime('%B %d, %Y')}",
        footer_s))
    
    doc.build(story)
    return output_path


def calculate_security_score(
    weak_points: int,
    bugs: int,
    total_tests: int
) -> int:
    score = 100
    score -= weak_points * 5
    score -= bugs * 10
    if total_tests > 0:
        pass_rate = max(0,
            (total_tests - bugs) / total_tests)
        score = int(score * pass_rate)
    return max(0, min(100, score))


def get_score_label(score: int) -> str:
    if score >= 80: return "SECURE"
    elif score >= 60: return "MODERATE RISK"
    elif score >= 40: return "VULNERABLE"
    else: return "CRITICAL RISK"


def classify_severity(weak_point: str) -> str:
    text = weak_point.lower()
    if any(w in text for w in [
        'sql injection', 'injection', 'arbitrary code',
        'execution', 'password', 'credential',
        'overflow', 'authentication'
    ]):
        return "CRITICAL"
    elif any(w in text for w in [
        'division', 'crash', 'null', 'none',
        'error', 'exception', 'naming conflict',
        'syntax error', 'unsafe'
    ]):
        return "HIGH"
    elif any(w in text for w in [
        'truncat', 'file', 'resource', 'leak',
        'handle', 'type', 'index', 'boundary',
        'incomplete'
    ]):
        return "MEDIUM"
    else:
        return "LOW"