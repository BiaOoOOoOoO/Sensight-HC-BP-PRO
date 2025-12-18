import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from google.api_core import exceptions
import time
import io
from docx import Document
from pptx import Presentation
from pptx.util import Pt
from tenacity import retry, stop_after_attempt, wait_exponential

# ==========================================
# 0. 模型配置 (基于您的付费权限)
# ==========================================
# 映射您提到的最新商业化模型名称
AVAILABLE_MODELS = {
    "Gemini 3.0 Pro (最强逻辑/旗舰)": "gemini-3.0-pro",
    "Gemini 3.0 Flash (极速/低延迟)": "gemini-3.0-flash",
    "Gemini 2.5 Flash-Lite (轻量级)": "gemini-2.5-flash-lite"
}

st.set_page_config(
    page_title="BioVenture Analyst (Gemini 3.0)",
    page_icon="🧬",
    layout="wide"
)

# ==========================================
# 1. UI 样式：黑黄配色 (专业版)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #1A1A1A !important; font-weight: 700; }
    
    /* 侧边栏优化 */
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }

    /* 按钮样式 */
    div.stButton > button {
        background-color: #FFD700; color: #000000; border: none;
        border-radius: 6px; padding: 10px 24px; font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    div.stButton > button:hover { background-color: #E5C100; transform: translateY(-1px); }

    /* 报告容器 */
    .report-container {
        background-color: white; padding: 30px; 
        border: 1px solid #E0E0E0; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px; color: #333; line-height: 1.6;
    }
    
    /* 状态条 */
    .status-box {
        padding: 10px; border-radius: 5px; margin-bottom: 10px;
        font-family: monospace; font-size: 0.9em;
    }
    .status-search { background-color: #E3F2FD; color: #0D47A1; border-left: 4px solid #2196F3; }
    .status-gen { background-color: #FFF3E0; color: #E65100; border-left: 4px solid #FF9800; }
    .status-success { background-color: #E8F5E9; color: #1B5E20; border-left: 4px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心功能：搜索与生成
# ==========================================

def search_market_data(query_text):
    """联网检索最新临床/市场数据 (用于事实核查)"""
    search_context = ""
    try:
        # 提取关键词
        seed = query_text[:100].replace("\n", " ")
        queries = [
            f"{seed} clinical trial phase 3 results competitors",
            f"{seed} market size 2025 forecast CAGR",
            f"{seed} disadvantages safety warning"
        ]
        
        with DDGS() as ddgs:
            for q in queries:
                time.sleep(0.3) # 微小延迟
                results = ddgs.text(q, max_results=2)
                if results:
                    for r in results:
                        search_context += f"- [Source: {r['title']}]: {r['body']}\n"
    except Exception:
        search_context = "Search Unavailable. Analysis relying on internal model knowledge."
    return search_context

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_report(prompt, api_key, model_id):
    """
    调用 Gemini 3.0/2.5 模型。
    包含自动重试机制 (Tenacity)，应对短暂的网络波动。
    """
    genai.configure(api_key=api_key)
    
    # 针对付费版的安全设置：放开限制，允许处理医疗专业术语
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    generation_config = {
        "temperature": 0.1, # 保持输出稳定性
        "max_output_tokens": 8192, # 3.0 Pro 支持更长输出
    }
    
    model = genai.GenerativeModel(model_id, safety_settings=safety_settings, generation_config=generation_config)
    
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 3. Prompt 构建 (专业/非角色扮演)
# ==========================================
def build_prompt(user_input, search_data):
    return f"""
    [OBJECTIVE]
    You are a professional Bio-Pharma Analyst Tool.
    Your task is to review the user's Business Plan (BP) input, cross-reference it with market data, and provide a rigorous modification report.
    
    [STRICT RULES]
    1. NO Roleplay (Do not say "As an investor...").
    2. Tone: Objective, Clinical, Data-Driven.
    3. Language: Professional Chinese (Mainland Standard).
    
    [INPUT TEXT]
    {user_input}
    
    [MARKET INTELLIGENCE (SEARCH DATA)]
    {search_data}
    
    [OUTPUT SECTIONS]
    
    ## 1. 数据核查与纠偏 (Data Audit)
    - Validate specific numbers (Market Size, CAGR, Efficacy Rates) in the Input.
    - If input is vague, provide specific data from the Search Data.
    - Format: "原表述 -> 修正建议 (来源)"
    
    ## 2. 竞品深度对标 (Competitor Matrix)
    Markdown Table comparing User's Project vs 3 Global Competitors.
    Cols: [Competitor], [Mechanism], [Stage], [Pros], [Cons/Safety Risks].
    
    ## 3. 专业化改写 (Professional Refinement)
    Rewrite the input paragraph using Investment Banking standard terminology.
    - Eliminate colloquialisms.
    - Focus on "Clinical Value Proposition" and "Commercialization Potential".
    
    ## 4. PPT 摘要 (Slide Deck Bullets)
    5 high-impact bullet points for a slide deck.
    """

# ==========================================
# 4. 文件导出引擎
# ==========================================
def create_word_doc(content):
    doc = Document()
    doc.add_heading('BP Modification Report (Gemini 3.0 Analysis)', 0)
    
    # 清洗 Markdown 标记并排版
    for line in content.split('\n'):
        clean_line = line.strip()
        if clean_line.startswith('## '):
            doc.add_heading(clean_line.replace('## ', ''), level=2)
        elif clean_line.startswith('|'):
            # 表格行简单转为列表，防止乱码 (复杂表格需更重型的解析)
            doc.add_paragraph(clean_line, style='List Bullet')
        else:
            p = doc.add_paragraph(clean_line)
            p.paragraph_format.space_after = Pt(6)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_ppt_slides(content):
    prs = Presentation()
    # Title Slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "BP Optimization Analysis"
    slide.placeholders[1].text = "Powered by Google Gemini 3.0"
    
    # Content Slides
    sections = content.split('## ')
    for section in sections:
        if not section.strip(): continue
        lines = section.split('\n')
        title = lines[0].strip()
        body = "\n".join(lines[1:])[:900]
        
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = title
        slide.placeholders[1].text = body
        
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 5. 主界面逻辑
# ==========================================
with st.sidebar:
    st.image("https://placehold.co/200x60/1A1A1A/FFD700?text=BIO+ANALYST", caption="Gemini Paid Edition")
    st.markdown("---")
    
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.subheader("🤖 模型选择 (Model Selection)")
    # 这里让您自己选，不再帮您做决定
    selected_model_label = st.selectbox(
        "选择您的付费模型:", 
        list(AVAILABLE_MODELS.keys()),
        index=0 # 默认选 3.0 Pro
    )
    model_id = AVAILABLE_MODELS[selected_model_label]
