import streamlit as st
import os
import sys

# Disable the large file loading by default to prevent OOM
st.set_page_config(page_title="GIS Bootstrapper", page_icon="🏗️")

st.title("🏗️ GIS Service: Ultra-Minimal Bootstrapper")

st.write("This is a fail-safe version of the application. If you can see this, it means the basic Streamlit environment is working.")

st.sidebar.markdown("### 🔍 System Info")
st.sidebar.write(f"Python Version: {sys.version}")
st.sidebar.write(f"CPU Cores: {os.cpu_count()}")

# Test imports only when clicked
if st.button("🚀 Test GIS Libraries (Geopandas, etc.)"):
    with st.spinner("Testing imports..."):
        results = []
        for lib in ["pandas", "geopandas", "pyogrio", "folium", "rtree"]:
            try:
                __import__(lib)
                results.append(f"✅ {lib}: Success")
            except Exception as e:
                results.append(f"❌ {lib}: Failed ({str(e)})")
        
        for r in results:
            st.write(r)

st.write("---")
st.write("### 📂 Data Discovery")
found_files = []
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".gpkg"):
            rel_path = os.path.join(root, file)
            size = os.path.getsize(rel_path) / (1024*1024)
            found_files.append((rel_path, size))

if found_files:
    for f, s in found_files:
        st.write(f"📍 Found: `{f}` ({s:.2f} MB)")
else:
    st.error("❌ No `.gpkg` data files found in the repository!")

st.write("---")
st.info("If this page loads but the main app crashes, the issue is 100% the RAM limit (1GB).")
