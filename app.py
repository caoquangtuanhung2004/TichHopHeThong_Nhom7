from flask import Flask, render_template

from routes.emplyees import app as employees_app
from routes.departments import departments_app
from routes.positions import positions_app

app = Flask(__name__)

# Đăng ký Blueprint
app.register_blueprint(employees_app)
app.register_blueprint(departments_app)
app.register_blueprint(positions_app)

@app.route("/")
def home():  
    #return render_template("employees.html")
    #return render_template("add_employees.html")
    return render_template("home.html")

@app.route("/employees_list")
def employees_list():
    return render_template('/employees.html')

@app.route('/update_employee')
def update_employees():
    return render_template("update_employees.html")
#xemlaij keo loi
@app.route('/add_employee')
def add_employees():
    return render_template("add_employees.html")

@app.route('/employeesquanly')
def employeesquanly():
    return render_template("quanlyemployees.html")

@app.route('/Departments')
def Departments_list():
    return render_template("list_Departments.html")

@app.route('/update_Departments')
def update_Departments():
    return render_template("update_departments.html")
@app.route('/add_department')
def add_department_page():
    return render_template("add_departments.html")

@app.route('/Positions')
def Positions_list():
    return render_template("list_positions.html")

@app.route('/add_positions')
def add_positions():
    return render_template("add_positions.html")

if __name__ == '__main__':
    app.run(debug=True)
