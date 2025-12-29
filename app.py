import streamlit as st
import os

st.set_page_config(page_title="GIS Safe Boot")

st.title("🛡️ GIS Service - Safe Boot")

st.write("This application is currently in **Safe Boot Mode** to diagnose deployment issues.")

st.info("If you see this message, the basic Streamlit server is running correctly.")

st.sidebar.markdown("### 🔍 Diagnostics")
st.sidebar.write(f"CWD: {os.getcwd()}")

# Check for data files
st.write("### 📂 Data Check")
found_gpkg = False
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".gpkg"):
            size = os.path.getsize(os.path.join(root, file)) / (1024 * 1024)
            st.write(f"✅ Found: `{os.path.join(root, file)}` ({size:.2f} MB)")
            found_gpkg = True

if not found_gpkg:
    st.error("❌ No .gpkg files found in the repository.")

# Delayed Import Test
if st.button("🧪 Test GIS Libraries"):
    with st.spinner("Importing GeoPandas..."):
        try:
            import geopandas as gpd
            st.success(f"✅ GeoPandas {gpd.__version__} loaded successfully!")
        except Exception as e:
            st.error(f"❌ GeoPandas failed: {e}")
            
    with st.spinner("Importing Folium..."):
        try:
            import folium
            st.success("✅ Folium loaded successfully!")
        except Exception as e:
            st.error(f"❌ Folium failed: {e}")

st.write("---")
st.warning("If the app crashes AFTER clicking the test button, the issue is a library conflict or RAM limit.")
