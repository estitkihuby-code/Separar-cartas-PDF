import streamlit as st
import pymupdf
import pandas as pd
import re
import io
import zipfile

st.set_page_config(page_title="Separar Cartas PDF", page_icon="📄")

st.title("📄 Separador de Cartas PDF")
st.write(
    "Sube el PDF con todas las cartas y el Excel con los nombres. "
    "La app genera un PDF individual por cada carta, listos para descargar."
)

# ==========================
# 1. ARCHIVOS DE ENTRADA
# ==========================

st.header("1. Archivos")

pdf_file = st.file_uploader("PDF con todas las cartas", type=["pdf"])
excel_file = st.file_uploader("Excel con los nombres", type=["xlsx", "xls"])

# ==========================
# 2. PARÁMETROS
# ==========================

st.header("2. Parámetros")

col1, col2 = st.columns(2)
with col1:
    hoja = st.text_input("Nombre de la hoja de Excel", value="Hoja1")
    paginas_por_doc = st.number_input(
        "Páginas por carta", min_value=1, value=2, step=1
    )
with col2:
    columna = st.text_input("Columna con los nombres", value="Segunda Carta")

# ==========================
# 3. VALIDACIÓN PREVIA (opcional, antes de procesar)
# ==========================

if excel_file is not None:
    try:
        excel_file.seek(0)
        df_preview = pd.read_excel(excel_file, sheet_name=hoja)
        excel_file.seek(0)
        if columna in df_preview.columns:
            st.success(f"Excel leído correctamente: {len(df_preview)} nombres encontrados.")
        else:
            st.warning(
                f"La columna '{columna}' no existe en la hoja '{hoja}'. "
                f"Columnas disponibles: {list(df_preview.columns)}"
            )
    except Exception as e:
        st.error(f"No se pudo leer el Excel: {e}")

# ==========================
# 4. PROCESAMIENTO
# ==========================

st.header("3. Generar PDFs")

if st.button("Separar cartas", type="primary"):

    if pdf_file is None or excel_file is None:
        st.error("Debes subir el PDF y el Excel antes de continuar.")
        st.stop()

    try:
        df = pd.read_excel(excel_file, sheet_name=hoja)
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        st.stop()

    if columna not in df.columns:
        st.error(f"La columna '{columna}' no existe en la hoja '{hoja}'.")
        st.stop()

    pdf_bytes = pdf_file.read()
    pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    total_paginas = pdf.page_count
    total_documentos = total_paginas // paginas_por_doc

    st.write(f"Total páginas: {total_paginas}")
    st.write(f"Total PDFs a generar: {total_documentos}")

    if len(df) < total_documentos:
        st.error(
            f"El Excel tiene {len(df)} nombres pero se necesitan {total_documentos}."
        )
        pdf.close()
        st.stop()

    zip_buffer = io.BytesIO()
    progreso = st.progress(0)

    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for i in range(total_documentos):
            nombre = str(df.loc[i, columna])
            nombre = re.sub(r'[\\/:*?"<>|]', "_", nombre)

            nuevo = pymupdf.open()
            inicio = i * paginas_por_doc
            fin = inicio + paginas_por_doc - 1
            nuevo.insert_pdf(pdf, from_page=inicio, to_page=fin)

            doc_bytes = nuevo.tobytes()
            nuevo.close()

            zf.writestr(f"{nombre}.pdf", doc_bytes)

            progreso.progress((i + 1) / total_documentos)

    pdf.close()
    zip_buffer.seek(0)

    st.success(f"¡Listo! Se generaron {total_documentos} PDFs.")

    st.download_button(
        label="⬇️ Descargar todos los PDFs (.zip)",
        data=zip_buffer,
        file_name="cartas_separadas.zip",
        mime="application/zip",
    )
