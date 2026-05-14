import streamlit as st
import requests
import fitz  # PyMuPDF
from datetime import datetime

st.set_page_config(page_title="Tilang PDF Merger", page_icon="📄", layout="centered")

# ================== HEADER DENGAN LOGO ==================
col_logo, col_title = st.columns([1.2, 5])
with col_logo:
    try:
        st.image("rhiesna_logo.png", width=160)
    except:
        st.warning("Logo tidak ditemukan (rhiesna_logo.png)")

with col_title:
    st.title("Tilang PDF Merger")
    st.markdown("**by : Rhiesna Creative**")

st.divider()

# ================== TABS ==================
tab1, tab2 = st.tabs(["📝 Input Manual", "🔢 Range Generator"])

# ===================== TAB 1: INPUT MANUAL =====================
with tab1:
    st.subheader("Masukkan Nomor Register Tilang")
    nomor_input = st.text_area(
        label="",
        height=250,
        placeholder="I0006928\nG4341343\nB5678901\n\n(Satu nomor per baris)",
        help="Masukkan nomor register satu per baris"
    )

# ===================== TAB 2: RANGE GENERATOR =====================
with tab2:
    st.subheader("🔢 Range Generator")
    
    col_prefix, col_start, col_end = st.columns([1, 2, 2])
    
    with col_prefix:
        prefix = st.text_input("Prefix", value="I", max_chars=1, help="Contoh: I, G, B, J, dll")
    
    with col_start:
        start_num = st.number_input("Nomor Awal", min_value=0, value=1000, step=1)
    
    with col_end:
        end_num = st.number_input("Nomor Akhir", min_value=0, value=1010, step=1)
    
    if st.button("🔢 Generate Range", type="primary", use_container_width=True):
        if end_num < start_num:
            st.error("Nomor Akhir harus lebih besar dari Nomor Awal!")
        else:
            generated = [f"{prefix}{str(i).zfill(7)}" for i in range(start_num, end_num + 1)]
            
            st.success(f"✅ Berhasil generate **{len(generated)}** nomor")
            st.code("\n".join(generated))
            
            # Tombol Copy
            st.button("📋 Copy Semua ke Clipboard", 
                     on_click=lambda: st.toast("✅ Sudah dicopy ke clipboard!", icon="📋"),
                     key="copy_btn")
            
            # Simpan ke session state supaya bisa dipakai di tab manual
            st.session_state.generated_numbers = "\n".join(generated)

# ================== PROSES GABUNGAN (di luar tab) ==================
st.divider()
st.subheader("🚀 Proses & Gabungkan PDF")

# Ambil nomor dari tab yang aktif
if 'generated_numbers' in st.session_state and st.session_state.get('generated_numbers'):
    default_value = st.session_state.generated_numbers
else:
    default_value = ""

nomor_input_final = st.text_area(
    label="Nomor yang akan diproses:",
    value=default_value,
    height=150,
    placeholder="Nomor akan muncul di sini...",
    help="Bisa dari Input Manual atau dari Range Generator"
)

if st.button("🚀 PROSES & GABUNGKAN PDF", type="primary", use_container_width=True):
    if not nomor_input_final.strip():
        st.error("Masukkan minimal 1 nomor register!")
    else:
        nomor_list = [line.strip() for line in nomor_input_final.splitlines() if line.strip()]
        total = len(nomor_list)
        processed = 0
        success_list = []
        failed_list = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        master_doc = fitz.open()
        base_url = "https://dakgargakkum.korlantas.polri.go.id/document/tilang/"

        for i, nomor in enumerate(nomor_list, 1):
            full_url = base_url + nomor
            status_text.write(f"⏳ Memproses: **{i}/{total}** | {nomor}")
            progress_bar.progress(i / total)

            try:
                r = requests.get(full_url, timeout=60)
                if r.status_code == 200 and r.content.startswith(b'%PDF'):
                    src_doc = fitz.open(stream=r.content, filetype="pdf")
                   
                    court = "???"
                    for page in src_doc:
                        text = page.get_text().upper()
                        for name, initial in {
                            "JAKARTA TIMUR": "JT", "JAKARTA UTARA": "JU",
                            "JAKARTA BARAT": "JB", "JAKARTA PUSAT": "JP",
                            "JAKARTA SELATAN": "JS"
                        }.items():
                            if name in text:
                                court = initial
                                break
                        if court != "???":
                            break

                    for page in src_doc:
                        rect = fitz.Rect(50, 20, 550, 65)
                        header_text = f"{court} - {nomor}"
                        page.insert_textbox(rect, header_text, fontsize=18,
                                          color=(0,0,0), align=fitz.TEXT_ALIGN_LEFT,
                                          fontname="helv", border_width=0)

                    master_doc.insert_pdf(src_doc)
                    src_doc.close()
                    processed += 1
                    success_list.append(nomor)
                else:
                    failed_list.append(nomor)
            except:
                failed_list.append(nomor)

        progress_bar.progress(1.0)
        status_text.write(f"✅ **Selesai!** {processed}/{total} file berhasil diproses.")

        # Hasil Berhasil & Gagal
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ **Berhasil: {len(success_list)}**")
            if success_list:
                st.code("\n".join(success_list))
        with col2:
            st.error(f"❌ **Gagal: {len(failed_list)}**")
            if failed_list:
                st.code("\n".join(failed_list))

        if processed > 0:
            output_name = f"HASIL_TILANG_GABUNGAN_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
            master_doc.save(output_name)
            master_doc.close()

            with open(output_name, "rb") as f:
                st.download_button(
                    label="📥 Download Hasil Gabungan",
                    data=f,
                    file_name=output_name,
                    mime="application/pdf",
                    use_container_width=True
                )

st.caption("© Wawan Risnawan Digital & Creative Center")