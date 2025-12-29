import streamlit as st
import os

# --- APP VERSION ---
VERSION = "2.1.0 (Multi-Select Edition)"

# 1. Page Config
st.set_page_config(
    page_title=f"الماسة كونسلت GIS - {VERSION}",
    page_icon="🌍",
    layout="wide"
)

# Initialize Session State for Multi-Select
if 'selected_requests' not in st.session_state:
    st.session_state.selected_requests = set()

# 2. Lazy Imports
try:
    import geopandas as gpd
    import pandas as pd
    import folium
    from folium.plugins import LocateControl
    from streamlit_folium import st_folium
    import traceback
except Exception as e:
    st.error(f"❌ خطأ في تحميل المكتبات: {e}")
    st.stop()

# 3. Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #0A1128; color: white; }
    .legend-box {
        padding: 15px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .legend-item { display: flex; align-items: center; margin-bottom: 8px; gap: 12px; font-size: 0.9em; }
    .dot { height: 14px; width: 14px; border-radius: 3px; display: inline-block; border: 1px solid white; }
    .stMetric { background: rgba(0, 230, 118, 0.1); border-radius: 10px; padding: 10px; border: 1px solid #00E676; }
</style>
""", unsafe_allow_html=True)

# 4. Helpers
def get_color(status):
    status = str(status)
    if 'مقبول' in status: return '#00E676'
    if 'مرفوض' in status or 'ملغى' in status: return '#FF1744'
    return '#FFEA00'

def get_assets_path():
    possible = ["assets/gis", ".", "gis_service/assets/gis"]
    for p in possible:
        if os.path.exists(p) and any(f.endswith('.gpkg') for f in os.listdir(p)):
            return p
    return "."

ASSETS_PATH = get_assets_path()

# 5. Data Loading
@st.cache_data(ttl=3600)
def load_meta(file_name, base_path):
    path = os.path.join(base_path, file_name)
    return gpd.read_file(path, engine='pyogrio', columns=['gov', 'sec'], use_arrow=True)

@st.cache_data(ttl=3600)
def load_map_data(file_name, base_path, gov, sec):
    path = os.path.join(base_path, file_name)
    where = f"gov = '{gov}' AND sec = '{sec}'"
    cols = ['geometry', 'requestnumber', 'gov', 'sec', 'survey_review_status']
    gdf = gpd.read_file(path, engine='pyogrio', columns=cols, where=where, use_arrow=True)
    gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)
    if gdf.crs is None: gdf.set_crs(epsg=4326, inplace=True)
    else: gdf = gdf.to_crs(epsg=4326)
    gdf['status_color'] = gdf['survey_review_status'].apply(get_color)
    return gdf

# 6. Main App
def main():
    st.sidebar.markdown(f"### 🌍 El Massa GIS")
    st.sidebar.markdown(f"**إصدار التحديد المتعدد: {VERSION}**")
    
    if st.sidebar.button("🔄 تحديث شامل واعادة تعيين"):
        st.cache_data.clear()
        st.session_state.selected_requests = set()
        st.rerun()

    if st.session_state.selected_requests:
        if st.sidebar.button("🗑️ مسح التحديد الحالي"):
            st.session_state.selected_requests = set()
            st.rerun()

    st.title("🌐 نظام التحديد المتعدد للخرائط - هضبة الماسة")

    files = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.gpkg')] if os.path.exists(ASSETS_PATH) else []
    if not files:
        st.error("⚠️ لم يتم العثور على ملفات.")
        return
    
    target_file = files[0]

    # Legend Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🎨 مفتاح الحالات")
    st.sidebar.markdown(f"""
    <div class="legend-box">
        <div class="legend-item"><span class="dot" style="background:#00E676"></span> تم القبول</div>
        <div class="legend-item"><span class="dot" style="background:#FFEA00"></span> قيد المراجعة</div>
        <div class="legend-item"><span class="dot" style="background:#FF1744"></span> مرفوض / ملغى</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        meta_df = load_meta(target_file, ASSETS_PATH)
        govs = sorted(meta_df['gov'].unique())
        sel_gov = st.sidebar.selectbox("اختر المحافظة", ["-- اختر --"] + govs)
        
        if sel_gov != "-- اختر --":
            secs = sorted(meta_df[meta_df['gov'] == sel_gov]['sec'].unique())
            sel_sec = st.sidebar.selectbox(f"اختر القسم في {sel_gov}", ["-- اختر --"] + secs)
            
            if sel_sec != "-- اختر --":
                with st.spinner("⏳ جاري تحميل البيانات..."):
                    gdf = load_map_data(target_file, ASSETS_PATH, sel_gov, sel_sec)
                
                if not gdf.empty:
                    # Metrics Row
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("إجمالي الطلبات في القسم", len(gdf))
                    with c2: st.metric("الطلبات المختارة", len(st.session_state.selected_requests))
                    with c3:
                        accepted = len(gdf[gdf['status_color'] == '#00E676'])
                        st.metric("تم القبول", f"{accepted} ({int(accepted/max(len(gdf),1)*100)}%)")

                    # Map rendering
                    center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
                    m = folium.Map(location=center, zoom_start=14)
                    LocateControl(auto_start=False).add_to(m)
                    
                    folium.TileLayer(
                        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
                        attr="Google Satellite",
                        name="Satellite",
                        overlay=False,
                        control=True
                    ).add_to(m)

                    # Mark selected features differently if needed
                    geo_json_layer = folium.GeoJson(
                        gdf,
                        name="Requests",
                        style_function=lambda f: {
                            'fillColor': f['properties'].get('status_color'),
                            'color': '#FFFFFF' if f['properties'].get('requestnumber') not in st.session_state.selected_requests else '#00B0FF',
                            'weight': 1 if f['properties'].get('requestnumber') not in st.session_state.selected_requests else 4,
                            'fillOpacity': 0.6 if f['properties'].get('requestnumber') not in st.session_state.selected_requests else 0.8
                        },
                        highlight_function=lambda f: {'weight': 5, 'color': '#00E676', 'fillOpacity': 0.9},
                        tooltip=folium.GeoJsonTooltip(fields=['requestnumber', 'survey_review_status'], aliases=['رقم الطلب:', 'الحالة:'])
                    ).add_to(m)

                    st.info("💡 اضغط على الأشكال في الخريطة لتحديدها. الضغط على شكل مختار مسبقاً سيزيله من القائمة.")
                    
                    map_out = st_folium(m, height=550, width='100%', key="multi_select_map")

                    # UPDATE SELECTION STATE
                    if map_out.get("last_object_clicked"):
                        clicked_obj = map_out["last_object_clicked"]
                        # Robust check: ensure 'properties' exists and contains 'requestnumber'
                        if "properties" in clicked_obj and "requestnumber" in clicked_obj["properties"]:
                            clicked_req = clicked_obj["properties"]["requestnumber"]
                            
                            # Toggle selection
                            if clicked_req in st.session_state.selected_requests:
                                st.session_state.selected_requests.remove(clicked_req)
                            else:
                                st.session_state.selected_requests.add(clicked_req)
                            st.rerun()

                    # DISPLAY SELECTED DATA
                    st.divider()
                    if st.session_state.selected_requests:
                        display_df = gdf[gdf['requestnumber'].isin(st.session_state.selected_requests)]
                        st.success(f"📋 الطلبات المختارة حالياً ({len(display_df)}):")
                    else:
                        display_df = gdf
                        st.subheader("📋 كافة الطلبات في هذا القسم")

                    st.dataframe(
                        display_df.drop(columns=['geometry', 'status_color']),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("لا توجد بيانات.")
            else:
                st.info("المرجو اختيار القسم.")
        else:
            st.info("المرجو اختيار المحافظة.")
            
    except Exception as e:
        st.error("خطأ تقني")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
