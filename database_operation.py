import sqlite3
import numpy as np
import datetime

def connect_db(db_file="database.db"):
    """连接到SQLite数据库并返回连接和游标"""
    conn = sqlite3.connect(db_file, check_same_thread=False)
    cursor = conn.cursor()
    return conn, cursor

def close_sqlite(conn, cursor):
    if conn:
        conn.commit()
        cursor.close()
        conn.close()


def save_ins_to_people(job_id, name, department_id, face_vector, is_manager):
    vector_bytes = face_vector.tobytes()  # 转换为字节流
    conn, cursor = connect_db()
    cursor.execute("INSERT INTO people (job_id, name, department_id, face_vector, is_manager) VALUES (?, ?, ?, ?, ?)",
                   (job_id, name, department_id, vector_bytes, is_manager))
    conn.commit()
    close_sqlite(conn, cursor)

def load_name_by_job_id_from_people(job_id):
    conn, cursor = connect_db()
    cursor.execute("SELECT name FROM people WHERE job_id = ?",
                   (job_id,))
    result = cursor.fetchone()[0]
    close_sqlite(conn, cursor)
    return result

def load_all_face_vector_from_people():
    # 查询数据库中所有存储的向量
    conn, cursor = connect_db()
    cursor.execute("SELECT job_id, face_vector FROM people")
    rows = cursor.fetchall()  # 获取所有的记录
    close_sqlite(conn, cursor)
    vectors = []
    for row in rows:
        vector_id = row[0]
        vector_bytes = row[1]  # 获取存储的BLOB字节流
        # 将字节流恢复为numpy数组
        vector = np.frombuffer(vector_bytes, dtype=np.float32)  # 假设是32位浮点数
        vectors.append((vector_id, vector))
    return vectors

def save_ins_to_department(id, name):
    conn, cursor = connect_db()
    cursor.execute("INSERT INTO department (id, name) VALUES (?, ?)",
                   (id, name))
    conn.commit()
    close_sqlite(conn, cursor)

def load_all_ins_from_department():
    conn, cursor = connect_db()
    cursor.execute("SELECT * FROM department")
    rows = cursor.fetchall()  # 获取所有的记录
    close_sqlite(conn, cursor)
    return rows

def load_all_name_from_department():
    conn, cursor = connect_db()
    cursor.execute("SELECT name FROM department")
    rows = cursor.fetchall()  # 获取所有的记录
    close_sqlite(conn, cursor)
    result = []
    for row in rows:
        name = row[0]
        result.append(name)
    return result

def load_id_by_name_from_department(name):
    conn, cursor = connect_db()
    cursor.execute("SELECT id FROM department WHERE name = ?",
                   (name,))
    result = cursor.fetchone()[0]
    close_sqlite(conn, cursor)
    return result

def load_all_manager_face_vector_from_people():
    # 查询数据库中所有存储的向量
    conn, cursor = connect_db()
    cursor.execute("SELECT job_id, face_vector FROM people WHERE is_manager = 1")
    rows = cursor.fetchall()  # 获取所有的记录
    close_sqlite(conn, cursor)
    vectors = []
    for row in rows:
        vector_id = row[0]
        vector_bytes = row[1]  # 获取存储的BLOB字节流
        # 将字节流恢复为numpy数组
        vector = np.frombuffer(vector_bytes, dtype=np.float32)  # 假设是32位浮点数
        vectors.append((vector_id, vector))
    return vectors

