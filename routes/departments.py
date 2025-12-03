from flask import Blueprint, jsonify, request
from config.sqlserver_connecttion import get_sqlserver_conn
from config.mysql_connection import get_mysql_conn

departments_app = Blueprint('departments', __name__)


#hien thi danh sach phong ban
@departments_app.route('/departments', methods=['GET'])
def get_departments():
    conn = get_sqlserver_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT DepartmentID, DepartmentName FROM Departments")
    rows = cursor.fetchall()

    data = [{"DepartmentID": r[0], "DepartmentName": r[1]} for r in rows]

    return jsonify(data)


#laydanhsach hien thi form update
@departments_app.route('/departments/<int:departments_id>', methods=['GET'])
def get_departments_by_id(departments_id):
    conn=get_sqlserver_conn()
    cursor = conn.cursor()

    cursor.execute("""SELECT DepartmentID, DepartmentName FROM Departments WHERE DepartmentID=? 
            """,(departments_id,))
    r= cursor.fetchone()


    if not r:
         return jsonify({"error": "Không tìm thấy phòng ban nào"}), 404
    
    departments ={
        "DepartmentID": r[0],
        "DepartmentName": r[1]
    }
    return jsonify(departments)


#api cap nhat phong ban 
@departments_app.route('/departments/<int:departments_id>', methods=['PUT'])
def update_departments(departments_id):
    data = request.json

    sql_conn = get_sqlserver_conn()
    sql_cursor = sql_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        # UPDATE SQL SERVER
        sql_cursor.execute("""
            UPDATE Departments
            SET DepartmentName = ?,
                UpdatedAt = GETDATE()
            WHERE DepartmentID = ?
        """, (
            data.get("DepartmentName"),
            departments_id
        ))
        sql_conn.commit()

        # UPDATE MYSQL (đã sửa)
        mysql_cursor.execute("""
            UPDATE Departments
            SET DepartmentName = %s
            WHERE DepartmentID = %s
        """, (
            data.get("DepartmentName"),
            departments_id
        ))
        mysql_conn.commit()

        #print("Rows affected MySQL:", mysql_cursor.rowcount)

        return jsonify({"message": "Cập nhật phòng ban thành công!"})

    except Exception as e:
        sql_conn.rollback()
        mysql_conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        sql_cursor.close()
        sql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()


#API Xóa phòng ban 

@departments_app.route('/delete-dept/<int:dept_id>', methods=['DELETE'])
def delete_department(dept_id):
    sql_conn = get_sqlserver_conn()
    sql_cursor = sql_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        # 1. KIỂM TRA PHÒNG BAN CÓ NHÂN VIÊN TRONG SQL SERVER KHÔNG
        sql_cursor.execute("""
            SELECT COUNT(*) 
            FROM Employees 
            WHERE DepartmentID = ?
        """, (dept_id,))
        count_sql = sql_cursor.fetchone()[0]

        # 2. KIỂM TRA PHÒNG BAN CÓ NHÂN VIÊN TRONG MYSQL KHÔNG
        mysql_cursor.execute("""
            SELECT COUNT(*) 
            FROM employees 
            WHERE DepartmentID = %s
        """, (dept_id,))
        count_mysql = mysql_cursor.fetchone()[0]

        if count_sql > 0 or count_mysql > 0:
            return jsonify({"error": "Phòng ban đang có nhân viên, không thể xóa!"}), 400

        # 3. XÓA PHÒNG BAN TRONG SQL SERVER
        sql_cursor.execute("""
            DELETE FROM Departments WHERE DepartmentID = ?
        """, (dept_id,))
        sql_conn.commit()

        # 4. XÓA PHÒNG BAN TRONG MYSQL
        mysql_cursor.execute("""
            DELETE FROM Departments WHERE DepartmentID = %s
        """, (dept_id,))
        mysql_conn.commit()

        return jsonify({"message": "Xóa phòng ban thành công!"})

    except Exception as e:
        sql_conn.rollback()
        mysql_conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        sql_cursor.close()
        sql_conn.close()

        mysql_cursor.close()
        mysql_conn.close()


# API THÊM MỚI PHÒNG BAN
import re

# API thêm mới phòng ban
@departments_app.route('/departments', methods=['POST'])
def add_department():
    data = request.json

    sql_conn = get_sqlserver_conn()
    sql_cursor = sql_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        DepartmentName = data.get("DepartmentName")

        if not DepartmentName or DepartmentName.strip() == "":
            return jsonify({"error": "Tên phòng ban không được để trống!"}), 400
        
      
        regex = r"^[a-zA-Z0-9À-Ỹà-ỹ\s]+$"
        if not re.match(regex, DepartmentName):
            return jsonify({"error": "Tên phòng ban không được chứa ký tự đặc biệt!"}), 400
        
     
        sql_cursor.execute("SELECT COUNT(*) FROM Departments WHERE DepartmentName = ?", (DepartmentName,))
        existed = sql_cursor.fetchone()[0]

        if existed > 0:
            return jsonify({"error": "Tên phòng ban đã tồn tại!"}), 400

      
        sql_cursor.execute("""
            INSERT INTO Departments (DepartmentName, CreatedAt)
            OUTPUT INSERTED.DepartmentID
            VALUES (?, GETDATE())
        """, (DepartmentName,))
        
        new_dep_id = sql_cursor.fetchone()[0]
        sql_conn.commit()

        
        mysql_cursor.execute("""
            INSERT INTO Departments (DepartmentID, DepartmentName)
            VALUES (%s, %s)
        """, (new_dep_id, DepartmentName))
        mysql_conn.commit()

        return jsonify({
            "message": "Thêm phòng ban thành công!",
            "DepartmentID": new_dep_id,
            "DepartmentName": DepartmentName
        }), 201

    except Exception as e:
        sql_conn.rollback()
        mysql_conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        sql_cursor.close()
        sql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()
