#!/usr/bin/env python3
"""langchain-classic 源码架构分析 PDF 生成脚本"""
import os, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                 Table, TableStyle, Flowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 颜色
CP = HexColor("#1a73e8"); CS = HexColor("#34a853"); CA = HexColor("#ea4335")
CO = HexColor("#f9ab00"); CV = HexColor("#9334e6"); CD = HexColor("#202124")
CG = HexColor("#5f6368"); CL = HexColor("#f8f9fa"); CW = white
BB = HexColor("#e8f0fe"); BG = HexColor("#e6f4ea"); BY = HexColor("#fef7e0"); BP = HexColor("#f3e8fd")

# 中文字体
FC = "Helvetica"; FB = "Helvetica-Bold"
for fp in ["/System/Library/Fonts/STHeiti Medium.ttc","/System/Library/Fonts/PingFang.ttc",
           "/System/Library/Fonts/Supplemental/Songti.ttc","/Library/Fonts/Arial Unicode.ttf",
           "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont("CF", fp)); FC = FB = "CF"; break
        except: continue

class Diagram(Flowable):
    def __init__(s, w, h, fn): Flowable.__init__(s); s.width=w; s.height=h; s.fn=fn
    def wrap(s,aW,aH): return s.width, s.height
    def draw(s): s.fn(s.canv, s.width, s.height)

def rrect(c,x,y,w,h,r,fc,sc=None,sw=1):
    c.saveState(); c.setFillColor(fc); c.setStrokeColor(sc or fc); c.setLineWidth(sw)
    c.roundRect(x,y,w,h,r,fill=1,stroke=1); c.restoreState()

def arrow(c,x1,y1,x2,y2,col=None,lw=1.5):
    col = col or CD; c.saveState(); c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(lw)
    c.line(x1,y1,x2,y2)
    a=math.atan2(y2-y1,x2-x1); al=8; aa=math.pi/6
    p=c.beginPath(); p.moveTo(x2,y2)
    p.lineTo(x2-al*math.cos(a-aa),y2-al*math.sin(a-aa))
    p.lineTo(x2-al*math.cos(a+aa),y2-al*math.sin(a+aa)); p.close()
    c.drawPath(p,fill=1); c.restoreState()

def tbox(c,t,x,y,w,h,sz=9,col=None):
    col = col or CD; c.saveState(); c.setFont(FC,sz); c.setFillColor(col)
    tw=c.stringWidth(t,FC,sz); c.drawString(x+(w-tw)/2,y+(h-sz)/2+1,t); c.restoreState()

def diamond(c,cx,cy,w,h,fc,sc=None):
    c.saveState(); c.setFillColor(fc); c.setStrokeColor(sc or fc); c.setLineWidth(1)
    p=c.beginPath(); p.moveTo(cx,cy+h/2); p.lineTo(cx+w/2,cy); p.lineTo(cx,cy-h/2)
    p.lineTo(cx-w/2,cy); p.close(); c.drawPath(p,fill=1,stroke=1); c.restoreState()

# ====== 绘图函数 ======
def draw_agent_flow(cv, W, H):
    cv.setFont(FB,13); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"Agent 执行主流程图 (AgentExecutor)")
    bw,bh=140,30; sx=W/2-bw/2; mid=W/2
    nodes=[(H-65,"用户输入 (inputs)",BB,CP),(H-110,"prep_inputs() 准备输入",BG,CS),
           (H-155,"Memory.load_memory_variables()",BY,CO),(H-200,"Agent.plan() 决策",BP,CV)]
    for ny,lb,bg,bd in nodes:
        rrect(cv,sx,ny,bw,bh,6,bg,bd,1.5); tbox(cv,lb,sx,ny,bw,bh,8)
    for i in range(len(nodes)-1): arrow(cv,mid,nodes[i][0],mid,nodes[i+1][0]+bh)
    dcy=H-255; diamond(cv,mid,dcy,130,40,BP,CV)
    cv.setFont(FC,8); cv.setFillColor(CD); t="AgentFinish?"; cv.drawString(mid-cv.stringWidth(t,FC,8)/2,dcy-4,t)
    arrow(cv,mid,nodes[3][0],mid,dcy+20)
    # No -> Tool
    tool_nodes=[(H-315,"Tool.run() 执行工具",BB,CP),(H-360,"观察结果 (observation)",BG,CS),
                (H-405,"更新 intermediate_steps",BY,CO)]
    for ny,lb,bg,bd in tool_nodes:
        rrect(cv,sx,ny,bw,bh,6,bg,bd,1.5); tbox(cv,lb,sx,ny,bw,bh,8)
    arrow(cv,mid,dcy-20,mid,tool_nodes[0][0]+bh)
    cv.setFont(FC,7); cv.setFillColor(CA); cv.drawString(mid+5,dcy-18,"No")
    for i in range(len(tool_nodes)-1): arrow(cv,mid,tool_nodes[i][0],mid,tool_nodes[i+1][0]+bh)
    # 循环箭头
    lx=sx+bw+15
    cv.saveState(); cv.setStrokeColor(CA); cv.setLineWidth(1.5); cv.setDash(3,3)
    cv.line(lx,tool_nodes[2][0]+bh/2,lx+30,tool_nodes[2][0]+bh/2)
    cv.line(lx+30,tool_nodes[2][0]+bh/2,lx+30,nodes[3][0]+bh/2); cv.restoreState()
    arrow(cv,lx+30,nodes[3][0]+bh/2,sx+bw,nodes[3][0]+bh/2,CA)
    cv.setFont(FC,7); cv.setFillColor(CA); cv.drawString(lx+32,(tool_nodes[2][0]+nodes[3][0])/2+bh/2,"迭代循环")
    # Yes -> Finish
    fx=sx-80; fy=H-255
    cv.setFont(FC,7); cv.setFillColor(CS); cv.drawString(mid-80,dcy+2,"Yes")
    arrow(cv,mid-65,dcy,fx+55,dcy,CS)
    fin=[(fy-40,"prep_outputs()",BG,CS),(fy-80,"Memory.save_context()",BG,CS),(fy-120,"返回最终结果",BB,CP)]
    for ny,lb,bg,bd in fin:
        rrect(cv,fx-45,ny,100,28,6,bg,bd,1.5); tbox(cv,lb,fx-45,ny,100,28,8)
    for i in range(len(fin)-1): arrow(cv,fx+5,fin[i][0],fx+5,fin[i+1][0]+28,CS)
    cv.setFont(FC,7); cv.setFillColor(CG)
    cv.drawString(15,25,"回调事件: on_chain_start → on_llm_start → on_agent_action → on_tool_start → on_tool_end → on_chain_end")

