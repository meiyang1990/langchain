#!/usr/bin/env python3
"""LangChain-Core 源码架构分析文档 PDF 生成脚本"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, Flowable, Frame, PageTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ========== 注册中文字体 ==========
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
pdfmetrics.registerFont(TTFont("Chinese", FONT_PATH, subfontIndex=0))
pdfmetrics.registerFont(TTFont("ChineseBold", FONT_PATH, subfontIndex=1))

# ========== 颜色定义 ==========
PRIMARY = HexColor("#1a56db")
SECONDARY = HexColor("#3b82f6")
ACCENT = HexColor("#0ea5e9")
BG_LIGHT = HexColor("#f0f9ff")
BG_CODE = HexColor("#f8fafc")
BORDER = HexColor("#e2e8f0")
TEXT_PRIMARY = HexColor("#1e293b")
TEXT_SECONDARY = HexColor("#64748b")
HIGHLIGHT_GREEN = HexColor("#dcfce7")
HIGHLIGHT_YELLOW = HexColor("#fef9c3")
HIGHLIGHT_BLUE = HexColor("#dbeafe")
DARK_BG = HexColor("#1e293b")

# ========== 页面设置 ==========
PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 25*mm
RIGHT_MARGIN = 25*mm
TOP_MARGIN = 25*mm
BOTTOM_MARGIN = 25*mm


# ========== 自定义 Flowable ==========
class HorizontalLine(Flowable):
    """水平分隔线"""
    def __init__(self, width, color=BORDER, thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 4

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 2, self.width, 2)


class ColoredBox(Flowable):
    """带背景色的文本框"""
    def __init__(self, text, width, bg_color=BG_LIGHT, border_color=SECONDARY, font_name="Chinese", font_size=9, padding=8):
        Flowable.__init__(self)
        self.text = text
        self.box_width = width
        self.bg_color = bg_color
        self.border_color = border_color
        self.font_name = font_name
        self.font_size = font_size
        self.padding = padding
        self._calc_height()

    def _calc_height(self):
        lines = self.text.split('\n')
        line_height = self.font_size * 1.4
        self.height = len(lines) * line_height + self.padding * 2

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.setStrokeColor(self.border_color)
        self.canv.setLineWidth(0.5)
        self.canv.roundRect(0, 0, self.box_width, self.height, 4, fill=1, stroke=1)
        # 左侧强调线
        self.canv.setFillColor(self.border_color)
        self.canv.rect(0, 0, 3, self.height, fill=1, stroke=0)
        # 文本
        self.canv.setFillColor(TEXT_PRIMARY)
        self.canv.setFont(self.font_name, self.font_size)
        lines = self.text.split('\n')
        line_height = self.font_size * 1.4
        y = self.height - self.padding - self.font_size
        for line in lines:
            self.canv.drawString(self.padding + 5, y, line)
            y -= line_height


class DiagramBox(Flowable):
    """架构图/流程图 - ASCII art 风格展示"""
    def __init__(self, title, text, width, bg_color=BG_CODE, title_bg=DARK_BG):
        Flowable.__init__(self)
        self.title = title
        self.text = text
        self.box_width = width
        self.bg_color = bg_color
        self.title_bg = title_bg
        self.font_size = 8
        self.title_font_size = 10
        self._calc_height()

    def _calc_height(self):
        lines = self.text.split('\n')
        line_height = self.font_size * 1.5
        self.height = len(lines) * line_height + 50  # 50 for title area + padding

    def draw(self):
        # 外框
        self.canv.setStrokeColor(BORDER)
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.box_width, self.height, 6, fill=0, stroke=1)
        # 标题栏
        title_h = 24
        self.canv.setFillColor(self.title_bg)
        self.canv.roundRect(0, self.height - title_h, self.box_width, title_h, 6, fill=1, stroke=0)
        self.canv.setFillColor(self.title_bg)
        self.canv.rect(0, self.height - title_h, self.box_width, title_h / 2, fill=1, stroke=0)
        # 标题文字
        self.canv.setFillColor(white)
        self.canv.setFont("ChineseBold", self.title_font_size)
        self.canv.drawString(12, self.height - 17, self.title)
        # 内容区域背景
        self.canv.setFillColor(self.bg_color)
        self.canv.rect(1, 1, self.box_width - 2, self.height - title_h - 2, fill=1, stroke=0)
        # 文本内容
        self.canv.setFillColor(TEXT_PRIMARY)
        self.canv.setFont("Chinese", self.font_size)
        lines = self.text.split('\n')
        line_height = self.font_size * 1.5
        y = self.height - title_h - 15
        for line in lines:
            self.canv.drawString(12, y, line)
            y -= line_height


# ========== 样式定义 ==========
def get_styles():
    styles = {}
    styles['cover_title'] = ParagraphStyle(
        'CoverTitle', fontName='ChineseBold', fontSize=28, leading=38,
        textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=12
    )
    styles['cover_subtitle'] = ParagraphStyle(
        'CoverSubtitle', fontName='Chinese', fontSize=14, leading=22,
        textColor=TEXT_SECONDARY, alignment=TA_CENTER, spaceAfter=6
    )
    styles['h1'] = ParagraphStyle(
        'Heading1', fontName='ChineseBold', fontSize=20, leading=28,
        textColor=PRIMARY, spaceBefore=20, spaceAfter=10,
        borderPadding=(0, 0, 6, 0)
    )
    styles['h2'] = ParagraphStyle(
        'Heading2', fontName='ChineseBold', fontSize=15, leading=22,
        textColor=SECONDARY, spaceBefore=16, spaceAfter=8
    )
    styles['h3'] = ParagraphStyle(
        'Heading3', fontName='ChineseBold', fontSize=12, leading=18,
        textColor=TEXT_PRIMARY, spaceBefore=12, spaceAfter=6
    )
    styles['body'] = ParagraphStyle(
        'Body', fontName='Chinese', fontSize=10, leading=17,
        textColor=TEXT_PRIMARY, spaceAfter=6, alignment=TA_JUSTIFY
    )
    styles['body_indent'] = ParagraphStyle(
        'BodyIndent', fontName='Chinese', fontSize=10, leading=17,
        textColor=TEXT_PRIMARY, spaceAfter=6, leftIndent=20
    )
    styles['bullet'] = ParagraphStyle(
        'Bullet', fontName='Chinese', fontSize=10, leading=16,
        textColor=TEXT_PRIMARY, spaceAfter=3, leftIndent=20,
        bulletIndent=8, bulletFontName='Chinese', bulletFontSize=10
    )
    styles['code'] = ParagraphStyle(
        'Code', fontName='Chinese', fontSize=8, leading=13,
        textColor=TEXT_PRIMARY, spaceAfter=4, leftIndent=10,
        backColor=BG_CODE
    )
    styles['table_header'] = ParagraphStyle(
        'TableHeader', fontName='ChineseBold', fontSize=9, leading=14,
        textColor=white, alignment=TA_CENTER
    )
    styles['table_cell'] = ParagraphStyle(
        'TableCell', fontName='Chinese', fontSize=9, leading=14,
        textColor=TEXT_PRIMARY
    )
    styles['caption'] = ParagraphStyle(
        'Caption', fontName='Chinese', fontSize=9, leading=14,
        textColor=TEXT_SECONDARY, alignment=TA_CENTER, spaceAfter=8
    )
    styles['toc'] = ParagraphStyle(
        'TOC', fontName='Chinese', fontSize=11, leading=22,
        textColor=TEXT_PRIMARY, leftIndent=0
    )
    styles['toc_sub'] = ParagraphStyle(
        'TOCSub', fontName='Chinese', fontSize=10, leading=20,
        textColor=TEXT_SECONDARY, leftIndent=20
    )
    return styles


def make_table(headers, rows, col_widths=None):
    """创建统一风格的表格"""
    s = get_styles()
    data = [[Paragraph(h, s['table_header']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), s['table_cell']) for c in row])

    if col_widths is None:
        content_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
        col_widths = [content_width / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Chinese'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('LINEBELOW', (0, 0), (-1, 0), 2, PRIMARY),
    ])
    t.setStyle(style)
    return t


# ========== 页眉页脚 ==========
def header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    # 页眉
    canvas_obj.setStrokeColor(PRIMARY)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(LEFT_MARGIN, PAGE_HEIGHT - 18*mm, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 18*mm)
    canvas_obj.setFont("ChineseBold", 8)
    canvas_obj.setFillColor(TEXT_SECONDARY)
    canvas_obj.drawString(LEFT_MARGIN, PAGE_HEIGHT - 16*mm, "LangChain-Core 源码架构分析文档")
    canvas_obj.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 16*mm, "v0.1.16")
    # 页脚
    canvas_obj.setStrokeColor(BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(LEFT_MARGIN, BOTTOM_MARGIN - 5*mm, PAGE_WIDTH - RIGHT_MARGIN, BOTTOM_MARGIN - 5*mm)
    canvas_obj.setFont("Chinese", 8)
    canvas_obj.setFillColor(TEXT_SECONDARY)
    canvas_obj.drawCentredString(PAGE_WIDTH / 2, BOTTOM_MARGIN - 10*mm, f"- {doc.page} -")
    canvas_obj.restoreState()


# ========== 文档内容 ==========
def build_document():
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "langchain-core-source-analysis.pdf")
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN
    )

    s = get_styles()
    story = []
    content_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

    # ==================== 封面 ====================
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("LangChain-Core", s['cover_title']))
    story.append(Paragraph("源码架构分析文档", s['cover_title']))
    story.append(Spacer(1, 15*mm))
    story.append(HorizontalLine(content_width, PRIMARY, 2))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("基于 v0.1.16 版本源码深度分析", s['cover_subtitle']))
    story.append(Paragraph("涵盖核心类设计、流程图、时序图等架构说明", s['cover_subtitle']))
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("langchain-core 是 LangChain 生态的基础抽象层", s['cover_subtitle']))
    story.append(Paragraph("定义了 Runnable、消息、模型、工具等核心协议", s['cover_subtitle']))
    story.append(PageBreak())

    # ==================== 目录 ====================
    story.append(Paragraph("目  录", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))
    story.append(Spacer(1, 6*mm))
    toc_items = [
        ("一、项目整体架构概览", [
            "1.1 模块组织结构",
            "1.2 分层架构图",
            "1.3 核心类全景继承关系图",
        ]),
        ("二、Runnable 编排框架（LCEL 核心）", [
            "2.1 Runnable 核心类设计",
            "2.2 管道操作符工作流程图",
            "2.3 RunnableSequence 串行执行时序图",
            "2.4 RunnableParallel 并行执行时序图",
            "2.5 特殊 Runnable 实现",
        ]),
        ("三、语言模型抽象层", [
            "3.1 模型类继承体系",
            "3.2 ChatModel.invoke() 完整调用时序图",
            "3.3 流式生成(stream)时序图",
            "3.4 with_structured_output 流程图",
        ]),
        ("四、消息类型与 Prompt 模板系统", [
            "4.1 消息类型继承体系",
            "4.2 Prompt 模板系统设计",
            "4.3 Prompt 到消息的转换流程图",
        ]),
        ("五、回调与追踪系统", [
            "5.1 回调系统架构图",
            "5.2 事件分发时序图",
            "5.3 追踪器与回调的关系",
        ]),
        ("六、工具系统与输出解析", [
            "6.1 工具系统核心设计",
            "6.2 工具调用完整时序图",
            "6.3 输出解析器体系",
        ]),
        ("七、数据层：文档、检索与向量存储", [
            "7.1 数据层类图",
            "7.2 RAG 完整流程图",
        ]),
        ("八、序列化与反序列化系统", [
            "8.1 序列化机制",
            "8.2 安全反序列化流程图",
        ]),
    ]
    for title, subs in toc_items:
        story.append(Paragraph(title, s['toc']))
        for sub in subs:
            story.append(Paragraph(sub, s['toc_sub']))
    story.append(PageBreak())

    # ==================== 第一章：项目整体架构概览 ====================
    story.append(Paragraph("一、项目整体架构概览", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("1.1 模块组织结构", s['h2']))
    story.append(Paragraph(
        "langchain-core 是整个 LangChain 生态的基础层，定义了所有核心抽象、协议和基础类型。"
        "整个包按功能职责分为 20 个子包，约 195 个 Python 文件。下面按功能分层说明各模块的职责：",
        s['body']
    ))

    story.append(make_table(
        ["功能层", "模块", "核心职责"],
        [
            ["核心编排层", "runnables/", "LCEL 核心，Runnable 基类及管道操作符、序列/并行执行"],
            ["模型抽象层", "language_models/", "BaseLLM、BaseChatModel 等语言模型基类"],
            ["消息系统", "messages/", "BaseMessage 及 AI/Human/System/Tool 消息类型"],
            ["输入/输出层", "prompts/, output_parsers/, outputs/", "Prompt 模板系统和结构化输出解析"],
            ["数据层", "documents/, document_loaders/, vectorstores/, indexing/", "文档模型、加载器、向量存储、索引"],
            ["工具与 Agent", "tools/, agents.py", "工具抽象、@tool 装饰器、Agent 基础定义"],
            ["可观测性", "callbacks/, tracers/", "回调管理器、追踪器、事件分发"],
            ["基础设施", "utils/, load/, _api/, _security/", "通用工具、序列化/反序列化、API 标记、安全"],
        ],
        [content_width * 0.15, content_width * 0.35, content_width * 0.50]
    ))
    story.append(Spacer(1, 6*mm))

    # 1.2 分层架构图
    story.append(Paragraph("1.2 分层架构图", s['h2']))
    story.append(DiagramBox(
        "图 1-1：LangChain-Core 分层架构图",
        """
  +============================================================================+
  |                          应用层 (Application Layer)                         |
  |   Chain / Agent / RAG Pipeline / Custom Application                        |
  +============================================================================+
                                       |
  +============================================================================+
  |                       编排层 (Orchestration Layer)                          |
  |   Runnable | RunnableSequence | RunnableParallel | RunnableBranch          |
  |   RunnablePassthrough | RunnableWithFallbacks | RunnableLambda             |
  +============================================================================+
             |                    |                    |
  +==================+  +==================+  +==================+
  |  模型层 (Model)  |  | 数据层 (Data)    |  | 工具层 (Tool)    |
  | BaseChatModel    |  | Document         |  | BaseTool         |
  | BaseLLM          |  | BaseLoader       |  | StructuredTool   |
  | Embeddings       |  | VectorStore      |  | @tool            |
  +==================+  | BaseRetriever    |  +==================+
                        +==================+
                                       |
  +============================================================================+
  |                      输入/输出层 (I/O Layer)                                |
  |   PromptTemplate | ChatPromptTemplate | BaseOutputParser                   |
  |   BaseMessage (AI/Human/System/Tool) | PromptValue                        |
  +============================================================================+
                                       |
  +============================================================================+
  |                    可观测性层 (Observability Layer)                          |
  |   BaseCallbackHandler | CallbackManager | BaseTracer                       |
  +============================================================================+
                                       |
  +============================================================================+
  |                     基础设施层 (Infrastructure Layer)                       |
  |   Serializable | RunnableConfig | utils/ | _api/ | _security/              |
  +============================================================================+
