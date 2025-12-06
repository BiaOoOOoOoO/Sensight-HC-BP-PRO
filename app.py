import streamlit as st
import google.generativeai as genai

# ================= 配置区 =================
st.set_page_config(
    page_title="Sensight 晟策 | 智能投行合伙人",
    page_icon="🧬",
    layout="wide"
)

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/4a90e2/dna-helix.png", width=50)
    st.title("Sensight 晟策")
    st.markdown("---")
    
    # 获取 API Key
    api_key = st.text_input("请输入 Google API Key", type="password")
    
    st.markdown("### 关于我们")
    st.info("基于 10 年医疗 VC 经验构建的数字化大脑，为您提供 CFA 级商业叙事服务。")
    st.markdown("---")
    st.caption("Powered by Gemini 2.5 Pro")

# ================= 核心逻辑区 =================

st.title("🚀 Sensight 晟策 · 商业计划书智能生成")
st.markdown("### 让技术语言回归商业价值")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 项目输入")
    project_name = st.text_input("项目名称/代号", placeholder="例如：新型丝素蛋白人造血管")
    raw_text = st.text_area("2. 把您的技术背景、临床数据、团队优势丢在这里：", height=400, 
                            placeholder="我们做的是... 融资金额是... 核心数据是...")
    
    generate_btn = st.button("✨ 立即生成 Executive Summary", type="primary")

with col2:
    st.subheader("3. 交付结果")
    
    if generate_btn:
        if not api_key:
            st.error("请先在左侧侧边栏输入您的 API Key 才能启动大脑。")
        elif not raw_text:
            st.warning("巧妇难为无米之炊，请先输入项目信息。")
        else:
            try:
                # 配置 Gemini
                genai.configure(api_key=api_key)
                
                # 🌟 关键修改：使用了你清单里最强的稳定版模型
                model = genai.GenerativeModel('gemini-2.5-pro') 
                
                # 你的核心 Prompt
                system_prompt = """
                # Role
                你现在是 Sensight (晟策) 的首席医疗投资顾问。
                
                # Task
                接收用户的输入，直接将其重写为标准的 **Executive Summary (执行摘要)**。
                
                # CRITICAL RULES
                1. 禁止闲聊，直接输出 Markdown 内容。
                2. 如果用户遗漏细节，根据行业常识进行合理估算或占位。
                
                # Output Format
                请严格按照以下 Markdown 结构输出：
                ### [项目名称] - Executive Summary
                #### 🚀 投资亮点 (Investment Highlights)
                * **[核心技术]**: (提炼技术壁垒)
                * **[验证数据]**: (强调动物/临床数据)
                * **[商业壁垒]**: (强调专利/排他性)
                #### 🩺 未满足需求 (Unmet Needs)
                * (描述现有疗法痛点)
                #### 💡 解决方案 (Solution)
                * (描述产品优势)
                #### 📅 融资与规划 (Ask & Milestones)
                * (描述融资用途及预期节点)
                """
                
                user_prompt = f"项目名称：{project_name}\n项目原始信息：{raw_text}"
                
                with st.spinner("Sensight (Gemini 2.5) 正在拆解您的商业逻辑..."):
                    response = model.generate_content(system_prompt + "\n\n" + user_prompt)
                    st.markdown(response.text)
                    st.success("生成完成！您可以直接复制上方内容。")
                    
            except Exception as e:
                st.error(f"发生错误: {e}")
