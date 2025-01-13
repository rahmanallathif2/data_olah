import pandas as pd
import streamlit as st
import sqlite3
from io import BytesIO

# Fungsi untuk menggabungkan string menggunakan CONCAT
def concat(*args):
    return ''.join(str(arg) for arg in args if arg)

# Fungsi untuk mengimpor file Excel atau CSV
def upload_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Format file tidak didukung. Silakan upload file CSV atau Excel.")

# Fungsi untuk memproses data menggunakan query SQL
def process_data(dataregis_df, masterkel_df):
    # Membuat koneksi SQLite lokal
    conn = sqlite3.connect(':memory:')  # Database lokal di memori
    conn.create_function("CONCAT", -1, concat)  # Menambahkan fungsi CONCAT
    cursor = conn.cursor()

    # Membuat tabel sementara di SQLite untuk dataregis dan masterkel
    dataregis_df.to_sql('dataregis', conn, index=False, if_exists='replace')
    masterkel_df.to_sql('masterkel', conn, index=False, if_exists='replace')

    # Menjalankan query SQL
    query = """
    WITH MatchedData AS (
        SELECT 
            dr.no_polisi,
            dr.full_address,
            dr.kd_camat,
            dr.kecamatan,
            dr.nm_merek_kb,
            dr.nm_model_kb,
            dr.kd_jenis_kb,
            dr.jenis_kendaraan,
            dr.th_buatan,
            dr.no_chasis,
            dr.no_mesin,
            dr.warna_kb,
            dr.tg_pros_bayar,
            mk.kelurahan AS kelurahan_masterkel,
            mk.kecamatan AS kecamatan_masterkel,
            mk.kelurahan_master AS kelurahan_master,
            mk.kecamatan_master AS kecamatan_master,
            ROW_NUMBER() OVER (PARTITION BY dr.no_polisi ORDER BY dr.no_polisi) AS rn
        FROM dataregis dr
        LEFT JOIN masterkel mk 
           ON dr.full_address LIKE CONCAT('%', mk.kelurahan, '%')
    )
    SELECT *
    FROM MatchedData
    WHERE rn = 1;
    """
    result_df = pd.read_sql(query, conn)
    conn.close()
    return result_df

# Fungsi untuk menyimpan dataframe ke Excel dan membuat link unduh
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Hasil Proses')
    processed_data = output.getvalue()
    return processed_data

# Fungsi utama untuk menjalankan aplikasi Streamlit
def main():
    st.title("Aplikasi Pengolahan Data")

    # Upload file dataregis dan master kelurahan
    dataregis_file = st.file_uploader("Upload file dataregis (CSV atau Excel)", type=["csv", "xlsx"])
    masterkel_file = st.file_uploader("Upload file masterkel (CSV atau Excel)", type=["csv", "xlsx"])

    if dataregis_file is not None and masterkel_file is not None:
        try:
            dataregis_df = upload_file(dataregis_file)
            masterkel_df = upload_file(masterkel_file)

            st.write("Kolom pada file dataregis:", dataregis_df.columns)
            st.write("Kolom pada file masterkel:", masterkel_df.columns)

            result_df = process_data(dataregis_df, masterkel_df)

            st.write("Hasil Proses Data:")
            st.write(result_df)

            # Tombol untuk mengunduh hasil dalam format Excel
            excel_data = to_excel(result_df)
            st.download_button(
                label="Unduh Hasil dalam Format Excel",
                data=excel_data,
                file_name="hasil_proses_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# Jalankan aplikasi Streamlit
if __name__ == "__main__":
    main()