""",
        content_width
    ))
    story.append(Spacer(1, 4*mm))

    # 1.3 核心类全景继承关系
    story.append(Paragraph("1.3 核心类全景继承关系图", s['h2']))
    story.append(DiagramBox(
        "图 1-2：核心类继承全景图",
        """
  BaseModel (Pydantic)
    |
    +-- Serializable (ABC)                 ← 序列化基础能力
          |
          +-- BaseMedia                    ← 媒体基类
          |     +-- Document               ← 文档模型 (page_content + metadata)
          |     +-- Blob                   ← 原始数据 (懒加载)
          |
          +-- BaseMessage                  ← 消息基类 (content + type)
          |     +-- HumanMessage           ← 用户消息
          |     +-- AIMessage              ← AI 回复 (含 tool_calls)
          |     +-- SystemMessage          ← 系统提示
          |     +-- ToolMessage            ← 工具返回 (含 tool_call_id)
          |     +-- BaseMessageChunk       ← 流式消息块 (支持 __add__ 合并)
          |
          +-- Runnable (ABC, Generic[I, O]) ← 核心编排协议
                |
                +-- RunnableSerializable   ← 可序列化的 Runnable
                |     +-- RunnableSequence     ← 串行管道 (A | B | C)
                |     +-- RunnableParallel     ← 并行执行 ({k1: R1, k2: R2})
                |     +-- RunnablePassthrough  ← 透传 / assign / pick
                |     +-- RunnableBranch       ← 条件分支路由
                |     +-- RunnableBindingBase  ← 绑定配置/参数
                |     |     +-- RunnableWithFallbacks  ← 故障转移
                |     |     +-- RunnableWithMessageHistory ← 消息历史
                |     +-- BaseLanguageModel    ← 语言模型基类
                |     |     +-- BaseChatModel  ← 聊天模型 (输出 AIMessage)
                |     |     +-- BaseLLM        ← 文本模型 (输出 str)
                |     +-- BasePromptTemplate   ← Prompt 模板基类
                |     +-- BaseTool             ← 工具基类
                |     +-- BaseOutputParser     ← 输出解析基类
                |     +-- BaseRetriever        ← 检索器基类
                |
                +-- RunnableLambda         ← 包装普通函数
                +-- RunnableGenerator      ← 包装生成器函数
