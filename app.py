import streamlit as st
import time
import io

# ==========================================
# 1. 启动自检 (防止因缺库导致白屏)
# ==========================================
try:
    import google.generativeai as genai
    from duckduckgo_search import DDGS
    from docx import Document
    from pptx import Presentation
    from pptx.util import Pt
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError as e:
    st.error(f"⚠️ 启动失败：缺少必要库。请检查 requirements.txt 是否包含所有依赖。\n\n详细错误: {e}")
    st.stop()

# ==========================================
# 2. 页面配置
# ==========================================
st.set_page_config(
    page_title="BioVenture Analyst (Pro)",
    page_icon="🧬",
    layout="wide"
)

# ==========================================
# 3. CSS 样式 (修复可能的显示问题)
# ==========================================
st.markdown("""
<style>
    /* 强制全局背景色，防止暗黑模式冲突 */
    .stApp { background-color: #FAFAFA; color: #333333; }
    
    /* 标题颜色 */
    h1, h2, h3 { color: #1A1A1A !important; }
    
    /* 侧边栏背景 */
    [data-testid="stSidebar"] { background-color: #F0F2F6; }

    /* 按钮样式优化 */
    div.stButton > button {
        background-color: #FFD700; color: #000000; border: none;
        width: 100%; padding: 10px; font-weight: bold; border-radius: 5px;
    }
    div.stButton > button:hover { background-color: #E5C100; }

    /* 报告区域容器 */
    .report-box {
        background: white; padding: 25px; border-radius: 8px;
        border: 1px solid #ddd; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 核心功能逻辑
# ==========================================

# 预设模型列表 (根据 Google 最新 API 更新)
MODEL_OPTIONS = {
    "Gemini 2.0 Flash Exp (最新预览)": "gemini-2.0-flash-exp",
    "Gemini 1.5 Pro (最强逻辑)": "gemini-1.5-pro", 
    "Gemini 1.5 Flash (最快速度)": "gemini-1.5-flash",
    "自定义 (Custom)": "custom"
}

def search_market_data(query):
    """联网搜索"""
    context = ""
    try:
        with DDGS() as ddgs:
            results = ddgs.text(f"{query[:50]} clinical trial market data 2025", max_results=2)
            if results:
                for r in results:
                    context += f"- {r['body']}\n"
    except Exception:
        context = "Search unavailable."
    return context

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_content(model_id, api_key, prompt):
    """调用 API 生成"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 5. Word/PPT 导出工具
# ==========================================
def create_word(text):
    doc = Document()
    doc.add_heading('BP Modification Report', 0)
    doc.add_paragraph(text)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_ppt(text):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "BP Analysis Summary"
    slide.placeholders[1].text = text[:800] # 简单截断防止溢出
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 6. 主界面布局
# ==========================================
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("Gemini API Key", type="password")
    
    # 模型选择器
    model_choice = st.selectbox("选择模型引擎", list(MODEL_OPTIONS.keys()))
    
    # 如果选了自定义，或者用户是高级付费用户想用特定ID
    if model_choice == "自定义 (Custom)":
        final_model_id = st.text_input("输入模型 ID", value="gemini-1.5-pro-002")
    else:
        final_model_id = MODEL_OPTIONS[model_choice]
        
    st.info(f"当前调用 ID: `{final_model_id}`")

st.title("🧬 BioVenture BP Analyst")
st.markdown("专为付费版 Gemini 用户优化的 BP 深度修改工具。")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 输入 BP 核心段落")
    user_input = st.text_area("粘贴文本...", height=400, placeholder="例如：我们的口服 GLP-1 处于二期临床...")
    
    if st.button("开始分析与修改"):
        if not api_key:
            st.error("请先在左侧输入 API Key")
        elif not user_input:
            st.warning("请输入内容")
        else:
            with col2:
                status = st.status("正在分析中...", expanded=True)
                
                # 1. 搜索
                status.write("🔍 正在联网核实数据...")
                search_res = search_market_data(user_input)
                
                # 2. 生成
                status.write(f"⚡ 正在调用 {final_model_id}...")
                
                prompt = f"""
                You are a professional Bio-Pharma Analyst. 
                Task: Review the Input BP, Fact-check using Search Data, and Rewrite professionally.
                
                Input: {user_input}
                Search Data: {search_res}
                
                Output Sections:
                1. Data Audit (Correct specific numbers)
                2. Competitor Table (Markdown)
                3. Professional Rewrite (Investment Banking Style)
                4. PPT Bullets
                
                Output in Professional Chinese.
                """
                
                try:
                    res_text = generate_content(final_model_id, api_key, prompt)
                    status.update(label="分析完成", state="complete", expanded=False)
                    
                    # 渲染结果
                    st.subheader("2. 分析结果")
                    st.markdown(f'<div class="report-box">{res_text}</div>', unsafe_allow_html=True)
                    
                    # 下载按钮
                    st.download_button("📄 下载 Word", create_word(res_text), "report.docx")
                    st.download_button("📊 下载 PPT", create_ppt(res_text), "slides.pptx")
                    
                except Exception as e:
                    status.update(label="发生错误", state="error")
                    st.error(f"API 调用失败: {e}")
                    st.caption("提示：如果是 404 Not Found，说明该模型 ID 在您当前的 API 地区暂不可用，请尝试切换其他模型。")
