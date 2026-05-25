import pandas as pd
import os
import re

OUTPUT_DIR = 'extracted-sheets'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Tạo chính xác danh sách các file từ 2013 đến 2023 đúng theo cấu trúc của bạn
excel_paths = [f'raw-data/{year}-raw-data.xlsx' for year in range(2013, 2024)]

def extract_sheets(file_path):
    # Lấy số năm trực tiếp từ đường dẫn bằng regex (luôn đúng vì danh sách đã chuẩn hóa)
    year = re.search(r'\d{4}', file_path).group()
    
    # Kiểm tra file có tồn tại thực tế trong thư mục không trước khi đọc
    if not os.path.exists(file_path):
        print(f"⚠️ Bỏ qua: Không tìm thấy file {file_path}")
        return

    try:
        xls = pd.ExcelFile(file_path)

        # Duyệt qua từng tab trong file Excel
        for sheet_name in xls.sheet_names:
            # Chỉ lọc các tab có tên chứa cụm từ 'Daily Traffic Summary'
            if 'daily traffic summary' in sheet_name.lower():
                df = pd.read_excel(xls, sheet_name=sheet_name)
                
                # Format lại tên file: thay khoảng trắng/ký tự đặc biệt bằng dấu gạch dưới
                safe_sheet_name = re.sub(r'[\\/*?:"<>| ]', '_', sheet_name)
                output_file = os.path.join(OUTPUT_DIR, f"{year}-{safe_sheet_name}.csv")
                
                # Xuất file CSV hỗ trợ tiếng Việt
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"✅ Đã xuất: {output_file}")
                
    except Exception as e:
        print(f"❌ Lỗi xử lý file {file_path}: {e}")

# Chạy vòng lặp qua danh sách đường dẫn cấu trúc chuẩn
for path in excel_paths:
    extract_sheets(path)