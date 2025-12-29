import streamlit as st
import os
import sys
import subprocess

st.set_page_config(page_title="GIS System Check")

st.title("🛡️ GIS System Diagnostic")

# 1. System Info
st.subheader("💻 System Information")
st.code(f"Python Version: {sys.version}\nPlatform: {sys.platform}\nCWD: {os.getcwd()}")

# 2. Check Installed Packages
st.subheader("📦 Installed Packages (Check)")
try:
    result = subprocess.check_output([sys.executable, "-m", "pip", "list"], text=True)
    with st.expander("Show Pip List"):
        st.code(result)
except Exception as e:
    st.error(f"Could not list packages: {e}")

# 3. Test GIS Libraries
st.subheader("🧪 Library Integration Test")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**GeoPandas**")
    try:
        import geopandas as gpd
        st.success(f"✅ Loaded (v{gpd.__version__})")
    except Exception as e:
        st.error(f"❌ Failed: {e}")

with col2:
    st.write("**Pyogrio**")
    try:
        import pyogrio
        st.success("✅ Loaded")
    except Exception as e:
        st.error(f"❌ Failed: {e}")

with col3:
    st.write("**RTree**")
    try:
        import rtree
        st.success("✅ Loaded")
    except Exception as e:
        st.error(f"❌ Failed: {e}")

# 4. Data File Check
st.subheader("📂 Assets Check")
paths = ["assets/gis", "gis_assets", ".", ".."]
for p in paths:
    full = os.path.abspath(p)
    if os.path.exists(full):
        files = os.listdir(full)
        st.write(f"📁 `{p}` ({full}): {files}")
    else:
        st.write(f"❌ `{p}` does not exist")

# 5. Memory Status
try:
    import psutil
    mem = psutil.virtual_memory()
    st.subheader("📊 Memory Status")
    st.write(f"Total: {mem.total / (1024**3):.2f} GB")
    st.write(f"Available: {mem.available / (1024**3):.2f} GB")
    st.write(f"Used: {mem.percent}%")
except:
    st.info("psutil not available")

st.info("If all libraries are ✅ but you still get 'Oh no' when loading the map, it is definitely a RAM issue with the 148MB file.")
