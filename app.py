import streamlit as st
import requests
import fitz  # PyMuPDF
from datetime import datetime, timedelta
import csv
import os
import pandas as pd
import json

st.set_page_config(page_title="Tilang PDF Merger", page_icon="📄", layout="centered")

# ================== LOAD & SAVE USERS (PERMANEN) ==================
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

# Load users
if "users" not in st.session_state:
    st.session_state.users = load_users()
    # Pastikan superadmin selalu ada
    if "wawanris" not in st.session_state.users:
        st.session_state.users["wawanris"] = {
            "password": "gakkum789", 
            "role": "superadmin", 
            "last_active": None
        }
        save_users(st.session_state.users)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "current_role" not in st.session_state:
    st.session_state.current_role = None

# ================== UPDATE LAST ACTIVE ==================
def update_last_active(username):
    if username in st.session_state.users:
        st.session_state.users[username]["last_active"] = datetime.now()
        save_users(st.session_state.users)

# ================== CEK OPERATOR ONLINE ==================
def get_online_users():
    online = []
    offline = []
    now = datetime.now()
    for user, data in st.session_state.users.items():
        if data.get("role") == "operator":
            last = data.get("last_active")
            if last and (now - last) < timedelta(minutes=15):
                online.append(user)
            else:
                offline.append(user)
    return online, offline

# ================== CATAT LOGIN KE CSV ==================
def log_login(username):
    update_last_active(username)
    
    filename = "login_history.csv"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    role = st.session_state.users.get(username, {}).get("role", "operator")

    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["Waktu Login", "Username", "Role", "Total Login"])

    rows = []
    total = 1
    if os.path.exists(filename):
        with open(filename, "r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            rows = reader[1:] if len(reader) > 1 else []
            for row in rows:
                if row[1] == username:
                    total = int(row[3]) + 1
                    break

    new_row = [now_str, username, role, total]
    rows = [row for row in rows if row[1] != username]
    rows.append(new_row)

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Waktu Login", "Username", "Role", "Total Login"])
        writer.writerows(rows)

# ================== LOGIN PAGE ==================
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
                
                log_login(username)
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

role_display = st.session_state.current_role.upper() if st.session_state.current_role else "USER"
st.markdown(f"**👤 Login sebagai:** `{st.session_state.current_user}` | **Role:** `{role_display}`")

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

# ================== SUPER ADMIN MENU ==================
if st.session_state.current_role == "superadmin":
    with st.sidebar:
        st.header("⚙️ Super Admin Menu")
        menu = st.radio("Pilih Menu", ["📝 PDF Merger", "👥 Kelola Operator", "👥 Operator Online", "📊 Riwayat Login"])
        
        if menu == "👥 Kelola Operator":
            st.subheader("Tambah Operator Baru")
            new_user = st.text_input("Username Operator Baru")
            new_pass = st.text_input("Password Operator Baru", type="password")
            if st.button("Tambahkan Operator", type="primary"):
                if new_user and new_pass and new_user not in st.session_state.users:
                    st.session_state.users[new_user] = {
                        "password": new_pass, 
                        "role": "operator", 
                        "last_active": None
                    }
                    save_users(st.session_state.users)
                    st.success(f"✅ Operator `{new_user}` berhasil ditambahkan!")
                else:
                    st.error("❌ Username sudah ada atau kosong!")

        elif menu == "👥 Operator Online":
            st.subheader("👥 Operator yang Sedang Online")
            online, offline = get_online_users()
            if online:
                st.success(f"🟢 **Sedang Online ({len(online)} orang)**")
                for user in online:
                    st.write(f"✅ **{user}** — Aktif sekarang")
            else:
                st.info("Tidak ada operator yang sedang online")
            if offline:
                st.write("---")
                st.subheader(f"⚪ Offline ({len(offline)} orang)")
                for user in offline:
                    st.write(f"👤 {user}")

        elif menu == "📊 Riwayat Login":
            st.subheader("📊 Riwayat Login Operator")
            if os.path.exists("login_history.csv"):
                df = pd.read_csv("login_history.csv")
                st.dataframe(df, use_container_width=True)
                with open("login_history.csv", "rb") as f:
                    st.download_button(
                        label="📥 Download CSV",
                        data=f,
                        file_name=f"login_history_{datetime.now().strftime('%Y-%m-%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("Belum ada riwayat login.")

# ================== MAIN APP - PDF MERGER ==================
if st.session_state.current_role == "superadmin" and 'menu' in locals() and menu != "📝 PDF Merger":
    st.info("📌 Anda sedang berada di menu Super Admin")
else:
    tab1, tab2 = st.tabs(["📝 Input Manual", "🔢 Range Generator"])

    with tab1:
        st.subheader("Masukkan Nomor Register Tilang")
        nomor_input = st.text_area(
            label="",
            height=200,
            placeholder="I0006928\nG4341343\nB5678901\n\n(Satu nomor per baris)",
            help="Masukkan nomor register satu per baris"
        )

    with tab2:
        st.subheader("🔢 Range Generator")
        col_prefix, col_start, col_end = st.columns([1, 2, 2])
        with col_prefix:
            prefix = st.text_input("Prefix", value="I", max_chars=1)
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
                st.session_state.generated_numbers = "\n".join(generated)

    # ================== PROSES & GABUNGKAN PDF ==================
    st.divider()
    st.subheader("🚀 Proses & Gabungkan PDF")

    default_value = st.session_state.get('generated_numbers', "")
    nomor_input_final = st.text_area(
        label="Nomor yang akan diproses:",
        value=default_value,
        height=150,
        placeholder="Nomor akan muncul di sini..."
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
                                              color=(0,0,0), align=fitz.TEXT_ALIGN_LEFT)

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
