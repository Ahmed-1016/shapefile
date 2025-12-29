import streamlit as st
import geopandas as gpd
import pandas as pd
import os

st.title("🚀 Baseline Environment Test")

st.success("If you see this, the core libraries (Streamlit, Geopandas) are loaded!")

st.write("### Environment Details")
st.write(f"CWD: {os.getcwd()}")

# Test Data access
path = "assets/gis/13-12-2025.gpkg"
if os.path.exists(path):
    st.write(f"✅ Data file found: {path}")
    st.write(f"Size: {os.path.getsize(path)/(1024*1024):.1f} MB")
else:
    st.error("❌ Data file NOT found. Searching...")
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".gpkg"):
                st.write(f"Found at: {os.path.join(root, f)}")

if st.button("Run Memory Intensive Test (Load GDF)"):
    try:
        with st.spinner("Loading 148MB file..."):
            gdf = gpd.read_file(path)
            st.write(f"✅ Success! Loaded {len(gdf)} rows.")
            st.dataframe(gdf.head(10))
    except Exception as e:
        st.error(f"❌ Failed to load: {e}")
