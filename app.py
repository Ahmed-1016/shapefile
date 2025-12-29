import streamlit as st
import os

# 1. Page Config (Must be first)
st.set_page_config(
    page_title="El Massa Consult - GIS Premium",
    page_icon="🌍",
    layout="wide"
)

# 2. Lazy Imports
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
    .stApp { background-color: #0A1128; color: white; }
    .stSelectbox label { color: #00E676 !important; font-weight: bold; }
    .css-1r6slb0 { background-color: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 20px; }
</style>
""", unsafe_allow_html=True)

# 4. Path Detection
def get_assets_path():
    possible = ["assets/gis", "."]
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
        # Load only essential columns
        essential = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
        
        # We use pyogrio with arrow for maximum memory efficiency
        gdf = gpd.read_file(path, engine='pyogrio', columns=essential, use_arrow=True)

        # Safety valve: 20k rows is roughly the stable limit for streamlit's serialization
        if len(gdf) > 20000:
            gdf = gdf.sample(20000)
            st.sidebar.warning("⚠️ Large dataset: Showing 20,000 sampled records for stability.")
            
        # Simplify geometry (0.0001 is ~10m accuracy) - Essential to prevent browser crash
        gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)
        
        # Stringify columns for serialization
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
        st.title("🌍 El Massa Consult - GIS Platform")
        
        st.sidebar.markdown("### 🛠️ System Status")
        if st.sidebar.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.rerun()

        files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
        
        if not files:
            uploaded = st.file_uploader("Upload GPKG", type=['gpkg'])
            if uploaded:
                if not os.path.exists("temp"): os.makedirs("temp")
                save_path = f"temp/{uploaded.name}"
                with open(save_path, "wb") as f: f.write(uploaded.getbuffer())
                target_file, target_path = uploaded.name, "temp"
            else: return
        else:
            target_file, target_path = files[0], ASSETS_PATH

        with st.spinner("⏳ Loading Geospatial Intelligence..."):
            gdf, err = load_data_safe(target_file, target_path)
        
        if err:
            st.error(err)
            return

        st.sidebar.success(f"✅ Records Loaded: {len(gdf)}")

        # Filters
        c1, c2 = st.columns(2)
        with c1:
            govs = sorted(gdf['gov'].unique()) if 'gov' in gdf.columns else []
            sel_gov = st.selectbox("اختر المحافظة", ["الكل"] + govs)
        filtered = gdf if sel_gov == "الكل" else gdf[gdf['gov'] == sel_gov]
        
        with c2:
            secs = sorted(filtered['sec'].unique()) if 'sec' in filtered.columns else []
            sel_sec = st.selectbox("اختر القسم", ["الكل"] + secs)
        if sel_sec != "الكل": filtered = filtered[filtered['sec'] == sel_sec]

        st.divider()

        if sel_sec == "الكل" and len(filtered) > 5000:
            st.info("💡 يرجى اختيار قسماً محدداً لعرض الخريطة التفاعلية")
            st.dataframe(filtered.drop(columns='geometry').head(100), use_container_width=True)
        elif not filtered.empty:
            # Map Rendering
            center = [filtered.geometry.centroid.y.mean(), filtered.geometry.centroid.x.mean()]
            m = folium.Map(location=center, zoom_start=14)
            
            # Google Hybrid Tile
            google_hybrid = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
            folium.TileLayer(
                tiles=google_hybrid,
                attr="Google Satellite",
                name="Satellite View",
                overlay=False,
                control=True
            ).add_to(m)

            folium.GeoJson(
                filtered,
                style_function=lambda f: {
                    'fillColor': '#00E676' if 'مقبول' in str(f['properties'].get('survey_review_status')) else '#FF1744',
                    'color': 'white', 'weight': 1, 'fillOpacity': 0.5
                },
                tooltip=folium.GeoJsonTooltip(fields=['requestnumber', 'survey_review_status'], aliases=['طلب رقم:', 'الحالة:'])
            ).add_to(m)
            
            st_folium(m, height=600, width='100%')
            st.dataframe(filtered.drop(columns='geometry'), use_container_width=True)
        else:
            st.warning("⚠️ لا توجد بيانات مطابقة للمواصفات")

    except Exception as e:
        st.error("🚨 Critical System Failure")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
