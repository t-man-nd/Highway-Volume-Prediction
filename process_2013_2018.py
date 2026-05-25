import pandas as pd
import numpy as np
import os

def create_daily_traffic_summary(file_path, output_path, year, sheet_name=0):
    """
    Xử lý dữ liệu trực tiếp từ file Excel (hoặc CSV).
    Nếu truyền vào file Excel, cần chỉ định tên sheet chứa dữ liệu (mặc định lấy sheet đầu tiên).
    """
    print(f"Dang xu ly du lieu nam {year} tu file: {file_path}...")
    
    # 1. Đọc file, bỏ qua 4 dòng tiêu đề rác ở đầu
    # Dòng số 5 và 6 trong file đóng vai trò là Header (Multi-index)
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=[4, 5])
        else:
            # Nếu là file Excel
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=[4, 5])
    except Exception as e:
        print(f"[Loi] khi doc file {file_path}: {e}")
        return
    
    # Chuẩn hóa tên cột để dễ thao tác (Gộp 2 dòng tiêu đề thành 1)
    flat_cols = []
    for col in df.columns:
        lvl0 = str(col[0]) if not pd.isna(col[0]) else ''
        lvl1 = str(col[1]) if not pd.isna(col[1]) else ''
        flat_cols.append((lvl0, lvl1))
    
    # Tìm tất cả các Trạm ID duy nhất
    stations = []
    station_col_indices = {} 
    
    for idx, (lvl0, lvl1) in enumerate(flat_cols):
        # Nếu cột này chứa ID trạm và cột kế bên nó là 'monthly'
        if '-' in lvl1 and idx + 1 < len(flat_cols) and 'monthly' in flat_cols[idx+1][1].lower():
            stations.append(lvl1)
            station_col_indices[lvl1] = idx

    if not stations:
        print(f"[Canh bao] Khong tim thay tram nao cho nam {year}. Vui long kiem tra lai cau truc file.")
        return

    # 2. Bóc tách và làm sạch dữ liệu thô
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    df.rename(columns={'col_0': 'Month', 'col_1': 'Day', 'col_2': 'DayOfWeek', 'col_3': 'TimeBegin'}, inplace=True)
    
    # Chỉ giữ lại các hàng có dữ liệu giờ thực tế (chứa ký tự ':')
    df = df[df['TimeBegin'].astype(str).str.contains(':', na=False)].copy()
    
    # Điền đầy đủ tên Tháng xuống các hàng trống
    df['Month'] = df['Month'].ffill()
    df['Day'] = pd.to_numeric(df['Day'], errors='coerce').ffill()
    
    # Bỏ qua các dòng không có ngày hợp lệ
    df = df.dropna(subset=['Day'])
    df['Day'] = df['Day'].astype(int)
    
    month_mapping = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    # Xử lý trường hợp tháng đã là số
    def get_month_num(m):
        if pd.isna(m): return 1
        m_str = str(m).strip()
        if m_str.isdigit(): return int(m_str)
        return month_mapping.get(m_str, 1)

    df['Month_Num'] = df['Month'].apply(get_month_num)
    
    # Tạo cột 'Date'
    df['Date'] = df.apply(lambda row: f"{year}-{int(row['Month_Num']):02d}-{int(row['Day']):02d}", axis=1)
    # Xử lý các ngày không hợp lệ (vd 29/2 năm không nhuận) nếu có
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # 3. Trích xuất và gom tổng
    daily_data = {'Date': df['Date'].unique()}
    daily_df = pd.DataFrame(daily_data).sort_values('Date').reset_index(drop=True)
    
    for station in stations:
        col_idx = station_col_indices[station]
        col_name = f"col_{col_idx}"
        
        station_series = df[col_name].copy()
        station_series = station_series.astype(str).str.replace('no data', '', case=False).str.strip()
        station_series = pd.to_numeric(station_series, errors='coerce')
        
        temp_df = df[['Date']].copy()
        temp_df['Traffic'] = station_series
        
        grouped = temp_df.groupby('Date').agg(
            total_traffic=('Traffic', 'sum'),
            valid_count=('Traffic', 'count')
        )
        
        grouped.loc[grouped['valid_count'] == 0, 'total_traffic'] = np.nan
        daily_df = daily_df.merge(grouped[['total_traffic']].rename(columns={'total_traffic': station}), on='Date', how='left')
    
    daily_df['Date'] = daily_df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    daily_df.fillna('no data', inplace=True)
    
    # 4. Xuất ra file
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    daily_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"[Hoan thanh] Da tao file: {output_path}")

# ==========================================
# CHẠY TỰ ĐỘNG CHO CÁC NĂM TỪ 2013 ĐẾN 2018
# ==========================================
if __name__ == "__main__":
    # Danh sách các năm cần xử lý (bạn viết nhầm 1016 thành 2016)
    years_to_process = [2013, 2014, 2015, 2016, 2017, 2018]
    
    # Thư mục chứa dữ liệu thô và thư mục xuất kết quả
    raw_dir = "raw-data"
    out_dir = "extracted-sheets"
    
    # Giả định dữ liệu nằm ở sheet có tên 'Numbered Highways' (dựa trên tên file bạn cung cấp)
    # Nếu file Excel cũ của bạn chỉ có 1 sheet, hoặc tên khác, bạn có thể chỉnh lại biến này
    target_sheet = "Numbered Highways" 
    
    for year in years_to_process:
        file_path = os.path.join(raw_dir, f"{year}-raw-data.xlsx")
        
        if not os.path.exists(file_path):
            print(f"[Canh bao] Khong tim thay file goc: {file_path}")
            continue
            
        output_csv = os.path.join(out_dir, f"Daily_Traffic_Summary_{year}.csv")
        
        # Gọi hàm xử lý (Đọc trực tiếp từ file Excel)
        create_daily_traffic_summary(
            file_path=file_path, 
            output_path=output_csv, 
            year=year, 
            sheet_name=target_sheet
        )
