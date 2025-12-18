import streamlit as st
from google import genai
from google.genai import types
from duckduckgo_search import DDGS
import time
import io
from docx import Document
from pptx import Presentation
from tenacity import retry, stop_after_attempt, wait_exponential

# ==========================================
# 0. 配置：使用官方最新 SDK 和模型
# ==========================================
# 你指定的最新模型
MODEL_ID = "gemini-2.5-flash"

st.set_page_config(
    page_title="BioVenture BP Pro (Gemini 2.5)",
    page_icon="🧬",
    layout="wide"
)

# ==========================================
# 1. UI 样式
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #1A1A1A !important; font-weight: 700; }
    
    div.stButton > button {
        background-color: #FFD700; color: #000000; border: none;
        width: 100%; padding: 12px; font-weight: bold; border-radius: 6px;
    }
    div.stButton > button:hover { background-color: #E5C100; }

    .report-box {
        background: white; padding: 30px; 
        border: 1px solid #ddd; border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        color: #333; line-height: 1.6;
    }
    
    .status-ok { color: #2E7D32; background: #E8F5E9; padding: 4px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心逻辑 (适配 google-genai SDK)
# ==========================================

def search_market_data(query):
    """联网验证数据"""
    context = ""
    try:
        keyword = query[:50].replace("\n", " ")
        with DDGS() as ddgs:
            results = ddgs.text(f"{keyword} clinical trial market size 2025", max_results=2)
            if results:
                for r in results:
                    context += f"- {r['body']}\n"
    except Exception:
        context = "Search unavailable. Using internal knowledge."
    return context

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_report(api_key, user_input, search_data):
    """
    使用新版 SDK (google-genai) 调用 gemini-2.5-flash
    """
    # 1. 初始化 Client (新版写法)
    client = genai.Client(api_key=api_key)
    
    # 2. 构建 Prompt
    system_instruction = """
    You are a Bio-Pharmaceutical Investment Banking Analyst Tool.
    NO Roleplay. Tone: Objective, Dry, Professional.
    Output Language: Professional Chinese.
    """
    
    full_prompt = f"""
    [TASK]
    Review the Input BP Text, cross-check with Search Data, and output a rigorous Modification Report.
    
    [INPUT TEXT]
    {user_input}
    
    [SEARCH DATA]
    {search_data}
    
    [OUTPUT SECTIONS]
    ## 1. 核心数据核查 (Data Audit)
    - Verify Market Size, CAGR, and Clinical Data.
    - Format: "原数据 -> 修正数据 (来源)"
    
    ## 2. 竞品深度对标 (Competitor Matrix)
    Markdown Table: [Competitor], [Modality], [Stage], [Key Strength], [Critical Weakness].
    
    ## 3. 专业化改写 (Professional Rewrite)
    Rewrite input to Investment Banking standards.
    
    ## 4. PPT 摘要 (Slide Bullets)
    5 concise bullet points.
    """
    
    # 3. 调用 Generate Content (新版 Config 写法)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        )
    )
    
    return response.text

# ==========================================
# 3. 文件导出
# ==========================================
def create_word(text):
    doc = Document()
    doc.add_heading('BP Modification Report', 0)
    if text:
        for line in text.split('\n'):
            if line.startswith('## '):
                doc.add_heading(line.replace('## ', ''), level=2)
            else:
                doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_ppt(text):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "BP Analysis Summary"
    if text:
        slide.placeholders[1].text = text[:900]
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 4. 主程序界面
# ==========================================
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    st.info(f"🚀 **官方 SDK 模式**\n已启用 `google-genai` 库\n内核模型: `{MODEL_ID}`")

st.title("🧬 Sensight Healthcare BP PRO (Gemini 2.5)")
st.markdown(f"基于 Google 最新 **{MODEL_ID}** 模型构建的 BP 分析工具。")

user_input = st.text_area("输入 BP 内容...", height=300)

if st.button("开始专业分析"):
    if not api_key:
        st.error("请先在左侧输入 API Key")
    elif not user_input:
        st.warning("请输入 BP 内容")
    else:
        status = st.status("正在运行...", expanded=True)
        
        try:
            # 1. 搜索
            status.write("🔍 正在联网验证市场数据...")
            search_res = search_market_data(user_input)
            
            # 2. 生成 (调用新 SDK)
            status.write(f"⚡ 正在调用 {MODEL_ID} (Client v2)...")
            final_report = generate_report(api_key, user_input, search_res)
            
            status.update(label="分析完成", state="complete", expanded=False)
            
            # 展示
            st.markdown(f'<div class="report-box">{final_report}</div>', unsafe_allow_html=True)
            
            # 下载
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📄 下载 Word", create_word(final_report), "BP_Report.docx")
            with c2:
                st.download_button("📊 下载 PPT", create_ppt(final_report), "BP_Slides.pptx")
                
        except Exception as e:
            status.update(label="发生错误", state="error")
            st.error(f"调用失败: {e}")
            st.markdown("""
            **排查建议：**
            1. 确认 `requirements.txt` 中已包含 `google-genai`。
            2. 确认 API Key 有权限访问 `gemini-2.5-flash` (部分区域可能需申请)。
            """)
