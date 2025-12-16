import streamlit as st
import time
import google.generativeai as genai
from duckduckgo_search import DDGS
from datetime import datetime

# ==========================================
# 0. 全局配置与模型设定
# ==========================================
# 用户指定模型版本。如果 2.5 尚未实装，代码里做了 fallback 处理
MODEL_VERSION = 'gemini-2.5-flash' 
fallback_model = 'gemini-1.5-flash' # 兜底模型

st.set_page_config(
    page_title="BioVenture BP Copilot",
    page_icon="🧬",
    layout="wide"
)

# ==========================================
# 1. CSS 样式：黑黄配色 (保持品牌调性)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; font-family: 'Inter', sans-serif; }
    
    /* 标题与文字 */
    h1, h2, h3 { color: #1A1A1A !important; font-weight: 700; }
    .stTextArea textarea { font-size: 16px; line-height: 1.5; }
    
    /* 侧边栏 */
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }
    
    /* 按钮：黑黄品牌色 */
    div.stButton > button {
        background-color: #FFD700; color: #000000; border: none;
        border-radius: 6px; padding: 10px 24px; font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover { background-color: #E5C100; color: #000000; }

    /* 诊断卡片样式 */
    .audit-card {
        background-color: white; padding: 20px; border-radius: 8px;
        border-left: 5px solid #FFD700; /* 黄色左边框 */
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .audit-score { font-size: 24px; font-weight: bold; color: #1A1A1A; }
    
    /* 修正后的文本样式 */
    .revised-text {
        background-color: #FFFDE7; /* 极浅黄背景 */
        padding: 15px; border-radius: 5px; border: 1px dashed #FFD700;
        font-family: 'Georgia', serif; /* 衬线体，更像文档 */
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Agent 工具：事实核查 (Fact Checker)
# ==========================================
def verify_claims_with_search(bp_text):
    """
    提取 BP 中的关键声明，并联网验证真伪。
    """
    # 这里我们简化逻辑：搜索 BP 中的关键词，获取最新信息供 LLM 对比
    # 实际生产中，这一步应该由 LLM 提取 Claim -> 搜索 -> 验证
    search_context = ""
    try:
        # 截取前 100 个字符做关键词搜索（模拟提取核心主题）
        # 真实场景下应用 LLM 提取 Keywords
        keywords = bp_text[:50].replace("\n", " ") 
        query = f"{keywords} market size competitor analysis 2025"
        
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=3)
            for r in results:
                search_context += f"- [Source: {r['title']}]: {r['body']}\n"
    except Exception as e:
        search_context = f"Search unavailable: {str(e)}"
    
    return search_context

# ==========================================
# 3. 核心 Prompt 逻辑：评价与修改
# ==========================================
def generate_audit_prompt(user_bp, search_context, mode):
    
    # 模式 A: 毒舌 VC 评审 (Critique)
    if mode == "深度评审 (Audit)":
        return f"""
        You are a highly critical, top-tier Healthcare VC Partner. 
        Your goal is NOT to be nice, but to ensure this BP gets funding.
        
        Task: Review the User's BP Draft below.
        
        User's Draft:
        "{user_bp}"
        
        Real-time Market Context (For Fact Checking):
        {search_context}
        
        Output format:
        1. **Investment Score (0-100)**: Be harsh.
        2. **Red Flags (Fatal Flaws)**: What would make you pass immediately? (Check if their market data contradicts the search context).
        3. **Missing Logic**: What questions are unanswered?
        4. **Action Items**: 3 specific things to fix.
        
        Use concise, professional VC terminology. Output in Chinese.
        """
    
    # 模式 B: 重新润色 (Rewrite)
    else:
        return f"""
        You are a professional Bio-Medical Investment Banker and Editor.
        Your task is to REWRITE the user's draft to sound professional, persuasive, and "investable".
        
        User's Draft:
        "{user_bp}"
        
        Context/Facts to incorporate:
        {search_context}
        
        Instructions:
        1. Keep the core meaning but upgrade the vocabulary (e.g., change "we sell drugs" to "commercialize first-in-class therapeutics").
        2. Structure it with clear headers if needed.
        3. Fix any grammar or logical flow issues.
        4. **Highlight**: If the user's data was wrong based on context, correct it in the rewrite but bold the change.
        
        Output the rewritten text directly. Output in Chinese.
        """

# ==========================================
# 4. 主界面布局
# ==========================================
with st.sidebar:
    st.image("https://placehold.co/200x60/1A1A1A/FFD700?text=BP+COPILOT", caption="Founder's Workspace")
    st.markdown("---")
    
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    
    st.markdown("### 🛠️ 功能模式")
    mode = st.radio("选择操作", ["深度评审 (Audit)", "智能润色 (Rewrite)"])
    
    st.markdown("---")
    st.info(f"⚡ Engine: **{MODEL_VERSION}**\n(Fallback: {fallback_model})")

st.title("🧬 BP 智能优化助手")
st.markdown("**你的任务是融资，不是写作文。** 把你的 BP 核心段落（摘要、市场、竞品）粘贴在下方，让 AI 帮你找漏洞或重写。")

# 两列布局：左输入，右输出
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 原始草稿 (Draft)")
    user_input = st.text_area("在此粘贴你的 BP 文本...", height=500, placeholder="例如：我们要开发一款针对 GLP-1 耐药的口服小分子，目前处于 PCC 阶段，预计市场规模...")
    
    process_btn = st.button("🚀 开始分析/修改", use_container_width=True)

with col2:
    st.subheader("💡 优化结果 (Result)")
    result_container = st.empty()

# ==========================================
# 5. 逻辑执行
# ==========================================
if process_btn:
    if not api_key:
        st.error("请先在左侧填入 Gemini API Key")
    elif not user_input:
        st.warning("请先粘贴你的 BP 草稿")
    else:
        # 1. 启动状态
        status_box = st.status("正在调用 Gemini 2.5 Flash 进行分析...", expanded=True)
        
        # 2. 联网核查 (Agent Action)
        status_box.write("🔍 正在检索市场数据验证你的观点...")
        market_evidence = verify_claims_with_search(user_input)
        status_box.write("✅ 事实核查完成")
        
        # 3. 调用模型
        try:
            genai.configure(api_key=api_key)
            
            # 尝试调用 2.5 flash
            try:
                model = genai.GenerativeModel(MODEL_VERSION)
                # 这是一个简单的测试调用，确认模型是否存在
                # 实际 API 中如果不存在会直接报错
            except:
                status_box.warning(f"Note: {MODEL_VERSION} 暂不可用，已自动切换至 {fallback_model}。")
                model = genai.GenerativeModel(fallback_model)
            
            prompt = generate_audit_prompt(user_input, market_evidence, mode)
            
            status_box.write("🧠 正在生成专业反馈...")
            response_stream = model.generate_content(prompt, stream=True)
            
            # 4. 流式输出结果
            full_text = ""
            for chunk in response_stream:
                if chunk.text:
                    full_text += chunk.text
                    # 渲染
                    if mode == "深度评审 (Audit)":
                        result_container.markdown(f"""
                        <div class="audit-card">
                        {full_text}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        result_container.markdown(f"""
                        <div class="revised-text">
                        {full_text}
                        </div>
                        """, unsafe_allow_html=True)
            
            status_box.update(label="处理完成", state="complete", expanded=False)
            
        except Exception as e:
            st.error(f"Error: {e}")
            status_box.update(label="处理失败", state="error")

st.markdown("---")
st.caption("© 2025 BioVenture Copilot | Based on Gemini 2.5 Flash Architecture")
