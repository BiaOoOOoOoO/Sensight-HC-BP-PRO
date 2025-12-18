import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
from datetime import datetime
import io
from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt

# ==========================================
# 0. 全局配置
# ==========================================
MODEL_VERSION = 'gemini-2.0-flash-exp' # 建议使用最新实验版或 1.5-pro
FALLBACK_MODEL = 'gemini-1.5-flash'

st.set_page_config(
    page_title="BioVenture Analyst Pro",
    page_icon="🧬",
    layout="wide"
)

# ==========================================
# 1. UI 样式：黑黄配色 (专业工具风)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; font-family: 'Inter', sans-serif; }
    
    /* 标题与文字 */
    h1, h2, h3 { color: #1A1A1A !important; font-weight: 700; }
    
    /* 按钮：黑黄品牌色 */
    div.stButton > button {
        background-color: #FFD700; color: #000000; border: none;
        border-radius: 6px; padding: 10px 24px; font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover { background-color: #E5C100; color: #000000; }

    /* 分析报告卡片 */
    .report-container {
        background-color: white; padding: 30px; 
        border: 1px solid #E0E0E0; border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* 重点强调 */
    .highlight { background-color: #FFF9C4; padding: 2px 5px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心逻辑：搜索与分析
# ==========================================

def search_market_data(query_text):
    """联网获取扎实的竞品与临床数据"""
    search_context = ""
    try:
        # 提取前 80 字符作为搜索种子
        seed = query_text[:80].replace("\n", " ")
        # 针对性搜索词
        queries = [
            f"{seed} market size 2025 CAGR",
            f"{seed} clinical trial results phase 3 competitors",
            f"{seed} limitations and side effects"
        ]
        
        with DDGS() as ddgs:
            for q in queries:
                results = ddgs.text(q, max_results=2)
                for r in results:
                    search_context += f"- [Source: {r['title']}]: {r['body']}\n"
    except Exception:
        search_context = "Network search limit reached. Using internal knowledge base."
    return search_context

def generate_analysis(user_input, search_data, api_key):
    """
    生成核心分析报告。
    关键点：Temperature 设为 0.1 保证一致性；关闭安全过滤防止误杀医疗词汇。
    """
    genai.configure(api_key=api_key)
    
    # 宽松的安全设置（防止报错 invalid operation / finish_reason 1）
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # 极低温度保证一致性
    generation_config = {
        "temperature": 0.1,
        "max_output_tokens": 4000,
    }

    try:
        model = genai.GenerativeModel(MODEL_VERSION, 
                                      safety_settings=safety_settings,
                                      generation_config=generation_config)
    except:
        model = genai.GenerativeModel(FALLBACK_MODEL,
                                      safety_settings=safety_settings,
                                      generation_config=generation_config)

    prompt = f"""
    [System Role]
    You are an expert Bio-Pharmaceutical Data Analyst. 
    Your task is NOT to roleplay, but to provide a rigorous, objective, and data-driven "Modification Report" for a Business Plan (BP).
    
    [Input BP Text]
    {user_input}
    
    [Verified Market Data (Reference Only)]
    {search_data}
    
    [Output Requirements]
    1. **Language**: Professional Chinese (Mainland Medical/Investment Standard).
    2. **Tone**: Objective, Direct, High-Signal. No "I think" or "Investors might". Just facts.
    3. **Consistency**: Ensure clinical data and numbers are precise.
    4. **Structure**:
       - **Section 1: Critical Data Rectification**: Correct any market size, CAGR, or competitor status errors in the input based on search data.
       - **Section 2: Competitor Deep Dive**: A detailed Markdown Table comparing the user's project vs. Top 3 Competitors (Mechanism, Stage, Pros, Cons).
       - **Section 3: Professional Rewrite**: Rewrite the core paragraph of the BP. Replace colloquialisms with professional terminology (e.g., change "drugs that kill cancer" to "cytotoxic therapeutics").
       - **Section 4: PPT Outline**: Provide 4 key bullet points for a slide deck summary.

    Output the report directly.
    """
    
    # 使用非流式调用，以确保生成完整的对象供后续文件处理
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 3. 文件生成引擎 (Word & PPT)
# ==========================================

def create_word_doc(content):
    """生成 Word 文档"""
    doc = Document()
    doc.add_heading('BioVenture BP Modification Report', 0)
    
    # 简单处理：将 Markdown 文本按行写入
    for line in content.split('\n'):
        if line.startswith('##'):
            doc.add_heading(line.replace('#', '').strip(), level=2)
        elif line.startswith('###'):
            doc.add_heading(line.replace('#', '').strip(), level=3)
        else:
            doc.add_paragraph(line)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_ppt_slides(content):
    """生成 PPT 文档"""
    prs = Presentation()
    
    # 1. 标题页
    slide_layout = prs.slide_layouts[0] 
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "BP Optimization Report"
    subtitle.text = "Generated by BioVenture Analyst AI"
    
    # 2. 内容页 (简单解析文本，每 500 字符一页，避免溢出)
    # 在实际生产中，应该让 LLM 输出 JSON 格式来完美映射 PPT，这里做简化处理
    chunks = content.split('## ') # 按章节分割
    
    for chunk in chunks:
        if not chunk.strip(): continue
        
        lines = chunk.split('\n')
        header = lines[0].strip()
        body_text = "\n".join(lines[1:])[:800] # 截断防止溢出
        
        bullet_slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(bullet_slide_layout)
        
        shapes = slide.shapes
        title_shape = shapes.title
        body_shape = shapes.placeholders[1]
        
        title_shape.text = header
        body_shape.text = body_text

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 4. 主界面逻辑
# ==========================================

with st.sidebar:
    st.image("https://placehold.co/200x60/1A1A1A/FFD700?text=BIO+ANALYST", caption="Professional Tool")
    st.markdown("---")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    st.info("💡 **Mode:** Professional Analysis (Non-Roleplay)\n\n**Stability:** High (Temp=0.1)")

st.title("🧬 BP 修改建议与数据核查工具")
st.markdown("请输入 BP 核心段落。系统将进行**事实核查**、**数据修补**并生成**专业级修改建议**。")

user_input = st.text_area("Input Core Data / 输入 BP 文本", height=300, 
                          placeholder="粘贴您的摘要、竞品分析或临床数据描述...")

if st.button("开始专业分析 (Generate Report)", use_container_width=True):
    if not api_key:
        st.error("❌ 请输入 API Key")
    elif not user_input:
        st.warning("⚠️ 请输入文本内容")
    else:
        status_box = st.status("正在执行分析任务...", expanded=True)
        
        # 1. 搜索
        status_box.write("🔍 检索全球数据库 (Market/Clinical Data)...")
        search_data = search_market_data(user_input)
        
        # 2. 生成
        status_box.write("🧠 执行一致性分析 (Temperature=0.1)...")
        try:
            analysis_text = generate_analysis(user_input, search_data, api_key)
            
            status_box.update(label="分析完成", state="complete", expanded=False)
            
            # 3. 展示结果
            st.markdown(f"""
            <div class="report-container">
            {analysis_text}
            </div>
            """, unsafe_allow_html=True)
            
            # 4. 下载区域
            st.markdown("### 📥 导出报告")
            col1, col2 = st.columns(2)
            
            with col1:
                # 生成 Word
                word_file = create_word_doc(analysis_text)
                st.download_button(
                    label="📄 下载 Word 报告 (.docx)",
                    data=word_file,
                    file_name="BP_Analysis_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            
            with col2:
                # 生成 PPT
                ppt_file = create_ppt_slides(analysis_text)
                st.download_button(
                    label="📊 下载演示文稿 (.pptx)",
                    data=ppt_file,
                    file_name="BP_Summary_Slides.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
                
        except Exception as e:
            status_box.update(label="发生错误", state="error")
            st.error(f"Error Details: {str(e)}")
            st.warning("如果遇到 'finish_reason is 1'，通常是因为 Google 认为医疗内容敏感。代码中已尝试调低安全阈值。")

st.markdown("---")
st.caption("© 2025 BioVenture Analyst | Data provided by Real-time Search & Gemini 2.0")
