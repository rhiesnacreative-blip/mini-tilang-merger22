import streamlit as st
import requests
import fitz  # PyMuPDF
from datetime import datetime
import os
import json

st.set_page_config(page_title="Tilang PDF Merger", page_icon="📄", layout="centered")

# ================== USER DATA ==================
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=2)

if "users" not in st.session_state:
    st.session_state.users = load_users()
    if "wawanris" not in st.session_state.users:
        st.session_state.users["wawanris"] = {"password": "gakkum789", "role": "superadmin"}
        save_users(st.session_state.users)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "current_role" not in st.session_state:
    st.session_state.current_role = None

# ================== LOGIN ==================
def show_login():
    st.markdown("<h1 style='text-align: center; color: #00f5ff;'>🔐 Tilang PDF Merger</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            if username in st.session_state.users and st.session_state.users[username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.session_state.current_role = st.session_state.users[username]["role"]
                st.success(f"✅ Login berhasil sebagai **{username}**")
                st.rerun()
            else:
                st.error("❌ Username atau Password salah!")

if not st.session_state.logged_in:
    show_login()
    st.stop()

# ================== HEADER ==================
col_logout1, col_logout2 = st.columns([8, 2])
with col_logout2:
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.current_role = None
        st.rerun()

st.markdown(f"**👤 Login sebagai:** `{st.session_state.current_user}` | **Role:** `{st.session_state.current_role.upper()}`")

col_logo, col_title = st.columns([1.2, 5])
with col_logo:
    try:
        st.image("rhiesna_logo.png", width=160)
    except:
        pass
with col_title:
    st.title("Tilang PDF Merger")
    st.markdown("**by : Rhiesna Creative**")

st.divider()

# ================== SUPER ADMIN - TAMBAH OPERATOR ==================
if st.session_state.current_role == "superadmin":
    with st.expander("⚙️ Kelola Operator (Super Admin Only)", expanded=False):
        st.subheader("Tambah Operator Baru")
        new_user = st.text_input("Username Operator Baru")
        new_pass = st.text_input("Password Operator Baru", type="password")
        if st.button("Tambahkan Operator", type="primary"):
            if new_user and new_pass and new_user not in st.session_state.users:
                st.session_state.users[new_user] = {"password": new_pass, "role": "operator"}
                save_users(st.session_state.users)
                st.success(f"✅ Operator `{new_user}` berhasil ditambahkan!")
            else:
                st.error("❌ Username sudah ada atau kosong!")

st.divider()

# ================== RANGE GENERATOR & INPUT ==================
tab1, tab2 = st.tabs(["📝 Input Manual", "🔢 Range Generator"])

with tab1:
    st.subheader("Masukkan Nomor Register Tilang")
    nomor_input = st.text_area(label="", height=200, placeholder="I0006928\nG4341343\nB5678901")

with tab2:
    st.subheader("🔢 Range Generator")
    col1, col2, col3 = st.columns([1,2,2])
    prefix = col1.text_input("Prefix", value="I", max_chars=2)
    start_num = col2.number_input("Nomor Awal", min_value=0, value=1000)
    end_num = col3.number_input("Nomor Akhir", min_value=0, value=1010)
    
    if st.button("🔢 Generate Range", type="primary", use_container_width=True):
        if end_num >= start_num:
            generated = [f"{prefix}{str(i).zfill(7)}" for i in range(start_num, end_num + 1)]
            st.success(f"✅ Berhasil generate **{len(generated)}** nomor")
            st.code("\n".join(generated))
            st.session_state.generated_numbers = "\n".join(generated)
        else:
            st.error("Nomor Akhir harus lebih besar!")

# ================== PROSES PDF ==================
st.divider()
st.subheader("🚀 Proses & Gabungkan PDF")

# Ambil nomor dari Range atau Manual
default_value = st.session_state.get('generated_numbers', "")
nomor_input_final = st.text_area(label="Nomor yang akan diproses:", value=default_value, height=150)

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
            status_text.write(f"⏳ Memproses: **{i}/{total}** | {nomor}")
            progress_bar.progress(i / total)

            try:
                r = requests.get(base_url + nomor, timeout=60)
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
                        page.insert_textbox(rect, header_text, fontsize=18, color=(0,0,0), align=fitz.TEXT_ALIGN_LEFT)

                    master_doc.insert_pdf(src_doc)
                    src_doc.close()
                    processed += 1
                    success_list.append(nomor)
                else:
                    failed_list.append(nomor)
            except:
                failed_list.append(nomor)

        progress_bar.progress(1.0)
        status_text.write(f"✅ **Selesai!** {processed}/{total} file berhasil.")

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ Berhasil: {len(success_list)}")
            if success_list:
                st.code("\n".join(success_list))
        with col2:
            st.error(f"❌ Gagal: {len(failed_list)}")
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