def save_ins_to_history(job_id):
    result = -1
    # 获取当天日期字符串和当前时间字符串（精确到分钟）
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    current_time_str = datetime.datetime.now().strftime("%H:%M")
    current_dt = datetime.datetime.strptime(f"{today_str} {current_time_str}", "%Y-%m-%d %H:%M")
    # 连接数据库
    conn, cursor = connect_db()
    # 查询当天且 job_id 相同的记录
    cursor.execute("SELECT sign_in, sign_out FROM history WHERE date=? AND job_id=?", (today_str, job_id))
    record = cursor.fetchone()
    if record is None:
        # 情况1：没有记录，插入一条新的记录
        cursor.execute(
            "INSERT INTO history (date, job_id, sign_in, sign_out) VALUES (?, ?, ?, ?)",
            (today_str, job_id, current_time_str, "")
        )
        conn.commit()
        result = 1
    else:
        sign_in_str, sign_out = record
        # 如果已有记录且 sign_out 为空
        if sign_out in (None, "", "NULL"):
            # 将 sign_in 字符串与当天日期组合后解析为 datetime 对象
            try:
                sign_in_dt = datetime.datetime.strptime(f"{today_str} {sign_in_str}", "%Y-%m-%d %H:%M")
            except Exception as e:
                result = -2
                close_sqlite(conn, cursor)
                return result
            # 计算当前时间与 sign_in 之间的时间差（分钟）
            time_diff = (current_dt - sign_in_dt).total_seconds() / 60.0
            if time_diff > 10:
                # 情况2：时间差超过 10 分钟，则更新 sign_out 为当前时间
                cursor.execute(
                    "UPDATE history SET sign_out=? WHERE date=? AND job_id=?",
                    (current_time_str, today_str, job_id)
                )
                conn.commit()
                result = 2
            else:
                # 情况：时间差不超过 10 分钟，不做任何操作
                result = 0
        else:
            # 情况3：已有记录且 sign_out 不为空，什么都不做
            result = -1
    # 关闭数据库连接
    close_sqlite(conn, cursor)
    return result

def load_attendance(date_str):
    """
    date_str: 日期字符串，格式 "YYYY-MM-DD"
        返回：列表，每个元素为字典，包含 "job_id", "name", "department", "day_duration","attendance_day", "month_duration"
    """
    # 连接数据库
    conn, cursor = connect_db()

    # 获取所有员工及部门名称
    cursor.execute("""
        SELECT p.job_id, p.name, d.name
        FROM people p
        JOIN department d ON p.department_id = d.id
    """)
    employees = cursor.fetchall()  # [(job_id, name, department), ...]

    # 构造字典，key 为 job_id，值为员工信息字典
    emp_dict = {}
    for job_id, name, dept in employees:
        emp_dict[job_id] = {
            "job_id": job_id,
            "name": name,
            "department": dept,
            "day_duration": 0.0,     # 当日工作时长（小时）
            "attendance_day": 0,     # 当月出勤天数
            "month_duration": 0.0    # 当月工作时长（小时）
        }

    # 定义日期格式
    dt_format = "%Y-%m-%d %H:%M"
    # 当前日期对象（当天）对应的 datetime 对象，用于计算时差
    # 注意：此处仅用于解析当天签到/签退时间时拼接 date_str 与时间字符串
    # 查询当天记录：只计算 sign_out 非空的记录
    cursor.execute("""
        SELECT job_id, sign_in, sign_out
        FROM history
        WHERE date = ? AND sign_out IS NOT NULL AND sign_out <> ''
    """, (date_str,))
    daily_records = cursor.fetchall()  # [(job_id, sign_in, sign_out), ...]

    # 计算当天每个员工的工作时长（单位：小时，保留一位小数）
    for rec in daily_records:
        job_id, sign_in, sign_out = rec
        try:
            dt_sign_in = datetime.datetime.strptime(date_str + " " + sign_in, dt_format)
            dt_sign_out = datetime.datetime.strptime(date_str + " " + sign_out, dt_format)
            duration = (dt_sign_out - dt_sign_in).total_seconds() / 3600.0
            duration = round(duration, 1)
        except Exception as e:
            print("时间解析错误:", e)
            duration = 0.0

        # 记录当天的工作时长（假设每天只有一条记录）
        if job_id in emp_dict:
            emp_dict[job_id]["day_duration"] = duration

    # 计算当月出勤天数和月工作时长
    # 根据给定日期的前 7 个字符获取 "YYYY-MM"
    month_prefix = date_str[:7]  # 如 "2023-03"
    # 查询当月所有记录
    cursor.execute("""
        SELECT date, job_id, sign_in, sign_out
        FROM history
        WHERE date LIKE ? AND sign_out IS NOT NULL AND sign_out <> ''
    """, (month_prefix + "-%",))
    monthly_records = cursor.fetchall()  # [(date, job_id, sign_in, sign_out), ...]

    # 使用字典聚合每个员工的当月出勤天数和工作时长
    monthly_agg = {}
    for rec in monthly_records:
        record_date, job_id, sign_in, sign_out = rec
        try:
            dt_sign_in = datetime.datetime.strptime(record_date + " " + sign_in, dt_format)
            dt_sign_out = datetime.datetime.strptime(record_date + " " + sign_out, dt_format)
            duration = (dt_sign_out - dt_sign_in).total_seconds() / 3600.0
            duration = round(duration, 1)
        except Exception as e:
            print("解析时间错误:", e)
            duration = 0.0

        if job_id not in monthly_agg:
            monthly_agg[job_id] = {"attendance_day": 0, "month_duration": 0.0}
        monthly_agg[job_id]["attendance_day"] += 1
        monthly_agg[job_id]["month_duration"] += duration

    # 将聚合的月数据合并到员工字典中（并保留一位小数）
    for job_id, agg in monthly_agg.items():
        if job_id in emp_dict:
            emp_dict[job_id]["attendance_day"] = agg["attendance_day"]
            emp_dict[job_id]["month_duration"] = round(agg["month_duration"], 1)

    # 转换为列表
    result = list(emp_dict.values())
    close_sqlite(conn, cursor)
    return result

