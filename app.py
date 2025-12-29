import streamlit as st
import os

# 1. Page Config (Must be first)
st.set_page_config(
    page_title="El Massa Consult - GIS Premium",
    page_icon="🌍",
    layout="wide"
)

# 2. Lazy Imports to catch errors
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from streamlit_folium import st_folium
    import traceback
except Exception as e:
    st.error(f"❌ Error during library import: {e}")
    st.stop()

# 3. Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0A0E27; color: white; }
</style>
""", unsafe_allow_html=True)

# 4. Path Detection
def get_assets_path():
    possible = ["assets/gis", "gis_assets", "."]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 5. Optimized Data Loading
@st.cache_data
def load_data_safe(file_name, base_path):
    path = os.path.join(base_path, file_name)
    if not os.path.exists(path):
        return None, f"❌ File not found: {path}"
    
    try:
        # Load only essential columns + Row limit as a safety valve
        essential = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
        
        # We use pyogrio with arrow for maximum memory efficiency
        try:
            gdf = gpd.read_file(path, engine='pyogrio', columns=essential, use_arrow=True)
        except:
            gdf = gpd.read_file(path)
            gdf = gdf[[c for c in essential if c in gdf.columns]]

        # IF the file is still too big, we sample it to prevent OOM
        if len(gdf) > 20000:
            st.sidebar.warning(f"⚠️ Large dataset ({len(gdf)} rows). Loading top 20,000 for stability.")
            gdf = gdf.head(20000)
            
        # Simplify geometry aggressively (0.0001 is ~10m accuracy)
        gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)
        
        # Cleanup
        for col in gdf.columns:
            if col != 'geometry':
                gdf[col] = gdf[col].astype(str).replace('nan', '')
        
        if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
        else: gdf = gdf.to_crs(epsg=4326)
        
        return gdf, None
    except Exception as e:
        return None, f"❌ Data Error: {str(e)}"

# 6. Main App
def main():
    try:
        st.title("🌍 El Massa Consult - GIS View")
        
        # Sidebar info
        st.sidebar.markdown("### 🛠️ System Status")
        st.sidebar.text(f"Path: {ASSETS_PATH}")
        if st.sidebar.button("🧹 Clear Cache & Reload"):
            st.cache_data.clear()
            st.rerun()

        files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
        
        if not files:
            st.info("Please upload a file or ensure assets/gis exists.")
            uploaded = st.file_uploader("Upload GPKG", type=['gpkg'])
            if uploaded:
                if not os.path.exists("temp"): os.makedirs("temp")
                save_path = f"temp/{uploaded.name}"
                with open(save_path, "wb") as f: f.write(uploaded.getbuffer())
                target_file, target_path = uploaded.name, "temp"
            else: return
        else:
            target_file, target_path = files[0], ASSETS_PATH

        with st.spinner("⏳ Processing GIS Data..."):
            gdf, err = load_data_safe(target_file, target_path)
        
        if err:
            st.error(err)
            return

        st.sidebar.success(f"✅ Loaded {len(gdf)} records")

        # Layout
        col1, col2 = st.columns(2)
        with col1:
            govs = sorted(gdf['gov'].unique()) if 'gov' in gdf.columns else []
            sel_gov = st.selectbox("المحافظة", ["الكل"] + govs)
        
        filtered = gdf
        if sel_gov != "الكل": filtered = filtered[filtered['gov'] == sel_gov]
        
        with col2:
            secs = sorted(filtered['sec'].unique()) if 'sec' in filtered.columns else []
            sel_sec = st.selectbox("القسم", ["الكل"] + secs)
        
        if sel_sec != "الكل": filtered = filtered[filtered['sec'] == sel_sec]

        st.divider()

        if sel_sec == "الكل":
            st.info("💡 اختر قسماً محدداً لعرض الخريطة التفاعلية")
        elif not filtered.empty:
            # Simple Folium Map
            center = [filtered.geometry.centroid.y.mean(), filtered.geometry.centroid.x.mean()]
            m = folium.Map(location=center, zoom_start=13, tiles="CartoDB dark_matter")
            
            # Add GeoJson
            folium.GeoJson(
                filtered,
                style_function=lambda f: {
                    'fillColor': '#4CAF50' if f['properties'].get('survey_review_status') == 'مقبول' else '#F44336',
                    'color': 'white', 'weight': 1, 'fillOpacity': 0.6
                },
                tooltip=folium.GeoJsonTooltip(fields=['requestnumber', 'survey_review_status'])
            ).add_to(m)
            
            st_folium(m, height=550, width='100%')
            st.dataframe(filtered.drop(columns='geometry'), use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ لا توجد بيانات للمعيار المختار")

    except Exception as e:
        st.error("🚨 Critical System Failure")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
