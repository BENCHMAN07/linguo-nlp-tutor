"""Build the Linguo course project report as a formatted Word document."""
from __future__ import annotations

import os
from pathlib import Path
from textwrap import wrap

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Linguo_NLP_Project_Report.docx"
ASSETS = ROOT / "report_assets"
ASSETS.mkdir(exist_ok=True)
NAVY = "123B4A"
TEAL = "147D83"
AMBER = "E9A23B"
PALE = "EAF3F2"
INK = "20323B"
MUTED = "60737C"


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def diagram(path: Path, title: str, boxes: list[tuple[str, str]], arrows: bool = True):
    width, height = 1500, 330
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((52, 28), title, font=font(31, True), fill=f"#{NAVY}")
    n = len(boxes)
    gap = 24
    box_w = (width - 104 - gap * (n - 1)) // n
    y0, y1 = 105, 260
    for i, (heading, sub) in enumerate(boxes):
        x0 = 52 + i * (box_w + gap)
        x1 = x0 + box_w
        draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=f"#{PALE}", outline=f"#{TEAL}", width=3)
        draw.text((x0 + 18, y0 + 19), heading, font=font(23, True), fill=f"#{NAVY}")
        yy = y0 + 58
        for line in wrap(sub, max(16, box_w // 11))[:3]:
            draw.text((x0 + 18, yy), line, font=font(18), fill=f"#{INK}")
            yy += 25
        if arrows and i < n - 1:
            ax = x1 + 2
            bx = x1 + gap - 3
            cy = (y0 + y1) // 2
            draw.line((ax, cy, bx, cy), fill=f"#{AMBER}", width=5)
            draw.polygon([(bx, cy), (bx - 12, cy - 9), (bx - 12, cy + 9)], fill=f"#{AMBER}")
    img.save(path)


def shade(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: str, bold=False, color=INK, size=9):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def page_field(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = " PAGE "
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    value = OxmlElement("w:t"); value.text = "1"
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, value, end):
        run._r.append(element)


def add_para(doc, text, *, bold_lead=None, italic=False, after=6):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(after)
    if bold_lead and text.startswith(bold_lead):
        p.add_run(bold_lead).bold = True
        p.add_run(text[len(bold_lead):])
    else:
        run = p.add_run(text)
        run.italic = italic
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level)
    p.paragraph_format.keep_with_next = True
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(3)
    p.add_run(text)
    return p


def figure(doc, path: Path, label: str, width=6.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    run = cap.add_run(label)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor.from_string(MUTED)


def table(doc, headers, rows, widths=None, size=8):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    for i, label in enumerate(headers):
        set_cell_text(t.rows[0].cells[i], label, True, "FFFFFF", size)
        shade(t.rows[0].cells[i], NAVY)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], str(value), False, INK, size)
            if ri % 2 == 1:
                shade(cells[i], "F2F6F6")
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    return t


def add_code(doc, code):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(.22)
    p.paragraph_format.right_indent = Inches(.15)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(7)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), "F0F4F4"); pPr.append(shd)
    r = p.add_run(code)
    r.font.name = "Consolas"; r.font.size = Pt(8); r.font.color.rgb = RGBColor.from_string(NAVY)


def capture_screenshots():
    from playwright.sync_api import sync_playwright
    base = os.environ.get("LINGUO_REPORT_URL", "http://127.0.0.1:8123")
    outputs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 960}, device_scale_factor=1)
        page.add_init_script("localStorage.setItem('linguo-player', 'Demo Asha')")
        page.goto(base, wait_until="networkidle")
        page.wait_for_timeout(800)
        home = ASSETS / "linguo_home_screenshot.png"
        page.screenshot(path=str(home), full_page=True)
        outputs.append(home)
        page.goto(base + "/#teacher", wait_until="networkidle")
        page.wait_for_timeout(600)
        teacher = ASSETS / "linguo_teacher_screenshot.png"
        page.screenshot(path=str(teacher), full_page=True)
        outputs.append(teacher)
        page.goto(base + "/#practice", wait_until="networkidle")
        page.wait_for_timeout(500)
        practice = ASSETS / "linguo_practice_screenshot.png"
        page.screenshot(path=str(practice), full_page=True)
        outputs.append(practice)
        browser.close()
    return outputs