def draw_chain_flow(cv, W, H):
    cv.setFont(FB,13); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"Chain 执行流程图 (模板方法模式)")
    bw,bh=160,32; sx=W/2-bw/2; mid=W/2
    steps=[(H-65,"chain.invoke(input, config)",BB,CP),(H-112,"CallbackManager.on_chain_start()",BY,CO),
           (H-159,"prep_inputs(input)",BG,CS),(H-206,"memory.load_memory_variables()",BP,CV),
           (H-253,"_validate_inputs(inputs)",CL,CG),(H-300,"_call(inputs, run_manager)",BB,CP),
           (H-347,"_validate_outputs(outputs)",CL,CG),(H-394,"prep_outputs(inputs, outputs)",BG,CS),
           (H-441,"memory.save_context()",BP,CV),(H-488,"on_chain_end() / on_chain_error()",BY,CO)]
    for ny,lb,bg,bd in steps:
        rrect(cv,sx,ny,bw,bh,6,bg,bd,1.5); tbox(cv,lb,sx,ny,bw,bh,8)
    for i in range(len(steps)-1): arrow(cv,mid,steps[i][0],mid,steps[i+1][0]+bh)
    cv.saveState(); cv.setStrokeColor(CA); cv.setDash(4,4); cv.setLineWidth(1)
    cv.roundRect(sx-10,steps[5][0]-5,bw+20,bh+10,4,fill=0,stroke=1); cv.restoreState()
    cv.setFont(FC,7); cv.setFillColor(CG); cv.drawString(sx-80,steps[5][0]+bh/2,"← 子类实现(抽象方法)")

def draw_rag_flow(cv, W, H):
    cv.setFont(FB,13); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"RAG 检索增强生成流程图 (RetrievalQA)")
    lx,ly=30,H-65; bw,bh=130,28
    lnodes=[(ly,"用户提问 (query)",BB,CP),(ly-50,"Retriever.检索文档",BG,CS),
            (ly-100,"VectorStore.相似度搜索",BP,CV),(ly-150,"返回 Top-K 文档",BY,CO)]
    for ny,lb,bg,bd in lnodes:
        rrect(cv,lx,ny,bw,bh,5,bg,bd,1.2); tbox(cv,lb,lx,ny,bw,bh,7.5)
    lm=lx+bw/2
    for i in range(len(lnodes)-1): arrow(cv,lm,lnodes[i][0],lm,lnodes[i+1][0]+bh)
    rx=W-30-bw
    rnodes=[(ly-150,"CombineDocumentsChain",BG,CS),(ly-200,"Stuff / MapReduce / Refine",BP,CV),
            (ly-250,"LLMChain.生成回答",BB,CP),(ly-300,"最终答案 + 源文档",BY,CO)]
    for ny,lb,bg,bd in rnodes:
        rrect(cv,rx,ny,bw,bh,5,bg,bd,1.2); tbox(cv,lb,rx,ny,bw,bh,7.5)
    rm=rx+bw/2
    for i in range(len(rnodes)-1): arrow(cv,rm,rnodes[i][0],rm,rnodes[i+1][0]+bh)
    arrow(cv,lx+bw,lnodes[3][0]+bh/2,rx,rnodes[0][0]+bh/2,CA,2)
    cv.setFont(FC,7); cv.setFillColor(CA); cv.drawCentredString(W/2,lnodes[3][0]+bh/2+8,"docs 传递")
    sy=ly-340; sw=(W-40)/3-10
    for i,(nm,dc,bg) in enumerate([("Stuff","拼接所有文档为一个 Prompt",BB),("MapReduce","先 Map 各文档再 Reduce 合并",BG),("Refine","逐篇文档迭代精炼结果",BP)]):
        bx=20+i*(sw+10); rrect(cv,bx,sy,sw,45,5,bg,CG,1)
        cv.setFont(FB,9); cv.setFillColor(CD); cv.drawCentredString(bx+sw/2,sy+28,nm)
        cv.setFont(FC,7); cv.setFillColor(CG); cv.drawCentredString(bx+sw/2,sy+12,dc)

