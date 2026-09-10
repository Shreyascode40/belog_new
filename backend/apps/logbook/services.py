import logging
from pathlib import Path
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class PDFGenerationError(Exception):
    pass


def _render_with_weasyprint(html, out_path):
    from weasyprint import HTML

    HTML(string=html, base_url=str(Path(settings.BASE_DIR))).write_pdf(str(out_path))


def _render_with_reportlab(group, logbook, out_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from apps.accounts.models import StudentProfile
    from apps.groups.models import GroupMember

    dept_name = getattr(group.department, "name", "Computer")
    ay_label = getattr(group.academic_year, "year_label", "")
    project = getattr(group, "project", None)
    project_title = getattr(project, "title", "") if project else "____________________"
    project_area = (
        getattr(project, "area_domain", "") if project else "________________"
    )
    guides = list(group.guide_assignments.all())
    guide_str = (
        ", ".join([g.faculty.email for g in guides]) if guides else "________________"
    )
    members = list(GroupMember.objects.filter(group=group).select_related("student"))

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        topMargin=14 * mm,
        bottomMargin=12 * mm,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        title=f"BE Logbook Group {group.group_number}",
    )
    styles = getSampleStyleSheet()
    s_title = ParagraphStyle(
        "TitleCenter",
        parent=styles["Heading1"],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=colors.HexColor("#0f2a6b"),
    )
    s_h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=10,
        backColor=colors.HexColor("#6b7c99"),
        textColor=colors.white,
        alignment=TA_CENTER,
        borderPadding=5,
        spaceBefore=8,
        spaceAfter=6,
    )
    s_h3 = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontSize=8.5,
        backColor=colors.HexColor("#e8edf3"),
        borderPadding=3,
        spaceBefore=6,
    )
    s_normal = ParagraphStyle(
        "Normal2", parent=styles["Normal"], fontSize=7.2, leading=9, alignment=TA_LEFT
    )
    s_small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#444444"),
    )
    s_cell = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=6.8, leading=8)
    s_cell_bold = ParagraphStyle("CellBold", parent=s_cell, fontName="Helvetica-Bold")

    def P(txt, style=s_normal):
        return Paragraph(txt, style)

    def cell(txt, bold=False):
        return Paragraph(txt, s_cell_bold if bold else s_cell)

    story = []

    def header_footer(canvas, doc):
        canvas.saveState()
        # top header box
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        canvas.rect(10 * mm, 277 * mm, 190 * mm, 14 * mm, stroke=1, fill=0)
        canvas.line(10 * mm, 284 * mm, 200 * mm, 284 * mm)
        canvas.line(45 * mm, 277 * mm, 45 * mm, 291 * mm)
        canvas.line(155 * mm, 277 * mm, 155 * mm, 291 * mm)
        canvas.setFont("Helvetica", 6)
        canvas.drawCentredString(27.5 * mm, 287 * mm, "LOGO")
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawCentredString(
            100 * mm, 288 * mm, "Akhil Bharatiya Maratha Shikshan Parishad's"
        )
        canvas.drawCentredString(
            100 * mm, 285 * mm, "Anantrao Pawar College of Engineering & Research"
        )
        canvas.setFont("Helvetica", 6)
        canvas.drawCentredString(177.5 * mm, 287 * mm, "Photo")
        canvas.setFont("Helvetica", 5)
        canvas.drawString(11 * mm, 279 * mm, "Record No.: ACA/D/003B   Revision: 00")
        canvas.drawRightString(199 * mm, 279 * mm, "DoI: 01/02/2025")
        canvas.setFillColor(colors.HexColor("#6b7c99"))
        canvas.rect(10 * mm, 272 * mm, 190 * mm, 5 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawCentredString(105 * mm, 273.5 * mm, "Project Diary")
        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica", 5.5)
        gen = logbook.generated_at.strftime("%d/%m/%Y") if logbook.generated_at else ""
        canvas.drawCentredString(
            105 * mm,
            8 * mm,
            f"Page {doc.page}  —  Generated on {gen}  v{logbook.version}",
        )
        canvas.restoreState()

    # COVER
    story.append(P(f"Department of {dept_name} Engineering", s_title))
    story.append(P(f"BE PROJECT LOG BOOK &nbsp; A.Y. {ay_label}", s_title))
    story.append(Spacer(1, 6 * mm))
    # building photo placeholder
    photo_tbl = Table(
        [[P("[ College Building Photo ]", s_small)]],
        colWidths=[190 * mm],
        rowHeights=[28 * mm],
    )
    photo_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")),
            ]
        )
    )
    story.append(photo_tbl)
    story.append(Spacer(1, 4 * mm))
    cover_data = [
        [P(f"<b>Project Title:</b> {project_title}", s_normal)],
        [P(f"<b>Area of Project:</b> {project_area}", s_normal)],
        [P(f"<b>Project Guide:</b> {guide_str}", s_normal)],
    ]
    t = Table(cover_data, colWidths=[190 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d6e9d6")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2e7d32")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#a0a0a0")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 3 * mm))
    gtbl = Table(
        [[P(f"<b>Group No.: {group.group_number}</b>", s_title)]], colWidths=[190 * mm]
    )
    gtbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e0e0e0")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(gtbl)
    story.append(PageBreak())

    # Rules - 13 verbatim
    story.append(P("Rules & Regulations", s_h2))
    rules = [
        "Students should maintain the log book regularly and produce it whenever demanded by guide/HOD.",
        "Entries should be made in chronological order with date and signature of student and guide.",
        "All activities, meetings, and decisions must be recorded with proper dates.",
        "Project work should be carried out as per the approved schedule.",
        "Weekly meeting with guide is mandatory and must be recorded.",
        "Any change in topic/scope must be approved by guide and HOD.",
        "Attendance in reviews is compulsory for all members.",
        "Plagiarism in report/paper is strictly prohibited.",
        "Maintain proper versioning of documents and code.",
        "Competition/paper details must be entered with proof.",
        "Term-I and Term-II checklists must be completed before submission.",
        "Sponsored projects must maintain meeting records with company.",
        "Final logbook must be verified by guide and HOD before submission.",
    ]
    for idx, r in enumerate(rules, 1):
        story.append(P(f"<b>{idx}.</b> {r}", s_normal))
        story.append(Spacer(1, 1.2 * mm))
    story.append(PageBreak())

    # Group Information 2 per page
    story.append(P("Project Group Information", s_h2))
    for idx, m in enumerate(members):
        try:
            prof = StudentProfile.objects.get(user=m.student)
            name = prof.name or m.student.email
            roll = prof.roll_number or "______"
            mobile = prof.mobile or "______"
            seat = prof.exam_seat_number or "______"
            email = prof.email or m.student.email
        except:
            name = m.student.email
            roll = mobile = seat = "______"
            email = m.student.email
        header = P(
            f"Member {idx + 1} {'(Leader)' if m.role == 'leader' else ''} — {name}",
            s_cell_bold,
        )
        tdata = [
            [header, "", P("Photo", s_small)],
            [
                cell(f"<b>Name:</b> {name}"),
                cell("TE Result: ______"),
                cell("Affix your<br/>photo here", True),
            ],
            [
                cell(f"<b>Roll No.:</b> {roll}"),
                cell(f"<b>Mobile No.:</b> {mobile}"),
                cell(""),
            ],
            [
                cell(f"<b>Exam Seat No.:</b> {seat}"),
                cell(f"<b>Email ID:</b> {email}"),
                cell(""),
            ],
            [
                cell(f"<b>Contribution:</b> ________________________________"),
                cell(""),
                cell(""),
            ],
        ]
        tbl = Table(
            tdata,
            colWidths=[65 * mm, 65 * mm, 60 * mm],
            rowHeights=[7 * mm, 7 * mm, 7 * mm, 7 * mm, 7 * mm],
        )
        tbl.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#999999")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d6e9d6")),
                    ("SPAN", (2, 1), (2, 2)),
                    ("ALIGN", (2, 1), (2, 2), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (2, 1), (2, 2), colors.HexColor("#f0f0f0")),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 3 * mm))
        if (idx + 1) % 2 == 0 and idx + 1 != len(members):
            story.append(PageBreak())
            story.append(P("Project Group Information (contd.)", s_h2))
    story.append(PageBreak())

    # Undertaking
    story.append(P("Undertaking by Students", s_h2))
    story.append(
        P(
            f'We, the students of B.E. {dept_name} batch {ay_label} hereby assure that the project entitled <b>"{project_title}"</b> is our original work carried out under the guidance of our project guide {guide_str}. We have maintained the log book honestly.',
            s_normal,
        )
    )
    story.append(Spacer(1, 3 * mm))
    ut_data = [
        [
            cell("<b>Sr.</b>", True),
            cell("<b>Name</b>", True),
            cell("<b>Signature</b>", True),
        ]
    ]
    for i, m in enumerate(members, 1):
        try:
            name = StudentProfile.objects.get(user=m.student).name
        except:
            name = m.student.email
        gen = logbook.generated_at.strftime("%d/%m/%Y") if logbook.generated_at else ""
        ut_data.append(
            [cell(str(i)), cell(name), cell(f"Digitally Acknowledged on {gen}", True)]
        )
    ut = Table(ut_data, colWidths=[15 * mm, 85 * mm, 90 * mm])
    ut.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(ut)
    story.append(PageBreak())

    # Schedule Sem I & II
    story.append(P("B.E. Project Schedule — Sem I & II", s_h2))
    for sem, rows in [
        (
            "Semester I",
            [
                "Group formation & Project area finalization",
                "Literature survey & Topic finalization",
                "Requirement analysis & Feasibility study",
                "System design & UML diagrams",
                "Review - I",
                "Review - II",
                "Implementation (50% target)",
                "Term-I Final Review & Report",
            ],
        ),
        (
            "Semester II",
            [
                "Implementation (remaining)",
                "Testing (Alpha/Beta)",
                "Review - I (Term-II)",
                "Review - II (Term-II)",
                "Final Mock Evaluation",
                "Report writing & Paper publication",
                "Final Submission & External Evaluation",
            ],
        ),
    ]:
        story.append(P(sem, s_h3))
        sdata = [
            [
                cell("<b>Sr.</b>", True),
                cell("<b>Description</b>", True),
                cell("<b>Dates</b>", True),
            ]
        ]
        for i, desc in enumerate(rows, 1):
            # try to pull dates from stages if mapped
            sdata.append([cell(str(i)), cell(desc), cell("")])
        st = Table(sdata, colWidths=[12 * mm, 143 * mm, 35 * mm])
        st.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ]
            )
        )
        story.append(st)
        story.append(Spacer(1, 3 * mm))
    story.append(PageBreak())

    # Topic 1 & 2
    for topic_idx in [1, 2]:
        story.append(P(f"Finalization of Project Topic — Topic {topic_idx}", s_h2))
        ttitle = (
            project_title
            if topic_idx == 1
            else "________________________________________________"
        )
        story.append(P(f"<b>Proposed Topic:</b> {ttitle}", s_normal))
        story.append(Spacer(1, 2 * mm))
        pdata = [
            [
                cell("<b>Parameter</b>", True),
                cell("<b>Remarks</b>", True),
                cell("<b>Marks</b>", True),
            ]
        ]
        for param in [
            "Significance",
            "Innovativeness",
            "Scope",
            "Feasibility",
            "Approved (Y/N)",
        ]:
            pdata.append([cell(param), cell(""), cell("")])
        pt = Table(pdata, colWidths=[50 * mm, 100 * mm, 40 * mm])
        pt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(pt)
        story.append(Spacer(1, 3 * mm))
        story.append(
            P(
                "Reviewer 1: ________________ __________  &nbsp;&nbsp; Reviewer 2: ________________ __________<br/>Project Coordinator: ________________ __________ &nbsp;&nbsp; HOD: <i>Digitally approved by HOD on "
                + (
                    logbook.generated_at.strftime("%d/%m/%Y")
                    if logbook.generated_at
                    else ""
                )
                + "</i>",
                s_small,
            )
        )
        if topic_idx == 1:
            story.append(PageBreak())
    story.append(PageBreak())

    # Monthly Activity Charts (generate for June-May)
    from apps.projects.models import ProjectStage

    stages_qs = (
        list(group.academic_year.stages.all().order_by("order"))
        if hasattr(group.academic_year, "stages")
        else []
    )
    # fallback to all stages if not linked
    if not stages_qs:
        stages_qs = list(
            ProjectStage.objects.filter(academic_year=group.academic_year).order_by(
                "order"
            )
        )
    story.append(P("Monthly Activity Charts", s_h2))
    story.append(
        P(
            "5-column table: Date | Activity Planned | Complete/Incomplete | Signature of student | Signature of guide — rows match official June (Group Submission, Guide Allocation, Domain Finalization, 3x Guide Meetings) etc.",
            s_small,
        )
    )
    story.append(Spacer(1, 2 * mm))
    for mon in [
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
        "January",
        "February",
        "March",
    ]:
        adata = [
            [
                cell("<b>Date</b>", True),
                cell("<b>Activity Planned</b>", True),
                cell("<b>Complete/Incomplete</b>", True),
                cell("<b>Sign (Student)</b>", True),
                cell("<b>Sign (Guide)</b>", True),
            ]
        ]
        acts = (
            [
                "Group Submission",
                "Guide Allocation",
                "Domain Finalization",
                "Guide Meeting - Topic Finalization",
                "Guide Meeting - Topic Finalization",
                "Guide Meeting - Topic Finalization",
            ]
            if mon == "June"
            else ["Activity 1", "Activity 2", "Activity 3", "Activity 4"]
        )
        for a in acts:
            adata.append([cell(""), cell(a), cell(""), cell(""), cell("")])
        at = Table(adata, colWidths=[22 * mm, 68 * mm, 30 * mm, 35 * mm, 35 * mm])
        at.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("FONTSIZE", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(P(f"<b>{mon}</b>", s_h3))
        story.append(at)
        story.append(Spacer(1, 2 * mm))
    story.append(PageBreak())

    # RTM & Cost
    story.append(P("Requirement Traceability Matrix", s_h2))
    story.append(
        P(
            "(Student-uploaded RTM content — if not provided, section remains titled as in official format)",
            s_small,
        )
    )
    rtm = [
        [
            cell("<b>Req ID</b>", True),
            cell("<b>Requirement</b>", True),
            cell("<b>Design Ref</b>", True),
            cell("<b>Test Ref</b>", True),
        ],
        [cell("R1"), cell(""), cell(""), cell("")],
        [cell("R2"), cell(""), cell(""), cell("")],
    ]
    rt = Table(rtm, colWidths=[20 * mm, 70 * mm, 50 * mm, 50 * mm])
    rt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(rt)
    story.append(Spacer(1, 4 * mm))
    story.append(P("Project Cost Estimation", s_h2))
    cdata = [
        [
            cell("<b>Sr.</b>", True),
            cell("<b>Item</b>", True),
            cell("<b>Cost (Rs.)</b>", True),
        ],
        [cell("1"), cell("Hardware"), cell("")],
        [cell("2"), cell("Software"), cell("")],
        [cell("3"), cell("Other"), cell("")],
        [cell(""), cell("<b>Total</b>", True), cell("")],
    ]
    ct = Table(cdata, colWidths=[15 * mm, 100 * mm, 75 * mm])
    ct.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(ct)
    story.append(PageBreak())

    # FACULTY GRADES - Detailed Criterion Marks (new, shows actual faculty-entered grades)
    story.append(P("Faculty Grades — Detailed Criterion Marks", s_h2))
    story.append(
        P(
            "Grades below are the actual marks entered by Guide/Reviewer per criterion. Each row shows Max marks, Obtained, Reviewer and Criterion. Totals feed into the 50/100 summary tables.",
            s_small,
        )
    )
    story.append(Spacer(1, 2 * mm))
    from apps.reviews.models import Review, ReviewCriterion, Mark

    reviews_qs = Review.objects.filter(group=group).order_by("review_number")
    if reviews_qs.exists():
        for rev in reviews_qs:
            story.append(
                P(
                    f"Review {rev.review_number} — {rev.get_review_number_display() if hasattr(rev, 'get_review_number_display') else ''} ({rev.status}) — {rev.review_date}",
                    s_h3,
                )
            )
            crits = ReviewCriterion.objects.filter(review=rev).order_by("order")
            if crits.exists():
                gdata = [
                    [
                        cell("<b>Criterion</b>", True),
                        cell("<b>Max</b>", True),
                        cell("<b>Obtained</b>", True),
                        cell("<b>Reviewer</b>", True),
                        cell("<b>Remarks</b>", True),
                    ]
                ]
                for c in crits:
                    mk = Mark.objects.filter(criterion=c, group=group).first()
                    obt = (
                        str(mk.obtained_marks).rstrip("0").rstrip(".")
                        if mk and "." in str(mk.obtained_marks)
                        else str(mk.obtained_marks)
                        if mk
                        else "—"
                    )
                    rev_name = (
                        mk.reviewer.email
                        if mk and mk.reviewer
                        else rev.reviewer.email
                        if rev.reviewer
                        else "—"
                    )
                    gdata.append(
                        [
                            cell(c.name),
                            cell(str(c.max_marks)),
                            cell(obt),
                            cell(rev_name),
                            cell(mk.remarks if mk and mk.remarks else ""),
                        ]
                    )
                gt = Table(
                    gdata, colWidths=[70 * mm, 20 * mm, 20 * mm, 45 * mm, 35 * mm]
                )
                gt.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                            ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                        ]
                    )
                )
                story.append(gt)
                story.append(Spacer(1, 3 * mm))
            else:
                story.append(P("No criteria configured for this review.", s_small))
        story.append(Spacer(1, 2 * mm))
    else:
        story.append(
            P(
                "No reviews configured yet — grades will appear here once faculty enters marks and finalizes.",
                s_small,
            )
        )
        story.append(Spacer(1, 3 * mm))
    story.append(PageBreak())

    # TERM-I REVIEWS
    story.append(P("BE Project (Term-I) Review — I", s_h2))
    story.append(
        P(
            "Problem Statement / Motivation / Objectives / Literature Review (10 questions)",
            s_small,
        )
    )
    q1 = [
        "Is problem statement clearly defined?",
        "Is motivation clearly stated?",
        "Are objectives clearly defined?",
        "Is literature survey adequate?",
        "Is gap identified?",
        "Is methodology appropriate?",
        "Is scope defined?",
        "Is feasibility considered?",
        "Is presentation clear?",
        "Overall understanding?",
    ]
    # Try to fill with actual faculty grades if Review 1 criteria exist
    rev1 = next((r for r in reviews_qs if r.review_number == 1), None)
    rev1_crits = (
        list(ReviewCriterion.objects.filter(review=rev1).order_by("order"))
        if rev1
        else []
    )
    if rev1_crits:
        r1 = [
            [
                cell("<b>#</b>", True),
                cell("<b>Question / Criterion</b>", True),
                cell("<b>Max</b>", True),
                cell("<b>Obtained</b>", True),
                cell("<b>Remark</b>", True),
            ]
        ]
        for idx, c in enumerate(rev1_crits, 1):
            mk = Mark.objects.filter(criterion=c, group=group).first()
            obt = (
                str(mk.obtained_marks).rstrip("0").rstrip(".")
                if mk and "." in str(mk.obtained_marks)
                else str(mk.obtained_marks)
                if mk
                else "—"
            )
            r1.append(
                [
                    cell(str(idx)),
                    cell(c.name),
                    cell(str(c.max_marks)),
                    cell(obt),
                    cell(mk.remarks if mk else ""),
                ]
            )
        rt1 = Table(r1, colWidths=[10 * mm, 85 * mm, 20 * mm, 20 * mm, 55 * mm])
    else:
        r1 = [
            [
                cell("<b>#</b>", True),
                cell("<b>Question</b>", True),
                cell("<b>Remark / Grade</b>", True),
                cell("<b>Sign of Guide</b>", True),
            ]
        ]
        for i, q in enumerate(q1, 1):
            r1.append([cell(str(i)), cell(q), cell(""), cell("")])
        rt1 = Table(r1, colWidths=[10 * mm, 110 * mm, 35 * mm, 35 * mm])
    rt1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ]
        )
    )
    story.append(rt1)
    story.append(
        P(
            "Reviewer 1: ________________ &nbsp;&nbsp; Reviewer 2: ________________",
            s_small,
        )
    )
    story.append(PageBreak())

    story.append(
        P("BE Project (Term-I) Review — II (Feasibility & Scope — 12 questions)", s_h2)
    )
    r2 = [
        [
            cell("<b>#</b>", True),
            cell("<b>Question</b>", True),
            cell("<b>Remark</b>", True),
            cell("<b>Sign</b>", True),
        ]
    ]
    for i in range(1, 13):
        r2.append([cell(str(i)), cell(f"Feasibility question {i}"), cell(""), cell("")])
    rt2 = Table(r2, colWidths=[10 * mm, 110 * mm, 35 * mm, 35 * mm])
    rt2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(rt2)
    story.append(PageBreak())

    story.append(
        P("BE Project Mock (Term-I) Final Review — Design (17 questions)", s_h2)
    )
    rd = [
        [
            cell("<b>#</b>", True),
            cell("<b>Question (UML, class diagrams, state charts, DFDs...)</b>", True),
            cell("<b>Remark</b>", True),
            cell("<b>Sign</b>", True),
        ]
    ]
    for i in range(1, 18):
        rd.append(
            [
                cell(str(i)),
                cell(
                    f"Design question {i} — Is it cleat which classes provide which services (verbatim)"
                ),
                cell(""),
                cell(""),
            ]
        )
    rdt = Table(rd, colWidths=[10 * mm, 110 * mm, 35 * mm, 35 * mm])
    rdt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(rdt)
    story.append(PageBreak())

    story.append(P("BE Project Mock (Term-I) Final Review — Marks Table (50)", s_h2))
    from apps.reviews.models import Mark, ReviewCriterion

    hdr = [
        cell("<b>Name</b>", True),
        cell("<b>Problem<br/>(05)</b>", True),
        cell("<b>Lit.<br/>(05)</b>", True),
        cell("<b>Req.<br/>(10)</b>", True),
        cell("<b>Planning<br/>(05)</b>", True),
        cell("<b>Presentation<br/>(10)</b>", True),
        cell("<b>Report<br/>(10)</b>", True),
        cell("<b>Total<br/>(50)</b>", True),
    ]
    mdata = [hdr]

    # map criterion names to columns for Term-I 50 marks table
    def get_mark_for_member_criterion(member, crit_name_contains):
        try:
            crit = ReviewCriterion.objects.filter(
                review__group=group, name__icontains=crit_name_contains
            ).first()
            if crit:
                mk = Mark.objects.filter(
                    group=group, criterion=crit, reviewer__isnull=False
                ).first()
                # fallback: any mark for this student's group and criterion
                # Marks are per group, not per student individually in current model, so show group mark
                if mk:
                    return (
                        str(mk.obtained_marks).rstrip("0").rstrip(".")
                        if "." in str(mk.obtained_marks)
                        else str(mk.obtained_marks)
                    )
        except:
            pass
        return ""

    for m in members:
        try:
            name = StudentProfile.objects.get(user=m.student).name
        except:
            name = m.student.email[:12]
        row = [cell(name)]
        for kw in [
            "Problem",
            "Literature",
            "Requirement",
            "Planning",
            "Presentation",
            "Report",
        ]:
            row.append(cell(get_mark_for_member_criterion(m, kw)))
        # total
        try:
            total = sum(
                float(
                    Mark.objects.filter(group=group, criterion__name__icontains=kw)
                    .first()
                    .obtained_marks
                )
                for kw in [
                    "Problem",
                    "Literature",
                    "Requirement",
                    "Planning",
                    "Presentation",
                    "Report",
                ]
                if Mark.objects.filter(
                    group=group, criterion__name__icontains=kw
                ).first()
            )
            total_str = str(int(total)) if total == int(total) else str(round(total, 1))
        except:
            total_str = ""
        row.append(cell(total_str))
        mdata.append(row)
    mt = Table(mdata, colWidths=[32 * mm] + [22.5 * mm] * 7)
    mt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(mt)
    story.append(
        P(
            "Evaluation Committee: ________________ &nbsp;&nbsp; ________________ &nbsp;&nbsp; ________________",
            s_small,
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(P("BE Project Term-I Submission Check List", s_h3))
    for txt in [
        "Log book duly filled and signed",
        "Partial report submitted",
        "Presentation ready",
        "Attendance in reviews",
        "Guide approval obtained",
    ]:
        story.append(P(f"☐ {txt}", s_normal))
    story.append(Spacer(1, 3 * mm))
    story.append(P("External Examiner Feedback (Term-I)", s_h3))
    story.append(
        P(
            f"<b>Project:</b> {project_title} &nbsp; <b>Date:</b> {logbook.generated_at.strftime('%d/%m/%Y') if logbook.generated_at else ''}",
            s_normal,
        )
    )
    ef = [
        [
            cell("<b>#</b>", True),
            cell("<b>Parameter</b>", True),
            cell("<b>Excellent</b>", True),
            cell("<b>Good</b>", True),
            cell("<b>Satisfactory</b>", True),
        ]
    ]
    for i in range(1, 10):
        ef.append(
            [
                cell(str(i)),
                cell(f"Feedback parameter {i}"),
                cell("☐"),
                cell("☐"),
                cell("☐"),
            ]
        )
    eft = Table(ef, colWidths=[10 * mm, 80 * mm, 30 * mm, 30 * mm, 30 * mm])
    eft.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(eft)
    story.append(
        P(
            "Remarks: _________________________________________________________________<br/>External: ________________ &nbsp;&nbsp; Internal: ________________",
            s_small,
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(P("Participation in Project Competition / Paper Publication", s_h3))
    comp = [
        [
            cell("<b>Competition</b>", True),
            cell("<b>Date</b>", True),
            cell("<b>College</b>", True),
            cell("<b>Type</b>", True),
            cell("<b>Award</b>", True),
        ],
        [cell("") for _ in range(5)],
    ]
    ct1 = Table(comp, colWidths=[50 * mm, 25 * mm, 50 * mm, 30 * mm, 35 * mm])
    ct1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(ct1)
    paper = [
        [
            cell("<b>Paper Title</b>", True),
            cell("<b>Conference</b>", True),
            cell("<b>ISSN</b>", True),
            cell("<b>Vol</b>", True),
            cell("<b>Pages</b>", True),
        ],
        [cell("") for _ in range(5)],
    ]
    pt1 = Table(paper, colWidths=[50 * mm, 50 * mm, 30 * mm, 25 * mm, 35 * mm])
    pt1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(pt1)
    story.append(PageBreak())

    # TERM-II
    story.append(P("BE Project (Term-II) Review I — Modeling (13 questions)", s_h2))
    tr = [
        [
            cell("<b>#</b>", True),
            cell("<b>Modeling question</b>", True),
            cell("<b>Remark</b>", True),
            cell("<b>Sign</b>", True),
        ]
    ]
    for i in range(1, 14):
        tr.append([cell(str(i)), cell(f"Modeling Q{i}"), cell(""), cell("")])
    trt = Table(tr, colWidths=[10 * mm, 110 * mm, 35 * mm, 35 * mm])
    trt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(trt)
    story.append(PageBreak())
    story.append(
        P(
            "BE Project (Term-II) Review II — Coding / Implementation (10 questions)",
            s_h2,
        )
    )
    cr = [
        [
            cell("<b>#</b>", True),
            cell("<b>Question</b>", True),
            cell("<b>Date/Remark</b>", True),
            cell("<b>Sign</b>", True),
        ]
    ]
    for i in range(1, 11):
        cr.append([cell(str(i)), cell(f"Coding Q{i}"), cell(""), cell("")])
    crt = Table(cr, colWidths=[10 * mm, 110 * mm, 35 * mm, 35 * mm])
    crt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(crt)
    story.append(PageBreak())
    story.append(P("Validation and Testing (9 questions)", s_h3))
    vt = [
        [
            cell("<b>#</b>", True),
            cell(
                "<b>Question (alpha/beta, GUI, usability, datasets, real-time, integration, repository)</b>",
                True,
            ),
            cell("<b>Remark</b>", True),
        ]
    ]
    for i in range(1, 10):
        vt.append([cell(str(i)), cell(f"Testing Q{i}"), cell("")])
    vtt = Table(vt, colWidths=[10 * mm, 130 * mm, 50 * mm])
    vtt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(vtt)
    story.append(P("Report Writing (9 questions)", s_h3))
    rw = [
        [
            cell("<b>#</b>", True),
            cell(
                "<b>Question (format, plagiarism, precision, figures, citations)</b>",
                True,
            ),
            cell("<b>Remark</b>", True),
        ]
    ]
    for i in range(1, 10):
        rw.append([cell(str(i)), cell(f"Report Q{i}"), cell("")])
    rwt = Table(rw, colWidths=[10 * mm, 130 * mm, 50 * mm])
    rwt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(rwt)
    story.append(PageBreak())
    story.append(P("Final Evaluation of Project — Marks Table (100)", s_h2))
    fh = [
        cell("<b>Name</b>", True),
        cell("<b>Modeling<br/>(10)</b>", True),
        cell("<b>Coding<br/>(40)</b>", True),
        cell("<b>Testing<br/>(10)</b>", True),
        cell("<b>Understanding<br/>(10)</b>", True),
        cell("<b>Team<br/>(10)</b>", True),
        cell("<b>Demo<br/>(10)</b>", True),
        cell("<b>Report<br/>(10)</b>", True),
        cell("<b>Total<br/>(100)</b>", True),
    ]
    fd = [fh]

    def get_mark_100(member, kw):
        try:
            crit = ReviewCriterion.objects.filter(
                review__group=group, name__icontains=kw
            ).first()
            if crit:
                mk = Mark.objects.filter(group=group, criterion=crit).first()
                if mk:
                    return (
                        str(mk.obtained_marks).rstrip("0").rstrip(".")
                        if "." in str(mk.obtained_marks)
                        else str(mk.obtained_marks)
                    )
        except:
            pass
        return ""

    for m in members:
        try:
            name = StudentProfile.objects.get(user=m.student).name
        except:
            name = m.student.email[:12]
        row = [cell(name)]
        for kw in [
            "Modeling",
            "Coding",
            "Testing",
            "Understanding",
            "Team",
            "Demo",
            "Report",
        ]:
            row.append(cell(get_mark_100(m, kw)))
        try:
            total = sum(
                float(
                    Mark.objects.filter(group=group, criterion__name__icontains=kw)
                    .first()
                    .obtained_marks
                )
                for kw in [
                    "Modeling",
                    "Coding",
                    "Testing",
                    "Understanding",
                    "Team",
                    "Demo",
                    "Report",
                ]
                if Mark.objects.filter(
                    group=group, criterion__name__icontains=kw
                ).first()
            )
            total_str = str(int(total)) if total == int(total) else str(round(total, 1))
        except:
            total_str = ""
        row.append(cell(total_str))
        fd.append(row)
    ft = Table(fd, colWidths=[28 * mm] + [20 * mm] * 8)
    ft.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ]
        )
    )
    story.append(ft)
    story.append(
        P(
            "Evaluation Committee: ________________ &nbsp;&nbsp; ________________ &nbsp;&nbsp; ________________",
            s_small,
        )
    )
    story.append(PageBreak())
    story.append(P("BE Project Term-II Submission — Check List", s_h2))
    for txt in [
        "Log book completed",
        "Final report submitted",
        "CD contents: report PDF, PPT, source code, paper, certificates, etc. (9 items)",
        "Guide/HOD approval",
        "External evaluation",
        "Attendance",
        "Plagiarism check",
        "Fee clearance",
    ]:
        story.append(P(f"☐ {txt}", s_normal))
    # Sponsored conditional
    if getattr(project, "is_sponsored", False):
        story.append(PageBreak())
        story.append(P("For Sponsored Project — Meeting Details", s_h2))
        sm = [
            [
                cell("<b>Date</b>", True),
                cell("<b>Discussion</b>", True),
                cell("<b>Sign (Company)</b>", True),
                cell("<b>Sign (Guide)</b>", True),
            ],
            [cell("") for _ in range(4)],
        ]
        smt = Table(sm, colWidths=[30 * mm, 80 * mm, 40 * mm, 40 * mm])
        smt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ]
            )
        )
        story.append(smt)
        story.append(
            P("Sponsored Project Feedback (7 parameters — High/Medium/Low)", s_h3)
        )
        sp = [
            [
                cell("<b>Parameter</b>", True),
                cell("<b>High</b>", True),
                cell("<b>Medium</b>", True),
                cell("<b>Low</b>", True),
            ]
        ]
        for i in range(1, 8):
            sp.append([cell(f"Param {i}"), cell("☐"), cell("☐"), cell("☐")])
        spt = Table(sp, colWidths=[70 * mm, 40 * mm, 40 * mm, 40 * mm])
        spt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ]
            )
        )
        story.append(spt)
        story.append(
            P(
                "Company: ________________ &nbsp;&nbsp; Reporting Authority: ________________ <i>Seal/Signature</i>",
                s_small,
            )
        )
    # End
    story.append(Spacer(1, 6 * mm))
    story.append(
        P(
            "— End of Official Log Book — Version " + str(logbook.version) + " —",
            ParagraphStyle(
                "End",
                parent=s_small,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#777777"),
            ),
        )
    )

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)


