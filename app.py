import streamlit as st
import requests
import pandas as pd
import base64

# ==========================================
# KONFIGURASI API
# ==========================================
API_URL = "https://script.google.com/macros/s/AKfycbx0TisI1nrnQXEFwZ7I8cbXg-H2Ys4NFh8QjQIBUISZQ3_K4EqaN1V87QOqwvkjEhNbNQ/exec" # MASUKKAN URL WEB APP ANDA

st.set_page_config(page_title="Dashboard SMAN 3 Sukabumi", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .metric-card {background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; border-top: 4px solid #0d6efd;}
    .metric-value {font-size: 1.8rem; font-weight: bold; color: #1e3d59;}
    .jenjang-card {background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    div[data-testid="stDialog"] { width: 500px !important; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI SINKRONISASI DATA ---
def fetch_data():
    with st.spinner("Menyinkronkan data dengan database..."):
        try:
            res = requests.get(f"{API_URL}?action=getDashboard")
            if res.status_code == 200 and res.json()['success']:
                st.session_state.data = res.json()['data']
                return True
        except Exception: pass
    return False

# --- SESSION & LOGIN PERSISTENCE ---
if 'logged_in' not in st.session_state:
    if st.query_params.get("logged_in") == "true":
        st.session_state.logged_in = True
        st.session_state.user_name = st.query_params.get("user", "Admin")
        if 'data' not in st.session_state: fetch_data()
    else:
        st.session_state.logged_in = False
        st.session_state.user_name = ""

if 'nav' not in st.session_state: st.session_state.nav = "Dashboard Utama"
if 'filter_kelas' not in st.session_state: st.session_state.filter_kelas = None

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🎓 SMAN 3 Sukabumi</h2><hr>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True, type="primary"):
            res = requests.get(f"{API_URL}?action=login&username={username}&password={password}")
            if res.status_code == 200 and res.json()['success']:
                st.session_state.logged_in, st.session_state.user_name = True, res.json()['name']
                st.query_params["logged_in"] = "true"
                st.query_params["user"] = st.session_state.user_name
                fetch_data()
                st.rerun()
            else: st.error("Username atau Password Salah.")
    st.stop()

data = st.session_state.data

# --- DIALOGS (POP-UP MODALS) ---
@st.dialog("👁️ Detail Siswa Lengkap")
def modal_detail(row):
    st.markdown(f"### {row['nama']}")
    c1, c2 = st.columns(2)
    c1.write(f"**NIPD:** {row['nipd']}")
    c1.write(f"**NISN:** {row['nisn']}")
    c1.write(f"**Jenis Kelamin:** {'Laki-laki' if row['jk']=='L' else 'Perempuan'}")
    c2.write(f"**Kelas:** {row['rombel']}")
    c2.write(f"**Agama:** {row.get('agama','-')}")
    c2.write(f"**Tempat, Tgl Lahir:** {row.get('tmpLahir','-')}, {row.get('tglLahir','-')}")
    st.write(f"**Alamat:** {row.get('alamat','-')}")
    if st.button("Tutup"): st.rerun()

@st.dialog("✏️ Edit Data Siswa")
def modal_edit(row):
    e_nama = st.text_input("Nama Siswa", row['nama'])
    c1, c2 = st.columns(2)
    e_nipd = c1.text_input("NIPD", row['nipd'])
    e_nisn = c2.text_input("NISN", row['nisn'])
    e_jk = c1.selectbox("Jenis Kelamin", ["L", "P"], index=0 if row['jk']=="L" else 1)
    e_rombel = c2.selectbox("Rombel", data['rombels'], index=data['rombels'].index(row['rombel']) if row['rombel'] in data['rombels'] else 0)
    if st.button("Simpan Perubahan", type="primary"):
        payload = {"action": "updateStudent", "rowIndex": row['rowIndex'], "data": {"nama": e_nama.upper(), "nipd": e_nipd, "jk": e_jk, "nisn": e_nisn, "rombel": e_rombel}}
        if requests.post(API_URL, json=payload).json()['success']:
            st.success("Tersimpan!"); fetch_data(); st.rerun()

@st.dialog("🗑️ Hapus Siswa")
def modal_delete(row):
    st.error(f"Anda yakin ingin menghapus data **{row['nama']}**?")
    if st.button("Ya, Hapus!", type="primary"):
        if requests.post(API_URL, json={"action": "deleteStudent", "rowIndex": row['rowIndex']}).json()['success']:
            fetch_data(); st.rerun()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title(f"👨‍💼 {st.session_state.user_name}")
menus = ["Dashboard Utama", "Manajemen Data Siswa", "Cetak Absensi", "Mutasi & Pindah Kelas"]
selected_nav = st.sidebar.radio("Menu Navigasi", menus, index=menus.index(st.session_state.nav) if st.session_state.nav in menus else 0)
st.session_state.nav = selected_nav
st.sidebar.write("---")
if st.sidebar.button("Muat Ulang Data 🔄", use_container_width=True): fetch_data(); st.rerun()
if st.sidebar.button("Logout 🚪", use_container_width=True):
    st.session_state.clear(); st.query_params.clear(); st.rerun()

# ==========================================
# HALAMAN 1: DASHBOARD UTAMA
# ==========================================
if st.session_state.nav == "Dashboard Utama":
    st.title("📊 Dashboard Utama & Rekapitulasi")
    sum_data = data['summary']
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'>Total Keseluruhan<div class='metric-value'>{sum_data['totalSiswa']}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'>Total Rombel<div class='metric-value'>{sum_data['totalRombel']}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'>Siswa Laki-laki<div class='metric-value' style='color:#0d6efd'>{sum_data['totalL']}</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'>Siswa Perempuan<div class='metric-value' style='color:#d63384'>{sum_data['totalP']}</div></div>", unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    st.subheader("📌 Rekapitulasi per Jenjang")
    jc, cols = sum_data['jenjangCount'], st.columns(3)
    for i, j in enumerate(["10", "11", "12"]):
        if j in jc:
            cols[i].markdown(f"<div class='jenjang-card'><h4 style='color:#198754'>JENJANG KELAS {'X' if j=='10' else 'XI' if j=='11' else 'XII'}</h4><h2 style='margin:0;'>{jc[j]['total']}</h2><p style='color:#6c757d; margin:0;'>Laki-laki: <b>{jc[j]['L']}</b> | Perempuan: <b>{jc[j]['P']}</b></p></div>", unsafe_allow_html=True)

    st.write("---")
    html_rekap = f"""
    <html><body style="font-family:Arial; font-size:12px;">
    <h3 style="text-align:center;">REKAPITULASI KELAS SMAN 3 KOTA SUKABUMI</h3>
    <table border="1" cellpadding="6" cellspacing="0" width="100%" style="border-collapse: collapse; text-align:center;">
        <tr style="background-color:#f0f0f0;"><th>Kelas</th><th>Wali Kelas</th><th>Laki-laki</th><th>Perempuan</th><th>Total Siswa</th></tr>
    """
    g_L, g_P, g_T = 0, 0, 0
    for j_kode, j_label in [("10", "X"), ("11", "XI"), ("12", "XII")]:
        sub_L, sub_P, sub_T = 0, 0, 0
        kelas_in_jenjang = sorted([k for k in sum_data['kelasCount'].keys() if k.startswith(j_kode)])
        for cls in kelas_in_jenjang:
            c = sum_data['kelasCount'][cls]
            html_rekap += f"<tr><td>{cls}</td><td style='text-align:left;'>{sum_data['walasMap'].get(cls, '-')}</td><td>{c['L']}</td><td>{c['P']}</td><td><b>{c['total']}</b></td></tr>"
            sub_L += c['L']; sub_P += c['P']; sub_T += c['total']
        if sub_T > 0:
            html_rekap += f"<tr style='background-color:#d1e7dd; font-weight:bold;'><td colspan='2'>JUMLAH KELAS {j_label}</td><td>{sub_L}</td><td>{sub_P}</td><td>{sub_T}</td></tr>"
            g_L += sub_L; g_P += sub_P; g_T += sub_T
            
    html_rekap += f"<tr style='background-color:#0f5132; color:white; font-weight:bold;'><td colspan='2'>TOTAL KESELURUHAN</td><td>{g_L}</td><td>{g_P}</td><td>{g_T}</td></tr>"
    html_rekap += "</table></body></html>"
    
    b64 = base64.b64encode(html_rekap.encode()).decode()
    st.markdown(f'<a href="data:text/html;base64,{b64}" download="Rekap_Jenjang_Kelas.html"><button style="padding:10px; background:#198754; color:white; border:none; border-radius:5px; cursor:pointer;">📥 Cetak Rekapitulasi per Jenjang (PDF/HTML)</button></a>', unsafe_allow_html=True)
    
# ==========================================
# HALAMAN 2: MANAJEMEN DATA SISWA 
# ==========================================
elif st.session_state.nav == "Manajemen Data Siswa":
    st.title("👥 Manajemen Data Siswa")
    
    df_siswa = pd.DataFrame(data['siswa']).sort_values(by="nama", ascending=True).reset_index(drop=True)
    def_idx = data['rombels'].index(st.session_state.filter_kelas) if st.session_state.filter_kelas in data['rombels'] else 0
    selected_kelas = st.selectbox("📌 Filter berdasarkan Kelas", data['rombels'], index=def_idx)
    st.session_state.filter_kelas = selected_kelas
    
    df_filtered = df_siswa[df_siswa['rombel'] == selected_kelas]
    search = st.text_input("🔍 Cari Nama (Otomatis Kapital) atau NISN...")
    if search: df_filtered = df_filtered[df_filtered['nama'].str.contains(search.upper(), case=False, na=False) | df_filtered['nisn'].astype(str).str.contains(search, na=False)]

    st.write("---")
    hcols = st.columns([0.5, 1.5, 3, 0.5, 1.5])
    for i, h in enumerate(["No", "NIPD / NISN", "Nama Siswa", "L/P", "Aksi"]): hcols[i].markdown(f"**{h}**")
    st.markdown("<hr style='margin:0; padding:0; margin-bottom:10px'>", unsafe_allow_html=True)

    for i, row in enumerate(df_filtered.to_dict('records')):
        cols = st.columns([0.5, 1.5, 3, 0.5, 1.5])
        cols[0].write(str(i+1))
        cols[1].write(f"{row['nipd']} / {row['nisn']}")
        cols[2].write(row['nama']) 
        cols[3].write(row['jk'])
        
        b1, b2, b3 = cols[4].columns([1, 1, 1])
        if b1.button("👁️", key=f"d_{row['rowIndex']}"): modal_detail(row)
        if b2.button("✏️", key=f"e_{row['rowIndex']}"): modal_edit(row)
        if b3.button("🗑️", key=f"del_{row['rowIndex']}"): modal_delete(row)
        st.markdown("<hr style='margin:0; padding:0; margin-bottom:5px; margin-top:5px; opacity:0.3'>", unsafe_allow_html=True)

# ==========================================
# HALAMAN 3: CETAK ABSENSI F4
# ==========================================
elif st.session_state.nav == "Cetak Absensi":
    st.title("🖨️ Cetak Absensi (1 Lembar F4)")
    
    col1, col2 = st.columns(2)
    p_kelas = col1.selectbox("Pilih Kelas", data['rombels'])
    p_bulan = col2.selectbox("Bulan", ["Juli", "Agustus", "September", "Oktober", "November", "Desember", "Januari", "Februari", "Maret", "April", "Mei", "Juni"])
    
    if st.button("Proses Dokumen Cetak (F4)"):
        res = requests.get(f"{API_URL}?action=getAbsensi&rombel={p_kelas}").json()
        students = res['data']['students']
        walas = res['data']['walas']
        walas_nip = res['data'].get('walasNip', '-') # NIP Baru
        
        html_absen = f"""
        <html>
        <head>
        <style>
            @page {{ size: 215.9mm 330.2mm; margin: 5mm; }} /* F4 Paper Size */
            body {{ font-family: Arial, sans-serif; font-size: 10px; margin: 0; }}
            .header {{ text-align: center; font-weight: bold; margin-bottom: 15px; line-height: 1.1; font-size: 12px; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
            th, td {{ border: 1px solid black; padding: 3px; text-align: center; overflow: hidden; }}
            .text-nowrap {{ white-space: nowrap; text-overflow: clip; }}
        </style>
        </head>
        <body>
            <table style="width: 100%; border: none; border-bottom: 2px solid black; margin-bottom: 10px;">
                <tr>
                    <td style="width: 15%; border: none; text-align: center; vertical-align: middle;">
                        <!-- Masukkan Direct Link Google Drive Anda pada atribut src di bawah ini -->
                        <img src="https://drive.google.com/uc?export=view&id=1iRhKSF6LNfIKJkBwo5SJO63hlErfCU4y" width="75">
                    </td>
                    <td style="width: 85%; border: none; text-align: center; vertical-align: middle; line-height: 1.2;">
                        <span style="font-weight: bold; font-size: 13px;">PEMERINTAH DAERAH PROVINSI JAWA BARAT<br>
                        DINAS PENDIDIKAN - CABANG DINAS PENDIDIKAN WILAYAH V<br>
                        SEKOLAH MENENGAH ATAS NEGERI 3 SUKABUMI</span><br>
                        <span style="font-weight: normal; font-size:10px;">Jalan Ciaul Baru No. 21 Kota Sukabumi-43116 Telp. (0266) 221453<br>E-mail : smanegeri3kotasukabumi@gmail.com</span>
                    </td>
                </tr>
            </table>
            
            <div style="text-align: center; font-weight: bold; font-size: 12px; margin-bottom: 15px;">
                DAFTAR KEHADIRAN SISWA<br>TAHUN PELAJARAN 2026-2027
            </div>
            <table style="border:none; text-align:left; font-weight:bold; margin-bottom:5px; font-size:11px;">
                <tr><td style="border:none; padding:0; width:50%;">Program/Kelas : {p_kelas}</td>
                <td style="border:none; padding:0; text-align:right;">Bulan : {p_bulan}</td></tr>
            </table>
            <table>
                <thead>
                    <tr>
                        <th rowspan="2" style="width:25px; font-size:10px;">No</th>
                        <th rowspan="2" style="width:110px;font-size:10px;" class="text-nowrap">No. Induk / NISN</th>
                        <th rowspan="2" style="width:250px;font-size:10px;" class="text-nowrap">Nama Peserta Didik</th>
                        <th rowspan="2" style="width:25px;font-size:10px;">L/P</th>
                        <th colspan="6" style="font-size:10px;">Tanggal</th>
                        <th colspan="3" style="font-size:10px;">Absensi</th>
                        <th rowspan="2" style="font-size:10px;">Jml<br>A+S+I</th>
                    </tr>
                    <tr>
                        <th>&nbsp;&nbsp;</th><th>&nbsp;&nbsp;</th><th>&nbsp;&nbsp;</th>
                        <th>&nbsp;&nbsp;</th><th>&nbsp;&nbsp;</th><th>&nbsp;&nbsp;</th>
                        <th style="width:15px;font-size:10px;">A</th><th style="width:15px;font-size:10px;">S</th><th style="width:15px;font-size:10px;">I</th>
                    </tr>
                </thead>
                <tbody>
        """
        for i, s in enumerate(students):
            # Memaksa 1 baris
            html_absen += f"<tr><td style='font-size:10px;'>{i+1}</td><td class='text-nowrap' style='font-size:9.5px;'>{s['nipd']} / {s['nisn']}</td><td style='text-align:left; font-size:10px;' class='text-nowrap'>{s['nama']}</td><td style='font-size:10px;'>{s['jk']}</td>"
            html_absen += "<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>"
            
        html_absen += f"""
                </tbody>
            </table>
            <br>
            <table style="border:none; text-align:center; margin-top:5px;">
                <tr>
                    <td style="border:none; text-align:left; vertical-align:top;font-size:10px;"><b>Keterangan:</b><br>Laki-laki: {sum([1 for s in students if s['jk']=='L'])}<br>Perempuan: {sum([1 for s in students if s['jk']=='P'])}<br>Jumlah: {len(students)}</td>
                    <td style="border:none; vertical-align:top;font-size:10px;">Mengetahui,<br>Kepala SMAN 3 Kota Sukabumi<br><br><br><br><b>Dr. Dudung Koswara, M.Pd</b><br>NIP. 196806061991031012</td>
                    <td style="border:none; vertical-align:top;font-size:10px;">Sukabumi, ........................<br>Wali Kelas<br><br><br><br><b>{walas}</b><br>NIP. {walas_nip}</td>
                </tr>
            </table>
        </body></html>
        """
        b64 = base64.b64encode(html_absen.encode()).decode()
        st.success("Berhasil! Layout 1 Baris (Satu Kolom) disesuaikan untuk Kertas F4.")
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Absensi_F4_{p_kelas}_{p_bulan}.html"><button style="padding:10px; background:#0d6efd; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">📥 Cetak Absensi Vertikal F4</button></a>', unsafe_allow_html=True)

# ==========================================
# HALAMAN 4: MUTASI & PINDAH KELAS
# ==========================================
elif st.session_state.nav == "Mutasi & Pindah Kelas":
    st.title("🔄 Rekap Mutasi & Pindah Kelas")
    
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Total Mutasi Masuk:** {len(data['mutasiMasuk'])} Siswa")
    c2.error(f"**Total Mutasi Keluar:** {len(data['mutasiKeluar'])} Siswa")
    c3.success(f"**Total Riwayat Pindah:** {len(data['riwayatPindah'])} Siswa")
    
    st.write("---")
    t1, t2, t3 = st.tabs(["➡️ Pindah Kelas & Riwayat", "📥 Mutasi Masuk", "📤 Mutasi Keluar"])
    
    with t1:
        st.subheader("📝 Formulir Pindah / Naik Kelas")
        df = pd.DataFrame(data['siswa']).sort_values('nama')
        siswa_list = df['nama'] + " (" + df['rombel'] + ") - " + df['nisn'].astype(str)
        p_siswa = st.selectbox("Pilih Siswa", siswa_list, key="p_siswa")
        p_rombel_baru = st.selectbox("Pindah ke Rombel", data['rombels'], key="p_rombel")
        
        if st.button("Proses Pindah Kelas", type="primary"):
            row_data = df.iloc[siswa_list.tolist().index(p_siswa)]
            payload = {"action": "pindahKelas", "data": {"rowIndex": int(row_data['rowIndex']), "nama": row_data['nama'], "nisn": row_data['nisn'], "kelasAsal": row_data['rombel'], "kelasTujuan": p_rombel_baru}}
            if requests.post(API_URL, json=payload).json()['success']:
                st.success("Berhasil dipindahkan & dicatat di Riwayat!"); fetch_data(); st.rerun()

        st.markdown("#### 📂 Tabel Riwayat Pindah Kelas")
        if len(data['riwayatPindah']) > 0:
            st.dataframe(pd.DataFrame(data['riwayatPindah'], columns=["No", "Tanggal", "NISN", "Nama", "Kelas Asal", "Kelas Tujuan"]).drop(columns=["No"]), use_container_width=True)
        else: st.info("Belum ada riwayat pindah kelas.")
    
    with t2:
        st.subheader("📥 Formulir Mutasi Masuk (Otomatis Masuk Master)")
        with st.form("f_masuk"):
            c1, c2 = st.columns(2)
            m_nama = c1.text_input("Nama Siswa").upper()
            m_jk = c2.selectbox("L/P", ["L", "P"])
            m_nis = c1.text_input("NIPD/NIS")
            m_nisn = c2.text_input("NISN")
            m_asal = c1.text_input("Asal Sekolah")
            m_kelas = c2.selectbox("Masuk ke Kelas", data['rombels'])
            m_tgl = c1.date_input("Tanggal Masuk")
            m_alasan = st.text_input("Alasan Masuk")
            if st.form_submit_button("Simpan Data Mutasi Masuk"):
                payload = {"action": "addMutasiMasuk", "data": {"nama":m_nama, "jk":m_jk, "nis":m_nis, "nisn":m_nisn, "asal":m_asal, "kelas":m_kelas, "tgl":str(m_tgl), "alasan":m_alasan}}
                requests.post(API_URL, json=payload)
                st.success("Mutasi Tercatat! Siswa baru telah ditambahkan ke Data Siswa."); fetch_data(); st.rerun()
                
        st.markdown("#### 📂 Tabel Mutasi Masuk")
        if len(data['mutasiMasuk']) > 0:
            st.dataframe(pd.DataFrame(data['mutasiMasuk'], columns=["No Urut", "No Absen", "NIS", "NISN", "Nama", "L/P", "Asal Sekolah", "Tgl", "Di Kelas", "Alasan", "Validasi"]).drop(columns=["No Absen", "Validasi"], errors='ignore'), use_container_width=True)
        else: st.info("Belum ada data mutasi masuk.")

    with t3:
        st.subheader("📤 Formulir Mutasi Keluar (Otomatis Hapus dari Master)")
        df_k = pd.DataFrame(data['siswa']).sort_values('nama')
        siswa_keluar_list = df_k['nama'] + " (" + df_k['rombel'] + ") - " + df_k['nisn'].astype(str)
        k_siswa = st.selectbox("Pilih Siswa yang Keluar", siswa_keluar_list, key="k_siswa")
        k_tujuan = st.text_input("Pindah Ke (Sekolah Tujuan)")
        k_tgl = st.date_input("Tanggal Keluar")
        k_alasan = st.text_input("Sebab-sebab Keluar")
        
        if st.button("Proses Mutasi Keluar", type="primary"):
            row_data = df_k.iloc[siswa_keluar_list.tolist().index(k_siswa)]
            payload = {"action": "addMutasiKeluar", "data": {"rowIndex": int(row_data['rowIndex']), "nama":row_data['nama'], "jk":row_data['jk'], "nis":row_data['nipd'], "nisn":row_data['nisn'], "kelas_asal":row_data['rombel'], "pindah_ke":k_tujuan, "tgl":str(k_tgl), "alasan":k_alasan}}
            requests.post(API_URL, json=payload)
            st.success("Tercatat di Mutasi Keluar! Siswa otomatis DIHAPUS dari master Data Siswa."); fetch_data(); st.rerun()
            
        st.markdown("#### 📂 Tabel Mutasi Keluar")
        if len(data['mutasiKeluar']) > 0:
            st.dataframe(pd.DataFrame(data['mutasiKeluar'], columns=["No Urut", "No Absen", "NIS", "NISN", "Nama", "L/P", "Pindah Ke", "Tgl", "Kelas Asal", "Sebab Keluar", "Validasi"]).drop(columns=["No Absen", "Validasi"], errors='ignore'), use_container_width=True)
        else: st.info("Belum ada data mutasi keluar.")
