#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 LangChain v1 源码架构分析 PDF 文档。

使用 reportlab 生成包含流程图、时序图说明和核心类设计的 PDF。
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor

# ─────────────── 字体注册 ───────────────
# 尝试多种中文字体路径
FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]

FONT_REGISTERED = False
CHINESE_FONT = "Helvetica"

for fp in FONT_PATHS:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont("ChineseFont", fp, subfontIndex=0))
            CHINESE_FONT = "ChineseFont"
            FONT_REGISTERED = True
            break
        except Exception:
            continue

if not FONT_REGISTERED:
    print("警告：未找到中文字体，中文可能无法正确显示。尝试使用 Helvetica。")


# ─────────────── 样式定义 ───────────────
styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "ChTitle", parent=styles["Title"],
    fontName=CHINESE_FONT, fontSize=24, leading=30,
    textColor=HexColor("#1a1a2e"), spaceAfter=20,
    alignment=TA_CENTER,
)

SUBTITLE_STYLE = ParagraphStyle(
    "ChSubTitle", parent=styles["Title"],
    fontName=CHINESE_FONT, fontSize=14, leading=18,
    textColor=HexColor("#555555"), spaceAfter=30,
    alignment=TA_CENTER,
)

H1_STYLE = ParagraphStyle(
    "ChH1", parent=styles["Heading1"],
    fontName=CHINESE_FONT, fontSize=18, leading=24,
    textColor=HexColor("#16213e"), spaceBefore=20, spaceAfter=12,
    borderWidth=0, borderPadding=0,
    borderColor=HexColor("#0f3460"),
)

H2_STYLE = ParagraphStyle(
    "ChH2", parent=styles["Heading2"],
    fontName=CHINESE_FONT, fontSize=14, leading=18,
    textColor=HexColor("#0f3460"), spaceBefore=14, spaceAfter=8,
)

H3_STYLE = ParagraphStyle(
    "ChH3", parent=styles["Heading3"],
    fontName=CHINESE_FONT, fontSize=12, leading=16,
    textColor=HexColor("#533483"), spaceBefore=10, spaceAfter=6,
)

BODY_STYLE = ParagraphStyle(
    "ChBody", parent=styles["Normal"],
    fontName=CHINESE_FONT, fontSize=10, leading=16,
    textColor=HexColor("#333333"), spaceAfter=6,
    alignment=TA_JUSTIFY,
)

CODE_STYLE = ParagraphStyle(
    "ChCode", parent=styles["Code"],
    fontName="Courier", fontSize=8, leading=12,
    textColor=HexColor("#2d3436"), spaceAfter=4,
    backColor=HexColor("#f5f5f5"),
    borderWidth=0.5, borderColor=HexColor("#dfe6e9"),
    borderPadding=4,
)

BULLET_STYLE = ParagraphStyle(
    "ChBullet", parent=BODY_STYLE,
    fontName=CHINESE_FONT, fontSize=10, leading=16,
    leftIndent=20, bulletIndent=8, spaceAfter=4,
)

TABLE_HEADER_STYLE = ParagraphStyle(
    "TableHeader", parent=styles["Normal"],
    fontName=CHINESE_FONT, fontSize=9, leading=12,
    textColor=colors.white, alignment=TA_CENTER,
)

TABLE_CELL_STYLE = ParagraphStyle(
    "TableCell", parent=styles["Normal"],
    fontName=CHINESE_FONT, fontSize=8.5, leading=12,
    textColor=HexColor("#333333"),
)


# ─────────────── 辅助函数 ───────────────
def h1(text):
    return Paragraph(text, H1_STYLE)

def h2(text):
    return Paragraph(text, H2_STYLE)

def h3(text):
    return Paragraph(text, H3_STYLE)

def body(text):
    return Paragraph(text, BODY_STYLE)

def bullet(text):
    return Paragraph(f"• {text}", BULLET_STYLE)

def code(text):
    return Paragraph(text, CODE_STYLE)

def spacer(h=6):
    return Spacer(1, h)

def hr():
    return HRFlowable(width="100%", thickness=1, color=HexColor("#dfe6e9"), spaceAfter=10, spaceBefore=10)

