
import streamlit as st
import pandas as pd
import re
import folium
from streamlit_folium import st_folium
from modules.geocode import geocode_address

st.set_page_config(layout="wide")
st.title("Контроль и валидация адресов | МОСЭНЕРГОСБЫТ")

def is_probable_address(value):
    if not isinstance(value, str):
        return False
    if any(x in value.lower() for x in ["ул", "улица", "просп", "г.", "город", "д.", "дом", "р-н"]):
        return True
    return False

def is_kad_number(value):
    return isinstance(value, str) and bool(re.match(r"^\\d{2}:\\d{2}:\\d{6,7}:\\d+$", value))

uploaded_file = st.file_uploader("📁 Загрузите Excel-файл с данными", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("📋 Загруженные данные")
    st.dataframe(df)

    address_column = None
    for col in df.columns:
        sample = df[col].dropna().astype(str).head(50)
        score = sum([is_probable_address(v) or is_kad_number(v) for v in sample])
        if score / len(sample) > 0.3:
            address_column = col
            break

    if not address_column:
        st.error("❌ Не удалось автоматически определить столбец с адресами.")
    else:
        st.success(f"✅ Найден столбец с адресами: **{address_column}**")

        df["is_kadastr"] = df[address_column].apply(is_kad_number)
        df["is_address"] = df[address_column].apply(is_probable_address)
        df["status"] = df.apply(lambda row: "кадастр" if row["is_kadastr"] else (
            "адрес" if row["is_address"] else "некорректный"), axis=1)

        st.subheader("🟢 Валидные адреса")
        valid_df = df[df["status"] == "адрес"]
        st.dataframe(valid_df)

        st.subheader("⚙️ Действия")
        if st.button("📍 Геокодировать и отобразить адреса по убыванию долга"):
            st.info("⏳ Геокодирование...")
            coords = []
            for _, row in valid_df.iterrows():
                addr = row[address_column]
                lat, lon = geocode_address(addr)
                coords.append((lat, lon))
            valid_df["lat"] = [c[0] for c in coords]
            valid_df["lon"] = [c[1] for c in coords]

            valid_coords = valid_df.dropna(subset=["lat", "lon"])

            # Сортировка по задолженности
            if "Задолженность" in valid_coords.columns:
                valid_coords = valid_coords.sort_values(by="Задолженность", ascending=False)

            # Карта с точками
            st.subheader("🗺️ Карта адресов по убыванию долга")
            if not valid_coords.empty:
                m = folium.Map(location=[valid_coords["lat"].mean(), valid_coords["lon"].mean()], zoom_start=11)
                for _, row in valid_coords.iterrows():
                    popup_text = f"{row[address_column]}\\nЗадолженность: {row['Задолженность']} ₽"
                    folium.Marker(
                        location=[row["lat"], row["lon"]],
                        popup=popup_text,
                        icon=folium.Icon(color="red")
                    ).add_to(m)
                st_folium(m, width=900, height=600)

                # Список адресов
                st.subheader("📄 Список адресов по убыванию долга:")
                for _, row in valid_coords.iterrows():
                    st.markdown(f"- **{row[address_column]}** — {row['Задолженность']} ₽")
            else:
                st.warning("Не удалось получить координаты ни для одного адреса.")