def draw_llmchain_seq(cv, W, H):
    cv.setFont(FB,13); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"LLMChain 调用时序图")
    actors=[("User",60,BB,CP),("LLMChain",170,BG,CS),("PromptTemplate",290,BY,CO),
            ("LLM",400,BP,CV),("OutputParser",510,BB,CP)]
    ty=H-55; aw,ah=80,24
    for nm,x,bg,bd in actors:
        rrect(cv,x-aw/2,ty,aw,ah,4,bg,bd,1.2); tbox(cv,nm,x-aw/2,ty,aw,ah,8)
    cv.saveState(); cv.setStrokeColor(CG); cv.setDash(3,3); cv.setLineWidth(0.8)
    for _,x,_,_ in actors: cv.line(x,ty,x,40)
    cv.restoreState()
    msgs=[(H-100,0,1,"invoke(inputs)",CP),(H-130,1,2,"format(inputs)",CS),(H-160,2,1,"PromptValue",CO),
          (H-190,1,3,"generate(prompts)",CS),(H-220,3,3,"LLM 推理中...",CV),(H-250,3,1,"LLMResult",CV),
          (H-280,1,4,"parse(result)",CS),(H-310,4,1,"结构化结果",CP),(H-340,1,0,"返回 {output_key: text}",CP)]
    for my,s,d,lb,col in msgs:
        sx2=actors[s][1]; dx2=actors[d][1]
        if s==d:
            cv.saveState(); cv.setStrokeColor(col); cv.setLineWidth(1.2)
            cv.line(sx2,my,sx2+30,my); cv.line(sx2+30,my,sx2+30,my-15); cv.restoreState()
            arrow(cv,sx2+30,my-15,sx2+2,my-15,col,1.2)
            cv.setFont(FC,7); cv.setFillColor(col); cv.drawString(sx2+5,my+4,lb)
        else:
            arrow(cv,sx2,my,dx2,my,col,1.2)
            cv.setFont(FC,7); cv.setFillColor(col); cv.drawCentredString((sx2+dx2)/2,my+4,lb)

def draw_agent_seq(cv, W, H):
    cv.setFont(FB,13); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"Agent 推理循环时序图")
    actors=[("User",50,BB,CP),("AgentExecutor",155,BG,CS),("Agent",265,BP,CV),
            ("LLM",365,BY,CO),("Tool",465,BB,CP),("Callback",555,BG,CS)]
    ty=H-55; aw,ah=72,24
    for nm,x,bg,bd in actors:
        rrect(cv,x-aw/2,ty,aw,ah,4,bg,bd,1.2); tbox(cv,nm,x-aw/2,ty,aw,ah,7.5)
    cv.saveState(); cv.setStrokeColor(CG); cv.setDash(3,3); cv.setLineWidth(0.8)
    for _,x,_,_ in actors: cv.line(x,ty,x,20)
    cv.restoreState()
    msgs=[(H-95,0,1,"invoke(input)",CP),(H-118,1,5,"on_chain_start",CS),
          (H-141,1,2,"plan(intermediate_steps)",CS),(H-164,2,3,"LLM.invoke(prompt)",CV),
          (H-187,3,2,"AgentAction(tool,input)",CO),(H-210,2,1,"AgentAction",CV),
          (H-233,1,5,"on_agent_action",CS),(H-256,1,4,"tool.run(tool_input)",CP),
          (H-279,4,1,"observation (str)",CP),(H-302,1,1,"update intermediate_steps",CS),
          (H-328,1,2,"plan(intermediate_steps)",CS),(H-351,2,3,"LLM.invoke(prompt+steps)",CV),
          (H-374,3,2,"AgentFinish(output)",CO),(H-397,2,1,"AgentFinish",CV),
          (H-420,1,5,"on_agent_finish",CS),(H-443,1,0,"返回最终结果",CP)]
    for my,s,d,lb,col in msgs:
        sx2=actors[s][1]; dx2=actors[d][1]
        if s==d:
            cv.saveState(); cv.setStrokeColor(col); cv.setLineWidth(1)
            cv.line(sx2,my,sx2+25,my); cv.line(sx2+25,my,sx2+25,my-12); cv.restoreState()
            arrow(cv,sx2+25,my-12,sx2+2,my-12,col,1); cv.setFont(FC,6.5); cv.setFillColor(col); cv.drawString(sx2+3,my+3,lb)
        else:
            arrow(cv,sx2,my,dx2,my,col,1); cv.setFont(FC,6.5); cv.setFillColor(col); cv.drawCentredString((sx2+dx2)/2,my+3,lb)
    cv.saveState(); cv.setStrokeColor(CA); cv.setDash(4,3); cv.setLineWidth(1.2)
    cv.roundRect(100,H-315,480,240,5,fill=0,stroke=1); cv.restoreState()
    cv.setFont(FB,8); cv.setFillColor(CA); cv.drawString(105,H-80,"loop [直到 AgentFinish 或超时]")

def draw_conv_seq(cv, W, H):
    cv.setFont(FB,12); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"对话检索链时序图 (ConversationalRetrievalChain)")
    actors=[("User",55,BB,CP),("ConvRetChain",165,BG,CS),("QuestionGen",285,BY,CO),
            ("Retriever",395,BP,CV),("CombineDocs",510,BB,CP)]
    ty=H-55; aw,ah=78,24
    for nm,x,bg,bd in actors:
        rrect(cv,x-aw/2,ty,aw,ah,4,bg,bd,1.2); tbox(cv,nm,x-aw/2,ty,aw,ah,7.5)
    cv.saveState(); cv.setStrokeColor(CG); cv.setDash(3,3); cv.setLineWidth(0.8)
    for _,x,_,_ in actors: cv.line(x,ty,x,50)
    cv.restoreState()
    msgs=[(H-100,0,1,"question + chat_history",CP),(H-135,1,2,"重写问题(q + history)",CS),
          (H-170,2,1,"standalone_question",CO),(H-205,1,3,"检索文档(new_q)",CS),
          (H-240,3,1,"List[Document]",CV),(H-275,1,4,"合并文档+生成答案",CS),
          (H-310,4,1,"answer",CP),(H-345,1,0,"{answer, source_documents}",CP)]
    for my,s,d,lb,col in msgs:
        sx2=actors[s][1]; dx2=actors[d][1]
        arrow(cv,sx2,my,dx2,my,col,1.2); cv.setFont(FC,7); cv.setFillColor(col)
        cv.drawCentredString((sx2+dx2)/2,my+4,lb)

