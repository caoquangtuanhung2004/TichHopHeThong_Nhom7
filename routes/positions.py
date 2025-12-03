from flask import Blueprint, jsonify, request
from config.sqlserver_connecttion import get_sqlserver_conn
from config.mysql_connection import get_mysql_conn
positions_app = Blueprint('positions', __name__)


#hien thị chuc vụ 
@positions_app.route('/positions', methods=['GET'])
def get_positions():
    conn = get_sqlserver_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT PositionID, PositionName FROM Positions")
    rows = cursor.fetchall()

    data = [{"PositionID": r[0], "PositionName": r[1]} for r in rows]

    return jsonify(data)


#laydanhsach hien thi form update
@positions_app.route('/positions/<int:positions_id>', methods=['GET'])
def get_positions_by_id(positions_id):
    conn=get_sqlserver_conn()
    cursor = conn.cursor()

    cursor.execute("""SELECT PositionID, PositionName FROM Positions WHERE PositionID=? 
            """,(positions_id,))
    r= cursor.fetchone()


    if not r:
         return jsonify({"error": "Không tìm thấy phòng ban nào"}), 404
    
    positions ={
        "PositionID": r[0],
        "PositionName": r[1]
    }
    return jsonify(positions)


#api cap nhat 
@positions_app.route('/positions/<int:positions_id>', methods=['PUT'])
def update_positions(positions_id):
    data = request.json

    sql_conn = get_sqlserver_conn()
    sql_cursor = sql_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        # UPDATE SQL SERVER
        sql_cursor.execute("""
            UPDATE Positions
            SET PositionName = ?,
                UpdatedAt = GETDATE()
            WHERE PositionID = ?
        """, (
            data.get("PositionName"),
            positions_id
        ))
        sql_conn.commit()

        # UPDATE MYSQL (đã sửa)
        mysql_cursor.execute("""
            UPDATE Positions
            SET PositionName = %s
            WHERE PositionID = %s
        """, (
            data.get("PositionName"),
            positions_id
        ))
        mysql_conn.commit()

        #print("Rows affected MySQL:", mysql_cursor.rowcount)

        return jsonify({"message": "Cập nhật chức vụ thành công!"})

    except Exception as e:
        sql_conn.rollback()
        mysql_conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        sql_cursor.close()
        sql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()


# ==============================
# API XÓA CHỨC VỤ
# ==============================

@positions_app.route('/delete-position/<int:pos_id>', methods=['DELETE'])
def delete_position(pos_id):
    sql_conn = get_sqlserver_conn()
    sql_cursor = sql_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        # 1. CHECK trong SQL Server có nhân viên không
        sql_cursor.execute("""
            SELECT COUNT(*) 
            FROM Employees 
            WHERE PositionID = ?
        """, (pos_id,))
        count_sql = sql_cursor.fetchone()[0]

        # 2. CHECK trong MySQL có nhân viên không
        mysql_cursor.execute("""
            SELECT COUNT(*) 
            FROM employees 
            WHERE PositionID = %s
        """, (pos_id,))
        count_mysql = mysql_cursor.fetchone()[0]

        if count_sql > 0 or count_mysql > 0:
            return jsonify({"error": "Chức vụ đang có nhân viên, không thể xóa!"}), 400

        # 3. XÓA vị trí trong SQL Server
        sql_cursor.execute("DELETE FROM Positions WHERE PositionID = ?", (pos_id,))
        sql_conn.commit()

        # 4. XÓA vị trí trong MySQL
        mysql_cursor.execute("DELETE FROM positions WHERE PositionID = %s", (pos_id,))
        mysql_conn.commit()

        return jsonify({"message": "Xóa chức vụ thành công!"})

    except Exception as e:
        sql_conn.rollback()
        mysql_conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        sql_cursor.close()
        sql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()


# ==============================
# API THÊM MỚI CHỨC VỤ
# ==============================
import re

@positions_app.route('/positions', methods=['POST'])
def add_position():
    data = request.json
    PositionName = data.get("PositionName")

    sql_conn = get_sqlserver_conn()
    sql_cursor = sql_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    try:
        # VALIDATE tên
        if not PositionName or PositionName.strip() == "":
            return jsonify({"error": "Tên chức vụ không được để trống!"}), 400

        regex = r"^[a-zA-Z0-9À-Ỹà-ỹ\s]+$"
        if not re.match(regex, PositionName):
            return jsonify({"error": "Tên chức vụ không được chứa ký tự đặc biệt!"}), 400

        # CHECK trùng tên trong SQL Server
        sql_cursor.execute("SELECT COUNT(*) FROM Positions WHERE PositionName = ?", (PositionName,))
        existed = sql_cursor.fetchone()[0]

        if existed > 0:
            return jsonify({"error": "Tên chức vụ đã tồn tại!"}), 400

        # THÊM vào SQL Server + lấy ID vừa tạo
        sql_cursor.execute("""
            INSERT INTO Positions (PositionName, CreatedAt)
            OUTPUT INSERTED.PositionID
            VALUES (?, GETDATE())
        """, (PositionName,))
        new_pos_id = sql_cursor.fetchone()[0]
        sql_conn.commit()

        # THÊM vào MySQL
        mysql_cursor.execute("""
            INSERT INTO positions (PositionID, PositionName)
            VALUES (%s, %s)
        """, (new_pos_id, PositionName))
        mysql_conn.commit()

        return jsonify({
            "message": "Thêm chức vụ thành công!",
            "PositionID": new_pos_id,
            "PositionName": PositionName
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


