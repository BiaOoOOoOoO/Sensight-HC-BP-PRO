import streamlit as st
import google.generativeai as genai
import pandas as pd
import time

# ================= 0. 页面配置 (更专业的设置) =================
st.set_page_config(
    page_title="Sensight 晟策 | 医疗创投智能系统",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS：隐藏 Streamlit 默认的汉堡菜单和脚标，让界面更干净
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stTextArea textarea {font-size: 14px;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ================= 1. 侧边栏：控制台 =================
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/4a90e2/dna-helix.png", width=60)
    st.title("Sensight Console")
    st.caption("医疗产业投融资决策系统 V2.0")
    
    st.markdown("---")
    
    # 功能导航
    task_mode = st.selectbox(
        "选择分析模块",
        ["执行摘要生成 (Executive Summary)", "市场空间测算 (Market Sizing)", "竞品格局分析 (Competitive Landscape)"]
    )
    
    st.markdown("---")
    api_key = st.text_input("系统授权码 (API Key)", type="password")
    
    st.markdown("### 💡 专业提示")
    if "Executive" in task_mode:
        st.info("执行摘要不仅是总结，更是钩子。本模块将基于 VC 逻辑重构您的叙事结构。")
    elif "Market" in task_mode:
        st.info("系统将基于流行病学数据进行 TAM/SAM/SOM 三级估算。")
    
    st.markdown("---")
    st.caption("© 2025 Sensight Capital. All Rights Reserved.")

# ================= 2. 主界面：结构化输入流 =================

st.title("🧬 Sensight 晟策 · 智能分析")

# 使用 Expander 把输入区折叠起来，显得更有条理
with st.expander("📝 项目基础信息录入 (点击展开/收起)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("项目名称", placeholder="例如：Molecule-X")
        indication = st.text_input("目标适应症", placeholder="例如：晚期非小细胞肺癌 (NSCLC)")
    with col2:
        stage = st.selectbox("当前临床阶段", ["临床前 (Pre-clinical)", "IND 申报阶段", "临床 I 期", "临床 II 期", "临床 III 期", "已上市"])
        modality = st.selectbox("技术模态", ["小分子化药", "单抗/双抗", "ADC", "细胞治疗 (CAR-T/NK)", "基因治疗", "医疗器械/耗材", "数字疗法"])

    # 核心差异化输入 (这是体现你专业度的地方，引导用户填什么)
    st.markdown("#### 核心要素解析")
    c1, c2 = st.columns(2)
    with c1:
        tech_highlight = st.text_area("核心技术/机制 (MoA)", height=100, placeholder="例如：采用全新的变构抑制机制，克服了现有的耐药突变...", help="请重点描述与竞品在机制上的不同之处")
    with c2:
        data_highlight = st.text_area("关键验证数据 (Data)", height=100, placeholder="例如：在头对头实验中，ORR 提升了 20%...", help="请提供动物实验或临床试验的核心数据")
    
    competitors = st.text_input("主要对标竞品 (可选)", placeholder="例如：奥希替尼 (AstraZeneca), 那个谁 (Competitor B)")

    start_btn = st.button("🚀 启动 Sensight 分析引擎", type="primary", use_container_width=True)

# ================= 3. 输出逻辑与结果展示 =================

if start_btn:
    if not api_key:
        st.error("❌ 未检测到授权码，请在左侧输入 API Key。")
    elif not project_name or not tech_highlight:
        st.warning("⚠️ 信息不完整：请至少填写【项目名称】和【核心技术】。")
    else:
        # === 模拟专业分析过程 (增加仪式感) ===
        status_box = st.status("🔍 Sensight 正在进行多维分析...", expanded=True)
        status_box.write("⚙️ 初始化 VC 评估模型...")
        time.sleep(1) # 假装思考，增加沉浸感
        status_box.write(f"🧬 识别技术模态: {modality} / 适应症: {indication}")
        status_box.write("📊 正在检索行业基准数据 (Benchmark)...")
        time.sleep(1)
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash''
            
            # 构建一个极其结构化的 Prompt
            user_input_structured = f"""
            项目名称: {project_name}
            适应症: {indication}
            阶段: {stage}
            模态: {modality}
            核心技术: {tech_highlight}
            关键数据: {data_highlight}
            竞品: {competitors}
            """
            
            if "Executive" in task_mode:
                system_prompt = """
                # Role
                你现在是 Sensight (晟策) 的首席医疗投资顾问。
                用户已经填写了结构化的尽职调查表单。请将这些碎片信息重构为一份逻辑严密的 Executive Summary。
                
                # Output Style
                不要输出 Markdown 标题，直接输出内容。
                使用专业、客观、极其精炼的投资银行行文风格。
                """
                prompt = system_prompt + "\n\n用户录入数据:\n" + user_input_structured
                
                status_box.write("✍️ 正在生成投资逻辑架构...")
                response = model.generate_content(prompt)
                status_box.update(label="✅ 分析完成", state="complete", expanded=False)
                
                # === 结果展示区 ===
                st.subheader("📄 投资摘要分析报告")
                st.markdown("---")
                st.markdown(response.text)
                
                # 增加下载按钮 (让它感觉像个文件)
                st.download_button(
                    label="📥 导出为报告 (TXT)",
                    data=response.text,
                    file_name=f"{project_name}_Executive_Summary.txt",
                    mime="text/plain"
                )

            elif "Market" in task_mode:
                # 针对市场分析的特殊处理
                system_prompt = """
                # Role
                你现在是 Sensight 的行业分析师。
                
                # Task
                根据用户的适应症和模态，估算 TAM/SAM/SOM。
                
                # Output Format
                请直接返回一个标准的 JSON 格式数据（不要包含 ```json 标记），方便我解析：
                {
                    "TAM_value": "数字+单位 (如 500亿 RMB)",
                    "TAM_desc": "简短的一句话逻辑",
                    "SAM_value": "数字+单位",
                    "SAM_desc": "简短的一句话逻辑",
                    "SOM_value": "数字+单位",
                    "SOM_desc": "简短的一句话逻辑",
                    "CAGR": "数字%",
                    "analysis": "一段详细的市场分析文字"
                }
                """
                prompt = system_prompt + "\n\n用户录入数据:\n" + user_input_structured
                
                status_box.write("🧮 正在构建费米估算模型...")
                response = model.generate_content(prompt)
                status_box.update(label="✅ 测算完成", state="complete", expanded=False)
                
                # 尝试解析 JSON (为了展示大数字卡片)
                try:
                    import json
                    # 清理一下可能存在的 markdown 标记
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_json)
                    
                    st.subheader("📈 市场空间测算 (Market Sizing)")
                    
                    # 炫酷的指标卡展示
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("TAM (潜在总市场)", data['TAM_value'], help=data['TAM_desc'])
                    c2.metric("SAM (可服务市场)", data['SAM_value'], help=data['SAM_desc'])
                    c3.metric("SOM (目标市场)", data['SOM_value'], help=data['SOM_desc'])
                    c4.metric("CAGR (年复合增长)", data['CAGR'])
                    
                    st.markdown("### 详细分析逻辑")
                    st.write(data['analysis'])
                    
                except:
                    # 如果 AI 没返回完美 JSON，兜底显示文本
                    st.write(response.text)

        except Exception as e:
            status_box.update(label="❌ 分析中断", state="error")
            st.error(f"系统错误: {e}")

