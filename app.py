
import streamlit as st
import pandas as pd
from modules.geocode import geocode_address
import folium
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Контроль задолженности | МОСЭНЕРГОСБЫТ")

uploaded_file = st.file_uploader("📁 Загрузите Excel-файл с адресами и задолженностями", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("📋 Загруженные данные")
    st.dataframe(df)

    # Геокодирование
    st.subheader("🌐 Геокодирование адресов")
    coords = []
    for index, row in df.iterrows():
        addr = row.get("Адрес")
        if pd.notna(addr):
            lat, lon = geocode_address(addr)
            coords.append((lat, lon))
        else:
            coords.append((None, None))

    df["lat"] = [c[0] for c in coords]
    df["lon"] = [c[1] for c in coords]

    # Отображение карты
    st.subheader("🗺️ Карта клиентов")
    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=12)
    for _, row in df.iterrows():
        if pd.notna(row["lat"]) and pd.notna(row["lon"]):
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"{row['Адрес']}\nЗадолженность: {row['Задолженность']} ₽",
                icon=folium.Icon(color="blue")
            ).add_to(m)
    st_folium(m, width=900, height=600)

    # Кнопка для скачивания файла с координатами
    st.subheader("💾 Сохранить результат")
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label="⬇️ Скачать Excel с координатами",
        data=output.getvalue(),
        file_name="updated_clients.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
