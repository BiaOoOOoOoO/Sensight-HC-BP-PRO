import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from duckduckgo_search import DDGS
import time
import io
import re
from docx import Document
from pptx import Presentation
from pptx.util import Pt

# ==========================================
# 0. 系统配置：智能模型路由队列
# ==========================================
SYSTEM_VERSION = "Sensight BP PRO v3.5 (Auto-Fallback)"

# 优先尝试的模型列表。代码会按顺序尝试，直到成功。
# 1. gemini-2.5-flash: 您要求的最新版
# 2. gemini-2.0-flash: 备选新版
# 3. gemini-1.5-flash: 救命稻草 (免费层级额度最高，最不容易报错)
MODEL_PRIORITY_QUEUE = [
    "gemini-2.5-flash",
    "gemini-2.0-flash", 
    "gemini-1.5-flash"
]

st.set_page_config(
    page_title="Sensight Healthcare BP PRO",
    page_icon="🏥",
    layout="wide"
)

# ==========================================
# 1. UI 样式 (保持专业去 AI 化)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; font-family: 'Helvetica Neue', sans-serif; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 700; }
    [data-testid="stSidebar"] { background-color: #F1F5F9; border-right: 1px solid #E2E8F0; }
    div.stButton > button {
        background-color: #2563EB; color: white; border: none;
        width: 100%; padding: 12px; font-weight: 600; border-radius: 6px;
        transition: all 0.3s;
    }
    div.stButton > button:hover { background-color: #1d4ed8; }
    .report-box {
        background: white; padding: 40px; 
        border: 1px solid #E2E8F0; border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #334155; line-height: 1.8; font-size: 15px;
        min-height: 200px;
    }
    .status-box {
        padding: 10px 15px; border-radius: 6px; margin-bottom: 15px;
        background-color: #EFF6FF; border-left: 4px solid #2563EB;
        color: #1E40AF; font-size: 0.95em;
    }
    .status-warning {
        background-color: #FFF7ED; border-left: 4px solid #F97316; color: #9A3412;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心逻辑：带降级保护的生成器
# ==========================================

def search_market_data(query):
    """检索市场数据，含兜底逻辑"""
    context = ""
    try:
        clean_query = query[:60].replace("\n", " ")
        strategies = [
            f"{clean_query} market size clinical trial 2025",
            f"{clean_query} competitors mechanism of action"
        ]
        with DDGS() as ddgs:
            for q in strategies:
                time.sleep(0.5)
                # DuckDuckGo 可能会返回空，做个简单的异常捕获
                try:
                    results = list(ddgs.text(q, max_results=2))
                    if results:
                        for r in results:
                            context += f"- [Source: {r['title']}]: {r['body']}\n"
                except:
                    continue
    except Exception:
        pass

    if not context:
        context = "External live data unavailable. Analysis based on internal clinical protocols."
    return context

def stream_report_with_fallback(api_key, user_input, search_data, output_container, status_container):
    """
    智能流式生成：遇到 429 限流自动切换模型
    """
    client = genai.Client(api_key=api_key)
    
    system_instruction = """
    You are a Senior Healthcare Investment Consultant at Sensight.
    STRICT GUIDELINES:
    1. NEVER mention AI, Gemini, or fallback models.
    2. Tone: Professional, Objective.
    3. Language: Professional Chinese.
    """
    
    full_prompt = f"""
    [PROJECT INPUT]
    {user_input}
    
    [MARKET CONTEXT]
    {search_data}
    
    [TASK]
    Provide a Due Diligence Report.
    
    [SECTIONS]
    ## 1. 关键数据核查 (Data Verification)
    ## 2. 竞品格局 (Competitive Landscape) (Table)
    ## 3. 专业术语升级 (Terminology)
    ## 4. BP 幻灯片大纲 (Slides)
    """
    
    # === 核心逻辑：遍历模型列表 ===
    for model_id in MODEL_PRIORITY_QUEUE:
        try:
            # 尝试调用当前模型
            # 注意：这里使用新版 SDK 的 generate_content_stream
            response_stream = client.models.generate_content_stream(
                model=model_id,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )
            
            # 如果能走到这一步，说明没有报错，开始流式输出
            full_text = ""
            for chunk in response_stream:
                if chunk.text:
                    full_text += chunk.text
                    output_container.markdown(f'<div class="report-box">{full_text}</div>', unsafe_allow_html=True)
            
            # 成功后，记录日志并退出循环
            print(f"Success with {model_id}")
            return full_text, model_id

        except ClientError as e:
            # 捕获 Google API 错误 (如 429 Resource Exhausted)
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                status_container.markdown(f'<div class="status-box status-warning">⚠️ 引擎 {model_id} 繁忙 (限流)，正在自动切换至备用引擎...</div>', unsafe_allow_html=True)
                time.sleep(1) # 稍作停顿
                continue # 尝试下一个模型
            elif "404" in error_msg or "Not Found" in error_msg:
                # 如果模型不存在（比如 2.5 在某些区域未上线）
                continue
            else:
                # 其他严重错误直接抛出
                raise e
        except Exception as e:
            raise e

    # 如果所有模型都试完了还在报错
    raise Exception("所有可用引擎均因网络限流 (429) 无法响应。请稍后重试。")

# ==========================================
# 3. 文件生成 (Word & PPT)
# ==========================================
def create_word(text):
    doc = Document()
    doc.add_heading('Sensight Analysis Report', 0)
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('## '):
            doc.add_heading(line.replace('## ', ''), level=2)
        elif line:
            doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_ppt(text):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Project Optimization Report"
    slide.placeholders[1].text = "Generated by Sensight Solutions"
    
    sections = re.split(r'^##\s+', text, flags=re.MULTILINE)
    for section in sections:
        if not section.strip(): continue
        lines = section.strip().split('\n')
        header = lines[0].strip()
        bullets = [l.strip().lstrip('-*•') for l in lines[1:] if l.strip()]
        
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = header
        tf = slide.placeholders[1].text_frame
        tf.clear()
        for point in bullets[:6]:
            p = tf.add_paragraph()
            p.text = point
            p.font.size = Pt(18)
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 4. 主程序
# ==========================================
with st.sidebar:
    st.image("https://placehold.co/200x60/2563EB/FFFFFF?text=SENSIGHT", caption="Healthcare Solutions")
    st.markdown("---")
    api_key = st.text_input("系统授权密钥 (License Key)", type="password") 
    st.caption(f"系统版本: {SYSTEM_VERSION}")

st.title("Sensight 医疗项目 BP 优化系统")
st.markdown("请输入项目核心段落。系统将实时连接全球数据库进行分析。")

user_input = st.text_area("项目数据输入", height=300)

if st.button("生成专业分析报告"):
    if not api_key:
        st.error("请输入系统密钥")
    elif not user_input:
        st.warning("请输入内容")
    else:
        status = st.empty()
        report_container = st.empty()
        
        try:
            # 1. 搜索
            status.markdown('<div class="status-box">正在检索全球临床数据...</div>', unsafe_allow_html=True)
            search_res = search_market_data(user_input)
            
            # 2. 生成 (带自动降级)
            status.markdown('<div class="status-box">Sensight 引擎正在生成分析...</div>', unsafe_allow_html=True)
            final_report, used_model = stream_report_with_fallback(api_key, user_input, search_res, report_container, status)
            
            status.empty()
            st.success(f"分析完成") # 不向客户展示具体用了哪个模型，保持专业性
            
            # 3. 下载
            st.markdown("### 📥 导出文档")
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📄 导出 Word", create_word(final_report), "Report.docx")
            with c2:
                st.download_button("📊 导出 PPT", create_ppt(final_report), "Slides.pptx")
                
        except Exception as e:
            st.error(f"处理中断: {str(e)}")
            st.warning("提示：如果遇到 '429 Quota exceeded'，说明您的 API Key 免费额度已耗尽。请稍候再试。")