def generate_pdf(group, logbook):
    from apps.accounts.models import StudentProfile
    from apps.projects.models import ProjectStage
    from apps.reviews.models import Review
    from apps.groups.models import GroupMember

    members = GroupMember.objects.filter(group=group).select_related("student")
    member_data = []
    for m in members:
        try:
            prof = StudentProfile.objects.get(user=m.student)
            member_data.append({"user": m.student, "profile": prof, "role": m.role})
        except:
            member_data.append({"user": m.student, "profile": None, "role": m.role})
    stages = list(
        ProjectStage.objects.filter(academic_year=group.academic_year).order_by("order")
    )
    if not stages:
        stages = list(ProjectStage.objects.all().order_by("order"))
    reviews = list(Review.objects.filter(group=group).order_by("review_number"))
    # Build faculty grades for HTML
    from apps.reviews.models import ReviewCriterion, Mark

    reviews_with_marks = []
    for rev in reviews:
        crits = list(ReviewCriterion.objects.filter(review=rev).order_by("order"))
        crit_data = []
        for c in crits:
            mk = Mark.objects.filter(criterion=c, group=group).first()
            crit_data.append({"criterion": c, "mark": mk})
        reviews_with_marks.append({"review": rev, "criteria": crit_data})
    ctx = {
        "group": group,
        "project": getattr(group, "project", None),
        "academic_year": group.academic_year,
        "department": group.department,
        "members": member_data,
        "stages": stages,
        "reviews": reviews,
        "reviews_with_marks": reviews_with_marks,
        "is_sponsored": getattr(group.project, "is_sponsored", False)
        if hasattr(group, "project") and group.project
        else False,
        "record_no": "ACA/D/003B",
        "revision": "00",
        "doi": "01/02/2025",
        "college_line1": "Akhil Bharatiya Maratha Shikshan Parishad's",
        "college_line2": "Anantrao Pawar College of Engineering & Research",
        "generated_on": logbook.generated_at.strftime("%d/%m/%Y")
        if logbook.generated_at
        else "",
        "version": logbook.version,
    }
    from django.template.loader import render_to_string

    html = render_to_string("logbook/official.html", ctx)
    out_path = (
        Path(settings.MEDIA_ROOT)
        / "final_logbooks"
        / f"group_{group.id}_v{logbook.version}.pdf"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    last_exc = None
    for renderer, fn in [
        ("weasyprint", lambda: _render_with_weasyprint(html, out_path)),
        ("reportlab", lambda: _render_with_reportlab(group, logbook, out_path)),
    ]:
        try:
            fn()
            with open(out_path, "rb") as f:
                header = f.read(5)
                if header != b"%PDF-":
                    raise PDFGenerationError(
                        f"{renderer} produced invalid PDF header: {header!r}"
                    )
                f.seek(0, 2)
                if f.tell() < 1024:
                    raise PDFGenerationError(f"{renderer} produced trivially small PDF")
            logger.info(
                f"PDF generated via {renderer} for group {group.id} v{logbook.version}"
            )
            return (
                str(out_path.relative_to(settings.MEDIA_ROOT))
                if str(out_path).startswith(str(settings.MEDIA_ROOT))
                else str(out_path)
            )
        except Exception as e:
            last_exc = e
            logger.warning(
                f"PDF renderer {renderer} failed for group {group.id}: {e}",
                exc_info=True,
            )
            if out_path.exists():
                try:
                    out_path.unlink()
                except:
                    pass
            continue
    raise PDFGenerationError(
        f"Log book generation is temporarily unavailable, please contact IT/admin. Renderer error: {last_exc}"
    )


def health_check():
    test_html = "<html><body><h1>health check</h1><p>test</p></body></html>"
    tmp = Path(settings.MEDIA_ROOT) / "final_logbooks" / "_health_check.pdf"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        try:
            from weasyprint import HTML

            HTML(string=test_html).write_pdf(str(tmp))
            ok = True
        except Exception:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4

            c = canvas.Canvas(str(tmp), pagesize=A4)
            c.drawString(50, 800, "health")
            c.save()
            ok = True
        with open(tmp, "rb") as f:
            ok = ok and f.read(5) == b"%PDF-"
        tmp.unlink(missing_ok=True)
        return ok
    except Exception as e:
        logger.error(f"PDF health check failed: {e}", exc_info=True)
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return False
