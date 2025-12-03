from flask import Blueprint, jsonify, request
from config.sqlserver_connecttion import get_sqlserver_conn
from config.mysql_connection import get_mysql_conn
app = Blueprint('employees', __name__)

#api danh sach nhan vien
@app.route('/employees', methods=['GET'])
def get_employees():
    conn = get_sqlserver_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.EmployeeID,
            e.FullName,
            e.DateOfBirth,
            e.Gender,
            e.PhoneNumber,
            e.Email,
            e.HireDate,

            d.DepartmentName,
            p.PositionName,
            e.Status,

            e.CreatedAt,
            e.UpdatedAt
        FROM Employees e
        LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
        LEFT JOIN Positions p ON e.PositionID = p.PositionID
       
    """)

    rows = cursor.fetchall()

    employees = []
    for r in rows:
        employees.append({
            "EmployeeID": r[0],
            "FullName": r[1],
            "DateOfBirth": r[2],
            "Gender": r[3],
            "PhoneNumber": r[4],
            "Email": r[5],
            "HireDate": r[6],
            "DepartmentName": r[7],
            "PositionName": r[8],
            "Status": r[9],
            "CreatedAt": r[10],
            "UpdatedAt": r[11]
        })
    return jsonify(employees)


# APi them moi nhan vien
@app.route('/employees', methods=['POST'])
def add_employees():
    data = request.json

    sql_conn=get_sqlserver_conn()
    sql_cursor=sql_conn.cursor()

    mysql_conn=get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        #lay du lieu tu body gui len
        
        FullName = data.get("FullName")
        DateOfBirth = data.get("DateOfBirth")
        Gender = data.get("Gender")
        PhoneNumber = data.get("PhoneNumber")
        Email = data.get("Email")
        HireDate = data.get("HireDate")
        DepartmentID = data.get("DepartmentID")
        PositionID = data.get("PositionID")
        Status = data.get("Status")

        if not FullName:
            return jsonify({"error": "FullName không được để trống"})

        #insert vaof sql server tuoc
        sql_cursor.execute("""
            INSERT INTO Employees(
                FullName, DateOfBirth, Gender, PhoneNumber, Email,
                HireDate, DepartmentID, PositionID, Status, CreatedAt
            )
            OUTPUT INSERTED.EmployeeID
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, (
            FullName, DateOfBirth, Gender, PhoneNumber, Email,
            HireDate, DepartmentID, PositionID, Status
        ))

        #lay id cua nhan vien vua duojc tao owr sql server 
        new_employee_id=sql_cursor.fetchone()[0]
        sql_conn.commit()

        #dong bo sang mysql
        mysql_cursor.execute("""
            INSERT INTO employees (
                EmployeeID, FullName, DepartmentID, PositionID, Status
            )
            VALUES (%s, %s, %s, %s, %s)
        """,(
            new_employee_id, FullName, DepartmentID, PositionID,Status
        ))
        mysql_conn.commit()

        return jsonify({
            "message": "Thêm nhân viên thành công!",
            "EmployeeID": new_employee_id
        })
    except Exception as e:
        sql_conn.rollback
        mysql_conn.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        sql_cursor.close()
        sql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()