""",
        content_width
    ))
    story.append(PageBreak())

    # ==================== 第二章：Runnable 编排框架 ====================
    story.append(Paragraph("二、Runnable 编排框架（LCEL 核心）", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("2.1 Runnable 核心类设计", s['h2']))
    story.append(Paragraph(
        "Runnable 是 LangChain Expression Language (LCEL) 的核心协议。它是一个泛型抽象基类 "
        "Runnable[Input, Output]，定义了统一的执行接口。所有 LangChain 组件（模型、Prompt、解析器、"
        "检索器、工具等）都实现了此协议，因此可以通过 | 管道操作符自由组合。",
        s['body']
    ))

    story.append(Paragraph("<b>核心设计原则：</b>只有 invoke() 是唯一的抽象方法，其它所有方法都有基于它的默认实现。", s['body']))
    story.append(Spacer(1, 3*mm))

    story.append(make_table(
        ["方法", "类型", "默认行为", "子类可覆写优化"],
        [
            ["invoke(input)", "抽象方法", "子类必须实现", "-"],
            ["ainvoke(input)", "异步版本", "run_in_executor(invoke)", "原生 async 实现"],
            ["batch(inputs)", "批量执行", "线程池并行调用 invoke", "批量 API 调用"],
            ["abatch(inputs)", "异步批量", "asyncio.gather(ainvoke...)", "原生异步批量"],
            ["stream(input)", "流式输出", "yield invoke(input)", "真正的逐 token 流式"],
            ["astream(input)", "异步流式", "yield await ainvoke(input)", "原生异步流式"],
        ],
        [content_width * 0.18, content_width * 0.12, content_width * 0.35, content_width * 0.35]
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("<b>辅助方法（with_* 系列）：</b>", s['h3']))
    story.append(make_table(
        ["方法", "返回类型", "功能说明"],
        [
            ["with_config(config)", "RunnableBinding", "绑定固定配置"],
            ["with_retry(stop_after_attempt=3)", "RunnableRetry", "添加重试策略"],
            ["with_fallbacks(fallbacks)", "RunnableWithFallbacks", "添加故障转移方案"],
            ["with_listeners(on_start, on_end)", "RunnableBinding", "添加生命周期监听"],
            ["pipe(*others)", "RunnableSequence", "等价于 self | others[0] | ..."],
            ["pick(keys)", "RunnablePick", "从 dict 输出中选取 key"],
            ["assign(**kwargs)", "RunnableAssign", "向 dict 输出中添加新字段"],
        ],
        [content_width * 0.35, content_width * 0.25, content_width * 0.40]
    ))
    story.append(Spacer(1, 6*mm))

    # 2.2 管道操作符工作流程图
    story.append(Paragraph("2.2 管道操作符 ( | ) 工作流程图", s['h2']))
    story.append(Paragraph(
        "管道操作符是 LCEL 的核心语法糖，通过 Python 的 __or__ 和 __ror__ 魔术方法实现。"
        "coerce_to_runnable() 函数负责将各种类型自动转换为 Runnable：",
        s['body']
    ))
    story.append(DiagramBox(
        "图 2-1：管道操作符 ( | ) 类型转换与组合流程",
        """
  用户表达式: prompt | model | output_parser

  步骤1: prompt.__or__(model)
    |
    +-- coerce_to_runnable(model)
    |     +-- isinstance(model, Runnable) ? --> 直接使用
    |     +-- callable(model) ? -----------> RunnableLambda(model)
    |     +-- isinstance(model, dict) ? ---> RunnableParallel(model)
    |     +-- is_generator(model) ? -------> RunnableGenerator(model)
    |
    +-- 返回 RunnableSequence(prompt, model)

  步骤2: sequence.__or__(output_parser)
    |
    +-- 优化: 如果两边都是 RunnableSequence, 展平所有步骤避免嵌套
    |
    +-- 返回 RunnableSequence(prompt, model, output_parser)
           first=prompt, middle=[model], last=output_parser

  最终结构: RunnableSequence
    +-- first:  BasePromptTemplate   (格式化输入 -> PromptValue)
    +-- middle: [BaseChatModel]      (生成回复 -> AIMessage)
    +-- last:   BaseOutputParser     (解析输出 -> 结构化结果)
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 2.3 RunnableSequence 串行执行时序图
    story.append(Paragraph("2.3 RunnableSequence 串行执行时序图", s['h2']))
    story.append(DiagramBox(
        "图 2-2：RunnableSequence.invoke() 执行时序",
        """
  User          RunnableSequence     CallbackManager     Step1(Prompt)   Step2(Model)    Step3(Parser)
   |                  |                    |                  |               |               |
   |-- invoke(input)-->|                    |                  |               |               |
   |                  |-- configure() ----->|                  |               |               |
   |                  |<-- run_manager -----|                  |               |               |
   |                  |-- on_chain_start -->|                  |               |               |
   |                  |                    |-- notify handlers |               |               |
   |                  |                    |                  |               |               |
   |                  |-- get_child("seq:step:1") ----------->|               |               |
   |                  |-- invoke(input) -------------------- >|               |               |
   |                  |<-- prompt_value -------------------- -|               |               |
   |                  |                    |                  |               |               |
   |                  |-- get_child("seq:step:2") -------------------------- >|               |
   |                  |-- invoke(prompt_value) ------------------------------ >|               |
   |                  |<-- ai_message ------------------------------------ ---|               |
   |                  |                    |                  |               |               |
   |                  |-- get_child("seq:step:3") ----------------------------------------- >|
   |                  |-- invoke(ai_message) ----------------------------------------------- >|
   |                  |<-- parsed_output ------------------------------------------------ ---|
   |                  |                    |                  |               |               |
   |                  |-- on_chain_end --->|                  |               |               |
   |<-- parsed_output-|                    |                  |               |               |

  核心: 前一步输出 = 下一步输入, 每步注册为父 run 的子 run (seq:step:N)
""",
        content_width
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "<b>流式执行优化：</b>RunnableSequence 的 stream() 方法通过将每个步骤的 transform() 输出"
        "作为下一个步骤的输入迭代器，实现了真正的流式管道。数据不需要等待前一步完全结束，"
        "而是以 chunk 为单位逐步流转。",
        s['body']
    ))
    story.append(Spacer(1, 4*mm))

    story.append(ColoredBox(
        "RunnableSequence.batch() 优化策略:\n"
        "不是对每个输入单独调用 invoke，而是逐 step 调用 step.batch(all_inputs)。\n"
        "这让底层 LLM 等组件可以利用自身的批量 API 能力，大幅提升吞吐量。",
        content_width, HIGHLIGHT_YELLOW, HexColor("#eab308")
    ))
    story.append(Spacer(1, 6*mm))

    # 2.4 RunnableParallel 并行执行时序图
    story.append(Paragraph("2.4 RunnableParallel 并行执行时序图", s['h2']))
    story.append(DiagramBox(
        "图 2-3：RunnableParallel.invoke() 并行执行时序",
        """
  User          RunnableParallel     ThreadPool       Branch_A        Branch_B        Branch_C
   |                  |                 |                |               |               |
   |-- invoke(input)-->|                 |                |               |               |
   |                  |-- submit(A) ---->|                |               |               |
   |                  |-- submit(B) ---->|                |               |               |
   |                  |-- submit(C) ---->|                |               |               |
   |                  |                 |-- invoke(in) -->|               |               |
   |                  |                 |-- invoke(in) ---------------- ->|               |
   |                  |                 |-- invoke(in) -------------------------------- ->|
   |                  |                 |                |               |               |
   |                  |                 |<-- result_a ---|               |               |
   |                  |                 |<-- result_b ------------------|               |
   |                  |                 |<-- result_c ----------------------------------|
   |                  |<- collect all --|                |               |               |
   |<-- {"a": r_a,  --|                 |                |               |               |
   |     "b": r_b,    |                 |                |               |               |
   |     "c": r_c}    |                 |                |               |               |

  同步: ThreadPoolExecutor 并行    异步: asyncio.gather() 并行
  所有分支共享同一个 input, 结果汇聚为 dict[str, Any]
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 2.5 特殊 Runnable 实现
    story.append(Paragraph("2.5 特殊 Runnable 实现", s['h2']))
    story.append(make_table(
        ["类", "核心逻辑", "典型用法"],
        [
            ["RunnableLambda", "包装 callable/coroutine 为 Runnable", "runnable | (lambda x: x['key'])"],
            ["RunnablePassthrough", "透传输入，可执行副作用函数", "RunnablePassthrough()"],
            ["RunnableAssign", "将 mapper 结果合并到输入 dict", "RunnablePassthrough.assign(key=runnable)"],
            ["RunnablePick", "从 dict 选取指定 key", "runnable.pick('name')"],
            ["RunnableBranch", "条件路由：按序检查条件，执行匹配分支", "RunnableBranch((cond1, r1), (cond2, r2), default)"],
            ["RunnableWithFallbacks", "故障转移：主 Runnable 失败时尝试后备", "runnable.with_fallbacks([fallback1, fallback2])"],
            ["RunnableWithMessageHistory", "自动加载/保存消息历史到会话存储", "runnable.with_message_history(get_history)"],
            ["RunnableBinding", "绑定固定参数或配置到 Runnable", "model.bind(temperature=0)"],
        ],
        [content_width * 0.22, content_width * 0.38, content_width * 0.40]
    ))
    story.append(PageBreak())

    # ==================== 第三章：语言模型抽象层 ====================
    story.append(Paragraph("三、语言模型抽象层", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("3.1 模型类继承体系", s['h2']))
    story.append(DiagramBox(
        "图 3-1：语言模型类继承体系",
        """
  RunnableSerializable[LanguageModelInput, LanguageModelOutputVar]
    |
    +-- BaseLanguageModel[OutputVar] (ABC)        ← 顶层抽象基类
          |                                         字段: cache, verbose, callbacks, tags, metadata
          |                                         方法: get_token_ids(), get_num_tokens()
          |
          +-- BaseChatModel (BaseLanguageModel[AIMessage])  ← 聊天模型基类
          |     |  输入: list[BaseMessage]
          |     |  输出: AIMessage
          |     |  抽象方法: _generate(messages) -> ChatResult
          |     |  可选方法: _stream(), _astream(), bind_tools()
          |     |  高级方法: with_structured_output(schema)
          |     |  字段: rate_limiter, disable_streaming, profile
          |     |
          |     +-- SimpleChatModel              ← 便捷子类: 只需实现 _call()
          |
          +-- BaseLLM (BaseLanguageModel[str])   ← 文本补全模型基类
                |  输入: list[str]
                |  输出: str
                |  抽象方法: _generate(prompts: list[str]) -> LLMResult
                |
                +-- LLM                          ← 便捷子类: 只需实现 _call(prompt)

  类型别名:
    LanguageModelInput  = PromptValue | str | Sequence[MessageLikeRepresentation]
    LanguageModelOutput = BaseMessage | str
""",
        content_width
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("<b>实现自定义模型的最小接口：</b>", s['h3']))
    story.append(make_table(
        ["场景", "继承类", "必须实现", "可选实现"],
        [
            ["聊天模型", "BaseChatModel", "_generate(messages)->ChatResult + _llm_type", "_stream, _agenerate, bind_tools"],
            ["简单聊天模型", "SimpleChatModel", "_call(messages)->str + _llm_type", "-"],
            ["传统 LLM", "BaseLLM", "_generate(prompts:list[str])->LLMResult + _llm_type", "_stream, _agenerate"],
            ["简单 LLM", "LLM", "_call(prompt:str)->str + _llm_type", "_acall, _stream"],
        ],
        [content_width * 0.15, content_width * 0.18, content_width * 0.37, content_width * 0.30]
    ))
    story.append(Spacer(1, 6*mm))

    # 3.2 ChatModel.invoke() 完整调用时序图
    story.append(Paragraph("3.2 BaseChatModel.invoke() 完整调用时序图", s['h2']))
    story.append(DiagramBox(
        "图 3-2：ChatModel.invoke() 调用链时序图",
        """
  User              BaseChatModel          CallbackMgr          Cache           RateLimiter
   |                      |                     |                  |                |
   |-- invoke(input) ---->|                     |                  |                |
   |                      |-- _convert_input -->|                  |                |
   |                      |   str -> StringPromptValue             |                |
   |                      |   Seq[Msg] -> ChatPromptValue         |                |
   |                      |                     |                  |                |
   |                      |-- generate_prompt([pv]) ------->       |                |
   |                      |   --> generate([messages]) -->         |                |
   |                      |       --> _generate_with_cache -->     |                |
   |                      |           |                     |      |                |
   |                      |           |-- llm_cache.lookup ------->|                |
   |                      |           |   (缓存命中则直接返回)      |                |
   |                      |           |                     |      |                |
   |                      |           |-- rate_limiter.acquire ------------------>  |
   |                      |           |   (等待获取令牌)           |                |
   |                      |           |                     |      |                |
   |                      |           |-- _should_stream() ?       |                |
   |                      |           |   True:  _stream() -> generate_from_stream()
   |                      |           |   False: _generate(messages, stop, ...)     |
   |                      |           |                     |      |                |
   |                      |           |-- 设置 response_metadata, message.id        |
   |                      |           |-- llm_cache.update ------->|                |
   |                      |           |                     |      |                |
   |<-- result.generations[0][0].message (AIMessage) ------|      |                |
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 3.3 流式生成时序图
    story.append(Paragraph("3.3 流式生成 (stream) 时序图", s['h2']))
    story.append(DiagramBox(
        "图 3-3：BaseChatModel.stream() 流式生成时序图",
        """
  User              BaseChatModel          _stream()           CallbackMgr
   |                      |                     |                    |
   |-- stream(input) ---->|                     |                    |
   |                      |-- _should_stream()? |                    |
   |                      |   (检查: _stream 是否实现, disable_streaming, 显式参数)
   |                      |                     |                    |
   |                      |-- on_chat_model_start() --------------->|
   |                      |-- rate_limiter.acquire()                |
   |                      |                     |                    |
   |                      |-- _stream(msgs) --->|                    |
   |                      |                     |                    |
   |  <-- chunk_1 (AIMessageChunk) ------------|                    |
   |                      |-- on_llm_new_token(chunk_1) ----------->|
   |                      |                     |                    |
   |  <-- chunk_2 (AIMessageChunk) ------------|                    |
   |                      |-- on_llm_new_token(chunk_2) ----------->|
   |                      |                     |                    |
   |  <-- ... (更多 chunks)                     |                    |
   |                      |                     |                    |
   |  <-- chunk_last (chunk_position="last") --|                    |
   |                      |                     |                    |
   |                      |-- merge_all_chunks -> final_generation  |
   |                      |-- on_llm_end(LLMResult) -------------->|
   |                      |                     |                    |

  每个 chunk 都是 AIMessageChunk, 通过 __add__ 可以逐步合并为完整 AIMessage
  chunk 属性: content, tool_call_chunks, usage_metadata, chunk_position
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 3.4 with_structured_output 流程图
    story.append(Paragraph("3.4 with_structured_output 流程图", s['h2']))
    story.append(DiagramBox(
        "图 3-4：with_structured_output() 组装流程",
        """
  model.with_structured_output(schema, include_raw=False)
    |
    +-- 1. 检查 bind_tools 是否实现 (否则 raise NotImplementedError)
    |
    +-- 2. llm = self.bind_tools([schema], tool_choice="any")
    |       将 schema 绑定为工具，强制模型使用该工具
    |
    +-- 3. 根据 schema 类型选择解析器:
    |       +-- Pydantic BaseModel  --> PydanticToolsParser(first_tool_only=True)
    |       +-- dict / JSON Schema  --> JsonOutputKeyToolsParser(first_tool_only=True)
    |
    +-- 4. 组装 Runnable 链:
            |
            +-- include_raw=False:
            |     return  llm | output_parser
            |     输入 -> AIMessage(tool_calls) -> Pydantic实例/dict
            |
            +-- include_raw=True:
                  return  RunnableMap(raw=llm) | parser_with_fallback
                  输出: {"raw": AIMessage, "parsed": Model|dict, "parsing_error": Exception|None}
""",
        content_width
    ))
    story.append(PageBreak())

    # ==================== 第四章：消息类型与 Prompt 模板系统 ====================
    story.append(Paragraph("四、消息类型与 Prompt 模板系统", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("4.1 消息类型继承体系", s['h2']))
    story.append(DiagramBox(
        "图 4-1：消息类型继承体系与核心字段",
        """
  Serializable
    |
    +-- BaseMessage                              ← 消息基类
          字段: content (str | list[str|dict])   ← 支持纯文本和多模态
                additional_kwargs: dict          ← 模型提供商附加数据
                response_metadata: dict          ← 响应元数据
                type: str                        ← 类型判别符
                name, id: str | None             ← 可选标识
          属性: content_blocks -> list[ContentBlock] ← 标准化多模态访问
                text -> str                          ← 纯文本提取
          |
          +-- HumanMessage    (type="human")     ← 用户消息 (最简单)
          +-- AIMessage       (type="ai")        ← AI 回复
          |     字段: tool_calls, invalid_tool_calls, usage_metadata
          +-- SystemMessage   (type="system")    ← 系统提示
          +-- ToolMessage     (type="tool")      ← 工具返回结果
          |     字段: tool_call_id (必填), artifact, status
          +-- ChatMessage     (type="chat")      ← 通用消息 (含 role 字段)
          |
          +-- BaseMessageChunk                   ← 流式消息块
                方法: __add__(other) -> 合并两个 chunk
                |
                +-- AIMessageChunk (多重继承: AIMessage + BaseMessageChunk)
                      字段: tool_call_chunks, chunk_position
                      合并策略: content拼接, tool_call_chunks按index对齐, usage_metadata相加

  标准 ContentBlock 类型:
    TextContentBlock | ImageContentBlock | ToolCall | ToolCallChunk
    ReasoningContentBlock | Citation | NonStandardContentBlock
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 4.2 Prompt 模板系统设计
    story.append(Paragraph("4.2 Prompt 模板系统设计", s['h2']))
    story.append(DiagramBox(
        "图 4-2：Prompt 模板类继承体系",
        """
  RunnableSerializable[dict, PromptValue]
    |
    +-- BasePromptTemplate (ABC)              ← Prompt 模板基类
          字段: input_variables, optional_variables, partial_variables
          方法: invoke(dict) -> PromptValue
          |
          +-- StringPromptTemplate (ABC)      ← 字符串模板
          |     |  format_prompt() -> StringPromptValue
          |     |
          |     +-- PromptTemplate            ← 纯文本模板
          |           模板格式: f-string(默认) | mustache | jinja2
          |           "Hello {name}, welcome to {place}"
          |
          +-- BaseChatPromptTemplate (ABC)    ← 对话模板
                |  format_prompt() -> ChatPromptValue
                |
                +-- ChatPromptTemplate        ← 对话模板 (核心)
                      字段: messages: list[MessageLike]

  BaseMessagePromptTemplate (ABC)             ← 单条消息模板
    |
    +-- MessagesPlaceholder                   ← 动态消息列表占位符
    |     ("placeholder", "{chat_history}")
    |
    +-- _StringImageMessagePromptTemplate     ← 支持多模态
          +-- HumanMessagePromptTemplate
          +-- AIMessagePromptTemplate
          +-- SystemMessagePromptTemplate

  ChatPromptTemplate 支持 5 种输入格式:
    1. BaseMessagePromptTemplate 实例
    2. BaseMessage 实例
    3. ("human", "{input}") 元组
    4. (HumanMessage, "{input}") 元组
    5. "{input}" 字符串 (默认 human)
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 4.3 Prompt 到消息的转换流程图
    story.append(Paragraph("4.3 Prompt 到消息的完整转换流程图", s['h2']))
    story.append(DiagramBox(
        "图 4-3：从用户输入到模型输入的完整数据流",
        """
  用户输入 dict: {"input": "What is LangChain?", "chat_history": [...]}
    |
    v
  BasePromptTemplate.invoke(input_dict)
    |
    +-- _validate_input()                    验证变量完整性
    |
    +-- format_prompt(**kwargs)
          |
          +-- [PromptTemplate 路径]
          |     StringPromptTemplate.format_prompt()
          |       -> format(**kwargs)              模板字符串替换
          |       -> StringPromptValue(text=...)
          |           .to_messages() -> [HumanMessage(content=text)]
          |
          +-- [ChatPromptTemplate 路径]
                BaseChatPromptTemplate.format_prompt()
                  -> format_messages(**kwargs)
                       遍历 self.messages:
                         +-- BaseMessage 实例     -> 直接添加 (静态消息)
                         +-- MessagePromptTemplate -> .format_messages()
                         |     +-- 纯文本: format() -> Message(content=str)
                         |     +-- 多模态: 遍历子模板 -> Message(content=[dict...])
                         +-- MessagesPlaceholder  -> 注入外部消息列表
                  -> ChatPromptValue(messages=[SystemMessage, HumanMessage, ...])
    |
    v
  PromptValue
    +-- .to_messages() -> list[BaseMessage]    供 ChatModel 使用
    +-- .to_string()   -> str                  供 LLM 使用
""",
        content_width
    ))
    story.append(PageBreak())

    # ==================== 第五章：回调与追踪系统 ====================
    story.append(Paragraph("五、回调与追踪系统", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("5.1 回调系统架构图", s['h2']))
    story.append(Paragraph(
        "回调系统是 LangChain 的可观测性核心，支持日志记录、追踪、事件流等功能。"
        "系统由三层构成：事件定义层（Mixin）、回调处理器层（Handler）、回调管理器层（Manager）。",
        s['body']
    ))
    story.append(DiagramBox(
        "图 5-1：回调系统三层架构",
        """
  +==========================================================================+
  |                      事件定义层 (6 个 Mixin)                              |
  |  LLMManagerMixin  | ChainManagerMixin  | ToolManagerMixin                |
  |  RetrieverManagerMixin | CallbackManagerMixin | RunManagerMixin           |
  |  定义了 17+ 种回调事件方法签名                                            |
  +==========================================================================+
                                |  继承
                                v
  +==========================================================================+
  |                      处理器层 (Handler)                                   |
  |  BaseCallbackHandler (同步)  |  AsyncCallbackHandler (异步)               |
  |    +-- raise_error: bool     |    # 异步版本的所有方法                     |
  |    +-- run_inline: bool      |                                            |
  |    +-- ignore_llm/chain/...  |  BaseTracer = _TracerCore + Handler        |
  |                              |    # 追踪器就是一种特殊的 Handler            |
  +==========================================================================+
                                |  注册到
                                v
  +==========================================================================+
  |                      管理器层 (Manager)                                   |
  |  BaseCallbackManager                                                     |
  |    handlers: list[Handler]              当前层处理器                       |
  |    inheritable_handlers: list[Handler]  可继承到子运行的处理器              |
  |    tags / inheritable_tags              标签继承体系                       |
  |    metadata / inheritable_metadata      元数据继承体系                     |
  |                                                                          |
  |  CallbackManager                                                         |
  |    on_chain_start() -> CallbackManagerForChainRun                        |
  |    on_llm_start()   -> list[CallbackManagerForLLMRun]                    |
  |    on_tool_start()  -> CallbackManagerForToolRun                         |
  |                                                                          |
  |  RunManager 体系 (绑定 run_id 的分发器)                                   |
  |    ParentRunManager.get_child() -> 创建子 CallbackManager (只继承可继承项) |
  +==========================================================================+
""",
        content_width
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("<b>17 种回调事件一览：</b>", s['h3']))
    story.append(make_table(
        ["事件方法", "触发时机", "忽略条件"],
        [
            ["on_llm_start", "文本补全 LLM 开始", "ignore_llm"],
            ["on_chat_model_start", "聊天模型开始", "ignore_chat_model"],
            ["on_llm_new_token", "流式生成新 token", "ignore_llm"],
            ["on_llm_end / on_llm_error", "LLM 完成 / 出错", "ignore_llm"],
            ["on_chain_start / end / error", "Chain 开始 / 完成 / 出错", "ignore_chain"],
            ["on_tool_start / end / error", "Tool 开始 / 完成 / 出错", "ignore_agent"],
            ["on_retriever_start / end / error", "Retriever 开始 / 完成 / 出错", "ignore_retriever"],
            ["on_agent_action / finish", "Agent 执行动作 / 结束", "ignore_agent"],
            ["on_text / on_retry", "通用文本 / 重试事件", "无 / ignore_retry"],
            ["on_custom_event", "用户自定义事件", "ignore_custom_event"],
        ],
        [content_width * 0.30, content_width * 0.35, content_width * 0.35]
    ))
    story.append(Spacer(1, 6*mm))

    # 5.2 事件分发时序图
    story.append(Paragraph("5.2 Chain 调用 LLM 的事件分发时序图", s['h2']))
    story.append(DiagramBox(
        "图 5-2：回调事件传播完整时序",
        """
  用户代码            CallbackManager        Handler_1        Handler_2(Tracer)
    |                      |                    |                    |
    |-- chain.invoke(input, config={"callbacks": [handler1, tracer]})
    |                      |                    |                    |
    |-- CM.configure() --->|  合并所有来源的回调  |                    |
    |                      |  (config + 全局 + LangSmith)            |
    |                      |                    |                    |
    |-- cm.on_chain_start(serialized, inputs, run_id=A)              |
    |                      |-- handle_event --->|                    |
    |                      |     for handler:   |.on_chain_start()   |
    |                      |                    |              .on_chain_start()
    |                      |<-- return ChainRunManager(run_id=A)     |
    |                      |                    |                    |
    |   [链内部调用 LLM]    |                    |                    |
    |-- run_mgr.get_child("llm") --> 子 CallbackManager             |
    |   (parent_run_id=A, 只继承 inheritable handlers)              |
    |                      |                    |                    |
    |-- child_cm.on_llm_start(..., parent_run_id=A, run_id=B)       |
    |                      |-- handle_event --->| .on_llm_start()    |
    |                      |                    |              .on_llm_start()
    |                      |                    |              创建 Run(id=B, parent=A)
    |                      |                    |                    |
    |   [流式 token]        |                    |                    |
    |-- llm_mgr.on_llm_new_token("Hello")       |                    |
    |                      |-- handle_event --->| .on_llm_new_token()|
    |                      |                    |                    |
    |-- llm_mgr.on_llm_end(response)            |                    |
    |                      |-- @shielded ------>| .on_llm_end()      |
    |                      |   (取消保护)        |              .on_llm_end()
    |                      |                    |              完成 Run(id=B)
    |                      |                    |                    |
    |-- chain_mgr.on_chain_end(outputs)         |                    |
    |                      |-- @shielded ------>| .on_chain_end()    |
    |                      |                    |              .on_chain_end()
    |                      |                    |              持久化 Run(id=A)
""",
        content_width
    ))
    story.append(Spacer(1, 4*mm))

    # 5.3 追踪器与回调的关系
    story.append(Paragraph("5.3 追踪器与回调系统的关系", s['h2']))
    story.append(Paragraph(
        "追踪器（Tracer）通过多重继承同时具备回调处理器和 Run 管理的能力。它被注入到 "
        "CallbackManager 的 handlers 列表中，回调管理器不区分普通 handler 和 tracer。",
        s['body']
    ))

    story.append(ColoredBox(
        "关键设计：BaseTracer = _TracerCore + BaseCallbackHandler\n"
        "  - _TracerCore: 维护 run_map (run_id -> Run), order_map (dotted_order 层级路径)\n"
        "  - BaseCallbackHandler: 提供所有回调事件方法的接口\n"
        "  - 只有根运行 (parent_run_id=None) 完成时才触发 _persist_run() 持久化\n"
        "  - dotted_order 格式: 'timestamp+root_id.timestamp+child_id.timestamp+grandchild_id'",
        content_width, HIGHLIGHT_BLUE, SECONDARY
    ))
    story.append(PageBreak())

    # ==================== 第六章：工具系统与输出解析 ====================
    story.append(Paragraph("六、工具系统与输出解析", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("6.1 工具系统核心设计", s['h2']))
    story.append(Paragraph(
        "BaseTool 继承自 RunnableSerializable，因此工具本身就是 Runnable，可直接参与 LCEL 链式组合。"
        "@tool 装饰器是创建工具最便捷的方式，它根据函数签名自动推断参数 Schema。",
        s['body']
    ))

    story.append(DiagramBox(
        "图 6-1：工具系统类继承图",
        """
  RunnableSerializable[str | dict | ToolCall, Any]
    |
    +-- BaseTool (ABC)                             ← 工具基类
          字段: name, description, args_schema      ← 工具标识
                return_direct: bool                 ← Agent 是否直接返回
                response_format: "content" | "content_and_artifact"
                handle_tool_error: bool|str|Callable ← 错误处理策略
          方法: invoke() -> run() -> _run()         ← 模板方法模式
          |
          +-- StructuredTool                        ← 结构化工具 (@tool 创建)
          |     func: Callable                       同步函数引用
          |     coroutine: Callable                  异步函数引用
          |     from_function() 工厂方法
          |
          +-- Tool                                  ← 简单字符串工具

  @tool 装饰器:
    @tool              -> StructuredTool (自动推断 schema)
    @tool("name")      -> StructuredTool (自定义名称)
    @tool(parse_docstring=True) -> StructuredTool (从 docstring 提取描述)

  依赖注入系统:
    InjectedToolArg    -> 标注运行时注入参数 (不暴露给 LLM schema)
    InjectedToolCallId -> 自动注入 tool_call_id
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 6.2 工具调用完整时序图
    story.append(Paragraph("6.2 工具调用完整时序图", s['h2']))
    story.append(DiagramBox(
        "图 6-2：BaseTool.invoke() -> run() -> _run() 调用链时序",
        """
  User              BaseTool.invoke()     BaseTool.run()      CallbackMgr       子类._run()
   |                      |                    |                  |                |
   |-- invoke(input) ---->|                    |                  |                |
   |                      |-- _prep_run_args() |                  |                |
   |                      |   解析 ToolCall/str/dict, 提取 tool_call_id           |
   |                      |                    |                  |                |
   |                      |-- run(tool_input) ->|                  |                |
   |                      |                    |-- configure() -->|                |
   |                      |                    |-- _filter_injected_args()         |
   |                      |                    |-- on_tool_start() |                |
   |                      |                    |                  |-- notify -->   |
   |                      |                    |                  |                |
   |                      |                    |-- _to_args_and_kwargs()           |
   |                      |                    |   _parse_input() (Pydantic 验证)  |
   |                      |                    |   注入 InjectedToolCallId 等      |
   |                      |                    |                  |                |
   |                      |                    |-- _run(*args) ------------------>|
   |                      |                    |<-- content (str|dict|tuple) -----|
   |                      |                    |                  |                |
   |                      |                    |-- _format_output()               |
   |                      |                    |   有 tool_call_id -> ToolMessage |
   |                      |                    |   无 tool_call_id -> 原始值      |
   |                      |                    |                  |                |
   |                      |                    |-- on_tool_end -->|                |
   |<-- ToolMessage ------|                    |                  |                |

  错误处理: ToolException -> handle_tool_error 策略
            ValidationError -> handle_validation_error 策略
            其他 Exception -> 直接抛出
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 6.3 输出解析器体系
    story.append(Paragraph("6.3 输出解析器体系", s['h2']))
    story.append(DiagramBox(
        "图 6-3：输出解析器继承体系与解析流程",
        """
  BaseLLMOutputParser[T] (ABC, Generic[T])         ← 最底层抽象
    |
    +-- BaseGenerationOutputParser[T]                ← Generation 级别解析
    |
    +-- BaseOutputParser[T]                          ← 文本级别解析 (主用)
          |  抽象方法: parse(text: str) -> T
          |  方法: get_format_instructions() -> str
          |
          +-- StrOutputParser                        ← 直接返回文本
          +-- ListOutputParser                       ← 解析为列表
          +-- BaseCumulativeTransformOutputParser     ← 支持流式增量输出
          |     +-- JsonOutputParser                 ← 解析 JSON
          |           +-- PydanticOutputParser        ← 解析为 Pydantic 模型
          +-- OpenAI Tools/Functions Parser           ← 解析工具调用

  解析链路:
    invoke(input: str|BaseMessage)
      -> 包装为 Generation
      -> parse_result([generation])
         -> parse(result[0].text)         子类实现: 文本 -> 结构化

  PydanticOutputParser 两层解析:
    LLM输出文本 -> JSON解析(parse_json_markdown) -> dict -> Pydantic model_validate -> 类型安全对象
""",
        content_width
    ))
    story.append(PageBreak())

    # ==================== 第七章：数据层 ====================
    story.append(Paragraph("七、数据层：文档、检索与向量存储", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("7.1 数据层类图", s['h2']))
    story.append(DiagramBox(
        "图 7-1：数据层核心类关系图",
        """
  Serializable
    |
    +-- BaseMedia
          +-- Document (page_content: str, metadata: dict, id: str|None)
          +-- Blob (data: bytes|str|None, path: PathLike, mimetype: str)
                  惰性加载: from_path() 不立即读文件

  BaseLoader (ABC)                              ← 文档加载器
    抽象方法: lazy_load() -> Iterator[Document]
    便捷方法: load() -> list[Document]
              alazy_load() -> AsyncIterator[Document]  (默认线程池)

  VectorStore (ABC)                             ← 向量存储
    抽象方法: similarity_search(query, k=4) -> list[Document]
              from_texts(texts, embedding) -> VectorStore
    搜索方法: similarity_search_with_score()
              similarity_search_with_relevance_scores()
              max_marginal_relevance_search()
    统一入口: search(query, search_type="similarity|mmr|similarity_score_threshold")
    桥接方法: as_retriever() -> VectorStoreRetriever

  BaseRetriever (RunnableSerializable[str, list[Document]])  ← 检索器
    抽象方法: _get_relevant_documents(query) -> list[Document]
    |
    +-- VectorStoreRetriever                    ← 桥接 VectorStore
          vectorstore: VectorStore
          search_type: "similarity" | "mmr" | "similarity_score_threshold"
          search_kwargs: dict (k, score_threshold, filter, ...)

  Embeddings (ABC)                              ← 嵌入模型
    抽象方法: embed_documents(texts) -> list[list[float]]
              embed_query(text) -> list[float]
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # 7.2 RAG 完整流程图
    story.append(Paragraph("7.2 RAG 完整流程图", s['h2']))
    story.append(DiagramBox(
        "图 7-2：RAG (检索增强生成) 完整数据流",
        """
  === 索引阶段 (离线) ===

  原始数据 --> BaseLoader.lazy_load() --> list[Document]
                                           |
                                           v
                                    TextSplitter.split_documents()
                                           |
                                           v
                                    list[Document] (分块后)
                                           |
                                           v
                                    Embeddings.embed_documents() --> list[list[float]]
                                           |
                                           v
                                    VectorStore.add_documents() --> 存入向量数据库

  === 查询阶段 (在线) ===

  用户问题: "What is LangChain?"
    |
    v
  LCEL 管道:  {"question": RunnablePassthrough()}
              | RunnablePassthrough.assign(
                  context = itemgetter("question") | retriever | format_docs
                )
              | prompt
              | model
              | StrOutputParser()

  详细流程:
    1. retriever._get_relevant_documents("What is LangChain?")
         -> VectorStore.similarity_search(query, k=4)
         -> 返回 top-k 相关文档

    2. format_docs(documents) -> 拼接为上下文文本

    3. prompt.format_messages(context=..., question=...)
         -> [SystemMessage("基于以下上下文回答..."), HumanMessage("What is LangChain?")]

    4. model._generate(messages) -> AIMessage(content="LangChain 是一个...")

    5. StrOutputParser().parse(ai_message) -> "LangChain 是一个..."
""",
        content_width
    ))
    story.append(PageBreak())

    # ==================== 第八章：序列化与反序列化系统 ====================
    story.append(Paragraph("八、序列化与反序列化系统", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))

    story.append(Paragraph("8.1 序列化机制", s['h2']))
    story.append(Paragraph(
        "Serializable 是序列化的基类，通过 is_lc_serializable()、get_lc_namespace() 等方法"
        "控制序列化行为。序列化输出三种格式：constructor（可重建）、secret（敏感信息占位）、"
        "not_implemented（不可序列化）。",
        s['body']
    ))

    story.append(make_table(
        ["序列化类型", "TypedDict", "type 字段", "用途"],
        [
            ["可序列化对象", "SerializedConstructor", '"constructor"', "含 kwargs，可反序列化重建对象"],
            ["敏感信息", "SerializedSecret", '"secret"', "密钥占位符，值不被序列化"],
            ["不可序列化", "SerializedNotImplemented", '"not_implemented"', "含 repr 字符串，不可重建"],
        ],
        [content_width * 0.18, content_width * 0.25, content_width * 0.17, content_width * 0.40]
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "<b>to_json() 核心流程：</b>"
        "检查 is_lc_serializable() -> 遍历模型字段过滤有意义的值 -> "
        "收集 MRO 链上的 lc_secrets 和 lc_attributes -> "
        "用 _replace_secrets() 将秘密值替换为 SerializedSecret -> "
        '输出 {"lc": 1, "type": "constructor", "id": [...], "kwargs": {...}}',
        s['body']
    ))
    story.append(Spacer(1, 6*mm))

    # 8.2 安全反序列化流程图
    story.append(Paragraph("8.2 安全反序列化流程图", s['h2']))
    story.append(DiagramBox(
        "图 8-1：load() 安全反序列化流程",
        """
  load(obj, allowed_objects="core", secrets_map={...})
    |
    +-- Reviver 类 (用作 object_hook)
          |
          +-- 处理 type="secret":
          |     从 secrets_map 或环境变量获取实际值
          |
          +-- 处理 type="not_implemented":
          |     抛出 NotImplementedError 或返回 None
          |
          +-- 处理 type="constructor":
                |
                +-- 1. 白名单校验 (三级安全模型):
                |       "core"  -> 仅 langchain_core 映射中的类
                |       "all"   -> 含核心 + 可信合作伙伴集成
                |       显式列表 -> 仅指定的类
                |
                +-- 2. 命名空间校验:
                |       检查 id[0] 是否在 valid_namespaces 中
                |       禁止 langchain_community 通过路径加载
                |
                +-- 3. 动态导入:
                |       importlib.import_module(namespace) -> 获取类
                |
                +-- 4. init_validator:
                |       验证 kwargs 参数安全性
                |       _block_jinja2_templates() 阻止模板注入
                |
                +-- 5. 实例化:
                      cls(**kwargs)

  安全防护:
    - _is_escaped_dict() 处理被转义的 dict (防止 'lc' key 注入)
    - _block_jinja2_templates() 阻止 jinja2 模板注入攻击
    - DISALLOW_LOAD_FROM_PATH 禁止特定包的路径加载
""",
        content_width
    ))
    story.append(Spacer(1, 6*mm))

    # ==================== 附录 ====================
    story.append(Paragraph("附录：RunnableConfig 配置体系", s['h1']))
    story.append(HorizontalLine(content_width, PRIMARY, 1.5))
    story.append(Paragraph(
        "RunnableConfig 是贯穿所有 Runnable 组件的配置传递机制，以 TypedDict 形式定义，"
        "通过 ContextVar 在父子组件间自动传播。",
        s['body']
    ))

    story.append(make_table(
        ["字段", "类型", "说明"],
        [
            ["tags", "list[str]", "过滤标签，可继承到子运行"],
            ["metadata", "dict[str, Any]", "元数据，JSON 可序列化，可继承"],
            ["callbacks", "Callbacks", "回调处理器链，可继承"],
            ["run_name", "str", "Tracer 中显示的运行名称"],
            ["max_concurrency", "int | None", "最大并发数限制"],
            ["recursion_limit", "int", "递归调用限制，默认 25"],
            ["configurable", "dict[str, Any]", "运行时可配置字段（如 session_id）"],
            ["run_id", "UUID | None", "唯一运行标识符"],
        ],
        [content_width * 0.20, content_width * 0.25, content_width * 0.55]
    ))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("<b>配置传播五大工具函数：</b>", s['h3']))
    story.append(make_table(
        ["函数", "功能"],
        [
            ["ensure_config(config)", "补全默认值 + 合并 ContextVar 上下文配置"],
            ["patch_config(config, ...)", "用新值覆盖指定字段（替换 callbacks 时自动清除 run_name/run_id）"],
            ["merge_configs(*configs)", "合并多个配置：tags 取并集，metadata 合并，callbacks 智能合并"],
            ["get_config_list(config, length)", "将单个配置扩展为 batch 所需的配置列表"],
            ["run_in_executor(config, func)", "在线程池中运行，自动复制 contextvars.Context 到子线程"],
        ],
        [content_width * 0.35, content_width * 0.65]
    ))

    # Build
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF 文档已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    build_document()
