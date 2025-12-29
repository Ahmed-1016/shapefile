import streamlit as st
import sys
import os

st.title("🛡️ Minimal Boot Test")

st.write("### 1. System Check")
st.write(f"Python: {sys.version}")
st.write(f"CWD: {os.getcwd()}")

st.write("### 2. Library Import Test")

def test_import(name):
    try:
        __import__(name)
        st.success(f"✅ {name} imported successfully")
        return True
    except Exception as e:
        st.error(f"❌ {name} failed: {e}")
        return False

libs = ["pandas", "geopandas", "folium", "streamlit_folium", "pyogrio", "rtree"]

for lib in libs:
    test_import(lib)

st.write("### 3. Data File Discovery")
path = "assets/gis/13-12-2025.gpkg"
if os.path.exists(path):
    size = os.path.getsize(path) / (1024*1024)
    st.success(f"✅ Found data file: {path} ({size:.2f} MB)")
else:
    st.warning(f"⚠️ Data file not found at: {path}")
    # Search for any gpkg
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".gpkg"):
                st.write(f"Found: {os.path.join(root, file)}")

st.info("If you see this page, the environment is healthy. The crash is likely due to RAM exhaustion when loading the full map.")
