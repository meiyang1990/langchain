#!/usr/bin/env python3
"""
LangChain Partners 集成层源码架构分析文档生成器
生成包含流程图、时序图和核心类设计说明的 PDF 文档
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import (
    HexColor, black, white, Color,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Group
from reportlab.graphics import renderPDF

# ============================================================
# 颜色常量
# ============================================================
C_PRIMARY = HexColor("#1a73e8")
C_PRIMARY_DARK = HexColor("#0d47a1")
C_SECONDARY = HexColor("#34a853")
C_ACCENT = HexColor("#ea4335")
C_WARN = HexColor("#fbbc04")
C_BG_LIGHT = HexColor("#f8f9fa")
C_BG_BLUE = HexColor("#e8f0fe")
C_BG_GREEN = HexColor("#e6f4ea")
C_BG_ORANGE = HexColor("#fef7e0")
C_BG_RED = HexColor("#fce8e6")
C_BG_PURPLE = HexColor("#f3e8fd")
C_PURPLE = HexColor("#7b1fa2")
C_DARK = HexColor("#202124")
C_GRAY = HexColor("#5f6368")
C_BORDER = HexColor("#dadce0")
C_WHITE = white

# ============================================================
# 字体注册（使用系统中文字体）
# ============================================================
FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    # Fallback - reportlab default
]

CHINESE_FONT = "Helvetica"  # fallback
for fp in FONT_PATHS:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont("ChineseFont", fp))
            CHINESE_FONT = "ChineseFont"
            break
        except Exception:
            continue

MONO_FONT = "Courier"

# ============================================================
# 样式定义
# ============================================================
styles = getSampleStyleSheet()

def make_style(name, **kwargs):
    """Create or override a ParagraphStyle."""
    base = kwargs.pop("parent", styles["Normal"])
    return ParagraphStyle(name, parent=base, **kwargs)

S_COVER_TITLE = make_style(
    "CoverTitle", fontName=CHINESE_FONT, fontSize=28, leading=36,
    alignment=TA_CENTER, textColor=C_WHITE, spaceAfter=12,
)
S_COVER_SUB = make_style(
    "CoverSub", fontName=CHINESE_FONT, fontSize=14, leading=20,
    alignment=TA_CENTER, textColor=HexColor("#cfd8dc"),
)
S_H1 = make_style(
    "H1", fontName=CHINESE_FONT, fontSize=22, leading=30,
    textColor=C_PRIMARY_DARK, spaceBefore=24, spaceAfter=12,
)
S_H2 = make_style(
    "H2", fontName=CHINESE_FONT, fontSize=17, leading=24,
    textColor=C_PRIMARY, spaceBefore=18, spaceAfter=8,
)
S_H3 = make_style(
    "H3", fontName=CHINESE_FONT, fontSize=14, leading=20,
    textColor=C_DARK, spaceBefore=12, spaceAfter=6,
)
S_BODY = make_style(
    "Body", fontName=CHINESE_FONT, fontSize=10, leading=16,
    textColor=C_DARK, spaceAfter=6, alignment=TA_JUSTIFY,
)
S_BODY_SM = make_style(
    "BodySm", fontName=CHINESE_FONT, fontSize=9, leading=14,
    textColor=C_GRAY, spaceAfter=4,
)
S_CODE = make_style(
    "Code", fontName=MONO_FONT, fontSize=8.5, leading=12,
    textColor=C_DARK, backColor=C_BG_LIGHT, leftIndent=12,
    rightIndent=12, spaceBefore=4, spaceAfter=6,
    borderPadding=(4, 6, 4, 6),
)
S_BULLET = make_style(
    "Bullet", fontName=CHINESE_FONT, fontSize=10, leading=16,
    textColor=C_DARK, leftIndent=20, bulletIndent=8,
    spaceAfter=3,
)
S_TABLE_H = make_style(
    "TableH", fontName=CHINESE_FONT, fontSize=9, leading=13,
    textColor=C_WHITE, alignment=TA_CENTER,
)
S_TABLE_C = make_style(
    "TableC", fontName=CHINESE_FONT, fontSize=8.5, leading=12,
    textColor=C_DARK,
)


# ============================================================
# 自定义 Flowable: 带圆角的色块标题条
# ============================================================
class SectionBanner(Flowable):
    """A colored banner bar for section headings."""
    def __init__(self, text, color=C_PRIMARY, width=None, height=28):
        super().__init__()
        self.text = text
        self.color = color
        self._width = width
        self._height = height

    def wrap(self, aW, aH):
        self._width = self._width or aW
        return (self._width, self._height)

    def draw(self):
        c = self.canv
        w, h = self._width, self._height
        c.setFillColor(self.color)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont(CHINESE_FONT, 14)
        c.drawString(14, h / 2 - 5, self.text)


# ============================================================
# 辅助绘图类
# ============================================================
class BoxFlowDiagram(Flowable):
    """Generic flow diagram rendered as a Flowable."""

    def __init__(self, boxes, arrows, width=480, height=200,
                 box_w=110, box_h=32, font_size=8):
        super().__init__()
        self._width = width
        self._height = height
        self.boxes = boxes       # [(x, y, text, color), ...]
        self.arrows = arrows     # [(x1, y1, x2, y2), ...]
        self.box_w = box_w
        self.box_h = box_h
        self.font_size = font_size

    def wrap(self, aW, aH):
        return (self._width, self._height)

    def draw(self):
        c = self.canv
        bw, bh = self.box_w, self.box_h
        for (x, y, text, color) in self.boxes:
            c.setFillColor(color)
            c.roundRect(x, y, bw, bh, 6, fill=1, stroke=0)
            c.setFillColor(C_WHITE)
            c.setFont(CHINESE_FONT, self.font_size)
            # multi-line text
            lines = text.split("\n")
            for i, ln in enumerate(lines):
                ty = y + bh / 2 + (len(lines) - 1) * 5 - i * 12
                c.drawCentredString(x + bw / 2, ty - 3, ln)
        # arrows
        c.setStrokeColor(C_GRAY)
        c.setLineWidth(1.2)
        for (x1, y1, x2, y2) in self.arrows:
            c.line(x1, y1, x2, y2)
            # arrowhead
            import math
            angle = math.atan2(y2 - y1, x2 - x1)
            ax = x2 - 6 * math.cos(angle - 0.4)
            ay = y2 - 6 * math.sin(angle - 0.4)
            bx = x2 - 6 * math.cos(angle + 0.4)
            by = y2 - 6 * math.sin(angle + 0.4)
            c.setFillColor(C_GRAY)
            path = c.beginPath()
            path.moveTo(x2, y2)
            path.lineTo(ax, ay)
            path.lineTo(bx, by)
            path.close()
            c.drawPath(path, fill=1, stroke=0)


class SequenceDiagram(Flowable):
    """Simplified sequence diagram as a Flowable."""

    def __init__(self, participants, messages, width=480, height=300):
        super().__init__()
        self._width = width
        self._height = height
        self.participants = participants  # [name, ...]
        self.messages = messages  # [(from_idx, to_idx, label, is_return), ...]

    def wrap(self, aW, aH):
        return (self._width, self._height)

    def draw(self):
        c = self.canv
        n = len(self.participants)
        gap = self._width / (n + 1)
        top_y = self._height - 30
        box_w = 80
        box_h = 22

        # participant boxes and lifelines
        xs = []
        for i, name in enumerate(self.participants):
            x = gap * (i + 1)
            xs.append(x)
            c.setFillColor(C_PRIMARY)
            c.roundRect(x - box_w / 2, top_y, box_w, box_h, 4, fill=1, stroke=0)
            c.setFillColor(C_WHITE)
            c.setFont(CHINESE_FONT, 8)
            c.drawCentredString(x, top_y + 7, name)
            # lifeline
            c.setStrokeColor(C_BORDER)
            c.setDash(3, 3)
            c.line(x, top_y, x, 10)
            c.setDash()

        # messages
        msg_y = top_y - 28
        step = max(18, (top_y - 40) / max(len(self.messages), 1))
        for idx, (fi, ti, label, is_ret) in enumerate(self.messages):
            y = msg_y - idx * step
            x1, x2 = xs[fi], xs[ti]
            if is_ret:
                c.setStrokeColor(C_GRAY)
                c.setDash(4, 3)
            else:
                c.setStrokeColor(C_DARK)
                c.setDash()
            c.setLineWidth(1)
            c.line(x1, y, x2, y)
            # arrowhead
            import math
            direction = 1 if x2 > x1 else -1
            ax = x2 - direction * 6
            c.setFillColor(C_DARK if not is_ret else C_GRAY)
            path = c.beginPath()
            path.moveTo(x2, y)
            path.lineTo(ax, y + 3)
            path.lineTo(ax, y - 3)
            path.close()
            c.drawPath(path, fill=1, stroke=0)
            # label
            c.setFillColor(C_DARK)
            c.setFont(CHINESE_FONT, 7)
            mid_x = (x1 + x2) / 2
            c.drawCentredString(mid_x, y + 4, label)
        c.setDash()

# ============================================================
# 辅助函数
# ============================================================
def h1(text): return Paragraph(text, S_H1)
def h2(text): return Paragraph(text, S_H2)
def h3(text): return Paragraph(text, S_H3)
def p(text): return Paragraph(text, S_BODY)
def ps(text): return Paragraph(text, S_BODY_SM)
def code(text): return Paragraph(text.replace("\n", "<br/>").replace(" ", "&nbsp;"), S_CODE)
def bullet(text): return Paragraph(f"<bullet>&bull;</bullet> {text}", S_BULLET)
def spacer(h=6): return Spacer(1, h)
def hr(): return HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=8, spaceBefore=8)

def colored_table(headers, rows, col_widths=None):
    """Create a styled table."""
    data = [[Paragraph(h, S_TABLE_H) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), S_TABLE_C) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), CHINESE_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), C_WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_BG_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ]))
    return t


# ============================================================
# 页眉页脚
# ============================================================
def on_page(canvas, doc):
    canvas.saveState()
    # footer
    canvas.setFont(CHINESE_FONT, 7)
    canvas.setFillColor(C_GRAY)
    canvas.drawString(doc.leftMargin, 15 * mm,
                      "LangChain Partners 集成层架构分析文档")
    canvas.drawRightString(A4[0] - doc.rightMargin, 15 * mm,
                           f"第 {doc.page} 页")
    # top line
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(doc.leftMargin, A4[1] - doc.topMargin + 8,
                A4[0] - doc.rightMargin, A4[1] - doc.topMargin + 8)
    canvas.restoreState()

def on_first_page(canvas, doc):
    """Cover page - no header/footer."""
    pass


# ============================================================
# 构建文档内容
# ============================================================
def build_document():
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "langchain-partners-architecture.pdf"
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=25 * mm,
        bottomMargin=25 * mm,
    )
    story = []
    W = doc.width  # available width

    # ========== 封面 ==========
    story.append(Spacer(1, 60))

    # 封面色块
    class CoverBlock(Flowable):
        def __init__(self, w):
            super().__init__()
            self.w = w
        def wrap(self, aW, aH):
            return (self.w, 260)
        def draw(self):
            c = self.canv
            c.setFillColor(C_PRIMARY_DARK)
            c.roundRect(-10, 0, self.w + 20, 260, 12, fill=1, stroke=0)

    story.append(CoverBlock(W))
    story.append(Spacer(1, -230))
    story.append(Paragraph("LangChain Partners", S_COVER_TITLE))
    story.append(Paragraph("集成层源码架构分析文档", S_COVER_TITLE))
    story.append(Spacer(1, 16))
    story.append(Paragraph("核心流程图 | 时序图 | 类设计说明", S_COVER_SUB))
    story.append(Spacer(1, 10))
    story.append(Paragraph("基于 LangChain v0.1.16 源码分析", S_COVER_SUB))
    story.append(Spacer(1, 80))

    info_style = make_style("info", fontName=CHINESE_FONT, fontSize=10,
                            leading=18, textColor=C_GRAY, alignment=TA_CENTER)
    story.append(Paragraph("涵盖 OpenAI / Anthropic / Ollama / DeepSeek / HuggingFace", info_style))
    story.append(Paragraph("Groq / MistralAI / Fireworks / Chroma / Qdrant 等 15 个集成包", info_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("2026 年 3 月", info_style))
    story.append(PageBreak())

    # ========== 目录 ==========
    story.append(SectionBanner("目  录", C_PRIMARY_DARK))
    story.append(Spacer(1, 16))
    toc_items = [
        ("第一章", "Partners 集成层整体架构概览"),
        ("第二章", "核心类继承体系设计"),
        ("第三章", "Chat Model 调用流程图"),
        ("第四章", "流式输出（Streaming）时序图"),
        ("第五章", "Tool Calling（工具调用）流程图"),
        ("第六章", "结构化输出（Structured Output）流程图"),
        ("第七章", "Embeddings 嵌入处理流程图"),
        ("第八章", "向量存储（VectorStore）架构"),
        ("第九章", "OpenAI 集成包核心设计"),
        ("第十章", "Anthropic 集成包核心设计"),
        ("第十一章", "其他 Partner 集成包设计"),
        ("第十二章", "跨 Provider 对比分析"),
    ]
    for num, title in toc_items:
        story.append(Paragraph(
            f'<font color="{C_PRIMARY.hexval()}">{num}</font>  '
            f'{title}', S_BODY))
    story.append(PageBreak())

    # ========================================================
    # 第一章: 整体架构概览
    # ========================================================
    story.append(SectionBanner("第一章  Partners 集成层整体架构概览", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("1.1 架构定位"))
    story.append(p(
        "LangChain Partners 是 LangChain 生态系统中的<b>集成层</b>，位于 langchain-core "
        "基础抽象层之上，负责将各种第三方 AI 服务（大语言模型、嵌入模型、向量数据库等）"
        "接入 LangChain 统一的 Runnable 执行框架。每个 Partner 包都是独立版本管理的 Python 包，"
        "通过实现 langchain-core 定义的抽象接口来提供具体的服务集成。"
    ))
    story.append(spacer(8))

    story.append(h2("1.2 分层架构图"))
    # Layered architecture diagram
    layers = [
        (10, 160, "应用层\n(用户代码 / LangGraph Agent)", C_PURPLE, 460, 34),
        (10, 118, "集成层 (Partners)\nOpenAI | Anthropic | Ollama | HuggingFace | Chroma | Qdrant ...", C_PRIMARY, 460, 34),
        (10, 76, "核心抽象层 (langchain-core)\nRunnable | BaseChatModel | Embeddings | VectorStore | BaseTool", C_SECONDARY, 460, 34),
        (10, 34, "传输层\nhttpx / aiohttp / gRPC", C_GRAY, 460, 34),
    ]

    class LayeredDiagram(Flowable):
        def __init__(self):
            super().__init__()
        def wrap(self, aW, aH):
            return (480, 210)
        def draw(self):
            c = self.canv
            for (x, y, text, color, w, h) in layers:
                c.setFillColor(color)
                c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
                c.setFillColor(C_WHITE)
                c.setFont(CHINESE_FONT, 8)
                lines = text.split("\n")
                for i, ln in enumerate(lines):
                    c.drawCentredString(x + w/2, y + h/2 + 5 - i*12, ln)
            # arrows
            c.setStrokeColor(C_BORDER)
            c.setLineWidth(1)
            for base_y in [118+34, 76+34, 34+34]:
                c.line(240, base_y, 240, base_y + 8)

    story.append(LayeredDiagram())
    story.append(spacer(12))

    story.append(h2("1.3 Partner 包总览"))
    story.append(colored_table(
        ["包名", "类型", "核心类", "继承方式"],
        [
            ["langchain-openai", "LLM / Chat / Embed", "ChatOpenAI, OpenAIEmbeddings", "BaseChatOpenAI -> BaseChatModel"],
            ["langchain-anthropic", "Chat", "ChatAnthropic", "BaseChatModel (直接)"],
            ["langchain-ollama", "LLM / Chat / Embed", "ChatOllama, OllamaEmbeddings", "BaseChatModel (直接)"],
            ["langchain-deepseek", "Chat", "ChatDeepSeek", "BaseChatOpenAI (复用 OpenAI)"],
            ["langchain-huggingface", "LLM / Chat / Embed", "ChatHuggingFace, HuggingFaceEmbeddings", "BaseChatModel (直接)"],
            ["langchain-groq", "Chat", "ChatGroq", "BaseChatModel (独立实现)"],
            ["langchain-mistralai", "Chat / Embed", "ChatMistralAI, MistralAIEmbeddings", "BaseChatModel (独立实现)"],
            ["langchain-fireworks", "LLM / Chat / Embed", "ChatFireworks, FireworksEmbeddings", "BaseChatModel (独立实现)"],
            ["langchain-chroma", "VectorStore", "Chroma", "VectorStore"],
            ["langchain-qdrant", "VectorStore", "QdrantVectorStore", "VectorStore"],
        ],
        col_widths=[90, 80, 140, 150],
    ))
    story.append(PageBreak())

    # ========================================================
    # 第二章: 核心类继承体系
    # ========================================================
    story.append(SectionBanner("第二章  核心类继承体系设计", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("2.1 Runnable 统一执行接口"))
    story.append(p(
        "Runnable 是 LangChain 表达式语言（LCEL）的核心接口，所有可组合的组件都必须实现此协议。"
        "它定义了 <font name='Courier'>invoke</font>、<font name='Courier'>stream</font>、"
        "<font name='Courier'>batch</font> 三套方法（各含同步和异步版本），"
        "使得所有组件可以用 <font name='Courier'>|</font> 运算符自由组合成链式管道。"
    ))
    story.append(spacer(8))

    # Class hierarchy diagram
    story.append(h2("2.2 完整类继承树"))

    hier_boxes = [
        # Level 0 - Root
        (185, 370, "Runnable[I, O]\n(ABC)", C_DARK),
        # Level 1
        (165, 320, "RunnableSerializable\n[I, O]", C_GRAY),
        # Level 2
        (30, 265, "BaseLanguageModel\n[OutputVar]", C_PRIMARY),
        (310, 265, "BaseTool", C_ACCENT),
        # Level 3
        (0, 210, "BaseChatModel", C_PRIMARY),
        (140, 210, "BaseLLM", C_PRIMARY),
        # Level 4 - Partners
        (0, 150, "BaseChatOpenAI", C_SECONDARY),
        (130, 150, "ChatAnthropic", C_SECONDARY),
        (250, 150, "ChatOllama", C_SECONDARY),
        (360, 150, "ChatGroq", C_SECONDARY),
        # Level 5
        (0, 90, "ChatOpenAI", HexColor("#1565c0")),
        (0, 40, "ChatDeepSeek", HexColor("#0d47a1")),
    ]
    hier_arrows = [
        # Runnable -> RunnableSerializable
        (240, 370, 220, 352),
        # RS -> BaseLanguageModel
        (190, 320, 100, 297),
        # RS -> BaseTool
        (240, 320, 360, 297),
        # BLM -> BaseChatModel
        (80, 265, 55, 242),
        # BLM -> BaseLLM
        (100, 265, 190, 242),
        # BCM -> BaseChatOpenAI
        (50, 210, 55, 182),
        # BCM -> ChatAnthropic
        (55, 210, 180, 182),
        # BCM -> ChatOllama
        (55, 210, 300, 182),
        # BCM -> ChatGroq
        (55, 210, 410, 182),
        # BaseChatOpenAI -> ChatOpenAI
        (55, 150, 55, 122),
        # ChatOpenAI -> ChatDeepSeek
        (55, 90, 55, 72),
    ]
    story.append(BoxFlowDiagram(hier_boxes, hier_arrows, width=480, height=415, box_w=110, box_h=28, font_size=7))
    story.append(spacer(6))
    story.append(ps("图 2-1: Partners 核心类继承关系图（绿色=Partner实现，蓝色=OpenAI系列）"))
    story.append(spacer(12))

    # Separate classes
    story.append(h2("2.3 独立接口类"))
    story.append(p(
        "注意：<b>Embeddings</b> 和 <b>VectorStore</b> 是独立的 ABC 抽象类，"
        "<b>不继承 Runnable</b>。它们保持纯净的功能接口，VectorStore 通过 "
        "<font name='Courier'>as_retriever()</font> 方法桥接到 Runnable 体系。"
    ))
    story.append(colored_table(
        ["基类", "继承", "抽象方法", "Partner 实现"],
        [
            ["Embeddings", "ABC", "embed_documents(), embed_query()", "OpenAIEmbeddings, OllamaEmbeddings, HuggingFaceEmbeddings"],
            ["VectorStore", "ABC", "similarity_search()", "Chroma, QdrantVectorStore"],
        ],
        col_widths=[80, 50, 160, 170],
    ))
    story.append(spacer(8))

    story.append(h2("2.4 三级实现模式"))
    story.append(p(
        "LangChain 采用<b>三级实现模式</b>：基类提供完整的公开 API（invoke/stream/batch），"
        "但只要求子类实现带下划线的内部方法。基类负责回调管理、缓存、重试、速率限制等横切关注点。"
    ))
    story.append(colored_table(
        ["层级", "方法", "职责", "示例"],
        [
            ["公开 API", "invoke() / stream() / batch()", "回调链、缓存、重试、类型转换", "BaseChatModel.invoke()"],
            ["内部生成", "_generate() / _stream()", "实际的 API 调用和响应解析", "ChatOpenAI._generate()"],
            ["Payload 构建", "_get_request_payload()", "消息格式转换、参数组装", "ChatAnthropic._get_request_payload()"],
        ],
        col_widths=[70, 130, 140, 120],
    ))
    story.append(PageBreak())

    # ========================================================
    # 第三章: Chat Model 调用流程
    # ========================================================
    story.append(SectionBanner("第三章  Chat Model 调用流程图", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("3.1 统一调用流程"))
    story.append(p(
        "所有 Chat Model 的调用都遵循相同的流程，从用户调用 <font name='Courier'>invoke()</font> "
        "开始，经过基类的回调和缓存管理，最终调用 Partner 包的 <font name='Courier'>_generate()</font> "
        "方法完成实际的 API 请求。"
    ))

    # Flow diagram
    flow_boxes = [
        (5, 250, "用户代码\nmodel.invoke()", C_DARK),
        (145, 250, "BaseChatModel\n.invoke()", C_PRIMARY),
        (285, 250, "generate_prompt()\n消息预处理", C_PRIMARY),
        (5, 190, "_generate_with\n_cache()", C_PRIMARY),
        (145, 190, "_generate()\n抽象方法", C_ACCENT),
        (285, 190, "Partner 实现\n(如 ChatOpenAI)", C_SECONDARY),
        (5, 130, "_get_request\n_payload()", C_SECONDARY),
        (145, 130, "消息格式转换\n_format_messages()", C_SECONDARY),
        (285, 130, "HTTP API 调用\nclient.create()", HexColor("#1565c0")),
        (145, 70, "响应解析\n_format_output()", C_SECONDARY),
        (285, 70, "构建 ChatResult\nAIMessage", C_PRIMARY),
        (145, 10, "返回 AIMessage\n(含 tool_calls)", C_DARK),
    ]
    flow_arrows = [
        (115, 266, 145, 266),
        (255, 266, 285, 266),
        (340, 250, 60, 222),
        (60, 206, 145, 206),
        (255, 206, 285, 206),
        (340, 190, 60, 162),
        (115, 146, 145, 146),
        (255, 146, 285, 146),
        (340, 130, 200, 102),
        (255, 86, 285, 86),
        (200, 70, 200, 42),
    ]
    story.append(BoxFlowDiagram(flow_boxes, flow_arrows, width=480, height=295))
    story.append(ps("图 3-1: Chat Model 统一调用流程图"))
    story.append(spacer(12))

    story.append(h2("3.2 OpenAI 双 API 路由机制"))
    story.append(p(
        "ChatOpenAI 是唯一同时支持 <b>Chat Completions API</b> 和 <b>Responses API</b> 的实现。"
        "通过 <font name='Courier'>_use_responses_api()</font> 方法自动检测应使用哪个 API："
    ))
    story.append(bullet("使用了内置工具（web_search, file_search, computer_use 等）"))
    story.append(bullet("使用了 Responses API 专属参数（reasoning, truncation, previous_response_id）"))
    story.append(bullet("output_version 设置为 'responses/v1'"))
    story.append(bullet("模型名称匹配 Responses API 专属前缀（如 gpt-5-pro）"))

    api_route_boxes = [
        (170, 160, "_generate()\n入口", C_DARK),
        (50, 100, "has response_format?\nbeta.chat.completions\n.parse()", C_WARN),
        (190, 100, "_use_responses\n_api()?", C_ACCENT),
        (340, 130, "Responses API\nroot_client\n.responses.create()", C_SECONDARY),
        (340, 70, "Chat Completions\nclient.create()", C_PRIMARY),
    ]
    api_route_arrows = [
        (225, 160, 105, 132),
        (225, 160, 245, 132),
        (300, 120, 340, 146),
        (300, 100, 340, 86),
    ]
    story.append(BoxFlowDiagram(api_route_boxes, api_route_arrows, width=480, height=200, box_w=120, box_h=40, font_size=7))
    story.append(ps("图 3-2: OpenAI 双 API 路由决策流程"))
    story.append(PageBreak())

    # ========================================================
    # 第四章: Streaming 时序图
    # ========================================================
    story.append(SectionBanner("第四章  流式输出（Streaming）时序图", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("4.1 OpenAI Chat Completions 流式时序"))
    story.append(p(
        "流式输出是 LangChain 中最常用的交互模式。当调用 <font name='Courier'>stream()</font> 时，"
        "系统会逐块返回 AIMessageChunk，允许前端实时展示生成内容。"
    ))

    story.append(SequenceDiagram(
        participants=["用户代码", "BaseChatModel", "ChatOpenAI", "OpenAI API"],
        messages=[
            (0, 1, "model.stream(messages)", False),
            (1, 2, "_stream(messages, **kwargs)", False),
            (2, 2, "payload = _get_request_payload()", False),
            (2, 3, "client.create(stream=True)", False),
            (3, 2, "Stream[ChatCompletionChunk]", True),
            (2, 2, "_convert_chunk_to_generation_chunk()", False),
            (2, 1, "yield ChatGenerationChunk", True),
            (1, 1, "run_manager.on_llm_new_token()", False),
            (1, 0, "yield AIMessageChunk", True),
            (3, 2, "...(更多 chunk)", True),
            (2, 1, "yield ChatGenerationChunk (last)", True),
            (1, 0, "yield AIMessageChunk (last)", True),
        ],
        width=480, height=300,
    ))
    story.append(ps("图 4-1: OpenAI Chat Completions 流式输出时序图"))
    story.append(spacer(16))

    story.append(h2("4.2 Anthropic 流式时序"))
    story.append(p(
        "Anthropic 使用原始事件流（RawMessageStreamEvent），事件类型更丰富，"
        "需要跟踪 block_start_event 来关联工具调用块的后续增量。"
    ))

    story.append(SequenceDiagram(
        participants=["用户代码", "BaseChatModel", "ChatAnthropic", "Anthropic API"],
        messages=[
            (0, 1, "model.stream(messages)", False),
            (1, 2, "_stream(messages)", False),
            (2, 3, "messages.create(stream=True)", False),
            (3, 2, "message_start (usage)", True),
            (3, 2, "content_block_start", True),
            (3, 2, "content_block_delta (text)", True),
            (2, 2, "_make_message_chunk_from_event()", False),
            (2, 1, "yield ChatGenerationChunk", True),
            (1, 0, "yield AIMessageChunk", True),
            (3, 2, "content_block_delta (tool input)", True),
            (3, 2, "message_delta (stop_reason)", True),
            (2, 1, "yield last chunk", True),
        ],
        width=480, height=300,
    ))
    story.append(ps("图 4-2: Anthropic 流式输出时序图"))
    story.append(PageBreak())

    # ========================================================
    # 第五章: Tool Calling 流程
    # ========================================================
    story.append(SectionBanner("第五章  Tool Calling（工具调用）流程图", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("5.1 工具绑定与调用全流程"))
    story.append(p(
        "Tool Calling 是 LangChain 中最核心的能力之一，允许 LLM 调用外部工具。"
        "流程分为三个阶段：工具绑定 -> 模型推理 -> 工具执行。"
    ))

    tc_boxes = [
        (5, 290, "定义工具\n@tool / BaseTool", C_DARK),
        (140, 290, "bind_tools()\n工具绑定", C_PRIMARY),
        (275, 290, "convert_to\n_openai_tool()", C_PRIMARY),
        (410, 290, "返回 Runnable\n(bound model)", C_SECONDARY),
        # Phase 2
        (5, 220, "invoke(messages)\n调用模型", C_DARK),
        (140, 220, "_generate()\n发送含 tools", C_PRIMARY),
        (275, 220, "API 返回\ntool_calls", C_ACCENT),
        (410, 220, "解析为\nAIMessage", C_SECONDARY),
        # Phase 3
        (5, 150, "AIMessage\n.tool_calls", C_SECONDARY),
        (140, 150, "执行工具\ntool.invoke(args)", C_ACCENT),
        (275, 150, "返回\nToolMessage", C_DARK),
        (410, 150, "追加到消息\n继续对话", C_PRIMARY),
    ]
    tc_arrows = [
        (115, 306, 140, 306), (250, 306, 275, 306), (385, 306, 410, 306),
        (115, 236, 140, 236), (250, 236, 275, 236), (385, 236, 410, 236),
        (115, 166, 140, 166), (250, 166, 275, 166), (385, 166, 410, 166),
        # Phase transitions
        (460, 290, 460, 252),
        (460, 220, 460, 182),
    ]
    story.append(BoxFlowDiagram(tc_boxes, tc_arrows, width=520, height=340, box_w=110, box_h=30, font_size=7))
    story.append(ps("图 5-1: Tool Calling 完整流程图（三阶段）"))
    story.append(spacer(12))

    story.append(h2("5.2 工具格式转换对比"))
    story.append(colored_table(
        ["维度", "OpenAI 格式", "Anthropic 格式"],
        [
            ["外层结构", '{"type":"function","function":{...}}', '{"name":"...","input_schema":{...}}'],
            ["参数字段", "parameters (JSON Schema)", "input_schema (JSON Schema)"],
            ["tool_choice", '"auto" / "required" / {"type":"function",...}', '"auto" / "any" / {"type":"tool","name":"..."}'],
            ["内置工具", "有限 (code_interpreter)", "丰富 (text_editor, bash, web_search, mcp 等)"],
            ["strict 模式", "支持 (保证输出符合 schema)", "支持"],
            ["并行调用控制", "parallel_tool_calls 参数", "disable_parallel_tool_use (tool_choice 上)"],
        ],
        col_widths=[80, 180, 200],
    ))
    story.append(PageBreak())

    # ========================================================
    # 第六章: Structured Output
    # ========================================================
    story.append(SectionBanner("第六章  结构化输出（Structured Output）流程图", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("6.1 三种结构化输出方式"))
    story.append(p(
        "LangChain 通过 <font name='Courier'>with_structured_output()</font> 方法提供结构化输出能力，"
        "支持三种实现方式，各 Provider 默认方式不同。"
    ))

    so_boxes = [
        (160, 260, "with_structured\n_output(schema)", C_DARK),
        # 三个分支
        (10, 190, "json_schema\n(ChatOpenAI 默认)", C_PRIMARY),
        (170, 190, "function_calling\n(Anthropic 默认)", C_SECONDARY),
        (340, 190, "json_mode", C_WARN),
        # 实现
        (10, 120, "response_format=\njson_schema", C_PRIMARY),
        (170, 120, "bind_tools()\n+ OutputParser", C_SECONDARY),
        (340, 120, "response_format=\njson_object", C_WARN),
        # 输出
        (170, 50, "Pydantic Model\n或 dict", C_DARK),
    ]
    so_arrows = [
        (215, 260, 65, 222),
        (215, 260, 225, 222),
        (215, 260, 395, 222),
        (65, 190, 65, 152),
        (225, 190, 225, 152),
        (395, 190, 395, 152),
        (65, 120, 225, 82),
        (225, 120, 225, 82),
        (395, 120, 225, 82),
    ]
    story.append(BoxFlowDiagram(so_boxes, so_arrows, width=480, height=300, box_w=130, box_h=32, font_size=7))
    story.append(ps("图 6-1: 结构化输出三种方式流程图"))
    story.append(spacer(12))

    story.append(h2("6.2 各 Provider 默认方式对比"))
    story.append(colored_table(
        ["Provider", "默认 method", "json_schema", "function_calling", "json_mode"],
        [
            ["ChatOpenAI", "json_schema", "支持 (原生 Structured Output API)", "支持", "支持"],
            ["ChatAnthropic", "function_calling", "支持 (output_config.format)", "支持", "不支持 (重定向到 json_schema)"],
            ["ChatOllama", "json_schema", "支持 (format=schema)", "支持", "支持 (format='json')"],
            ["ChatGroq", "function_calling", "不支持", "支持", "支持"],
            ["ChatMistralAI", "function_calling", "不支持", "支持", "不支持"],
        ],
        col_widths=[80, 80, 120, 80, 100],
    ))
    story.append(PageBreak())

    # ========================================================
    # 第七章: Embeddings 流程
    # ========================================================
    story.append(SectionBanner("第七章  Embeddings 嵌入处理流程图", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("7.1 OpenAI Embeddings 长文本处理流程"))
    story.append(p(
        "OpenAIEmbeddings 实现了智能的长文本处理策略：将超长文本自动分块嵌入，"
        "然后按 token 数加权平均合并，最后 L2 归一化。"
    ))

    emb_boxes = [
        (5, 250, "embed_documents\n(texts)", C_DARK),
        (150, 250, "check_embedding\n_ctx_length?", C_ACCENT),
        # 短路径
        (340, 250, "直接分批发送\nclient.create()", C_PRIMARY),
        # 长路径
        (150, 180, "_get_len_safe\n_embeddings()", C_SECONDARY),
        (5, 180, "_tokenize()\ntiktoken 分词", C_SECONDARY),
        (5, 110, "按 ctx_length\n分块", C_SECONDARY),
        (150, 110, "分批发送 API\n(每批 <= 300K tokens)", C_PRIMARY),
        (310, 110, "_process_batched\n_chunked_embeddings()", C_SECONDARY),
        (310, 40, "按 token 数\n加权平均 + L2归一化", C_SECONDARY),
        (150, 40, "返回\nlist[list[float]]", C_DARK),
    ]
    emb_arrows = [
        (115, 266, 150, 266),
        (260, 266, 340, 266),
        (205, 250, 205, 212),
        (150, 196, 115, 196),
        (60, 180, 60, 142),
        (115, 126, 150, 126),
        (260, 126, 310, 126),
        (365, 110, 365, 72),
        (310, 56, 260, 56),
    ]
    story.append(BoxFlowDiagram(emb_boxes, emb_arrows, width=480, height=295))
    story.append(ps("图 7-1: OpenAI Embeddings 长文本安全处理流程"))
    story.append(spacer(12))

    story.append(h2("7.2 各 Provider Embeddings 实现对比"))
    story.append(colored_table(
        ["Provider", "核心类", "默认模型", "长文本处理", "本地/远程"],
        [
            ["OpenAI", "OpenAIEmbeddings", "text-embedding-ada-002", "自动分块+加权平均", "远程 API"],
            ["Ollama", "OllamaEmbeddings", "(用户指定)", "原生处理", "本地运行"],
            ["HuggingFace", "HuggingFaceEmbeddings", "BAAI/bge-base-en-v1.5", "sentence-transformers 处理", "本地运行"],
            ["HuggingFace", "HuggingFaceEndpointEmbeddings", "(用户指定)", "API 端处理", "远程 API"],
            ["Fireworks", "FireworksEmbeddings", "(用户指定)", "原生处理", "远程 API"],
            ["MistralAI", "MistralAIEmbeddings", "(用户指定)", "原生处理", "远程 API"],
        ],
        col_widths=[70, 120, 100, 100, 70],
    ))
    story.append(PageBreak())

    # ========================================================
    # 第八章: VectorStore 架构
    # ========================================================
    story.append(SectionBanner("第八章  向量存储（VectorStore）架构", C_PRIMARY_DARK))
    story.append(spacer(12))
    story.append(h2("8.1 VectorStore 检索流程"))

    vs_boxes = [
        (170, 250, "用户查询\nquery: str", C_DARK),
        (170, 190, "VectorStore\n.similarity_search()", C_PRIMARY),
        (30, 120, "embed_query()\n查询向量化", C_SECONDARY),
        (200, 120, "向量数据库检索\nANN/HNSW 算法", C_ACCENT),
        (370, 120, "返回 top-k\nDocument 列表", C_DARK),
        (30, 50, "as_retriever()\n转为 Retriever", C_PRIMARY),
        (200, 50, "VectorStore\nRetriever", C_PRIMARY),
        (370, 50, "接入 LCEL 链\n| prompt | llm", C_SECONDARY),
    ]
    vs_arrows = [
        (225, 250, 225, 222),
        (170, 206, 85, 152),
        (225, 190, 255, 152),
        (310, 136, 370, 136),
        (85, 120, 85, 82),
        (140, 66, 200, 66),
        (310, 66, 370, 66),
    ]
    story.append(BoxFlowDiagram(vs_boxes, vs_arrows, width=490, height=295))
    story.append(ps("图 8-1: VectorStore 检索与 Retriever 桥接流程"))
    story.append(spacer(12))

    story.append(h2("8.2 Chroma vs Qdrant 对比"))
    story.append(colored_table(
        ["维度", "Chroma", "Qdrant"],
        [
            ["核心类", "Chroma(VectorStore)", "QdrantVectorStore(VectorStore)"],
            ["存储后端", "ChromaDB (本地/服务端)", "Qdrant (本地/云端/内存)"],
            ["初始化方式", "from_documents() / 构造函数", "from_documents() / from_existing_collection()"],
            ["过滤能力", "$and/$or/$eq/$ne 等", "Filter + FieldCondition (类型丰富)"],
            ["距离函数", "cosine / l2 / ip", "cosine / dot / euclid / manhattan"],
            ["稀疏向量", "不支持", "支持 (SparseEmbedding + SparseRetrieval)"],
            ["多向量", "不支持", "支持 (命名向量)"],
            ["相似度+分数", "similarity_search_with_score()", "similarity_search_with_score()"],
            ["MMR 搜索", "max_marginal_relevance_search()", "max_marginal_relevance_search()"],
        ],
        col_widths=[80, 180, 200],
    ))
    story.append(PageBreak())

    # ========================================================
    # 第九章: OpenAI 集成包核心设计
    # ========================================================
    story.append(SectionBanner("第九章  OpenAI 集成包核心设计", C_PRIMARY_DARK))
    story.append(spacer(12))

    story.append(h2("9.1 包结构"))
    story.append(code(
        "langchain_openai/\n"
        "  chat_models/\n"
        "    base.py        # BaseChatOpenAI + ChatOpenAI (~5000行)\n"
        "    azure.py       # AzureChatOpenAI\n"
        "    _client_utils.py  # httpx 客户端管理\n"
        "    _compat.py     # 输出版本兼容层\n"
        "  embeddings/\n"
        "    base.py        # OpenAIEmbeddings\n"
        "    azure.py       # AzureOpenAIEmbeddings\n"
        "  llms/\n"
        "    base.py        # BaseOpenAI (Completions API)\n"
        "    azure.py       # AzureOpenAI\n"
        "  middleware/       # 内容审核中间件\n"
        "  tools/            # @custom_tool 装饰器\n"
        "  data/             # 模型能力 Profile"
    ))
    story.append(spacer(8))

    story.append(h2("9.2 BaseChatOpenAI 核心字段"))
    story.append(colored_table(
        ["字段", "类型", "说明"],
        [
            ["model_name", "str", "模型名称，默认 gpt-3.5-turbo"],
            ["temperature", "float | None", "采样温度"],
            ["max_tokens", "int | None", "最大生成 token 数"],
            ["streaming", "bool", "是否流式输出"],
            ["use_responses_api", "bool | None", "是否使用 Responses API"],
            ["output_version", "str | None", "AIMessage 输出格式版本 (v0/v1/responses)"],
            ["reasoning_effort", "str | None", "推理努力程度控制"],
            ["disabled_params", "dict | None", "禁用特定参数（兼容 OpenAI 兼容 API）"],
            ["extra_body", "Mapping | None", "透传自定义参数"],
            ["service_tier", "str | None", "服务层级 (auto/default/flex)"],
        ],
        col_widths=[100, 100, 260],
    ))
    story.append(spacer(8))

    story.append(h2("9.3 关键方法时序"))
    story.append(SequenceDiagram(
        participants=["用户", "ChatOpenAI", "BaseChatOpenAI", "OpenAI SDK"],
        messages=[
            (0, 1, "invoke(messages)", False),
            (1, 2, "_generate(messages)", False),
            (2, 2, "_get_request_payload()", False),
            (2, 2, "_use_responses_api() 路由决策", False),
            (2, 3, "client.create() / responses.create()", False),
            (3, 2, "ChatCompletion / Response", True),
            (2, 2, "_create_chat_result() 响应解析", False),
            (2, 1, "ChatResult", True),
            (1, 0, "AIMessage", True),
        ],
        width=480, height=260,
    ))
    story.append(ps("图 9-1: ChatOpenAI 核心调用时序"))
    story.append(spacer(8))

    story.append(h2("9.4 httpx 客户端缓存机制"))
    story.append(p(
        "OpenAI 包通过 <font name='Courier'>_client_utils.py</font> 实现了高效的连接管理："
    ))
    story.append(bullet("<b>_SyncHttpxClientWrapper</b>: 继承 openai.DefaultHttpxClient，添加 __del__ 清理"))
    story.append(bullet("<b>@lru_cache</b>: 缓存 httpx 客户端实例，避免每个 ChatOpenAI 实例创建新连接"))
    story.append(bullet("支持动态 API Key: 支持 SecretStr、同步/异步 callable 三种 API 密钥形式"))
    story.append(PageBreak())

    # ========================================================
    # 第十章: Anthropic 集成包核心设计
    # ========================================================
    story.append(SectionBanner("第十章  Anthropic 集成包核心设计", C_PRIMARY_DARK))
    story.append(spacer(12))

    story.append(h2("10.1 包结构"))
    story.append(code(
        "langchain_anthropic/\n"
        "  chat_models.py   # ChatAnthropic (~2119行)\n"
        "  llms.py          # AnthropicLLM (已废弃)\n"
        "  output_parsers.py # ToolsOutputParser\n"
        "  _compat.py       # v1 格式转换兼容层\n"
        "  _client_utils.py # httpx 客户端工厂\n"
        "  middleware/\n"
        "    anthropic_tools.py   # TextEditor + Memory 中间件\n"
        "    bash.py              # Bash 工具中间件\n"
        "    file_search.py       # 文件搜索中间件\n"
        "    prompt_caching.py    # 提示缓存中间件\n"
        "  data/             # 模型能力 Profile"
    ))
    story.append(spacer(8))

    story.append(h2("10.2 ChatAnthropic 核心设计"))
    story.append(p(
        "ChatAnthropic <b>直接继承 BaseChatModel</b>（不经过中间层），完全独立实现了对 Anthropic "
        "Messages API 的集成。与 OpenAI 实现的最大区别在于消息格式和系统消息的处理方式。"
    ))

    story.append(h3("10.2.1 消息格式转换"))
    story.append(colored_table(
        ["LangChain 消息", "Anthropic 格式", "说明"],
        [
            ["SystemMessage", "独立 system 参数", "Anthropic 的 system 是顶层参数，不在消息列表中"],
            ["HumanMessage", 'role: "user"', "直接映射"],
            ["AIMessage", 'role: "assistant"', "直接映射"],
            ["ToolMessage", 'user 消息中的 tool_result block', "合并到 HumanMessage 中（Anthropic 只有 user/assistant）"],
            ["图片内容", 'source + media_type', "与 OpenAI 的 image_url 格式不同"],
        ],
        col_widths=[100, 160, 200],
    ))
    story.append(spacer(8))

    story.append(h3("10.2.2 Beta 功能自动注入"))
    story.append(p(
        "ChatAnthropic 会在构建请求时自动扫描工具列表，根据工具类型自动追加所需的 Beta header。"
        "这使得用户无需手动管理 Beta 版本号。"
    ))
    story.append(colored_table(
        ["工具类型", "Beta Header", "功能"],
        [
            ["code_execution_20250522", "code-execution-2025-05-22", "代码执行"],
            ["mcp_toolset", "mcp-client-2025-11-20", "MCP 协议"],
            ["computer_20251124", "computer-use-2025-11-24", "计算机使用"],
            ["web_fetch_20250910", "web-fetch-2025-09-10", "网页抓取"],
            ["memory_20250818", "context-management-2025-06-27", "记忆/上下文管理"],
        ],
        col_widths=[120, 150, 190],
    ))
    story.append(spacer(8))

    story.append(h3("10.2.3 Thinking（推理）模式"))
    story.append(p(
        "Anthropic 的 thinking 参数允许模型进行显式推理，流式传输中通过 "
        "<font name='Courier'>thinking_delta</font> 和 <font name='Courier'>signature_delta</font> "
        "事件逐步返回推理过程。当 thinking 启用时，tool_choice 强制调用会被自动禁用（API 限制）。"
    ))
    story.append(spacer(8))

    story.append(h3("10.2.4 Prompt Caching 中间件"))
    story.append(p(
        "AnthropicPromptCachingMiddleware 可以自动为消息添加缓存控制标记，"
        "减少重复 token 的消费。支持 5 分钟和 1 小时两种 TTL。"
    ))
    story.append(PageBreak())

    # ========================================================
    # 第十一章: 其他 Partner 包设计
    # ========================================================
    story.append(SectionBanner("第十一章  其他 Partner 集成包设计", C_PRIMARY_DARK))
    story.append(spacer(12))

    story.append(h2("11.1 ChatOllama — 本地模型集成"))
    story.append(p(
        "ChatOllama <b>直接继承 BaseChatModel</b>，通过 ollama Python SDK 与本地运行的 Ollama "
        "服务通信。它是唯一一个面向<b>本地模型</b>的主要 Partner 包。"
    ))
    story.append(bullet("通过 ollama.Client / ollama.AsyncClient 与本地 Ollama 服务通信"))
    story.append(bullet("支持 format='json' 的 JSON 模式输出"))
    story.append(bullet("流式通过 ollama.Client.chat(stream=True) 实现"))
    story.append(bullet("OllamaEmbeddings 支持本地嵌入模型"))
    story.append(bullet("OllamaLLM 支持文本补全接口"))
    story.append(spacer(8))

    story.append(h2("11.2 ChatDeepSeek — OpenAI 兼容层复用"))
    story.append(p(
        "ChatDeepSeek 是<b>最优雅的集成实现</b>之一，它直接<b>继承 BaseChatOpenAI</b>，"
        "因为 DeepSeek API 与 OpenAI API 完全兼容。主要定制："
    ))
    story.append(bullet("默认 base_url 设置为 https://api.deepseek.com"))
    story.append(bullet("API Key 环境变量改为 DEEPSEEK_API_KEY"))
    story.append(bullet("特殊处理 reasoning_content（DeepSeek 的推理输出）"))
    story.append(bullet("重写 _convert_chunk_to_generation_chunk() 处理推理流"))
    story.append(spacer(8))

    story.append(h2("11.3 ChatHuggingFace — 多后端支持"))
    story.append(p(
        "ChatHuggingFace 支持两种后端运行方式："
    ))
    story.append(bullet("<b>HuggingFace Inference API</b>: 远程 API 调用，通过 InferenceClient"))
    story.append(bullet("<b>本地 Pipeline</b>: 使用 transformers 库本地运行模型"))
    story.append(bullet("通过 tokenizer.apply_chat_template() 将消息转换为模型特定格式"))
    story.append(bullet("自动检测模型是否支持 tool calling"))
    story.append(spacer(8))

    story.append(h2("11.4 ChatGroq — 高性能推理"))
    story.append(p(
        "ChatGroq <b>直接继承 BaseChatModel</b>，完全独立实现。"
        "使用 Groq SDK 调用 Groq 的高性能推理 API。支持 tool calling 和流式输出。"
    ))
    story.append(spacer(8))

    story.append(h2("11.5 ChatMistralAI — 独立实现"))
    story.append(p(
        "ChatMistralAI <b>直接继承 BaseChatModel</b>，使用 Mistral AI SDK。"
        "支持 tool calling、流式输出、异步调用。"
    ))
    story.append(spacer(8))

    story.append(h2("11.6 ChatFireworks — OpenAI 兼容"))
    story.append(p(
        "ChatFireworks <b>直接继承 BaseChatModel</b>，但内部使用 OpenAI SDK 与 "
        "Fireworks AI 的 OpenAI 兼容端点通信。这是一种混合模式：继承独立基类但复用 OpenAI 客户端。"
    ))
    story.append(PageBreak())

    # ========================================================
    # 第十二章: 跨 Provider 对比
    # ========================================================
    story.append(SectionBanner("第十二章  跨 Provider 对比分析", C_PRIMARY_DARK))
    story.append(spacer(12))

    story.append(h2("12.1 实现策略对比"))
    story.append(colored_table(
        ["实现策略", "代表 Provider", "优势", "劣势"],
        [
            ["继承 BaseChatOpenAI", "DeepSeek", "代码复用最大化，维护成本低", "受限于 OpenAI 的接口设计"],
            ["直接继承 BaseChatModel", "Anthropic, Ollama, Groq", "完全自主控制，可深度定制", "代码量大，每家独立维护"],
            ["独立实现 + OpenAI SDK", "Fireworks", "灵活性与复用的折中", "两层抽象可能复杂"],
        ],
        col_widths=[110, 120, 130, 100],
    ))
    story.append(spacer(12))

    story.append(h2("12.2 核心能力矩阵"))
    story.append(colored_table(
        ["能力", "OpenAI", "Anthropic", "Ollama", "DeepSeek", "Groq", "Mistral", "Fireworks"],
        [
            ["Chat Model", "Y", "Y", "Y", "Y", "Y", "Y", "Y"],
            ["Completions LLM", "Y", "Y (废弃)", "Y", "-", "-", "-", "Y"],
            ["Embeddings", "Y", "-", "Y", "-", "-", "Y", "Y"],
            ["Tool Calling", "Y", "Y", "Y", "Y", "Y", "Y", "Y"],
            ["Structured Output", "3种", "2种", "3种", "继承 OpenAI", "2种", "1种", "2种"],
            ["Streaming", "Y", "Y", "Y", "Y", "Y", "Y", "Y"],
            ["异步原生", "Y", "Y", "Y", "Y", "Y", "Y", "Y"],
            ["推理/思考", "reasoning_effort", "thinking", "-", "reasoning_content", "-", "-", "-"],
            ["内置工具", "有限", "丰富", "-", "-", "-", "-", "-"],
            ["Middleware", "审核", "缓存+工具+Bash", "-", "-", "-", "-", "-"],
        ],
        col_widths=[70, 52, 56, 48, 56, 44, 48, 56],
    ))
    story.append(spacer(12))

    story.append(h2("12.3 消息格式差异"))
    story.append(colored_table(
        ["维度", "OpenAI", "Anthropic", "Ollama"],
        [
            ["系统消息", "role: 'system' 消息", "独立 system 顶层参数", "role: 'system' 消息"],
            ["消息角色", "system/user/assistant/tool", "user/assistant (仅两种)", "system/user/assistant/tool"],
            ["ToolMessage", "独立 tool 角色", "合并到 user 的 tool_result block", "独立 tool 角色"],
            ["图片格式", "image_url", "source + media_type", "images 列表 (base64)"],
            ["工具调用", "tool_calls 字段", "content 中的 tool_use block", "message.tool_calls"],
        ],
        col_widths=[80, 140, 140, 100],
    ))
    story.append(spacer(12))

    story.append(h2("12.4 同步-异步桥接模式"))
    story.append(p(
        "所有 Partner 包都遵循 LangChain 的同步-异步桥接模式：默认情况下，所有异步方法 "
        "（ainvoke, astream, aembed_query 等）通过 <font name='Courier'>run_in_executor</font> "
        "自动将同步方法包装为异步版本。但大多数 Partner 包都重写了原生异步实现（如使用 "
        "AsyncOpenAI、AsyncAnthropic 客户端），以获得更好的性能。"
    ))
    story.append(spacer(20))
    story.append(hr())
    story.append(spacer(8))
    end_style = make_style("end", fontName=CHINESE_FONT, fontSize=10,
                           leading=16, textColor=C_GRAY, alignment=TA_CENTER)
    story.append(Paragraph("— 文档结束 —", end_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "本文档基于 LangChain v0.1.16 源码分析生成，涵盖 libs/partners 目录下所有核心集成包。",
        end_style
    ))

    # ========== 构建 PDF ==========
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_page)
    print(f"PDF 已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    build_document()