def draw_memory_flow(cv, W, H):
    cv.setFont(FB,13); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"Memory 记忆系统工作流程")
    bw,bh=150,28; mid=W/2
    cv.setFont(FB,10); cv.setFillColor(CS); cv.drawString(30,H-55,"① Chain 执行前（加载记忆）")
    pn=[(H-80,"chain.prep_inputs(input)",BB,CP),(H-120,"memory.load_memory_variables()",BG,CS),
        (H-160,"合并记忆变量到输入",BY,CO)]
    for ny,lb,bg,bd in pn:
        rrect(cv,mid-bw/2,ny,bw,bh,5,bg,bd,1.2); tbox(cv,lb,mid-bw/2,ny,bw,bh,8)
    for i in range(len(pn)-1): arrow(cv,mid,pn[i][0],mid,pn[i+1][0]+bh)
    cv.setFont(FB,10); cv.setFillColor(CA); cv.drawString(30,H-210,"② Chain 执行后（保存记忆）")
    qn=[(H-235,"chain.prep_outputs(in, out)",BB,CP),(H-275,"memory.save_context(in, out)",BG,CS),
        (H-315,"更新对话历史/实体摘要",BY,CO)]
    for ny,lb,bg,bd in qn:
        rrect(cv,mid-bw/2,ny,bw,bh,5,bg,bd,1.2); tbox(cv,lb,mid-bw/2,ny,bw,bh,8)
    for i in range(len(qn)-1): arrow(cv,mid,qn[i][0],mid,qn[i+1][0]+bh)
    rx=W-180; cv.setFont(FB,9); cv.setFillColor(CV); cv.drawString(rx,H-60,"Memory 类型:")
    for i,(nm,dc) in enumerate([("Buffer","全量存储对话历史"),("Window","滑动窗口截取"),("Summary","LLM 增量摘要"),("Entity","实体提取+摘要"),("Combined","多 Memory 组合")]):
        ty2=H-85-i*32; rrect(cv,rx,ty2,155,26,4,BP,CV,1)
        cv.setFont(FB,8); cv.setFillColor(CD); cv.drawString(rx+5,ty2+12,nm)
        cv.setFont(FC,7); cv.setFillColor(CG); cv.drawString(rx+60,ty2+12,dc)

def draw_router_flow(cv, W, H):
    cv.setFont(FB,13); cv.setFillColor(CP); cv.drawCentredString(W/2,H-25,"MultiRouteChain 路由流程图")
    mid=W/2; bw,bh=150,28
    rrect(cv,mid-bw/2,H-65,bw,bh,5,BB,CP,1.5); tbox(cv,"用户输入",mid-bw/2,H-65,bw,bh,9)
    rrect(cv,mid-bw/2,H-115,bw,bh,5,BG,CS,1.5); tbox(cv,"LLMRouterChain.路由决策",mid-bw/2,H-115,bw,bh,8)
    arrow(cv,mid,H-65,mid,H-87)
    diamond(cv,mid,H-170,140,40,BY,CO)
    cv.setFont(FC,8); cv.setFillColor(CD); t="Route(dest, inputs)"; cv.drawString(mid-cv.stringWidth(t,FC,8)/2,H-173,t)
    arrow(cv,mid,H-115,mid,H-150)
    dy=H-250
    for dx,lb,bg in [(70,"Chain A (文本分析)",BP),(mid-55,"Chain B (代码生成)",BB),(W-180,"Chain C (数据查询)",BG)]:
        rrect(cv,dx,dy,120,bh,5,bg,CG,1.2); tbox(cv,lb,dx,dy,120,bh,7.5)
        arrow(cv,mid,H-190,dx+60,dy+bh,CO,1.2)
    rrect(cv,mid-60,H-310,120,bh,5,BY,CO,1.5); tbox(cv,"Default Chain (默认)",mid-60,H-310,120,bh,8)
    cv.setFont(FC,7); cv.setFillColor(CG); cv.drawCentredString(mid,H-290,"dest = None 或不在列表中")

