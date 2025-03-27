
import streamlit as st
import pandas as pd
import re
from modules.geocode import geocode_address

st.set_page_config(layout="wide")
st.title("Контроль и валидация адресов | МОСЭНЕРГОСБЫТ")

# Функция для определения, является ли строка адресом
def is_probable_address(value):
    if not isinstance(value, str):
        return False
    if any(x in value.lower() for x in ["ул", "улица", "просп", "г.", "город", "д.", "дом", "р-н"]):
        return True
    return False

# Функция для определения кадастрового номера
def is_kad_number(value):
    return isinstance(value, str) and bool(re.match(r"^\d{2}:\d{2}:\d{6,7}:\d+$", value))

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
        st.dataframe(df[df["status"] == "адрес"])

        st.subheader("🟡 Кадастровые номера")
        st.dataframe(df[df["status"] == "кадастр"])

        st.subheader("🔴 Некорректные строки")
        st.dataframe(df[df["status"] == "некорректный"])

        # Кнопки для действий
        st.subheader("⚙️ Действия")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("📍 Геокодировать валидные адреса (основной)")
        with col2:
            st.button("🧠 Автоисправление некорректных строк")
        with col3:
            st.button("📬 Конвертировать кадастровые номера в адреса (Росреестр)")