#api lay nhan vien ddo voaf form update------------------
@app.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee_by_id(employee_id):
    conn = get_sqlserver_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.EmployeeID,
            e.FullName,
            e.DateOfBirth,
            e.Gender,
            e.PhoneNumber,
            e.Email,
            e.HireDate,

            e.DepartmentID,
            e.PositionID,
            e.Status,

            d.DepartmentName,
            p.PositionName
        FROM Employees e
        LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
        LEFT JOIN Positions p ON e.PositionID = p.PositionID
        WHERE e.EmployeeID = ?
    """, (employee_id,))


    r = cursor.fetchone()

    if not r:
        return jsonify({"error": "Không tìm thấy nhân viên"}), 404

    employee = {
    "EmployeeID": r[0],
    "FullName": r[1],
    "DateOfBirth": r[2],
    "Gender": r[3],
    "PhoneNumber": r[4],
    "Email": r[5],
    "HireDate": r[6],

    "DepartmentID": r[7],
    "PositionID": r[8],
    "Status": r[9],

    "DepartmentName": r[10],
    "PositionName": r[11]
}
    return jsonify(employee)

#api cap nhat nhan vien update_employees-------------------------------
@app.route('/employees/<int:employee_id>', methods=['PUT'])
def update_employees(employee_id):
    data = request.json

    sql_conn = get_sqlserver_conn()
    sql_cursor = sql_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        # Lấy trực tiếp ID từ giao diện
        DepartmentID = data.get("DepartmentID")
        PositionID = data.get("PositionID")

        # Update Employees SQL Server
        sql_cursor.execute("""
            UPDATE Employees
            SET FullName = ?, 
                DateOfBirth = ?, 
                Gender = ?, 
                PhoneNumber = ?, 
                Email = ?, 
                HireDate = ?, 
                DepartmentID = ?, 
                PositionID = ?, 
                Status = ?,
                UpdatedAt = GETDATE()
            WHERE EmployeeID = ?
        """, (
            data.get("FullName"),
            data.get("DateOfBirth"),
            data.get("Gender"),
            data.get("PhoneNumber"),
            data.get("Email"),
            data.get("HireDate"),
            DepartmentID,
            PositionID,
            data.get("Status"),
            employee_id
        ))
        sql_conn.commit()

        # Update MySQL
        mysql_cursor.execute("""
            UPDATE employees
            SET FullName = %s,
                DepartmentID = %s,
                PositionID = %s,
                Status = %s
            WHERE EmployeeID = %s
        """, (
            data.get("FullName"),
            DepartmentID,
            PositionID,
            data.get("Status"),
            employee_id
        ))
        mysql_conn.commit()

        return jsonify({"message": "Cập nhật nhân viên thành công!"})

    except Exception as e:
        sql_conn.rollback()
        mysql_conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        sql_cursor.close()
        sql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()


#api tim kiem nhan vien theo tên :
@app.route('/search-employees', methods=['GET'])
def search_employees_by_name():
    keyword = request.args.get("name", "")  # nhận ?name=

    conn = get_sqlserver_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                e.EmployeeID,
                e.FullName,
                e.DateOfBirth,
                e.Gender,
                e.PhoneNumber,
                e.Email,
                e.HireDate,
                d.DepartmentName,
                p.PositionName,
                e.Status
            FROM Employees e
            LEFT JOIN Departments d ON e.DepartmentID = d.DepartmentID
            LEFT JOIN Positions p ON e.PositionID = p.PositionID
            WHERE e.FullName COLLATE Latin1_General_CI_AI 
                  LIKE ? COLLATE Latin1_General_CI_AI
        """, (f"%{keyword}%",))

        rows = cursor.fetchall()

        employees = []
        for r in rows:
            employees.append({
                "EmployeeID": r[0],
                "FullName": r[1],
                "DateOfBirth": r[2],
                "Gender": r[3],
                "PhoneNumber": r[4],
                "Email": r[5],
                "HireDate": r[6],
                "DepartmentName": r[7],
                "PositionName": r[8],
                "Status": r[9]
            })

        return jsonify(employees)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# API xoá nhân viên
@app.route('/delete-employee/<int:id>', methods=['DELETE'])
def delete_employee(id):

 
    conn_sql = get_sqlserver_conn()
    cursor_sql = conn_sql.cursor()

    conn_my = get_mysql_conn()
    cursor_my = conn_my.cursor()

    try:
     

        # Kiểm tra bảng LƯƠNG (salaries)
        cursor_my.execute("SELECT COUNT(*) FROM salaries WHERE EmployeeID = %s", (id,))
        salary_count = cursor_my.fetchone()[0]

        if salary_count > 0:
            return jsonify({"error": "Nhân viên còn dữ liệu BẢNG LƯƠNG, không thể xoá!"}), 400

        # Kiểm tra bảng CHẤM CÔNG (attendance)
        cursor_my.execute("SELECT COUNT(*) FROM attendance WHERE EmployeeID = %s", (id,))
        attendance_count = cursor_my.fetchone()[0]

        if attendance_count > 0:
            return jsonify({"error": "Nhân viên còn dữ liệu CHẤM CÔNG, không thể xoá!"}), 400


    

        # Xoá trong bảng Dividends nếu có
        cursor_sql.execute("DELETE FROM Dividends WHERE EmployeeID = ?", (id,))
        conn_sql.commit()

        # Xoá nhân viên
        cursor_sql.execute("DELETE FROM Employees WHERE EmployeeID = ?", (id,))
        conn_sql.commit()


    # xoa my sql
        cursor_my.execute("DELETE FROM employees WHERE EmployeeID = %s", (id,))
        conn_my.commit()

        return jsonify({"message": "Xoá nhân viên thành công!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor_sql.close()
        conn_sql.close()
        cursor_my.close()
        conn_my.close()
