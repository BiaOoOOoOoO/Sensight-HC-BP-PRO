import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from google.api_core import exceptions
import time
import io
from docx import Document
from pptx import Presentation
from tenacity import retry, stop_after_attempt, wait_exponential

# ==========================================
# 0. 核心配置：锁定最强稳定版模型
# ==========================================
# 我们不使用实验版(Exp)，改用目前商业化最强逻辑模型 Gemini 1.5 Pro
# 这能最大程度避免 404 错误和莫名其妙的降智
STABLE_MODEL_ID = "gemini-1.5-pro"

st.set_page_config(
    page_title="BioVenture BP Pro",
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
    
    /* 侧边栏 */
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }

    /* 按钮样式 */
    div.stButton > button {
        background-color: #FFD700; color: #000000; border: none;
        width: 100%; padding: 12px; font-weight: bold; border-radius: 6px;
        font-size: 16px;
    }
    div.stButton > button:hover { background-color: #E5C100; }

    /* 报告结果框 */
    .report-box {
        background: white; padding: 30px; 
        border: 1px solid #ddd; border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        color: #333; line-height: 1.6;
    }
    
    /* 状态提示 */
    .status-tag {
        padding: 8px 12px; border-radius: 4px; font-size: 0.9em; margin-bottom: 10px;
        border-left: 4px solid #FFD700; background-color: #FFFDE7; color: #555;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 功能函数
# ==========================================

def search_market_data(query):
    """联网验证数据"""
    context = ""
    try:
        # 提取前50个字作为核心搜索词
        keyword = query[:50].replace("\n", " ")
        with DDGS() as ddgs:
            # 搜索两次以获取更多信息
            results = ddgs.text(f"{keyword} clinical trial data market size 2025", max_results=2)
            if results:
                for r in results:
                    context += f"- {r['body']}\n"
    except Exception:
        context = "Search unavailable (Network limit). Using internal knowledge base."
    return context

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_report(api_key, user_input, search_data):
    """
    核心生成逻辑。
    使用 Tenacity 进行自动重试，防止网络波动。
    """
    genai.configure(api_key=api_key)
    
    # 放宽安全限制，防止医疗术语（如cancer, kill, drug）被误拦截
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    model = genai.GenerativeModel(
        STABLE_MODEL_ID, 
        safety_settings=safety_settings,
        generation_config={"temperature": 0.2} # 低温度保证专业性
    )
    
    prompt = f"""
    You are a Bio-Pharmaceutical Investment Banking Analyst Tool.
    
    [TASK]
    Review the Input BP Text, cross-check with the Search Data, and output a rigorous Modification Report.
    
    [STRICT RULES]
    1. NO Roleplay. Do not say "As an AI" or "As an investor".
    2. Tone: Objective, Dry, Professional, High-Signal.
    3. Output Language: Professional Chinese.
    
    [INPUT TEXT]
    {user_input}
    
    [SEARCH DATA (CONTEXT)]
    {search_data}
    
    [OUTPUT SECTIONS]
    
    ## 1. 核心数据核查 (Data Audit)
    - Verify Market Size, CAGR, and Clinical Data in the input.
    - If user data is wrong based on Search Data, state: "原数据 -> 修正数据 (来源)"
    - If user data is correct, state "Data Verified".
    
    ## 2. 竞品深度对标 (Competitor Matrix)
    Markdown Table comparing User's Project vs 3 Global Competitors.
    Columns: [Competitor], [Modality], [Stage], [Key Strength], [Critical Weakness].
    
    ## 3. 专业化改写 (Professional Rewrite)
    Rewrite the input text to Investment Banking standards. 
    Replace colloquialisms with technical terms (e.g., "works fast" -> "rapid onset").
    
    ## 4. PPT 摘要 (Slide Bullets)
    5 concise bullet points for a slide deck.
    """
    
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 3. 文件导出逻辑
# ==========================================
def create_word(text):
    doc = Document()
    doc.add_heading('BP Modification Report', 0)
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
    # 简单截断处理
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
    # 这里输入你的 AIzaSy... Key
    api_key = st.text_input("Gemini API Key", type="password", placeholder="粘贴您的 API Key")
    
    st.info(f"✅ 已锁定引擎: **{STABLE_MODEL_ID}**")
    st.caption("目前 Google API 最稳定、逻辑最强的版本。")

st.title("🧬 Sensight Healthcare BP PRO")
st.markdown("请输入 BP 核心段落。系统将进行**实时数据验证**并生成**专业修改稿**。")

user_input = st.text_area("输入 BP 内容...", height=300, placeholder="例如：我们的口服小分子 GLP-1 正在进行二期临床，相比 Pfizer 的 Danuglipron 我们没有肝毒性...")

if st.button("开始专业分析"):
    if not api_key:
        st.error("请先在左侧输入 API Key")
    elif not user_input:
        st.warning("请输入 BP 内容")
    else:
        status = st.status("正在运行分析...", expanded=True)
        
        try:
            # 1. 搜索
            status.write("🔍 正在联网验证市场数据...")
            search_res = search_market_data(user_input)
            
            # 2. 生成
            status.write(f"⚡ 正在调用 {STABLE_MODEL_ID} 进行深度推理...")
            final_report = generate_report(api_key, user_input, search_res)
            
            status.update(label="分析完成", state="complete", expanded=False)
            
            # 3. 展示
            st.markdown(f'<div class="report-box">{final_report}</div>', unsafe_allow_html=True)
            
            # 4. 下载
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📄 下载 Word 报告", create_word(final_report), "BP_Report.docx")
            with c2:
                st.download_button("📊 下载 PPT 演示文稿", create_ppt(final_report), "BP_Slides.pptx")
                
        except Exception as e:
            status.update(label="发生错误", state="error")
            st.error(f"运行失败: {e}")
            
            # 针对性错误提示
            if "429" in str(e):
                st.warning("⚠️ 提示：触发了 API 调用频率限制。请稍等几秒钟再试，或者检查您的 Google Cloud 账户是否已关联结算账号（Pay-as-you-go）。")
            elif "404" in str(e):
                st.warning("⚠️ 提示：模型未找到。可能是您的 Key 所在区域不支持该模型，请尝试使用 VPN 切换至美国节点。")
