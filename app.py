import pandas as pd
import streamlit as st
from io import BytesIO

# Fungsi untuk mengimpor file Excel atau CSV
def upload_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Format file tidak didukung. Silakan upload file CSV atau Excel.")

# Fungsi untuk memproses data
def process_data(dataregis_df, masterkel_df):
    # Debug: Tampilkan beberapa data pertama dari kedua file
    print("Data Registrasi (dataregis_df):")
    print(dataregis_df.head())  # Debugging line
    print("Data Master Kelurahan (masterkel_df):")
    print(masterkel_df.head())  # Debugging line
    
    # Melakukan join antara dataregis dan masterkel dengan pandas
    merged_df = pd.merge(dataregis_df, masterkel_df, how='left', 
                         left_on='full_address', right_on='kelurahan', 
                         suffixes=('_dr', '_mk'))

    # Debug: Tampilkan beberapa baris setelah merge
    print("Data Setelah Merge:")
    print(merged_df.head())  # Debugging line

    # Menambahkan kolom yang sesuai dengan ROW_NUMBER pada SQL menggunakan pandas
    merged_df['rn'] = merged_df.groupby('no_polisi').cumcount() + 1

    # Debug: Tampilkan beberapa baris setelah penambahan kolom 'rn'
    print("Data Setelah Menambahkan Kolom 'rn':")
    print(merged_df.head())  # Debugging line

    # Memilih hanya baris dengan rn = 1 untuk setiap no_polisi
    result_df = merged_df[merged_df['rn'] == 1]

    # Debug: Tampilkan hasil akhir sebelum mengembalikan
    print("Data Hasil Seleksi (rn = 1):")
    print(result_df.head())  # Debugging line

    # Hapus kolom rn setelah proses selesai
    result_df = result_df.drop(columns=['rn'])

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

            # Proses data tanpa PostgreSQL
            result_df = process_data(dataregis_df, masterkel_df)

            if result_df.empty:
                st.write("Hasil proses data kosong.")
            else:
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

# Jalankan aplikasi S
