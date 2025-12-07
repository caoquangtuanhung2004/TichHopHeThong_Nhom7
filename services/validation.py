# services/validation.py

def validate_attendance_data(data):
    """
    Validate dữ liệu chấm công (chỉ kiểm tra format và bắt buộc).
    Không kết nối cơ sở dữ liệu.
    Trả về: (is_valid: bool, message: str)
    """
    if not isinstance(data, dict):
        return False, "Dữ liệu phải là object JSON."

    # Các trường bắt buộc: EmployeeID và CheckIn
    required_fields = ["EmployeeID", "CheckIn"]
    for field in required_fields:
        if field not in data or data[field] in (None, "", "null"):
            return False, f"Thiếu trường bắt buộc: {field}"

    # Kiểm tra EmployeeID không rỗng
    emp_id = str(data["EmployeeID"]).strip()
    if not emp_id:
        return False, "EmployeeID không được để trống."

    # Kiểm tra CheckIn có vẻ hợp lệ (ít nhất phải có độ dài hợp lý)
    check_in = data["CheckIn"]
    if not isinstance(check_in, str) or len(check_in) < 10:
        return False, "CheckIn không hợp lệ (phải là chuỗi thời gian)."

    # CheckOut không bắt buộc, nhưng nếu có thì phải là string
    check_out = data.get("CheckOut")
    if check_out is not None:
        if not isinstance(check_out, str):
            return False, "CheckOut phải là chuỗi thời gian (hoặc null)."

    return True, "OK"