def build():
    arch = ASSETS / "architecture.png"
    flow = ASSETS / "workflow.png"
    pipeline = ASSETS / "data_pipeline.png"
    diagram(arch, "Linguo system architecture", [
        ("Learner", "Browser forms and course questions"),
        ("FastAPI", "Routes, validation and application logic"),
        ("NLP layer", "NLTK, spaCy option and TF-IDF"),
        ("Data stores", "Lecture JSON and SQLite progress"),
        ("Results", "Feedback, citations and dashboard"),
    ])
    diagram(flow, "Practice and answer workflow", [
        ("1 · Input", "Question, phrase or two sentences"),
        ("2 · Prepare", "Tokenize and validate the request"),
        ("3 · Process", "Apply rule, parser or vector method"),
        ("4 · Respond", "Return result or grounded passage"),
        ("5 · Record", "Award XP and save progress"),
    ])
    diagram(pipeline, "Course material pipeline", [
        ("Source pages", "Course site, respectful crawl"),
        ("Normalize", "Extract lecture sections and metadata"),
        ("Build", "Create sourced question bank"),
        ("Retrieve", "TF-IDF rank of lecture passages"),
        ("Cite", "Return passage with source URL"),
    ])
    screenshots = capture_screenshots()

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(.72); sec.bottom_margin = Inches(.7)
    sec.left_margin = Inches(.82); sec.right_margin = Inches(.82)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"; normal.font.size = Pt(11); normal.font.color.rgb = RGBColor.from_string(INK)
    normal.paragraph_format.line_spacing = 1.5; normal.paragraph_format.space_after = Pt(6)
    for name, size, color in [("Heading 1", 17, NAVY), ("Heading 2", 13, TEAL), ("Heading 3", 11, NAVY)]:
        st = styles[name]; st.font.name = "Times New Roman"; st.font.size = Pt(size); st.font.bold = True; st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before = Pt(8); st.paragraph_format.space_after = Pt(5)
    header = sec.header.paragraphs[0]
    header.text = "LINGUO  |  COMPUTATIONAL LINGUISTICS PROJECT"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for r in header.runs:
        r.font.name = "Times New Roman"; r.font.size = Pt(8); r.font.color.rgb = RGBColor.from_string(MUTED)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Linguo · Academic Year 2026–2027  |  ")
    page_field(footer)
    for r in footer.runs:
        r.font.size = Pt(8); r.font.color.rgb = RGBColor.from_string(MUTED)

    # Cover
    for _ in range(3): doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("LINGUO"); r.bold = True; r.font.name = "Times New Roman"; r.font.size = Pt(36); r.font.color.rgb = RGBColor.from_string(NAVY)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("A Source-Grounded Computational Linguistics Tutor"); r.font.size = Pt(19); r.font.color.rgb = RGBColor.from_string(TEAL)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(20)
    p.add_run("NLP PROJECT REPORT").bold = True
    for _ in range(2): doc.add_paragraph()
    cover_rows = [
        ("Course", "Natural Language Processing / Computational Linguistics"),
        ("Student(s)", "Aditya Muralidharan and Litesh T"),
        ("Class / Section", "AG1"),
        ("Faculty", "Rebecca Kennet"),
        ("Department / Institution", "DSBS · SRM University"),
        ("Academic Year", "2026–2027"),
    ]
    t = doc.add_table(rows=0, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.style = "Light Shading Accent 1"
    for k, v in cover_rows:
        c = t.add_row().cells; set_cell_text(c[0], k, True, NAVY, 11); set_cell_text(c[1], v, False, INK, 11)
        c[0].width = Inches(2.15); c[1].width = Inches(4.05)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(26)
    rr = p.add_run("DSBS · SRM University"); rr.font.size = Pt(11); rr.font.color.rgb = RGBColor.from_string(MUTED)

    doc.add_page_break()
    heading(doc, "2. Abstract")
    add_para(doc, "Linguo is a local-first web tutor that helps students explore computational linguistics through short lessons, sourced questions, and interactive NLP demonstrations. It addresses the difficulty of connecting abstract language concepts to visible, repeatable examples. The current corpus contains 38 English lecture levels from the 21CSE552T course; its question bank has 380 automatically scored multiple-choice items and 430 ungraded reflection prompts. FastAPI serves a browser interface, while NLTK, scikit-learn TF-IDF, an optional spaCy model, and a small context-free grammar support the demonstrations and retrieval. TF-IDF ranks lecture passages and returns source links; SQLite stores learner progress. The application includes tokenization, POS output, optional named-entity recognition, stemming and lemmatization comparison, sentence similarity, CFG parsing, practice, dashboards, and teacher summaries. All 10 existing automated tests passed; no predictive accuracy score is claimed because the project does not train a supervised classifier.")
    add_para(doc, "Keywords: computational linguistics, NLP education, TF-IDF, information retrieval, tokenization, grammar parsing.", italic=True)

    doc.add_page_break()
    heading(doc, "3. Introduction")
    add_para(doc, "Natural language processing combines language knowledge and computation to analyze or generate human language. Students meeting the field often encounter many separate terms—tokens, parts of speech, grammar rules, ambiguity, and meaning—without a compact environment for trying them and seeing what changes. Linguo is designed as a course companion that turns lecture ideas into small experiments and sourced practice.")
    add_para(doc, "The project’s aim is to provide a browser-based, local learning loop: introduce a course idea, demonstrate a related operation, let the learner practice, and retain progress. Its objectives are to (1) organize published course material into navigable lecture levels; (2) retrieve relevant passages and cite their original lecture pages; (3) expose selected NLP operations on user-entered English text; (4) provide sourced practice questions and ungraded discussion prompts; and (5) display learner and class-level progress.")
    add_para(doc, "The intended users are students studying the computational linguistics course and an instructor reviewing a small demonstration class. Linguo accepts typed English text and course questions. It does not process speech, conduct unrestricted multilingual analysis, or replace instructor feedback. The expected outcome is a working local web application in which learners can inspect text processing, practice course vocabulary, and see their activity reflected in a dashboard.")
    add_para(doc, "The application is local-first. FastAPI hosts both the API and static interface; a SQLite database stores progress on the machine running the server. A Groq-backed practice integration is optional and disabled when no key is configured. The core retrieval and NLP sandbox continue in offline mode.")

    doc.add_page_break()
    heading(doc, "4. NLP Concepts and Techniques Used")
    heading(doc, "4.1 Text preparation and tokenization", 2)
    add_para(doc, "The sandbox accepts a short string and uses a regular-expression tokenizer to separate word-like sequences and punctuation. It also splits sentence strings at terminal punctuation followed by whitespace. The interface displays a simple illustrative subword split for longer tokens; this is a demonstration rule and is not a pretrained subword tokenizer. Input is passed to the selected tool rather than being silently rewritten by a general cleaning pipeline.")
    heading(doc, "4.2 POS tags and named entities", 2)
    add_para(doc, "When spaCy and its English en_core_web_sm model are installed, spaCy supplies token-level part-of-speech tags and named entities. If the model is missing, POS output labels ordinary tokens UNKNOWN and named-entity output is empty, with the interface indicating the dependency. This fallback is explicit so a missing model is not mistaken for a reliable linguistic judgment.")
    heading(doc, "4.3 Stemming and lemmatization", 2)
    add_para(doc, "The app compares Porter and Snowball English stems from NLTK. It uses spaCy lemmas when the model is present; otherwise the displayed lemma is the original lowercase token. Stemming is a suffix-oriented normalization heuristic, while lemmatization aims to return a dictionary form. The fallback makes the distinction visible but does not perform true lemmatization without spaCy.")
    heading(doc, "4.4 TF-IDF retrieval and similarity", 2)
    add_para(doc, "For course retrieval, each non-empty lecture section is represented with scikit-learn’s TF-IDF vectorizer using English stop words. Cosine similarity ranks passages against the query; only hits above a small relevance threshold are returned, with lecture title, URL, and score. The sandbox uses TF-IDF cosine similarity for two user-provided strings and also reports Jaccard similarity over their lowercase word sets. These sparse lexical methods are interpretable and lightweight, but they do not understand paraphrase or word meaning beyond shared vocabulary.")
    heading(doc, "4.5 Grammar and question answering", 2)
    add_para(doc, "The CFG demonstration uses a deliberately small hand-authored NLTK grammar with a few determiners, adjectives, nouns, and verbs. An NLTK chart parser searches for a parse; a sentence outside this vocabulary receives no matching tree. Course questions use ranked lecture passages rather than an ungrounded answer model. Optional AI features are designed to use retrieved passages and can be disabled when unavailable.")
    heading(doc, "4.6 Evaluation approach", 2)
    add_para(doc, "The current project is a teaching application, not a trained text classifier. The repository’s automated tests check representative outputs and key fallbacks, including empty retrieval. Because there is no labeled test corpus for a prediction task, accuracy, precision, recall, F1, BLEU, and ROUGE are not reported. TF-IDF relevance would need a human-labeled query–passage set for a defensible ranking evaluation.")

    doc.add_page_break()
    heading(doc, "5. Problem Analysis")
    add_para(doc, "Problem definition. Learners need a practical way to connect computational linguistics terminology to observable operations. Static notes provide explanations but do not necessarily let students change an input sentence, compare outputs, practice sourced concepts, and track progress in one place.")
    add_para(doc, "Existing approaches include lecture pages, textbooks, general-purpose NLP notebooks, and online text-analysis tools. Lecture material provides course alignment but can be less interactive. General tools can expose powerful models, but their outputs may be difficult to interpret or may not cite the class material. A small notebook can demonstrate algorithms but usually does not combine practice, feedback, and learner progress.")
    add_para(doc, "Linguo addresses these gaps with a course map, a source-linked retrieval tutor, a local NLP sandbox, a question bank, and progress views. Its question bank is derived from the lecture corpus; the exam-prep material has no answer key and is kept as ungraded reflection prompts. This prevents the application from inventing authoritative answers where the source does not provide them.")
    add_para(doc, "Benefits include low-friction local setup, visible intermediate outputs, traceable lecture sources, and practice that remains available without an AI service. Constraints include English-only rules and resources, a small CFG, lexical retrieval, possible spaCy installation gaps, and a course corpus limited to the pages collected. Generated multiple-choice questions are mechanically grounded but still require instructor review for pedagogical quality. The application is not a formal assessment system.")

    doc.add_page_break()
    heading(doc, "6. System Design / Workflow")
    figure(doc, arch, "Figure 1. Main application components and data exchange.")
    add_para(doc, "The browser sends requests to FastAPI endpoints, which validate the input and call the selected NLP or retrieval function. Lecture text is read from local JSON while learner records are stored in SQLite. Results return to the browser as structured JSON for display; optional AI routes use a separate configured service.")
    figure(doc, flow, "Figure 2. A typical practice request from input to saved progress.")
    add_para(doc, "A learner supplies a string or answers a course question. Linguo prepares the input, runs a deterministic rule, parser, retrieval method, or optional grounded AI feature, then renders feedback. Where an activity awards experience, the server updates the learner’s progress records.")
    doc.add_page_break()
    heading(doc, "6. System Design / Workflow (continued)")
    figure(doc, pipeline, "Figure 3. Course data preparation and grounded retrieval path.")
    add_para(doc, "The scraper caches pages from the course site and records a crawl report. The builder converts collected material into lecture and question JSON files. Retrieval operates on lecture sections and carries the originating lecture URL into the response so a student can inspect the source.")
    heading(doc, "Core data entities", 2)
    table(doc, ["Entity", "Purpose", "Representative fields"], [
        ("Player", "Local learner identity and totals", "name, XP, streak, daily goal"),
        ("Attempt", "Answer history", "question ID, topic, correctness, time"),
        ("LevelProgress", "Map completion", "lecture ID, stars, best score"),
        ("Badge / PlayerBadge", "Achievement definitions and awards", "name, condition, earned time"),
        ("SrsItem / Ratings", "Review scheduling and adaptive estimates", "due date, ease, rating"),
    ], size=9)
    heading(doc, "Design decisions", 2)
    bullet(doc, "Course data and learner data use separate formats: JSON for read-mostly content, SQLite for changing progress.")
    bullet(doc, "Retrieval results include original URLs so the interface can show and link evidence.")
    bullet(doc, "Optional AI is isolated behind configuration and grounded in retrieved course passages.")
    bullet(doc, "When resources are missing, the app reports a fallback or unavailable capability instead of implying a full model result.")

    doc.add_page_break()
    heading(doc, "7. Implementation Details")
    heading(doc, "7.1 Environment and components", 2)
    table(doc, ["Component", "Technology", "Role"], [
        ("Server/API", "Python 3.11+; FastAPI; Uvicorn", "HTTP routes, validation, static UI"),
        ("Persistence", "SQLAlchemy; SQLite", "Learner, attempt, badge and review records"),
        ("NLP utilities", "NLTK; scikit-learn; optional spaCy", "CFG, stems, TF-IDF and linguistic annotations"),
        ("Interface", "HTML, CSS and JavaScript", "Responsive single-page learning interface"),
        ("Optional AI", "Groq API configuration", "Grounded explanations and practice assistance"),
        ("Data collection", "Python requests, BeautifulSoup, Playwright", "Respectful crawl and page extraction"),
    ], size=8)
    add_para(doc, "The backend is organized into application routes and learning logic, NLP tools, tutor retrieval, AI policy and grounding modules, a scraper, and scripts for question construction, validation, and demo seeding. The frontend is served from the FastAPI application; it does not need a separate npm build step.")
    heading(doc, "7.2 Data source and size", 2)
    add_para(doc, "The course source is Rebecca Kennet’s 21CSE552T Computational Linguistics lecture site at SRM University. The local build contains 38 lecture levels across five units. It also contains 380 sourced multiple-choice questions and 430 reflection prompts. The prompts are not auto-graded because the course exam-prep material does not supply an answer key. The full scraped corpus and generated source-derived data are excluded from the GitHub repository; the report gives counts and methods without redistributing the course pages.")
    heading(doc, "7.3 Selected implementation", 2)
    add_para(doc, "Retrieval uses a sparse lexical baseline that rebuilds its TF-IDF matrix over the current lecture-section corpus for a request. This keeps the implementation simple for the prototype, though caching a fitted vectorizer would be more efficient as the corpus grows.")
    add_code(doc, "matrix = TfidfVectorizer(stop_words=\"english\").fit_transform(\n    [section_text for section_text in corpus] + [query]\n)\nscores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()\nranked = scores.argsort()[::-1][:limit]")
    add_para(doc, "The NLP sandbox applies a selected function to the user’s sentence and returns structured outputs. Similarity reports two complementary lexical measures; the grammar route returns up to three parses from the limited teaching grammar. Student submissions and attempts are persisted through SQLAlchemy models.")
    doc.add_page_break()
    heading(doc, "7. Implementation Details (continued)")
    heading(doc, "Important configuration", 2)
    bullet(doc, "Set up Python dependencies from requirements.txt and start the local ASGI server with Uvicorn.")
    bullet(doc, "The default SQLite file is data/linguo.sqlite3; LINGUO_DB can point to another local database path.")
    bullet(doc, "The first data build uses the scraper, question builder, validator, and demo seeder. The crawl can use Playwright Chromium for accordion-hidden links.")
    bullet(doc, "The optional spaCy English model enables model-based POS, NER, and lemmatization; without it, transparent fallback behavior is shown.")
    bullet(doc, "GROQ_API_KEY enables optional AI features. The local tutor, course map, and sandbox do not require it.")
    heading(doc, "Reproducible local run", 2)
    add_code(doc, "python -m pip install -r requirements.txt\npython -m playwright install chromium\npython scraper/scrape.py\npython scripts/build_questions.py\npython scripts/validate_data.py\npython scripts/seed_demo.py\npython -m uvicorn backend.app.main:app --reload")
    add_para(doc, "The application is intended for local academic demonstration. The report avoids including secrets, a database file, or the collected lecture text. AI service availability depends on the user’s configuration and provider connectivity.")

    doc.add_page_break()
    heading(doc, "8. Output Screens / Results")
    add_para(doc, "The screenshots below were captured from the running local application. They show the welcome/dashboard context, the seeded teacher summary, and the interactive NLP practice area. Demo learner records are labelled as demo data in the interface.")
    figure(doc, screenshots[0], "Figure 4. Linguo home screen with the Demo Asha learner profile.", 6.1)
    figure(doc, screenshots[1], "Figure 5. Teacher view summarizing the seeded class and sourced attempts.", 6.1)
    doc.add_page_break()
    heading(doc, "8. Output Screens / Results (continued)")
    figure(doc, screenshots[2], "Figure 6. Practice Lab interface for running interactive NLP demonstrations.", 6.1)
    heading(doc, "Representative measured examples", 2)
    table(doc, ["Input", "Operation", "Observed result"], [
        ("Hello, linguists. Study NLP!", "Tokenization", "7 token units; 2 sentence strings"),
        ("the linguist studies language", "Demo CFG", "A parse is found by the small grammar"),
        ("cats chase mice / same sentence", "TF-IDF cosine", "1.000 for identical input strings"),
        ("Empty query", "Lecture retrieval", "No hits returned"),
    ], size=8)
    add_para(doc, "These are deterministic examples and existing test assertions, not a held-out benchmark. No aggregate accuracy or ranking quality is reported. TF-IDF cosine is 1.0 for identical text by construction; that value should not be read as general system accuracy.")

    doc.add_page_break()
    heading(doc, "9. Testing and Evaluation")
    add_para(doc, "The repository test suite was run with pytest on the current project environment. Result: 10 tests passed. The tests cover core learning logic, NLP outputs, and retrieval behavior. No training/test split applies because Linguo does not fit a supervised predictive model.")
    table(doc, ["Test case", "Input", "Expected output", "Actual output / status"], [
        ("TC-01", "Hello, linguists. Study NLP!", "Token list and two sentences", "PASS; asserted in NLP tests"),
        ("TC-02", "Empty retrieval query", "No result; no invented passage", "PASS; returns empty list"),
        ("TC-03", "the linguist studies language", "Small CFG finds a parse", "PASS; asserted in NLP tests"),
        ("TC-04", "Text outside CFG vocabulary", "No parse; explicit unmatched result", "PASS; fallback behavior checked manually"),
        ("TC-05", "Identical sentence pair", "TF-IDF cosine near 1", "PASS; test requires value above 0.99"),
        ("TC-06", "context free grammar", "Passage with course source URL", "PASS; retrieval test checks text and URL"),
    ], size=8)
    add_para(doc, "The full suite result was 10 passed in approximately 3.7 seconds. The reported table summarizes representative cases from the test suite and a direct boundary check. It does not estimate real-world learner outcomes, general-purpose parsing quality, or the precision of course-passage ranking.")
    heading(doc, "Evaluation limitations", 2)
    bullet(doc, "No independently labeled query–passage relevance set is included, so retrieval precision and recall are unknown.")
    bullet(doc, "No labeled POS or named-entity corpus is evaluated; spaCy behavior depends on model installation and input domain.")
    bullet(doc, "The question bank is generated from course text; its pedagogical quality requires instructor review.")

    doc.add_page_break()
    heading(doc, "10. Features, Limitations and Future Enhancements")
    heading(doc, "Implemented features", 2)
    bullet(doc, "Five-unit course map with 38 lecture levels, source links, and practice questions.")
    bullet(doc, "Grounded passage retrieval using TF-IDF and cosine similarity.")
    bullet(doc, "Interactive tokenization, POS, optional NER, stem/lemma comparison, TF-IDF/Jaccard similarity, and CFG parsing.")
    bullet(doc, "Learner dashboard, XP, streaks, badges, level stars, daily challenge, boss review, leaderboard, and teacher summary.")
    bullet(doc, "Optional Groq practice features with offline fallback and usage policy.")
    heading(doc, "Known limitations", 2)
    bullet(doc, "The corpus is limited to collected English-language course pages; retrieval may miss paraphrases or return a weak lexical match.")
    bullet(doc, "The demonstration CFG covers a small vocabulary and grammar; it is not a general parser.")
    bullet(doc, "POS, NER, and lemmatization depend on the optional spaCy model. Fallback outputs have limited linguistic value.")
    bullet(doc, "Generated MCQs need instructor review, and reflection prompts remain ungraded.")
    bullet(doc, "There is no benchmark dataset or measured end-user learning study.")
    heading(doc, "Future work", 2)
    add_para(doc, "Useful next steps are to add instructor-reviewed questions and a labeled retrieval benchmark; cache TF-IDF features for faster queries; expand language and model support; improve explanations for model fallbacks; and conduct a small consent-based usability study. Any added course material should remain within the source’s permitted use and attribution requirements.")

    doc.add_page_break()
    heading(doc, "11. Conclusion")
    add_para(doc, "Linguo addresses the gap between reading computational linguistics concepts and trying them on actual text. It combines a sourced course map and practice bank with a compact NLP sandbox and learner progress tracking. The implemented prototype uses tokenization, stemming, optional linguistic annotations, TF-IDF retrieval and similarity, Jaccard overlap, and a small CFG parser. Its retrieval responses preserve lecture links, and its ungraded prompts avoid presenting missing answer keys as facts.")
    add_para(doc, "The project demonstrates how web application design, text processing, information retrieval, grammar parsing, data collection, and persistence can be assembled into a course-facing tool. Ten automated tests passed for the current implementation. Those checks support expected prototype behavior, while the lack of labeled evaluation data means that broader NLP quality claims remain open.")
    add_para(doc, "The next practical steps are to review generated questions with the course instructor and evaluate retrieval using labeled student queries and relevant lecture passages. The project can then improve ranking and explanations based on measured errors.")

    doc.add_page_break()
    heading(doc, "12. References")
    refs = [
        "Kennet, R. (n.d.). 21CSE552T Computational Linguistics course lectures. SRM University. https://lectures.rebeccakennet.com/21cse552t-computational-linguistics/ (accessed 20 November 2026).",
        "Bolshakov, I. A., & Gelbukh, A. (2004). Computational Linguistics: Models, Resources, Applications. IPN.",
        "Bird, S., Klein, E., & Loper, E. (2009). Natural Language Processing with Python. O’Reilly Media. https://www.nltk.org/book/",
        "Bird, S., & Loper, E. (2004). NLTK: The Natural Language Toolkit. Proceedings of the ACL Interactive Demonstrations, 69–72. https://doi.org/10.3115/1219044.1219075",
        "Honnibal, M., Montani, I., Van Landeghem, S., & Boyd, A. (2020–). spaCy: Industrial-strength Natural Language Processing in Python. https://spacy.io/",
        "Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html",
        "FastAPI. (n.d.). FastAPI documentation. https://fastapi.tiangolo.com/",
        "SQLAlchemy. (n.d.). SQLAlchemy documentation. https://docs.sqlalchemy.org/",
        "Playwright. (n.d.). Playwright Python documentation. https://playwright.dev/python/",
        "Linguo project repository source files: backend/app, backend/nlp, backend/tutor, frontend, scraper, and scripts (project implementation; accessed 20 November 2026).",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(.28); p.paragraph_format.first_line_indent = Inches(-.28)
        p.paragraph_format.line_spacing = 1.25; p.paragraph_format.space_after = Pt(8)
        p.add_run(f"{i}. {ref}")
    add_para(doc, "Citation note: The course site is acknowledged as the source of the local lecture corpus. Scraped pages and generated course-derived question files are excluded from the code repository to respect the project’s stated non-redistribution limitation.", italic=True)

    doc.core_properties.title = "Linguo NLP Project Report"
    doc.core_properties.subject = "Computational Linguistics course project"
    doc.core_properties.author = "Aditya Muralidharan; Litesh T"
    doc.save(OUT)
    print(f"Created {OUT}")
    print("Embedded screenshots:", ", ".join(str(x.relative_to(ROOT)) for x in screenshots))


if __name__ == "__main__":
    build()