# ====== PDF 构建 ======
def build_pdf(out):
    doc = SimpleDocTemplate(out, pagesize=A4, topMargin=2*cm, bottomMargin=1.5*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    W = A4[0] - 3*cm
    st = getSampleStyleSheet()
    s_t = ParagraphStyle("T",parent=st["Title"],fontName=FB,fontSize=22,spaceAfter=6,textColor=CP,alignment=TA_CENTER)
    s_st = ParagraphStyle("ST",parent=st["Normal"],fontName=FC,fontSize=12,spaceAfter=20,textColor=CG,alignment=TA_CENTER)
    s_h1 = ParagraphStyle("H1",parent=st["Heading1"],fontName=FB,fontSize=18,spaceBefore=20,spaceAfter=10,textColor=CP,borderColor=CP,borderWidth=2,borderPadding=5)
    s_h2 = ParagraphStyle("H2",parent=st["Heading2"],fontName=FB,fontSize=14,spaceBefore=14,spaceAfter=8,textColor=HexColor("#1565c0"))
    s_b = ParagraphStyle("B",parent=st["Normal"],fontName=FC,fontSize=10,leading=16,spaceAfter=6,alignment=TA_JUSTIFY)
    s_th = ParagraphStyle("TH",parent=st["Normal"],fontName=FB,fontSize=9,textColor=CW,alignment=TA_CENTER)
    s_td = ParagraphStyle("TD",parent=st["Normal"],fontName=FC,fontSize=8.5,leading=12)
    P = Paragraph; S = Spacer; PB = PageBreak
    TS = lambda d,cw: _mktable(d,cw)

    def _mktable(data, cw):
        t = Table(data, colWidths=cw)
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),CP),("TEXTCOLOR",(0,0),(-1,0),CW),
            ("FONTNAME",(0,0),(-1,-1),FC),("FONTSIZE",(0,0),(-1,-1),9),
            ("GRID",(0,0),(-1,-1),0.5,CG),("ROWBACKGROUNDS",(0,1),(-1,-1),[CW,CL]),
            ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        return t

    story = []
    # 封面
    story += [S(1,80), P("LangChain Classic", s_t),
              P("源码架构分析与设计说明", ParagraphStyle("ST2",parent=s_st,fontSize=16,textColor=CD,spaceAfter=10)),
              S(1,15), P("langchain-classic v1.0.3 (libs/langchain)", s_st), S(1,30)]

    cv_data = [["项目","langchain-classic (经典版 LangChain)"],["版本","v1.0.3"],["语言","Python >= 3.10"],
               ["核心依赖","langchain-core >= 1.2.19"],["框架体系","Pydantic v2 + LCEL (Runnable)"],
               ["设计模式","模板方法 / 策略 / 观察者 / 组合 / 工厂方法"]]
    ct = Table(cv_data, colWidths=[120,W-140])
    ct.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),BB),("TEXTCOLOR",(0,0),(0,-1),CP),
        ("FONTNAME",(0,0),(0,-1),FB),("FONTNAME",(1,0),(1,-1),FC),("FONTSIZE",(0,0),(-1,-1),10),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("GRID",(0,0),(-1,-1),0.5,CG),
        ("ROWBACKGROUNDS",(1,0),(1,-1),[CW,CL]),("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),("LEFTPADDING",(0,0),(-1,-1),8)]))
    story += [ct, PB()]

    # 目录
    story.append(P("目录", s_h1))
    toc = ["一、项目整体架构概览","二、核心模块说明","三、核心流程图",
           "    3.1 Agent 执行主流程","    3.2 Chain 执行流程","    3.3 RAG 检索增强生成流程",
           "    3.4 Memory 记忆工作流程","    3.5 Router Chain 路由流程",
           "四、核心时序图","    4.1 LLMChain 调用时序","    4.2 Agent 推理循环时序","    4.3 对话检索链时序",
           "五、核心类设计说明","    5.1 Chain 基类体系","    5.2 Agent 智能体体系","    5.3 Memory 记忆体系",
           "    5.4 Retriever 检索器体系","    5.5 OutputParser 输出解析器","    5.6 Callback 回调体系",
           "六、设计模式总结"]
    for item in toc:
        ind = 20 if item.startswith("    ") else 0
        story.append(P(item.strip(), ParagraphStyle("toc",parent=s_b,leftIndent=ind,fontSize=10.5,spaceAfter=4)))
    story.append(PB())

    # 第一章
    story.append(P("一、项目整体架构概览", s_h1))
    story.append(P("langchain-classic 是 LangChain 生态的<b>核心编排层</b>，负责将 langchain-core 提供的基础抽象（Runnable、BaseRetriever、BaseChatModel 等）和 langchain-community 提供的第三方集成组合成完整的应用。它是构建 LLM 应用的主要入口点。", s_b))
    story.append(P("架构分层", s_h2))
    story.append(_mktable([
        [P("<b>层次</b>",s_th),P("<b>包名</b>",s_th),P("<b>职责</b>",s_th)],
        [P("核心层",s_td),P("langchain-core",s_td),P("基础抽象、接口、Runnable 协议、LCEL 表达式语言",s_td)],
        [P("编排层",s_td),P("langchain-classic",s_td),P("Chain、Agent、Memory、Retriever、Evaluation 等具体实现",s_td)],
        [P("集成层",s_td),P("langchain-community",s_td),P("170+ 文档加载器、80+ LLM、60+ Embedding、80+ VectorStore",s_td)],
        [P("伙伴层",s_td),P("partners/*",s_td),P("OpenAI、Anthropic、Ollama 等官方维护的集成包",s_td)],
    ],[70,110,W-200]))
    story.append(S(1,10))
    story.append(P("核心模块结构", s_h2))
    story.append(_mktable([
        [P("<b>模块</b>",s_th),P("<b>目录</b>",s_th),P("<b>说明</b>",s_th),P("<b>核心类</b>",s_th)],
        [P("Agent",s_td),P("agents/",s_td),P("LLM 驱动的决策引擎，支持 8+ 种 Agent 类型",s_td),P("AgentExecutor, Agent, RunnableAgent",s_td)],
        [P("Chain",s_td),P("chains/",s_td),P("多组件组合的可复用调用序列",s_td),P("LLMChain, SequentialChain, RetrievalQA",s_td)],
        [P("Memory",s_td),P("memory/",s_td),P("维护对话状态和上下文",s_td),P("ConversationBufferMemory, EntityMemory",s_td)],
        [P("Retriever",s_td),P("retrievers/",s_td),P("根据查询返回相关文档",s_td),P("MultiQueryRetriever, SelfQueryRetriever",s_td)],
        [P("OutputParser",s_td),P("output_parsers/",s_td),P("解析 LLM 输出为结构化数据",s_td),P("StructuredOutputParser, PydanticOutputParser",s_td)],
        [P("Callback",s_td),P("callbacks/",s_td),P("监听执行事件的观察者模式",s_td),P("BaseCallbackHandler, CallbackManager",s_td)],
        [P("Evaluation",s_td),P("evaluation/",s_td),P("对 LLM 输出进行评分评估",s_td),P("StringEvaluator, PairwiseStringEvaluator",s_td)],
    ],[65,58,W-280,137]))
    story.append(PB())

    # 第二章
    story.append(P("二、核心模块说明", s_h1))
    story.append(P("2.1 延迟加载与向后兼容机制", s_h2))
    story.append(P("langchain-classic 采用 <b>__getattr__ 延迟加载模式</b>。主入口 __init__.py 中通过 _api/module 模块的 create_importer() 函数，实现了带废弃警告的动态导入。这使得包的导入时间极短，同时保持了与旧版 API 的兼容性。所有导出的 44 个符号均带有废弃警告，推荐用户迁移到 langchain-core 或 langchain-community 中的对应实现。", s_b))
    story.append(P("2.2 Runnable 与 LCEL 表达式语言", s_h2))
    story.append(P("LangChain 表达式语言 (LCEL) 是基于 Runnable 协议的组合式编程模型。Chain 基类继承自 RunnableSerializable，使得所有 Chain 都可以通过管道操作符 | 进行组合。新版代码全面拥抱 LCEL，如 create_stuff_documents_chain() 直接返回 Runnable 管道：RunnablePassthrough.assign(context=format_docs) | prompt | llm | output_parser。", s_b))
    story.append(P("2.3 工厂方法模式", s_h2))
    story.append(P("几乎所有核心类都提供了 from_llm() 或 from_llm_and_tools() 类方法，封装了复杂的构造逻辑。例如 RetrievalQA.from_chain_type(llm, chain_type='stuff', retriever=...) 会自动创建 LLMChain + StuffDocumentsChain + RetrievalQA 的完整链路。", s_b))
    story.append(PB())

    # 第三章：流程图
    story.append(P("三、核心流程图", s_h1))
    story.append(P("3.1 Agent 执行主流程", s_h2))
    story.append(P('AgentExecutor 是 Agent 的核心执行引擎，它驱动一个"思考-行动-观察"的迭代循环，直到 Agent 返回 AgentFinish 或达到最大迭代次数/最大执行时间。每次迭代中，Agent 通过 plan() 方法调用 LLM 进行决策，然后 AgentExecutor 执行对应的 Tool 并将观察结果追加到 intermediate_steps 中。', s_b))
    story += [S(1,10), Diagram(W, 460, draw_agent_flow), PB()]

    story.append(P("3.2 Chain 执行流程 (模板方法模式)", s_h2))
    story.append(P("Chain 基类采用经典的<b>模板方法模式</b>。invoke() 方法定义了完整的执行骨架：准备输入 → 加载记忆 → 验证输入 → 执行核心逻辑 → 验证输出 → 保存记忆 → 触发回调。子类只需实现抽象方法 _call()。", s_b))
    story += [S(1,10), Diagram(W, 530, draw_chain_flow), PB()]

    story.append(P("3.3 RAG 检索增强生成流程", s_h2))
    story.append(P("RetrievalQA 实现了经典的 RAG 模式：先通过 Retriever 检索相关文档，再通过 CombineDocumentsChain 将文档与问题组合后交给 LLM 生成回答。支持三种文档合并策略：Stuff（直接拼接）、MapReduce（分治合并）、Refine（迭代精炼）。", s_b))
    story += [S(1,10), Diagram(W, 430, draw_rag_flow), PB()]

    story.append(P("3.4 Memory 记忆工作流程", s_h2))
    story.append(P("Memory 系统与 Chain 紧密协作：在 Chain 执行前通过 load_memory_variables() 加载历史上下文，在执行后通过 save_context() 保存新的对话内容。支持多种记忆策略，从简单的全量存储到基于 LLM 的智能摘要。", s_b))
    story += [S(1,10), Diagram(W, 360, draw_memory_flow), S(1,15)]

    story.append(P("3.5 Router Chain 路由流程", s_h2))
    story.append(P("MultiRouteChain 实现了动态路由分发机制。LLMRouterChain 使用 LLM 分析用户输入，输出目标链名和处理后的输入，MultiRouteChain 根据路由结果分发到对应的目标链执行。", s_b))
    story += [S(1,10), Diagram(W, 340, draw_router_flow), PB()]

    # 第四章：时序图
    story.append(P("四、核心时序图", s_h1))
    story.append(P("4.1 LLMChain 调用时序", s_h2))
    story.append(P("LLMChain 是最基础的链类型，实现了 Prompt → LLM → OutputParser 的三步管道。它被 Agent、StuffDocumentsChain、ConversationSummaryMemory 等大量组件依赖。新版推荐使用 LCEL 替代：prompt | llm | parser。", s_b))
    story += [S(1,10), Diagram(W, 380, draw_llmchain_seq), PB()]

    story.append(P("4.2 Agent 推理循环时序", s_h2))
    story.append(P("Agent 的推理循环涉及 6 个参与者：User、AgentExecutor、Agent、LLM、Tool 和 Callback。AgentExecutor 协调整个流程，Agent 负责决策使用哪个 Tool，Callback 负责监听和记录事件。循环直到返回 AgentFinish 或达到限制。", s_b))
    story += [S(1,10), Diagram(W, 490, draw_agent_seq), PB()]

    story.append(P("4.3 对话检索链时序", s_h2))
    story.append(P("ConversationalRetrievalChain 实现了带对话历史的 RAG 流程。它先用 QuestionGenerator 将当前问题和历史对话组合重写为独立问题，然后检索文档，最后通过 CombineDocumentsChain 生成回答。", s_b))
    story += [S(1,10), Diagram(W, 380, draw_conv_seq), PB()]

    # 第五章：核心类设计
    story.append(P("五、核心类设计说明", s_h1))

    story.append(P("5.1 Chain 基类体系", s_h2))
    story.append(P("Chain 是所有链的抽象基类，继承自 RunnableSerializable[dict, dict]。它实现了模板方法模式，定义了完整的执行骨架，子类只需实现 _call() 抽象方法。", s_b))
    story.append(_mktable([
        [P("<b>类名</b>",s_th),P("<b>继承</b>",s_th),P("<b>职责</b>",s_th),P("<b>核心方法</b>",s_th)],
        [P("Chain",s_td),P("RunnableSerializable",s_td),P("所有链的抽象基类，定义执行骨架",s_td),P("invoke(), _call(), prep_inputs(), prep_outputs()",s_td)],
        [P("LLMChain",s_td),P("Chain",s_td),P("Prompt+LLM+Parser 的基础管道",s_td),P("generate(), prep_prompts(), create_outputs()",s_td)],
        [P("SequentialChain",s_td),P("Chain",s_td),P("多个链的串联执行，前序输出作为后序输入",s_td),P("_call() 串联调用子链",s_td)],
        [P("RetrievalQA",s_td),P("BaseRetrievalQA",s_td),P("检索+文档合并+生成的RAG链",s_td),P("_get_docs(), from_chain_type()",s_td)],
        [P("StuffDocumentsChain",s_td),P("BaseCombineDocsChain",s_td),P("将所有文档拼接为一个Prompt",s_td),P("combine_docs(), _get_inputs()",s_td)],
        [P("MapReduceDocsChain",s_td),P("BaseCombineDocsChain",s_td),P("先Map各文档再Reduce合并",s_td),P("combine_docs(): Map→Reduce",s_td)],
        [P("RefineDocsChain",s_td),P("BaseCombineDocsChain",s_td),P("逐篇文档迭代精炼结果",s_td),P("combine_docs(): initial→refine×N",s_td)],
        [P("ConvRetrievalChain",s_td),P("Chain",s_td),P("带对话历史的检索问答链",s_td),P("question_generator + retriever + combine",s_td)],
        [P("MultiRouteChain",s_td),P("Chain",s_td),P("根据LLM路由结果分发到目标链",s_td),P("router_chain.route() → dest_chain",s_td)],
    ],[85,90,W-340,145]))
    story.append(S(1,10))

    story.append(P("5.2 Agent 智能体体系", s_h2))
    story.append(P("Agent 体系分为三层：Agent（决策层）、AgentExecutor（执行层）和 Tool（工具层）。Agent 负责调用 LLM 决定使用哪个 Tool，AgentExecutor 负责协调整个推理-行动-观察循环，Tool 封装了与外界交互的能力。", s_b))
    story.append(_mktable([
        [P("<b>类名</b>",s_th),P("<b>职责</b>",s_th),P("<b>设计模式</b>",s_th)],
        [P("BaseSingleActionAgent",s_td),P("单动作 Agent 抽象基类，定义 plan() 接口",s_td),P("策略模式",s_td)],
        [P("BaseMultiActionAgent",s_td),P("多动作 Agent 抽象基类，可同时返回多个 Action",s_td),P("策略模式",s_td)],
        [P("RunnableAgent",s_td),P("将 Runnable 包装为 Agent 接口的适配器",s_td),P("适配器模式",s_td)],
        [P("Agent (经典)",s_td),P("基于 LLMChain + agent_scratchpad 的经典 Agent",s_td),P("模板方法",s_td)],
        [P("AgentExecutor",s_td),P("核心执行引擎，驱动思考-行动-观察循环",s_td),P("策略+迭代器",s_td)],
        [P("AgentExecutorIterator",s_td),P("将 Agent 循环暴露为 Python 迭代器",s_td),P("迭代器模式",s_td)],
        [P("AgentOutputParser",s_td),P("解析 LLM 输出为 AgentAction/AgentFinish",s_td),P("解释器模式",s_td)],
    ],[100,W-260,140]))
    story.append(S(1,8))
    story.append(P("Agent 类型枚举支持 8 种 Agent：ZERO_SHOT_REACT、REACT_DOCSTORE、SELF_ASK_WITH_SEARCH、CONVERSATIONAL_REACT、CHAT_ZERO_SHOT_REACT、CHAT_CONVERSATIONAL_REACT、STRUCTURED_CHAT_ZERO_SHOT_REACT、OPENAI_FUNCTIONS。", s_b))
    story.append(PB())

    story.append(P("5.3 Memory 记忆体系", s_h2))
    story.append(P("Memory 体系负责维护 Chain 的状态。BaseMemory 定义了 load_memory_variables() 和 save_context() 两个核心接口。BaseChatMemory 扩展了聊天消息存储能力。各种具体实现提供了不同的记忆策略。", s_b))
    story.append(_mktable([
        [P("<b>类名</b>",s_th),P("<b>策略</b>",s_th),P("<b>特点</b>",s_th)],
        [P("ConversationBufferMemory",s_td),P("全量存储",s_td),P("存储所有对话消息，简单但可能超出 token 限制",s_td)],
        [P("ConversationBufferWindowMemory",s_td),P("滑动窗口",s_td),P("只保留最近 K 轮对话",s_td)],
        [P("ConversationSummaryMemory",s_td),P("LLM 摘要",s_td),P("每次对话后用 LLM 增量更新摘要，节省 token",s_td)],
        [P("ConversationSummaryBufferMemory",s_td),P("摘要+缓冲",s_td),P("最近消息保留原文，超出部分自动摘要",s_td)],
        [P("ConversationEntityMemory",s_td),P("实体提取",s_td),P("用 LLM 提取实体并维护实体摘要（支持多种存储后端）",s_td)],
        [P("CombinedMemory",s_td),P("组合",s_td),P("将多个 Memory 的变量合并为统一视图（组合模式）",s_td)],
    ],[120,70,W-210]))
    story.append(S(1,10))

    story.append(P("5.4 Retriever 检索器体系", s_h2))
    story.append(P("Retriever 负责根据查询返回相关文档。BaseRetriever 定义了 _get_relevant_documents() 接口。langchain-classic 提供了多种增强型检索器：", s_b))
    story.append(_mktable([
        [P("<b>类名</b>",s_th),P("<b>策略</b>",s_th),P("<b>设计模式</b>",s_th)],
        [P("ContextualCompressionRetriever",s_td),P("先检索再压缩：base_retriever → base_compressor",s_td),P("装饰器模式",s_td)],
        [P("MultiQueryRetriever",s_td),P("LLM 生成多个查询变体 → 并行检索 → 去重合并",s_td),P("查询扩展模式",s_td)],
        [P("SelfQueryRetriever",s_td),P("LLM 生成结构化查询 → Visitor 翻译 → VectorStore 搜索",s_td),P("访问者模式",s_td)],
        [P("MultiVectorRetriever",s_td),P("为文档存储多种嵌入表示",s_td),P("策略模式",s_td)],
        [P("ParentDocumentRetriever",s_td),P("检索子文档，返回父文档",s_td),P("组合模式",s_td)],
        [P("EnsembleRetriever",s_td),P("多个检索器结果的加权融合",s_td),P("集成模式",s_td)],
    ],[115,W-275,140]))
    story.append(S(1,10))

    story.append(P("5.5 OutputParser 输出解析器", s_h2))
    story.append(P("OutputParser 负责将 LLM 的文本输出解析为结构化数据。核心接口是 parse(text) → T。", s_b))
    story.append(_mktable([
        [P("<b>解析器</b>",s_th),P("<b>输出类型</b>",s_th),P("<b>说明</b>",s_th)],
        [P("StructuredOutputParser",s_td),P("dict[str, Any]",s_td),P("基于 ResponseSchema 定义的 JSON 结构解析",s_td)],
        [P("PydanticOutputParser",s_td),P("Pydantic Model",s_td),P("自动生成格式指令，解析为 Pydantic 模型",s_td)],
        [P("OutputFixingParser",s_td),P("T",s_td),P("解析失败时用 LLM 修复输出",s_td)],
        [P("RetryOutputParser",s_td),P("T",s_td),P("解析失败时重试 LLM 调用",s_td)],
        [P("AgentOutputParser",s_td),P("AgentAction|AgentFinish",s_td),P("将 LLM 输出解析为 Agent 的行动或结束指令",s_td)],
    ],[100,90,W-210]))
    story.append(S(1,10))

    story.append(P("5.6 Callback 回调体系", s_h2))
    story.append(P("Callback 体系基于观察者模式，贯穿 LangChain 所有组件的执行过程。BaseCallbackHandler 通过多个 Mixin 组合了所有事件钩子。CallbackManager 负责管理和分发事件通知。", s_b))
    story.append(P("核心事件链：on_chain_start → on_llm_start → on_llm_new_token → on_llm_end → on_agent_action → on_tool_start → on_tool_end → on_agent_finish → on_chain_end。每个组件在执行时都会通过 RunManager 触发对应的回调事件。", s_b))
    story.append(PB())

    # 第六章：设计模式总结
    story.append(P("六、设计模式总结", s_h1))
    story.append(P("langchain-classic 在架构设计中大量运用了经典设计模式，以下是核心模式的总结：", s_b))
    story.append(_mktable([
        [P("<b>设计模式</b>",s_th),P("<b>应用位置</b>",s_th),P("<b>说明</b>",s_th)],
        [P("模板方法",s_td),P("Chain._call(), BaseCombineDocumentsChain.combine_docs()",s_td),P("基类定义执行骨架，子类实现核心逻辑",s_td)],
        [P("策略模式",s_td),P("Stuff/Refine/MapReduce; 各 OutputParser; 各 EntityStore",s_td),P("可替换的算法和存储实现",s_td)],
        [P("观察者模式",s_td),P("Callback 体系 (BaseCallbackHandler → CallbackManager)",s_td),P("事件通知机制贯穿所有组件的执行",s_td)],
        [P("迭代器模式",s_td),P("AgentExecutorIterator.__iter__/__aiter__",s_td),P("将 Agent 推理循环暴露为 Python 迭代器",s_td)],
        [P("组合模式",s_td),P("CombinedMemory, SequentialChain, MultiRouteChain",s_td),P("多个同类型组件组合为一个",s_td)],
        [P("工厂方法",s_td),P("from_llm() 类方法 (RetrievalQA, SelfQueryRetriever 等)",s_td),P("封装复杂的对象构建逻辑",s_td)],
        [P("建造者模式",s_td),P("VectorstoreIndexCreator",s_td),P("分步构建向量索引",s_td)],
        [P("访问者模式",s_td),P("SelfQueryRetriever 的 StructuredQueryTranslator",s_td),P("将统一查询翻译为各向量库方言",s_td)],
        [P("装饰器模式",s_td),P("ContextualCompressionRetriever",s_td),P("包装基础检索器，叠加压缩处理",s_td)],
        [P("适配器模式",s_td),P("RunnableAgent, format_scratchpad 函数族",s_td),P("将 Runnable/内部数据适配为目标接口",s_td)],
        [P("门面模式",s_td),P("VectorStoreIndexWrapper",s_td),P("隐藏链式构建的复杂性",s_td)],
    ],[70,W-325,235]))
    story.append(S(1,15))

    story.append(P("总结", s_h2))
    story.append(P("langchain-classic 作为 LangChain 生态的核心编排层，通过精心设计的抽象体系和丰富的设计模式，实现了高度的可扩展性和可组合性。其核心架构可以概括为：", s_b))
    story.append(P("• <b>Chain 是骨架</b>：模板方法模式确保了统一的执行流程（输入准备 → 记忆加载 → 核心逻辑 → 记忆保存 → 回调通知）", s_b))
    story.append(P("• <b>Agent 是大脑</b>：策略+迭代器模式驱动了「思考-行动-观察」的智能循环", s_b))
    story.append(P("• <b>Memory 是记忆</b>：多种策略模式支持从简单缓冲到 LLM 智能摘要的记忆管理", s_b))
    story.append(P("• <b>Retriever 是感知</b>：装饰器+访问者模式实现了灵活的文档检索增强", s_b))
    story.append(P("• <b>Callback 是神经</b>：观察者模式贯穿所有组件，提供完整的执行监控能力", s_b))
    story.append(P("• <b>LCEL 是未来</b>：基于 Runnable 协议的组合式编程正在逐步替代经典的 Chain 类", s_b))

    doc.build(story)
    print(f"PDF 已生成: {out}")

if __name__ == "__main__":
    build_pdf("/Users/chenmeiyang/Documents/code/javaworkspace/github.com/meiyang1990/langchain/langchain-classic-architecture.pdf")