def load_sign_history():
    """
    读取所有签到记录，返回格式为：
    [{"date": ..., "job_id": ..., "name": ..., "department": ..., "sign_in": ..., "sign_out": ...}, ...]
    """
    # 请将数据库文件路径替换为实际路径
    conn, cursor = connect_db()
    # 设置 row_factory 为 sqlite3.Row 便于后续将结果转换为字典
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 构造 SQL 查询，联结 history, people, department 三张表
    query = """
    SELECT h.date, h.job_id, p.name, d.name AS department, h.sign_in, h.sign_out
    FROM history h
    JOIN people p ON h.job_id = p.job_id
    JOIN department d ON p.department_id = d.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # 将查询结果转换为字典列表
    result = []
    for row in rows:
        record = {
            "date": row["date"],
            "job_id": row["job_id"],
            "name": row["name"],
            "department": row["department"],
            "sign_in": row["sign_in"],
            "sign_out": row["sign_out"]
        }
        result.append(record)

    close_sqlite(conn, cursor)
    return result

def load_people():
    """
    读取所有员工信息，返回格式为：
    [{"job_id": ..., "name": ..., "department": ..., "is_manager": ...}, ...]
    """
    # 连接数据库（请替换为实际的数据库文件路径）
    conn, cursor = connect_db()
    # 设置 row_factory 为 sqlite3.Row，方便按列名获取数据
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # SQL查询，将 people 表和 department 表进行联结
    query = """
        SELECT p.job_id, p.name, d.name AS department, p.is_manager
        FROM people p
        JOIN department d ON p.department_id = d.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # 将查询结果转换为字典列表
    result = []
    for row in rows:
        record = {
            "job_id": row["job_id"],
            "name": row["name"],
            "department": row["department"],
            "is_manager": row["is_manager"]
        }
        if record["is_manager"] == 1:
            record["is_manager"] = "管理员"
        else:
            record["is_manager"] = "员工"
        result.append(record)

    close_sqlite(conn, cursor)
    return result

if __name__ == "__main__":
    people_list = load_people()
    for record in people_list:
        print(record)