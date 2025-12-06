import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="模型侦探", page_icon="🔍")
st.title("🔍 API Key 模型侦探")

# 1. 输入 Key
api_key = st.text_input("请输入你的 API Key", type="password")

if st.button("开始侦查"):
    if not api_key:
        st.warning("请先输入 Key")
    else:
        # 2. 配置
        genai.configure(api_key=api_key)
        
        st.info("正在连接 Google 服务器查询户口...")
        
        try:
            # 3. 暴力拉取所有模型列表
            models_iter = genai.list_models()
            models = list(models_iter)
            
            if len(models) == 0:
                st.warning("连接成功，但你的 Key 似乎没有任何模型权限？")
            else:
                st.success(f"🎉 成功！找到了 {len(models)} 个可用模型：")
                # 4. 打印每一个模型的真实名字
                for m in models:
                    st.code(f"model = genai.GenerativeModel('{m.name.replace('models/', '')}')")
                    st.write(f"👆 说明: {m.description}")
                    st.markdown("---")
                    
        except Exception as e:
            st.error("❌ 侦查失败！核心报错如下（请截图发给 Gemini）：")
            st.error(e)
