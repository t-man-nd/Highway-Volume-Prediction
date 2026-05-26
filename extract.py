import os
import re
import pandas as pd
import numpy as np
import openpyxl

RAW_DIR = 'raw-data'
OUTPUT_DIR = 'extracted-sheets'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_daily_traffic_summary_sheets(years, raw_dir, extracted_dir):
    """Extract all Excel sheets containing 'Daily Traffic Summary' to CSV."""
    for year in years:
        file_path = os.path.join(raw_dir, f"{year}-raw-data.xlsx")

        if not os.path.exists(file_path):
            print(f"⚠️ Bỏ qua: Không tìm thấy file {file_path}")
            continue

        try:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                if 'daily traffic summary' in sheet_name.lower():
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    safe_sheet_name = re.sub(r'[\\/*?:"<>| ]', '_', sheet_name)
                    output_file = os.path.join(extracted_dir, f"{year}-{safe_sheet_name}.csv")
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                    print(f"✅ Đã xuất: {output_file}")
        except Exception as e:
            print(f"❌ Lỗi xử lý file {file_path}: {e}")


def create_daily_traffic_summary(file_path, output_path, year, sheet_name=0):
    """Process raw traffic data from Excel or CSV into daily totals."""
    print(f"Processing data for year {year} from file: {file_path}...")

    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=[4, 5])
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=[4, 5])
    except Exception as e:
        print(f"[Error] reading file {file_path}: {e}")
        return

    flat_cols = []
    for col in df.columns:
        lvl0 = str(col[0]) if not pd.isna(col[0]) else ''
        lvl1 = str(col[1]) if not pd.isna(col[1]) else ''
        flat_cols.append((lvl0, lvl1))

    stations = []
    station_col_indices = {}
    for idx, (_, lvl1) in enumerate(flat_cols):
        lvl1_str = str(lvl1).strip()
        if re.match(r'^\d+-\d+$', lvl1_str):
            stations.append(lvl1_str)
            station_col_indices[lvl1_str] = idx

    if not stations:
        print(f"[Warning] No stations found for year {year}. Please check the file structure.")
        return

    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    df.rename(columns={'col_0': 'Month', 'col_1': 'Day', 'col_2': 'DayOfWeek', 'col_3': 'TimeBegin'}, inplace=True)
    df = df[df['TimeBegin'].astype(str).str.contains(':', na=False)].copy()
    df['Month'] = df['Month'].ffill()
    df['Day'] = pd.to_numeric(df['Day'], errors='coerce').ffill()
    df = df.dropna(subset=['Day'])
    df['Day'] = df['Day'].astype(int)

    month_mapping = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    def get_month_num(m):
        if pd.isna(m):
            return 1
        m_str = str(m).strip()
        if m_str.isdigit():
            return int(m_str)
        return month_mapping.get(m_str, 1)

    df['Month_Num'] = df['Month'].apply(get_month_num)
    df['Date'] = df.apply(lambda row: f"{year}-{int(row['Month_Num']):02d}-{int(row['Day']):02d}", axis=1)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

    daily_df = pd.DataFrame({'Date': df['Date'].unique()}).sort_values('Date').reset_index(drop=True)

    for station in stations:
        col_name = f"col_{station_col_indices[station]}"
        station_series = df[col_name].astype(str).str.replace('no data', '', case=False).str.strip()
        station_series = pd.to_numeric(station_series, errors='coerce')

        temp_df = df[['Date']].copy()
        temp_df['Traffic'] = station_series
        grouped = temp_df.groupby('Date').agg(total_traffic=('Traffic', 'sum'), valid_count=('Traffic', 'count'))
        grouped.loc[grouped['valid_count'] == 0, 'total_traffic'] = np.nan
        daily_df = daily_df.merge(grouped[['total_traffic']].rename(columns={'total_traffic': station}), on='Date', how='left')

    daily_df['Date'] = daily_df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    daily_df.fillna('no data', inplace=True)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    daily_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"[Completed] Created file: {output_path}")


if __name__ == "__main__":
    extract_years = range(2015, 2024)
    extract_daily_traffic_summary_sheets(extract_years, RAW_DIR, OUTPUT_DIR)

    years_to_process = [2015, 2016, 2017, 2018]
    target_sheet = "Numbered Highways"

    for year in years_to_process:
        file_path = os.path.join(RAW_DIR, f"{year}-raw-data.xlsx")
        if not os.path.exists(file_path):
            print(f"[Warning] Original file not found: {file_path}")
            continue

        output_csv = os.path.join(OUTPUT_DIR, f"{year}-Daily_Traffic_Summary.csv")
        create_daily_traffic_summary(file_path=file_path, output_path=output_csv, year=year, sheet_name=target_sheet)
