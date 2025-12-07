# routes/attendance.py
from flask import Blueprint, render_template, jsonify, request
from config.mysql_connection import get_mysql_conn
from services.logging_service import logger
import re

attendance_app = Blueprint('attendance', __name__, template_folder='../templates')


# ========================
# 1. ROUTE HIỂN THỊ GIAO DIỆN (HTML) — CÓ DỮ LIỆU THẬT
# ========================

@attendance_app.route('/attendance/summary')
def attendance_summary_page():
    """Hiển thị trang tổng hợp chấm công"""
    conn = None
    try:
        conn = get_mysql_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.id, a.EmployeeID, a.CheckIn, a.CheckOut, a.Status, a.Note,
                   e.EmployeeName
            FROM attendance a
            LEFT JOIN employees e ON a.EmployeeID = e.EmployeeID
            ORDER BY a.CheckIn DESC
            LIMIT 100
        """)
        records = cursor.fetchall()
        return render_template('attendance_summary.html', records=records)
    except Exception as e:
        logger.error(f"Lỗi khi tải tổng hợp chấm công: {str(e)}")
        return render_template('attendance_summary.html', records=[], error="Không thể tải dữ liệu chấm công.")
    finally:
        if conn:
            conn.close()


@attendance_app.route('/attendance/detail/<employee_id>/<date>')
def attendance_detail_page(employee_id, date):
    """Hiển thị chi tiết chấm công của nhân viên vào ngày cụ thể"""
    conn = None
    try:
        conn = get_mysql_conn()
        cursor = conn.cursor(dictionary=True)
        # Lấy thông tin nhân viên
        cursor.execute("SELECT EmployeeName FROM employees WHERE EmployeeID = %s", (employee_id,))
        emp = cursor.fetchone()
        employee_name = emp['EmployeeName'] if emp else employee_id

        # Lấy các bản ghi chấm công trong ngày
        cursor.execute("""
            SELECT * FROM attendance
            WHERE EmployeeID = %s AND DATE(CheckIn) = %s
            ORDER BY CheckIn ASC
        """, (employee_id, date))
        records = cursor.fetchall()

        return render_template('attendance_detail.html',
                               employee_id=employee_id,
                               employee_name=employee_name,
                               date=date,
                               records=records)
    except Exception as e:
        logger.error(f"Lỗi chi tiết chấm công: {str(e)}")
        return render_template('attendance_detail.html',
                               employee_id=employee_id,
                               employee_name=employee_id,
                               date=date,
                               records=[],
                               error="Lỗi khi tải dữ liệu.")
    finally:
        if conn:
            conn.close()


@attendance_app.route('/attendance/update/<employee_id>/<date>')
def attendance_update_page(employee_id, date):
    """Hiển thị form cập nhật chấm công"""
    conn = None
    try:
        conn = get_mysql_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT EmployeeName FROM employees WHERE EmployeeID = %s", (employee_id,))
        emp = cursor.fetchone()
        employee_name = emp['EmployeeName'] if emp else employee_id

        # Lấy bản ghi đầu tiên trong ngày (để điền sẵn vào form)
        cursor.execute("""
            SELECT * FROM attendance
            WHERE EmployeeID = %s AND DATE(CheckIn) = %s
            ORDER BY CheckIn ASC
            LIMIT 1
        """, (employee_id, date))
        record = cursor.fetchone()

        return render_template('attendance_update.html',
                               employee_id=employee_id,
                               employee_name=employee_name,
                               date=date,
                               record=record)
    except Exception as e:
        logger.error(f"Lỗi form cập nhật: {str(e)}")
        return render_template('attendance_update.html',
                               employee_id=employee_id,
                               employee_name=employee_id,
                               date=date,
                               record=None,
                               error="Không thể tải dữ liệu.")
    finally:
        if conn:
            conn.close()


# ========================
# 2. API JSON (RESTful) — GIỮ NGUYÊN NHƯ CŨ
# ========================

@attendance_app.route('/api/attendance', methods=['GET'])
def get_attendance_list():
    """Lấy danh sách chấm công từ MySQL"""
    conn = get_mysql_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, EmployeeID, CheckIn, CheckOut, Status, Note 
            FROM attendance 
            ORDER BY CheckIn DESC 
            LIMIT 100
        """)
        data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        return jsonify({"error": "Lỗi khi lấy dữ liệu chấm công"}), 500
    finally:
        cursor.close()
        conn.close()


@attendance_app.route('/api/attendance', methods=['POST'])
def add_attendance():
    """Thêm mới bản ghi chấm công"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    employee_id = data.get("EmployeeID")
    check_in = data.get("CheckIn")
    check_out = data.get("CheckOut", None)
    status = data.get("Status", "Checked In")
    note = data.get("Note", "")

    if not employee_id or not check_in:
        return jsonify({"error": "Thiếu EmployeeID hoặc CheckIn"}), 400

    conn = get_mysql_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO attendance (EmployeeID, CheckIn, CheckOut, Status, Note)
            VALUES (%s, %s, %s, %s, %s)
        """, (employee_id, check_in, check_out, status, note))
        conn.commit()
        logger.info(f"Thêm chấm công cho NV {employee_id}")
        return jsonify({"message": "Thêm chấm công thành công!", "id": cursor.lastrowid}), 201
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding attendance: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@attendance_app.route('/api/attendance/<int:record_id>', methods=['PUT'])
def update_attendance(record_id):
    """Cập nhật bản ghi chấm công"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    check_in = data.get("CheckIn")
    check_out = data.get("CheckOut")
    status = data.get("Status")
    note = data.get("Note")

    if not any([check_in, check_out, status, note]):
        return jsonify({"error": "Không có dữ liệu để cập nhật"}), 400

    conn = get_mysql_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM attendance WHERE id = %s", (record_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Không tìm thấy bản ghi"}), 404

        updates = []
        values = []
        if check_in is not None:
            updates.append("CheckIn = %s")
            values.append(check_in)
        if check_out is not None:
            updates.append("CheckOut = %s")
            values.append(check_out)
        if status is not None:
            updates.append("Status = %s")
            values.append(status)
        if note is not None:
            updates.append("Note = %s")
            values.append(note)

        values.append(record_id)
        query = f"UPDATE attendance SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()

        logger.info(f"Cập nhật chấm công ID {record_id}")
        return jsonify({"message": "Cập nhật thành công!"})
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating attendance: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@attendance_app.route('/api/attendance/<int:record_id>', methods=['DELETE'])
def delete_attendance(record_id):
    """Xóa bản ghi chấm công"""
    conn = get_mysql_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM attendance WHERE id = %s", (record_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Không tìm thấy bản ghi để xóa"}), 404
        conn.commit()
        logger.info(f"Xóa chấm công ID {record_id}")
        return jsonify({"message": "Xóa thành công!"})
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting attendance: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()