def make_table(headers, rows, col_widths=None):
    """创建格式化表格"""
    header_cells = [Paragraph(h, TABLE_HEADER_STYLE) for h in headers]
    data = [header_cells]
    for row in rows:
        data.append([Paragraph(str(c), TABLE_CELL_STYLE) for c in row])

    if col_widths is None:
        col_widths = [460 / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#0f3460")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f8f9fa")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f1f3f5")]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    return t


def make_flow_box(drawing, x, y, w, h, text, fill_color="#e3f2fd", border_color="#1976d2", font_size=8):
    """在 Drawing 上绘制流程框"""
    r = Rect(x, y, w, h, fillColor=HexColor(fill_color), strokeColor=HexColor(border_color), strokeWidth=1)
    drawing.add(r)
    s = String(x + w/2, y + h/2 - font_size/3, text, fontName=CHINESE_FONT, fontSize=font_size, textAnchor='middle', fillColor=HexColor("#1a1a2e"))
    drawing.add(s)

def make_arrow(drawing, x1, y1, x2, y2, color="#666666"):
    """在 Drawing 上绘制箭头线"""
    line = Line(x1, y1, x2, y2, strokeColor=HexColor(color), strokeWidth=1)
    drawing.add(line)
    # 箭头头部
    arrow_size = 4
    if y1 > y2:  # 向下
        drawing.add(Polygon([x2 - arrow_size, y2 + arrow_size*1.5, x2, y2, x2 + arrow_size, y2 + arrow_size*1.5],
                            fillColor=HexColor(color), strokeColor=HexColor(color)))
    elif x1 < x2:  # 向右
        drawing.add(Polygon([x2 - arrow_size*1.5, y2 - arrow_size, x2, y2, x2 - arrow_size*1.5, y2 + arrow_size],
                            fillColor=HexColor(color), strokeColor=HexColor(color)))
    elif x1 > x2:  # 向左
        drawing.add(Polygon([x2 + arrow_size*1.5, y2 - arrow_size, x2, y2, x2 + arrow_size*1.5, y2 + arrow_size],
                            fillColor=HexColor(color), strokeColor=HexColor(color)))


def make_diamond(drawing, cx, cy, w, h, text, fill_color="#fff3e0", border_color="#e65100", font_size=7):
    """在 Drawing 上绘制菱形判断框"""
    points = [cx, cy + h/2, cx + w/2, cy, cx, cy - h/2, cx - w/2, cy]
    drawing.add(Polygon(points, fillColor=HexColor(fill_color), strokeColor=HexColor(border_color), strokeWidth=1))
    s = String(cx, cy - font_size/3, text, fontName=CHINESE_FONT, fontSize=font_size, textAnchor='middle', fillColor=HexColor("#333333"))
    drawing.add(s)


# ─────────────── 流程图绘制 ───────────────
def draw_agent_loop_flowchart():
    """绘制 Agent 主循环流程图"""
    d = Drawing(480, 420)
    # 背景
    d.add(Rect(0, 0, 480, 420, fillColor=HexColor("#fafbfc"), strokeColor=HexColor("#e0e0e0"), strokeWidth=0.5))

    # START
    make_flow_box(d, 200, 385, 80, 25, "START", "#c8e6c9", "#388e3c")
    make_arrow(d, 240, 385, 240, 365)

    # before_agent
    make_flow_box(d, 175, 340, 130, 25, "before_agent", "#e8eaf6", "#3f51b5")
    make_arrow(d, 240, 340, 240, 320)

    # before_model
    make_flow_box(d, 175, 295, 130, 25, "before_model", "#e8eaf6", "#3f51b5")
    make_arrow(d, 240, 295, 240, 275)

    # Model Node
    make_flow_box(d, 180, 250, 120, 25, "Model Node", "#bbdefb", "#1565c0")
    make_arrow(d, 240, 250, 240, 230)

    # wrap_model_call
    d.add(Rect(160, 225, 160, 10, fillColor=None, strokeColor=HexColor("#ff9800"), strokeWidth=0.5, strokeDashArray=[2,2]))
    s = String(240, 227, "wrap_model_call", fontName=CHINESE_FONT, fontSize=6, textAnchor='middle', fillColor=HexColor("#e65100"))
    d.add(s)

    # after_model
    make_flow_box(d, 175, 200, 130, 25, "after_model", "#e8eaf6", "#3f51b5")
    make_arrow(d, 240, 200, 240, 175)

    # 判断：有 tool_calls?
    make_diamond(d, 240, 155, 140, 35, "tool_calls?", "#fff3e0", "#e65100")

    # Yes -> Tools Node
    make_arrow(d, 310, 155, 400, 155, "#388e3c")
    d.add(String(340, 160, "Yes", fontName="Helvetica", fontSize=7, fillColor=HexColor("#388e3c")))
    make_flow_box(d, 370, 142, 90, 25, "Tools Node", "#fff9c4", "#f9a825")

    # wrap_tool_call
    d.add(Rect(365, 130, 100, 10, fillColor=None, strokeColor=HexColor("#ff9800"), strokeWidth=0.5, strokeDashArray=[2,2]))
    s = String(415, 132, "wrap_tool_call", fontName=CHINESE_FONT, fontSize=6, textAnchor='middle', fillColor=HexColor("#e65100"))
    d.add(s)

    # Tools -> back to before_model (loop)
    make_arrow(d, 415, 130, 415, 100, "#666666")
    d.add(Line(415, 100, 80, 100, strokeColor=HexColor("#666666"), strokeWidth=1))
    d.add(Line(80, 100, 80, 307, strokeColor=HexColor("#666666"), strokeWidth=1))
    make_arrow(d, 80, 307, 175, 307, "#666666")
    d.add(String(90, 200, "Loop", fontName="Helvetica-Oblique", fontSize=7, fillColor=HexColor("#999999")))

    # No -> 判断 structured_response?
    make_arrow(d, 240, 137, 240, 110)
    d.add(String(248, 127, "No", fontName="Helvetica", fontSize=7, fillColor=HexColor("#d32f2f")))

    # after_agent
    make_flow_box(d, 175, 80, 130, 25, "after_agent", "#e8eaf6", "#3f51b5")
    make_arrow(d, 240, 80, 240, 55)

    # END
    make_flow_box(d, 200, 30, 80, 25, "END", "#ffcdd2", "#c62828")

    return d


def draw_middleware_composition():
    """绘制中间件组合时序图"""
    d = Drawing(480, 320)
    d.add(Rect(0, 0, 480, 320, fillColor=HexColor("#fafbfc"), strokeColor=HexColor("#e0e0e0"), strokeWidth=0.5))

    # 参与者
    actors = [("Client", 60), ("Outer MW", 160), ("Inner MW", 260), ("Model", 380)]
    for name, x in actors:
        make_flow_box(d, x-35, 290, 70, 22, name, "#e3f2fd", "#1976d2", 8)
        d.add(Line(x, 290, x, 30, strokeColor=HexColor("#bbbbbb"), strokeWidth=0.5, strokeDashArray=[3,3]))

    y = 275
    step = 30

    # 1. Client -> Outer
    d.add(Line(60, y, 160, y, strokeColor=HexColor("#1976d2"), strokeWidth=1))
    d.add(Polygon([155, y-3, 160, y, 155, y+3], fillColor=HexColor("#1976d2")))
    d.add(String(110, y+4, "request", fontName="Helvetica", fontSize=7, fillColor=HexColor("#333333")))
    y -= step

    # 2. Outer -> Inner
    d.add(Line(160, y, 260, y, strokeColor=HexColor("#388e3c"), strokeWidth=1))
    d.add(Polygon([255, y-3, 260, y, 255, y+3], fillColor=HexColor("#388e3c")))
    d.add(String(195, y+4, "handler(req)", fontName="Helvetica", fontSize=7, fillColor=HexColor("#333333")))
    y -= step

    # 3. Inner -> Model
    d.add(Line(260, y, 380, y, strokeColor=HexColor("#e65100"), strokeWidth=1))
    d.add(Polygon([375, y-3, 380, y, 375, y+3], fillColor=HexColor("#e65100")))
    d.add(String(310, y+4, "handler(req)", fontName="Helvetica", fontSize=7, fillColor=HexColor("#333333")))
    y -= step

    # 4. Model -> Inner (response)
    d.add(Line(380, y, 260, y, strokeColor=HexColor("#e65100"), strokeWidth=1, strokeDashArray=[4,2]))
    d.add(Polygon([265, y-3, 260, y, 265, y+3], fillColor=HexColor("#e65100")))
    d.add(String(305, y+4, "ModelResponse", fontName="Helvetica", fontSize=7, fillColor=HexColor("#666666")))
    y -= step

    # 5. Inner -> Outer (response)
    d.add(Line(260, y, 160, y, strokeColor=HexColor("#388e3c"), strokeWidth=1, strokeDashArray=[4,2]))
    d.add(Polygon([165, y-3, 160, y, 165, y+3], fillColor=HexColor("#388e3c")))
    d.add(String(195, y+4, "ModelResponse", fontName="Helvetica", fontSize=7, fillColor=HexColor("#666666")))
    y -= step

    # 6. Outer -> Client (response)
    d.add(Line(160, y, 60, y, strokeColor=HexColor("#1976d2"), strokeWidth=1, strokeDashArray=[4,2]))
    d.add(Polygon([65, y-3, 60, y, 65, y+3], fillColor=HexColor("#1976d2")))
    d.add(String(95, y+4, "ModelResponse", fontName="Helvetica", fontSize=7, fillColor=HexColor("#666666")))

    # 标注
    d.add(Rect(15, 45, 150, 35, fillColor=HexColor("#fffde7"), strokeColor=HexColor("#f9a825"), strokeWidth=0.5))
    d.add(String(20, 65, "Outer wraps Inner", fontName="Helvetica-Bold", fontSize=7, fillColor=HexColor("#333333")))
    d.add(String(20, 53, "First in list = Outermost", fontName="Helvetica", fontSize=7, fillColor=HexColor("#666666")))

    return d


def draw_create_agent_flow():
    """绘制 create_agent 初始化流程图"""
    d = Drawing(480, 360)
    d.add(Rect(0, 0, 480, 360, fillColor=HexColor("#fafbfc"), strokeColor=HexColor("#e0e0e0"), strokeWidth=0.5))

    y = 335
    step = 40

    make_flow_box(d, 170, y, 140, 22, "create_agent()", "#c8e6c9", "#388e3c", 9)
    make_arrow(d, 240, y, 240, y - 18)
    y -= step

    make_flow_box(d, 140, y, 200, 22, "init_chat_model(model)", "#e3f2fd", "#1976d2", 8)
    make_arrow(d, 240, y, 240, y - 18)
    y -= step

    make_flow_box(d, 120, y, 240, 22, "resolve response_format strategy", "#fff3e0", "#e65100", 8)
    make_arrow(d, 240, y, 240, y - 18)
    y -= step

    make_flow_box(d, 130, y, 220, 22, "collect middleware hooks", "#e8eaf6", "#3f51b5", 8)
    make_arrow(d, 240, y, 240, y - 18)
    y -= step

    make_flow_box(d, 120, y, 240, 22, "chain wrap_model_call handlers", "#fce4ec", "#c62828", 8)
    make_arrow(d, 240, y, 240, y - 18)
    y -= step

    make_flow_box(d, 120, y, 240, 22, "chain wrap_tool_call handlers", "#fce4ec", "#c62828", 8)
    make_arrow(d, 240, y, 240, y - 18)
    y -= step

    make_flow_box(d, 120, y, 240, 22, "build StateGraph + add nodes/edges", "#e0f7fa", "#00695c", 8)
    make_arrow(d, 240, y, 240, y - 18)
    y -= step

    make_flow_box(d, 130, y, 220, 22, "graph.compile() => CompiledStateGraph", "#c8e6c9", "#388e3c", 8)

    return d


def draw_structured_output_flow():
    """绘制结构化输出处理流程图"""
    d = Drawing(480, 280)
    d.add(Rect(0, 0, 480, 280, fillColor=HexColor("#fafbfc"), strokeColor=HexColor("#e0e0e0"), strokeWidth=0.5))

    make_flow_box(d, 170, 250, 140, 22, "Model Response", "#bbdefb", "#1565c0", 9)
    make_arrow(d, 240, 250, 240, 233)

    make_diamond(d, 240, 215, 160, 30, "response_format?", "#fff3e0", "#e65100", 7)

    # None -> direct
    d.add(Line(320, 215, 420, 215, strokeColor=HexColor("#666666"), strokeWidth=1))
    d.add(String(350, 220, "None", fontName="Helvetica", fontSize=7, fillColor=HexColor("#999999")))
    make_flow_box(d, 380, 204, 90, 22, "return messages", "#c8e6c9", "#388e3c", 7)

    # has format -> check type
    make_arrow(d, 240, 200, 240, 180)

    make_diamond(d, 240, 162, 180, 30, "ProviderStrategy?", "#fff3e0", "#e65100", 7)

    # Yes -> provider
    d.add(Line(330, 162, 420, 162, strokeColor=HexColor("#388e3c"), strokeWidth=1))
    d.add(String(355, 167, "Yes", fontName="Helvetica", fontSize=7, fillColor=HexColor("#388e3c")))
    make_flow_box(d, 380, 151, 95, 22, "parse JSON content", "#e8eaf6", "#3f51b5", 7)

    # No -> ToolStrategy
    make_arrow(d, 240, 147, 240, 125)
    d.add(String(248, 137, "No", fontName="Helvetica", fontSize=7, fillColor=HexColor("#d32f2f")))

    make_diamond(d, 240, 107, 180, 30, "ToolStrategy + tool_calls?", "#fff3e0", "#e65100", 7)

    d.add(Line(330, 107, 420, 107, strokeColor=HexColor("#388e3c"), strokeWidth=1))
    d.add(String(355, 112, "Yes", fontName="Helvetica", fontSize=7, fillColor=HexColor("#388e3c")))
    make_flow_box(d, 378, 96, 98, 22, "parse tool args", "#e8eaf6", "#3f51b5", 7)

    make_arrow(d, 240, 92, 240, 70)
    make_flow_box(d, 140, 50, 200, 22, "return structured_response", "#c8e6c9", "#388e3c", 8)

    return d


# ─────────────── 文档内容构建 ───────────────
def build_document():
    """构建 PDF 文档内容"""
    story = []

    # ═══════════════ 封面 ═══════════════
    story.append(Spacer(1, 80))
    story.append(Paragraph("LangChain v1 源码架构分析", TITLE_STYLE))
    story.append(Spacer(1, 10))
    story.append(Paragraph("langchain_v1 核心模块设计与流程说明", SUBTITLE_STYLE))
    story.append(Spacer(1, 20))
    story.append(hr())
    story.append(Spacer(1, 10))
    story.append(Paragraph("版本：v1.2.13 (langchain_v1)", ParagraphStyle("ver", parent=BODY_STYLE, alignment=TA_CENTER, fontSize=10)))
    story.append(Paragraph("基于 Agent + Middleware 架构的下一代 LangChain 框架", ParagraphStyle("desc", parent=BODY_STYLE, alignment=TA_CENTER, fontSize=10, textColor=HexColor("#666666"))))
    story.append(PageBreak())

    # ═══════════════ 目录 ═══════════════
    story.append(h1("目  录"))
    story.append(spacer(10))
    toc_items = [
        "一、项目概览与整体架构",
        "二、模块结构说明",
        "三、核心流程图：Agent 主循环",
        "四、核心流程图：create_agent 初始化",
        "五、核心流程图：结构化输出处理",
        "六、核心时序图：中间件组合模式",
        "七、核心类设计说明 — AgentMiddleware",
        "八、核心类设计说明 — create_agent 工厂函数",
        "九、核心类设计说明 — ModelRequest / ModelResponse",
        "十、核心类设计说明 — 结构化输出策略",
        "十一、核心类设计说明 — init_chat_model 工厂",
        "十二、核心类设计说明 — init_embeddings 工厂",
        "十三、内置中间件一览",
        "十四、设计哲学与总结",
    ]
    for item in toc_items:
        story.append(Paragraph(item, ParagraphStyle("toc", parent=BODY_STYLE, fontSize=11, leading=20, leftIndent=20)))
    story.append(PageBreak())

    # ═══════════════ 一、项目概览 ═══════════════
    story.append(h1("一、项目概览与整体架构"))
    story.append(body(
        "LangChain v1（langchain_v1）是 LangChain 框架的下一代重构版本，采用了全新的"
        "<b>Agent + Middleware</b> 架构设计。与传统 LangChain（langchain-classic）相比，"
        "v1 版本做了极大的精简，移除了 Chains、Retrievers、Memory、VectorStores 等模块，"
        "转而以<b>中间件模式</b>实现所有横切关注点（cross-cutting concerns）。"
    ))
    story.append(spacer(6))
    story.append(body(
        "langchain_v1 构建在 <b>LangGraph</b>（状态图引擎）和 <b>langchain-core</b>（核心抽象层）之上，"
        "通过 StateGraph 构建 Agent 的执行图，将'模型调用-工具执行'循环编排为可编译的状态机。"
        "中间件可以在 Agent 生命周期的各个阶段插入自定义逻辑，实现重试、限流、PII 脱敏、摘要、"
        "人工审核等功能。"
    ))
    story.append(spacer(10))

    story.append(h2("核心设计原则"))
    story.append(bullet("<b>极简 API</b>：对外仅暴露 create_agent() 一个核心入口"))
    story.append(bullet("<b>中间件驱动</b>：所有扩展逻辑通过 AgentMiddleware 子类实现"))
    story.append(bullet("<b>基于 LangGraph</b>：Agent 执行流是一个可编译的 StateGraph"))
    story.append(bullet("<b>类型安全</b>：大量使用泛型、TypedDict、Protocol 确保类型安全"))
    story.append(bullet("<b>同步/异步双模式</b>：所有钩子和处理器均支持同步和异步版本"))
    story.append(PageBreak())

    # ═══════════════ 二、模块结构 ═══════════════
    story.append(h1("二、模块结构说明"))
    story.append(body("langchain_v1 的源码包非常精简，仅包含 6 个子模块，约 30 个源码文件："))
    story.append(spacer(6))
    story.append(make_table(
        ["模块", "文件数", "核心职责"],
        [
            ["agents/", "约 20 个", "Agent 工厂、中间件类型系统、17 种内置中间件"],
            ["chat_models/", "2 个", "聊天模型工厂 init_chat_model，支持 25+ 提供商"],
            ["embeddings/", "2 个", "嵌入模型工厂 init_embeddings，支持 10+ 提供商"],
            ["tools/", "2 个", "工具相关类型的重新导出（BaseTool、ToolRuntime 等）"],
            ["messages/", "1 个", "消息类型的统一重新导出（AIMessage、ToolMessage 等）"],
            ["rate_limiters/", "1 个", "速率限制器的重新导出"],
        ],
        col_widths=[80, 60, 320]
    ))
    story.append(spacer(10))
    story.append(body(
        "其中 <b>agents/</b> 是最核心、最庞大的模块。factory.py（约 1860 行）是整个框架的核心，"
        "middleware/types.py（约 2050 行）定义了完整的中间件类型系统。"
    ))
    story.append(PageBreak())

    # ═══════════════ 三、Agent 主循环流程图 ═══════════════
    story.append(h1("三、核心流程图：Agent 主循环"))
    story.append(body(
        "Agent 的核心执行流程是一个'模型调用-工具执行'的循环。当模型返回 tool_calls 时，"
        "Agent 会执行对应的工具，然后将结果反馈给模型，直到模型不再调用工具为止。"
        "中间件可以在循环的各个阶段插入自定义逻辑。"
    ))
    story.append(spacer(8))
    story.append(draw_agent_loop_flowchart())
    story.append(spacer(10))
    story.append(h3("流程说明"))
    story.append(bullet("<b>START -&gt; before_agent</b>：Agent 启动前执行一次（如初始化、资源加载）"))
    story.append(bullet("<b>before_model</b>：每次模型调用前执行（如消息预处理、限流检查）"))
    story.append(bullet("<b>Model Node</b>：调用 LLM，wrap_model_call 中间件可拦截此调用"))
    story.append(bullet("<b>after_model</b>：模型返回后执行（如响应后处理、日志记录）"))
    story.append(bullet("<b>tool_calls 判断</b>：如果 AIMessage 包含 tool_calls，进入工具执行"))
    story.append(bullet("<b>Tools Node</b>：并行执行工具，wrap_tool_call 中间件可拦截工具调用"))
    story.append(bullet("<b>Loop</b>：工具执行完毕后回到 before_model 开始下一轮循环"))
    story.append(bullet("<b>after_agent -&gt; END</b>：循环结束后执行一次（如资源清理、最终处理）"))
    story.append(PageBreak())

    # ═══════════════ 四、create_agent 初始化流程图 ═══════════════
    story.append(h1("四、核心流程图：create_agent 初始化"))
    story.append(body(
        "create_agent() 是构建 Agent 的唯一入口函数。它接受模型、工具、中间件等参数，"
        "构建一个完整的 StateGraph 并编译为可执行的 CompiledStateGraph。"
    ))
    story.append(spacer(8))
    story.append(draw_create_agent_flow())
    story.append(spacer(10))
    story.append(h3("初始化步骤详解"))
    story.append(bullet("<b>init_chat_model</b>：将模型字符串（如 'openai:gpt-4o'）解析为 BaseChatModel 实例"))
    story.append(bullet("<b>resolve response_format</b>：确定结构化输出策略（AutoStrategy/ToolStrategy/ProviderStrategy）"))
    story.append(bullet("<b>collect middleware hooks</b>：遍历中间件，分类收集各生命周期钩子"))
    story.append(bullet("<b>chain handlers</b>：将同类钩子组合为嵌套的处理器链（洋葱模型）"))
    story.append(bullet("<b>build StateGraph</b>：创建状态图，添加节点（model/tools/中间件）和边（包括条件边）"))
    story.append(bullet("<b>graph.compile()</b>：编译状态图，生成可执行的 CompiledStateGraph"))
    story.append(PageBreak())

    # ═══════════════ 五、结构化输出处理 ═══════════════
    story.append(h1("五、核心流程图：结构化输出处理"))
    story.append(body(
        "langchain_v1 支持两种结构化输出策略：<b>ProviderStrategy</b>（利用提供商原生的 JSON Schema 能力）"
        "和 <b>ToolStrategy</b>（通过工具调用实现结构化输出）。AutoStrategy 会根据模型能力自动选择最佳策略。"
    ))
    story.append(spacer(8))
    story.append(draw_structured_output_flow())
    story.append(spacer(10))
    story.append(h3("策略选择逻辑"))
    story.append(bullet("<b>AutoStrategy</b>：自动检测模型是否支持 provider 原生结构化输出。如支持则用 ProviderStrategy，否则回退到 ToolStrategy"))
    story.append(bullet("<b>ProviderStrategy</b>：利用 model.bind_tools() 的 response_format 参数，由提供商保证 JSON 格式合规"))
    story.append(bullet("<b>ToolStrategy</b>：将 schema 包装为虚拟工具（StructuredTool），强制模型调用该工具，从 tool_call args 中解析结构化响应"))
    story.append(PageBreak())

    # ═══════════════ 六、中间件组合时序图 ═══════════════
    story.append(h1("六、核心时序图：中间件组合模式"))
    story.append(body(
        "多个中间件的 wrap_model_call / wrap_tool_call 钩子采用<b>洋葱模型</b>组合，"
        "即列表中第一个中间件是最外层，最后一个是最内层。"
        "每个中间件通过 handler 回调链式调用下一层，最终到达实际的模型/工具执行。"
    ))
    story.append(spacer(8))
    story.append(draw_middleware_composition())
    story.append(spacer(10))
    story.append(h3("组合细节"))
    story.append(bullet("内部使用 _chain_model_call_handlers() 将多个 handler 函数通过 compose_two() 逐层嵌套"))
    story.append(bullet("每层中间件可以：修改请求、多次调用 handler（重试）、跳过 handler（短路）、修改响应"))
    story.append(bullet("Command 从内层到外层累积，最终由 _build_commands() 统一处理"))
    story.append(bullet("同步和异步版本分别实现（_chain_model_call_handlers / _chain_async_model_call_handlers）"))
    story.append(PageBreak())

    # ═══════════════ 七、AgentMiddleware ═══════════════
    story.append(h1("七、核心类设计说明 — AgentMiddleware"))
    story.append(body(
        "AgentMiddleware 是所有中间件的基类，定义了 Agent 生命周期中可扩展的钩子方法。"
        "它使用三个泛型参数：StateT（状态类型）、ContextT（运行时上下文）、ResponseT（结构化响应类型）。"
    ))
    story.append(spacer(6))

    story.append(h2("7.1 类签名"))
    story.append(code("class AgentMiddleware(Generic[StateT, ContextT, ResponseT])"))
    story.append(spacer(4))

    story.append(h2("7.2 生命周期钩子"))
    story.append(make_table(
        ["钩子方法", "执行时机", "执行频次", "可返回类型"],
        [
            ["before_agent / abefore_agent", "Agent 启动前", "仅一次", "dict | None"],
            ["before_model / abefore_model", "每次模型调用前", "每轮循环", "dict | None"],
            ["wrap_model_call / awrap_model_call", "拦截模型调用", "每轮循环", "ModelResponse | AIMessage | ExtendedModelResponse"],
            ["after_model / aafter_model", "模型返回后", "每轮循环", "dict | None"],
            ["wrap_tool_call / awrap_tool_call", "拦截工具调用", "每次工具调用", "ToolMessage | Command"],
            ["after_agent / aafter_agent", "Agent 结束后", "仅一次", "dict | None"],
        ],
        col_widths=[135, 85, 65, 175]
    ))
    story.append(spacer(8))

    story.append(h2("7.3 重要属性"))
    story.append(bullet("<b>state_schema</b>：中间件使用的自定义状态 TypedDict 类型，会与基础 AgentState 合并"))
    story.append(bullet("<b>tools</b>：中间件注册的额外工具列表"))
    story.append(bullet("<b>name</b>：中间件名称（默认为类名），用于状态图节点命名"))

    story.append(spacer(8))
    story.append(h2("7.4 装饰器快捷方式"))
    story.append(body("除了继承 AgentMiddleware 基类外，还可以通过装饰器快速创建中间件："))
    story.append(make_table(
        ["装饰器", "对应钩子", "说明"],
        [
            ["@before_agent", "before_agent", "Agent 执行前的一次性逻辑"],
            ["@before_model", "before_model", "模型调用前的预处理逻辑"],
            ["@after_model", "after_model", "模型返回后的后处理逻辑"],
            ["@after_agent", "after_agent", "Agent 结束后的清理逻辑"],
            ["@wrap_model_call", "wrap_model_call", "拦截模型调用的中间件"],
            ["@wrap_tool_call", "wrap_tool_call", "拦截工具调用的中间件"],
            ["@dynamic_prompt", "wrap_model_call", "动态生成系统提示词"],
            ["@hook_config", "任意钩子", "配置钩子行为（如 can_jump_to）"],
        ],
        col_widths=[110, 110, 240]
    ))
    story.append(PageBreak())

    # ═══════════════ 八、create_agent ═══════════════
    story.append(h1("八、核心类设计说明 — create_agent 工厂函数"))
    story.append(body(
        "create_agent() 是 langchain_v1 最核心的 API，位于 agents/factory.py。"
        "它是一个纯函数（非类），接受声明式配置参数，返回编译后的 StateGraph。"
    ))
    story.append(spacer(6))

    story.append(h2("8.1 函数签名"))
    story.append(code(
        "def create_agent(<br/>"
        "&nbsp;&nbsp;model: str | BaseChatModel,<br/>"
        "&nbsp;&nbsp;tools: Sequence[BaseTool | Callable | dict] | None = None,<br/>"
        "&nbsp;&nbsp;*,<br/>"
        "&nbsp;&nbsp;system_prompt: str | SystemMessage | None = None,<br/>"
        "&nbsp;&nbsp;middleware: Sequence[AgentMiddleware] = (),<br/>"
        "&nbsp;&nbsp;response_format: ResponseFormat | type | dict | None = None,<br/>"
        "&nbsp;&nbsp;state_schema: type[AgentState] | None = None,<br/>"
        "&nbsp;&nbsp;context_schema: type | None = None,<br/>"
        "&nbsp;&nbsp;checkpointer: Checkpointer | None = None,<br/>"
        "&nbsp;&nbsp;store: BaseStore | None = None,<br/>"
        "&nbsp;&nbsp;...<br/>"
        ") -> CompiledStateGraph"
    ))
    story.append(spacer(6))

    story.append(h2("8.2 核心参数说明"))
    story.append(make_table(
        ["参数", "类型", "说明"],
        [
            ["model", "str | BaseChatModel", "模型标识，如 'openai:gpt-4o' 或 BaseChatModel 实例"],
            ["tools", "Sequence[...] | None", "工具列表，支持 BaseTool、Callable、dict（内置提供商工具）"],
            ["system_prompt", "str | SystemMessage | None", "系统提示词，作为每次模型调用的前缀"],
            ["middleware", "Sequence[AgentMiddleware]", "中间件序列，按顺序应用"],
            ["response_format", "ResponseFormat | type | None", "结构化输出配置（Pydantic/TypedDict/dict）"],
            ["checkpointer", "Checkpointer | None", "状态持久化，用于多轮对话记忆"],
            ["store", "BaseStore | None", "跨线程数据持久化（跨会话/用户）"],
        ],
        col_widths=[95, 140, 225]
    ))
    story.append(spacer(6))

    story.append(h2("8.3 内部关键流程"))
    story.append(bullet("使用 _resolve_schema() 合并所有中间件的 state_schema 和基础 AgentState"))
    story.append(bullet("通过 _chain_model_call_handlers() 将 wrap_model_call 钩子组合为洋葱模型"))
    story.append(bullet("构建 StateGraph 时根据中间件类型动态添加节点和条件边"))
    story.append(bullet("使用 _add_middleware_edge() 支持中间件的 jump_to 条件跳转"))
    story.append(PageBreak())

    # ═══════════════ 九、ModelRequest / ModelResponse ═══════════════
    story.append(h1("九、核心类设计说明 — ModelRequest / ModelResponse"))

    story.append(h2("9.1 ModelRequest"))
    story.append(body(
        "ModelRequest 是模型调用的请求对象，封装了模型调用所需的全部信息。"
        "它是不可变设计，通过 override() 方法创建新的修改副本。"
    ))
    story.append(spacer(4))
    story.append(make_table(
        ["属性", "类型", "说明"],
        [
            ["model", "BaseChatModel", "要调用的聊天模型实例"],
            ["messages", "list[AnyMessage]", "消息列表（不含系统消息）"],
            ["system_message", "SystemMessage | None", "系统消息"],
            ["tools", "list[BaseTool | dict]", "可用工具列表"],
            ["response_format", "ResponseFormat | None", "结构化输出格式"],
            ["state", "AgentState", "当前 Agent 状态"],
            ["runtime", "Runtime[ContextT]", "运行时上下文"],
            ["model_settings", "dict[str, Any]", "额外模型设置"],
            ["tool_choice", "Any | None", "工具选择配置"],
        ],
        col_widths=[105, 130, 225]
    ))
    story.append(spacer(6))
    story.append(body(
        "<b>不可变模式</b>：直接属性赋值已被弃用，建议使用 request.override(model=new_model) 创建新实例。"
        "这种设计确保中间件链中各层看到的是独立的请求对象，避免副作用。"
    ))
    story.append(spacer(8))

    story.append(h2("9.2 ModelResponse"))
    story.append(body("ModelResponse 封装了模型调用的结果："))
    story.append(make_table(
        ["属性", "类型", "说明"],
        [
            ["result", "list[BaseMessage]", "模型返回的消息列表（通常包含一个 AIMessage）"],
            ["structured_response", "ResponseT | None", "解析后的结构化输出，如果指定了 response_format"],
        ],
        col_widths=[120, 160, 180]
    ))
    story.append(spacer(8))

    story.append(h2("9.3 ExtendedModelResponse"))
    story.append(body(
        "ExtendedModelResponse 是 wrap_model_call 中间件的扩展返回类型，"
        "除了包含 ModelResponse 外，还可以附带一个 Command 对象用于额外的状态更新。"
    ))
    story.append(PageBreak())

    # ═══════════════ 十、结构化输出策略 ═══════════════
    story.append(h1("十、核心类设计说明 — 结构化输出策略"))
    story.append(body(
        "langchain_v1 定义了三种结构化输出策略，通过 ResponseFormat 联合类型统一管理："
    ))
    story.append(spacer(6))

    story.append(make_table(
        ["策略类", "原理", "适用场景"],
        [
            ["AutoStrategy", "根据模型能力自动选择 Provider 或 Tool 策略", "推荐默认使用，无需关心模型支持情况"],
            ["ProviderStrategy", "利用模型提供商原生 JSON Schema（如 OpenAI response_format）", "模型原生支持结构化输出时性能最优"],
            ["ToolStrategy", "将 schema 包装为虚拟工具，通过 tool_call 解析", "通用兼容方案，支持所有模型"],
        ],
        col_widths=[100, 200, 160]
    ))
    story.append(spacer(8))

    story.append(h2("辅助类"))
    story.append(bullet("<b>_SchemaSpec</b>：Schema 描述封装，支持 Pydantic、dataclass、TypedDict、JSON Schema 四种类型"))
    story.append(bullet("<b>OutputToolBinding</b>：Tool 策略下的工具绑定信息，包含 schema、tool 实例和解析逻辑"))
    story.append(bullet("<b>ProviderStrategyBinding</b>：Provider 策略下的绑定信息，从 AIMessage 内容解析 JSON"))
    story.append(bullet("<b>StructuredOutputError</b>：结构化输出异常体系，包含 ValidationError 和 MultipleOutputsError"))
    story.append(PageBreak())

    # ═══════════════ 十一、init_chat_model ═══════════════
    story.append(h1("十一、核心类设计说明 — init_chat_model 工厂"))
    story.append(body(
        "init_chat_model() 是统一的聊天模型初始化入口，支持通过字符串标识符（如 'openai:gpt-4o'）"
        "创建任意提供商的模型实例。"
    ))
    story.append(spacer(6))

    story.append(h2("11.1 支持的提供商（25+）"))
    providers = [
        ["openai", "langchain-openai", "GPT-4o, o3-mini 等"],
        ["anthropic", "langchain-anthropic", "Claude Sonnet, Opus 等"],
        ["google_vertexai", "langchain-google-vertexai", "Gemini 系列"],
        ["google_genai", "langchain-google-genai", "Google GenAI"],
        ["bedrock / bedrock_converse", "langchain-aws", "Amazon Bedrock 系列"],
        ["azure_openai", "langchain-openai", "Azure OpenAI"],
        ["ollama", "langchain-ollama", "本地模型（Llama 等）"],
        ["deepseek", "langchain-deepseek", "DeepSeek 系列"],
        ["groq", "langchain-groq", "Groq 推理加速"],
        ["mistralai", "langchain-mistralai", "Mistral 系列"],
        ["xai", "langchain-xai", "Grok 系列"],
        ["cohere", "langchain-cohere", "Command 系列"],
        ["fireworks", "langchain-fireworks", "Fireworks AI"],
        ["together", "langchain-together", "Together AI"],
        ["perplexity", "langchain-perplexity", "Sonar 系列"],
    ]
    story.append(make_table(
        ["提供商 Key", "集成包", "模型示例"],
        providers,
        col_widths=[130, 155, 175]
    ))
    story.append(spacer(8))

    story.append(h2("11.2 _ConfigurableModel"))
    story.append(body(
        "当不指定固定模型或设置 configurable_fields 时，init_chat_model 返回 _ConfigurableModel。"
        "这是一个 Runnable 的延迟代理，在实际调用时才根据 config 参数实例化底层模型。"
        "支持队列化的声明式操作（如 bind_tools）在模型实例化后批量应用。"
    ))
    story.append(PageBreak())

    # ═══════════════ 十二、init_embeddings ═══════════════
    story.append(h1("十二、核心类设计说明 — init_embeddings 工厂"))
    story.append(body(
        "init_embeddings() 提供统一的嵌入模型初始化接口，设计模式与 init_chat_model 一致。"
    ))
    story.append(spacer(6))
    emb_providers = [
        ["openai", "langchain-openai", "text-embedding-3-small 等"],
        ["azure_openai", "langchain-openai", "Azure OpenAI Embeddings"],
        ["bedrock", "langchain-aws", "Amazon Titan Embed"],
        ["cohere", "langchain-cohere", "embed-english-v3.0 等"],
        ["google_vertexai", "langchain-google-vertexai", "VertexAI Embeddings"],
        ["google_genai", "langchain-google-genai", "Google GenAI Embeddings"],
        ["huggingface", "langchain-huggingface", "HuggingFace Embeddings"],
        ["mistralai", "langchain-mistralai", "Mistral Embeddings"],
        ["ollama", "langchain-ollama", "本地嵌入模型"],
    ]
    story.append(make_table(
        ["提供商 Key", "集成包", "模型示例"],
        emb_providers,
        col_widths=[110, 170, 180]
    ))
    story.append(PageBreak())

    # ═══════════════ 十三、内置中间件 ═══════════════
    story.append(h1("十三、内置中间件一览"))
    story.append(body(
        "langchain_v1 提供了 17 种预构建中间件，覆盖了 Agent 开发中常见的横切关注点："
    ))
    story.append(spacer(6))
    mw_list = [
        ["ModelRetryMiddleware", "wrap_model_call", "模型调用失败时自动重试，支持指数退避和异常过滤"],
        ["ModelFallbackMiddleware", "wrap_model_call", "模型调用失败时自动切换到备选模型"],
        ["ModelCallLimitMiddleware", "before_model", "限制模型调用次数（按线程/按运行），防止无限循环"],
        ["ToolRetryMiddleware", "wrap_tool_call", "工具调用失败时自动重试，支持指数退避"],
        ["ToolCallLimitMiddleware", "after_model", "限制工具调用次数（按线程/按运行/按工具名）"],
        ["HumanInTheLoopMiddleware", "after_model", "人工审核工具调用，支持审批/编辑/拒绝"],
        ["SummarizationMiddleware", "before_model", "自动摘要过长的对话历史，防止上下文溢出"],
        ["PIIMiddleware", "before_model + after_model", "PII 检测与处理（邮箱/信用卡/IP/URL 等）"],
        ["ShellToolMiddleware", "wrap_tool_call + tools", "提供持久化 Shell 会话工具，支持 Docker/主机/Codex 沙箱"],
        ["ContextEditingMiddleware", "before_model", "工具使用后编辑上下文（如清除旧工具结果）"],
        ["TodoListMiddleware", "tools", "提供 TODO 列表管理工具"],
        ["FilesystemFileSearchMiddleware", "tools", "提供文件系统搜索工具"],
        ["LLMToolEmulator", "wrap_model_call", "用 LLM 模拟工具行为（测试/模拟场景）"],
        ["LLMToolSelectorMiddleware", "wrap_model_call", "用 LLM 智能选择最相关的工具子集"],
    ]
    story.append(make_table(
        ["中间件", "钩子类型", "功能描述"],
        mw_list,
        col_widths=[140, 110, 210]
    ))
    story.append(spacer(8))
    story.append(h3("中间件分类"))
    story.append(bullet("<b>可靠性类</b>：ModelRetryMiddleware, ModelFallbackMiddleware, ToolRetryMiddleware"))
    story.append(bullet("<b>限流控制类</b>：ModelCallLimitMiddleware, ToolCallLimitMiddleware"))
    story.append(bullet("<b>安全合规类</b>：PIIMiddleware, HumanInTheLoopMiddleware"))
    story.append(bullet("<b>上下文管理类</b>：SummarizationMiddleware, ContextEditingMiddleware"))
    story.append(bullet("<b>工具扩展类</b>：ShellToolMiddleware, TodoListMiddleware, FilesystemFileSearchMiddleware"))
    story.append(bullet("<b>增强型类</b>：LLMToolEmulator, LLMToolSelectorMiddleware"))
    story.append(PageBreak())

    # ═══════════════ 十四、总结 ═══════════════
    story.append(h1("十四、设计哲学与总结"))
    story.append(spacer(6))

    story.append(h2("14.1 架构优势"))
    story.append(bullet("<b>极致精简</b>：整个框架仅约 30 个源文件，核心 API 只有 create_agent() 一个函数"))
    story.append(bullet("<b>中间件即功能</b>：所有横切关注点（重试/限流/PII/HITL 等）都通过可插拔中间件实现"))
    story.append(bullet("<b>声明式配置</b>：create_agent() 采用纯声明式参数，内部自动构建 StateGraph"))
    story.append(bullet("<b>类型安全</b>：大量使用 Generic、TypedDict、Protocol 和 Annotated，提供强类型保障"))
    story.append(bullet("<b>洋葱模型组合</b>：wrap_model_call/wrap_tool_call 采用经典的中间件洋葱模型"))
    story.append(spacer(8))

    story.append(h2("14.2 与 langchain-classic 的对比"))
    story.append(make_table(
        ["特性", "langchain-classic", "langchain_v1"],
        [
            ["核心概念", "Chain（链式调用）", "Agent + Middleware（中间件模式）"],
            ["模块数量", "chains/agents/memory/retrievers 等数十个模块", "仅 6 个精简模块"],
            ["编排引擎", "内置简单链式 + Agent 循环", "基于 LangGraph StateGraph"],
            ["扩展方式", "继承 Chain/Agent 子类", "实现 AgentMiddleware 钩子"],
            ["状态管理", "ConversationMemory 等", "StateGraph + Checkpointer"],
            ["结构化输出", "output_parsers", "ResponseFormat 策略模式"],
            ["类型安全", "较弱", "强类型（泛型+TypedDict+Protocol）"],
        ],
        col_widths=[90, 185, 185]
    ))
    story.append(spacer(8))

    story.append(h2("14.3 核心依赖关系"))
    story.append(body("langchain_v1 的依赖层次如下："))
    story.append(spacer(4))
    story.append(bullet("<b>langchain-core</b>：提供 BaseChatModel、BaseTool、BaseMessage 等核心抽象"))
    story.append(bullet("<b>langgraph</b>：提供 StateGraph、Runtime、Checkpointer、ToolNode 等编排能力"))
    story.append(bullet("<b>langsmith</b>：提供 @traceable 装饰器用于可观测性"))
    story.append(bullet("<b>pydantic</b>：提供数据验证和 JSON Schema 生成"))
    story.append(spacer(10))

    story.append(hr())
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "文档生成时间：2026-03-22 | 基于 langchain v1.2.13 源码分析",
        ParagraphStyle("footer", parent=BODY_STYLE, alignment=TA_CENTER, fontSize=9, textColor=HexColor("#999999"))
    ))

    return story


# ─────────────── 主函数 ───────────────
def main():
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "langchain-v1-architecture.pdf"
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=25*mm,
        leftMargin=25*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
        title="LangChain v1 源码架构分析",
        author="LangChain Source Code Analyzer",
    )

    story = build_document()
    doc.build(story)
    print(f"PDF 文档已生成：{output_path}")


if __name__ == "__main__":
    main()
