import sqlite3
import numpy as np
import datetime

def connect_db(db_file="face_recognition.db"):
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
    try:
        cursor.execute("INSERT INTO people (job_id, name, department_id, face_vector, is_manager) VALUES (?, ?, ?, ?, ?)",
                       (job_id, name, department_id, vector_bytes, is_manager))
        conn.commit()
    except Exception as e:
        print("创建员工时出错：", e)
    finally:
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

def save_ins_to_department(name):
    conn, cursor = connect_db()
    try:
        if name:
            cursor.execute("INSERT INTO department (name) VALUES (?)", (name,))
            conn.commit()
        else:
            print("存在空值，更新失败")
    except Exception as e:
        print("创建部门时出错：", e)
    finally:
        close_sqlite(conn, cursor)

def load_all_name_from_department():
    conn, cursor = connect_db()
    cursor.execute("SELECT name FROM department WHERE name != '未知'")
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
    """
    将员工签到/签退记录保存到history表中
    :param job_id: 员工工号
    :return: 
        1: 新插入一条签到记录，或当前时间与未签退记录的签到时间差小于10分钟
        2: 当前时间与未签退记录的签到时间差在10-30分钟之间
        3: 当前时间与未签退记录的签到时间差超过30分钟，更新为签退；或当前时间与最近签退时间差小于10分钟
        4: 当前时间与最近签退时间差在10-30分钟之间
    """
    # 获取当天日期字符串和当前时间字符串（精确到分钟）
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    current_time_str = datetime.datetime.now().strftime("%H:%M")
    current_dt = datetime.datetime.strptime(f"{today_str} {current_time_str}", "%Y-%m-%d %H:%M")
    
    # 连接数据库
    conn, cursor = connect_db()
    try:
        # 查询当天该员工的所有记录
        cursor.execute("""
            SELECT id, sign_in, sign_out 
            FROM history 
            WHERE date=? AND job_id=?
            ORDER BY 
                CASE WHEN sign_out IS NULL OR sign_out = '' THEN 1 ELSE 0 END DESC,
                sign_out DESC
        """, (today_str, job_id))
        
        records = cursor.fetchall()
        
        # 情况1: 当天不存在记录
        if not records:
            # 插入一条sign_in为当前时间，sign_out为空的记录
            cursor.execute(
                "INSERT INTO history (date, job_id, sign_in, sign_out) VALUES (?, ?, ?, ?)",
                (today_str, job_id, current_time_str, "")
            )
            conn.commit()
            return 1
        
        # 检查是否有未签退的记录（sign_out为空）
        for record_id, sign_in_str, sign_out in records:
            if not sign_out or sign_out.strip() == "":  # 找到未签退记录
                # 情况2: 存在记录且sign_in不为空而sign_out为空
                try:
                    # 解析签到时间
                    sign_in_dt = datetime.datetime.strptime(f"{today_str} {sign_in_str}", "%Y-%m-%d %H:%M")
                    
                    # 计算当前时间与签到时间的差（分钟）
                    time_diff = (current_dt - sign_in_dt).total_seconds() / 60.0
                    
                    if time_diff <= 10:
                        # 时间差不超过10分钟
                        return 1
                    elif 10 < time_diff <= 30:
                        # 时间差超过10分钟但不超过30分钟
                        return 2
                    else:
                        # 时间差超过30分钟，更新sign_out为当前时间
                        cursor.execute(
                            "UPDATE history SET sign_out=? WHERE id=?",
                            (current_time_str, record_id)
                        )
                        conn.commit()
                        return 3
                except Exception as e:
                    print(f"解析时间出错: {e}")
                    return -1
        
        # 情况3: 所有记录都已签退（sign_in和sign_out都不为空）
        # 由于之前的ORDER BY，records[0]应该是sign_out最大的记录
        if records:
            record_id, sign_in_str, sign_out_str = records[0]
            
            try:
                # 解析最近的签退时间
                sign_out_dt = datetime.datetime.strptime(f"{today_str} {sign_out_str}", "%Y-%m-%d %H:%M")
                
                # 计算当前时间与最近签退时间的差（分钟）
                time_diff = (current_dt - sign_out_dt).total_seconds() / 60.0
                
                if time_diff <= 10:
                    # 时间差不超过10分钟
                    return 3
                elif 10 < time_diff <= 30:
                    # 时间差超过10分钟但不超过30分钟
                    return 4
                else:
                    # 时间差超过30分钟，插入新记录
                    cursor.execute(
                        "INSERT INTO history (date, job_id, sign_in, sign_out) VALUES (?, ?, ?, ?)",
                        (today_str, job_id, current_time_str, "")
                    )
                    conn.commit()
                    return 1
            except Exception as e:
                print(f"解析时间出错: {e}")
                return -1
        
        # 理论上不会到达这里，但为了代码完整性添加
        return -1
    except Exception as e:
        print(f"添加历史记录时出错：{e}")
        return -1
    finally:
        # 关闭数据库连接
        close_sqlite(conn, cursor)

def load_attendance(date_str):
    """
    根据指定日期统计所有员工的出勤情况
    
    参数:
        date_str: 日期字符串，格式为"YYYY-MM-dd"
        
    返回:
        包含所有员工出勤统计信息的列表，每个元素是一个字典，格式为：
        {
            "job_id": 工号,
            "name": 姓名,
            "department": 部门,
            "day_duration": 当日工作时长(小时),
            "attendance_day": 当月出勤天数,
            "month_duration": 当月工作时长(小时)
        }
    """
    conn, cursor = connect_db()
    try:
        # 解析日期字符串
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        year_month = target_date.strftime("%Y-%m")
        
        # 查询所有员工信息
        cursor.execute("""
            SELECT p.job_id, p.name, d.name AS department
            FROM people p
            JOIN department d ON p.department_id = d.id
        """)
        employees = cursor.fetchall()
        
        result = []
        for employee in employees:
            job_id, name, department = employee
            
            # 查询指定日期的出勤记录
            cursor.execute("""
                SELECT sign_in, sign_out
                FROM history
                WHERE date = ? AND job_id = ?
                ORDER BY sign_in
            """, (date_str, job_id))
            daily_records = cursor.fetchall()
            
            # 计算当日工作时长（分钟）
            daily_minutes = 0
            for record in daily_records:
                sign_in, sign_out = record
                if sign_in and sign_out:
                    in_time = datetime.datetime.strptime(sign_in, "%H:%M")
                    out_time = datetime.datetime.strptime(sign_out, "%H:%M")
                    daily_minutes += (out_time - in_time).total_seconds() / 60
            
            # 查询当月所有出勤记录
            cursor.execute("""
                SELECT DISTINCT date, sign_in, sign_out
                FROM history
                WHERE date LIKE ? AND job_id = ?
                ORDER BY date
            """, (f"{year_month}%", job_id))
            monthly_records = cursor.fetchall()
            
            # 计算当月出勤天数和总工作时长
            monthly_days = 0
            monthly_minutes = 0
            current_date = None
            
            for record in monthly_records:
                date, sign_in, sign_out = record
                # 只有当sign_in和sign_out都不为空时才计入出勤天数
                if sign_in and sign_out:
                    if date != current_date:
                        monthly_days += 1
                        current_date = date
                    
                    in_time = datetime.datetime.strptime(sign_in, "%H:%M")
                    out_time = datetime.datetime.strptime(sign_out, "%H:%M")
                    monthly_minutes += (out_time - in_time).total_seconds() / 60
            
            # 将分钟转换为小时（四舍五入到整数）
            daily_hours = round(daily_minutes / 60)
            monthly_hours = round(monthly_minutes / 60)
            
            result.append({
                "job_id": job_id,
                "name": name,
                "department": department,
                "day_duration": daily_hours,
                "attendance_day": monthly_days,
                "month_duration": monthly_hours
            })
        
        return result
        
    except Exception as e:
        print(f"统计出勤情况时出错：{e}")
        return []
    finally:
        close_sqlite(conn, cursor)

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
    # 连接数据库
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

def delete_people_by_job_id(job_id):
    """
    根据给定的 job_id 删除 people 表中的行数据以及history表中对应的记录
    :param job_id: 要删除的工号
    """
    # 连接数据库
    conn, cursor = connect_db()
    try:
        # 删除 history 表中对应的记录
        cursor.execute("DELETE FROM history WHERE job_id = ?", (job_id,))
        history_rows_deleted = cursor.rowcount
        
        # 删除 people 表中的记录
        cursor.execute("DELETE FROM people WHERE job_id = ?", (job_id,))
        people_rows_deleted = cursor.rowcount
        
        conn.commit()
        
        # 检查是否删除成功
        if people_rows_deleted > 0:
            print(f"工号 {job_id} 对应的员工记录已成功删除。")
        else:
            print(f"未找到工号 {job_id} 对应的员工记录。")
            
        if history_rows_deleted > 0:
            print(f"工号 {job_id} 对应的 {history_rows_deleted} 条考勤记录已成功删除。")
    except Exception as e:
        print("删除过程中出错：", e)
    finally:
        close_sqlite(conn, cursor)

def update_people(job_id, new_job_id, new_name, new_department_id, new_is_manager):
    """
    更新 people 表中原始 job_id 对应的记录，将 job_id 及其他字段更新为新的值
    :param job_id: 原始的工号，用于定位记录
    :param new_job_id: 新的工号
    :param new_name: 新的姓名
    :param new_department_id: 新的部门编号
    :param new_is_manager: 新的是否为管理员（1 表示是，0 表示否）
    """
    conn, cursor = connect_db()
    # 执行 UPDATE 语句
    try:
        if new_job_id and new_name and new_department_id and new_is_manager:
            cursor.execute("""
                    UPDATE people
                    SET job_id = ?, name = ?, department_id = ?, is_manager = ?
                    WHERE job_id = ?
                """, (new_job_id, new_name, new_department_id, new_is_manager, job_id))
            conn.commit()
            if cursor.rowcount > 0:
                print("记录更新成功")
            else:
                print(f"未找到 job_id 为 {job_id} 的记录。")
        else:
            print("存在空值，更新失败")
    except Exception as e:
        print("更新过程中出错：", e)
    finally:
        close_sqlite(conn, cursor)

def update_department(old_name, new_name):
    """
    更新department表中的部门名称
    :param old_name: 原部门名称
    :param new_name: 新部门名称
    :return: 更新是否成功（True/False）
    """
    conn, cursor = connect_db()
    try:
        if new_name:
            # 更新部门名称
            cursor.execute("""
                UPDATE department
                SET name = ?
                WHERE name = ?
            """, (new_name, old_name))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"部门名称从 '{old_name}' 更新为 '{new_name}' 成功")
                return True
            else:
                print(f"未找到部门名称为 '{old_name}' 的记录")
                return False
        else:
            print("存在空值，更新失败")
    except Exception as e:
        print(f"更新部门名称时出错：{e}")
        return False
    finally:
        close_sqlite(conn, cursor)

def delete_department(name):
    """
    删除department表中指定name的部门记录，同时将people表中关联该部门的员工的department_id修改为0
    :param name: 要删除的部门名称
    :return: 是否删除成功（True/False）
    """
    conn, cursor = connect_db()
    try:
        # 首先查询department表中要删除部门的id
        cursor.execute("SELECT id FROM department WHERE name = ?", (name,))
        result = cursor.fetchone()
        if not result:
            print(f"未找到部门名称为 '{name}' 的记录")
            return False
        department_id = result[0]
        # 开始事务
        conn.execute("BEGIN TRANSACTION")
        # 更新people表中关联该部门的员工的department_id为0
        cursor.execute("""
            UPDATE people
            SET department_id = 0
            WHERE department_id = ?
        """, (department_id,))
        updated_employees_count = cursor.rowcount
        # 删除department表中的记录
        cursor.execute("DELETE FROM department WHERE id = ?", (department_id,))
        # 提交事务
        conn.commit()
        print(f"部门 '{name}' 已成功删除，{updated_employees_count} 名员工被重新分配到默认部门")
        return True
    except Exception as e:
        # 发生错误时回滚事务
        conn.rollback()
        print(f"删除部门时出错：{e}")
        return False
    finally:
        close_sqlite(conn, cursor)

def load_name_department_by_job_id_from_people(job_id):
    """
    根据工号获取员工姓名和部门名称
    :param job_id: 员工工号
    :return: 包含员工姓名和部门名称的元组(name, department_name)，如果未找到则返回(None, None)
    """
    conn, cursor = connect_db()
    try:
        # 联结查询people表和department表，获取员工姓名和部门名称
        cursor.execute("""
            SELECT p.name, d.name 
            FROM people p
            JOIN department d ON p.department_id = d.id
            WHERE p.job_id = ?
        """, (job_id,))
        result = cursor.fetchone()
        if result:
            return result  # 返回(name, department_name)元组
        else:
            return None, None  # 如果未找到记录，返回None元组
    except Exception as e:
        print(f"查询员工信息时出错：{e}")
        return None, None
    finally:
        close_sqlite(conn, cursor)

def save_history(date_str, job_id, sign_in, sign_out):
    """
    在history表中插入一条新记录，根据时间段的关系决定是合并还是新增记录
    :param date_str: 日期字符串，格式为"yyyy-MM-dd"
    :param job_id: 工号
    :param sign_in: 签到时间，格式为"HH:mm"
    :param sign_out: 签退时间，格式为"HH:mm"，可以为空字符串
    :return: 是否插入成功(True/False)，失败信息
    """
    # 参数验证
    if not date_str or not job_id or not sign_in or not sign_out:
        return False, "填写的信息不能为空"
    
    # 验证日期格式
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False, "日期格式错误"
    
    # 验证签到和签退时间的逻辑关系
    if sign_in and sign_out:
        # 比较签到和签退时间
        try:
            sign_in_time = datetime.datetime.strptime(sign_in, "%H:%M")
            sign_out_time = datetime.datetime.strptime(sign_out, "%H:%M")
            if sign_out_time <= sign_in_time:
                return False, "签退时间必须晚于签到时间"
        except ValueError:
            return False, "时间格式错误"
    
    # 连接数据库
    conn, cursor = connect_db()
    try:
        # 检查该job_id是否存在于people表中
        cursor.execute("SELECT 1 FROM people WHERE job_id = ?", (job_id,))
        if not cursor.fetchone():
            return False, f"工号 {job_id} 不存在于员工表中"
        
        # 解析新记录的签到时间
        try:
            new_in_time = datetime.datetime.strptime(sign_in, "%H:%M")
            new_out_time = datetime.datetime.strptime(sign_out, "%H:%M") if sign_out else None
        except ValueError:
            return False, "时间格式错误，无法处理"
        
        # 检查当天是否已有该工号的记录
        cursor.execute("""
            SELECT id, sign_in, sign_out 
            FROM history 
            WHERE date = ? AND job_id = ?
        """, (date_str, job_id))
        
        existing_records = cursor.fetchall()
        
        # 如果没有现有记录，直接插入新记录
        if not existing_records:
            cursor.execute("""
                INSERT INTO history (date, job_id, sign_in, sign_out)
                VALUES (?, ?, ?, ?)
            """, (date_str, job_id, sign_in, sign_out if sign_out else ""))
            
            conn.commit()
            return True, "记录添加成功"

        # 以下处理新记录有完整签到/签退时间的情况
        # 识别所有与新记录有交集的记录
        records_to_merge = []  # 需要合并的记录列表
        
        # 寻找与新记录有交集的所有记录
        for record in existing_records:
            record_id, existing_sign_in, existing_sign_out = record
            
            # 解析现有记录的时间
            try:
                existing_in_time = datetime.datetime.strptime(existing_sign_in, "%H:%M") if existing_sign_in else None
                existing_out_time = datetime.datetime.strptime(existing_sign_out, "%H:%M") if existing_sign_out else None
            except ValueError:
                continue  # 跳过无法解析的记录
            
            # 如果现有记录没有签退时间（即尚未签退）
            if existing_in_time and not existing_out_time:
                # 如果新签退时间早于现有签到时间，表示完全分离
                if new_out_time and new_out_time < existing_in_time:
                    continue
                
                # 否则需要合并
                records_to_merge.append((record_id, existing_in_time, existing_out_time))
            
            # 如果现有记录有完整的签到/签退时间
            elif existing_in_time and existing_out_time and new_out_time:
                # 检查两个时间段是否有交集
                # 两个时间段有交集的条件: not (新签出 < 旧签入 or 新签入 > 旧签出)
                if not (new_out_time < existing_in_time or new_in_time > existing_out_time):
                    # 有交集，需要合并
                    records_to_merge.append((record_id, existing_in_time, existing_out_time))
            
        # 如果没有找到需要合并的记录，插入新记录
        if not records_to_merge:
            cursor.execute("""
                INSERT INTO history (date, job_id, sign_in, sign_out)
                VALUES (?, ?, ?, ?)
            """, (date_str, job_id, sign_in, sign_out))
            
            conn.commit()
            return True, "新记录与现有记录无交集，已添加为独立记录"
        
        # 开始事务以确保操作的原子性
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # 计算所有需要合并的记录的时间并集
            # 初始化为新记录的时间
            earliest_in_time = new_in_time
            latest_out_time = new_out_time
            
            # 遍历所有需要合并的记录，找出最早的签到和最晚的签退
            for _, existing_in_time, existing_out_time in records_to_merge:
                if existing_in_time and existing_in_time < earliest_in_time:
                    earliest_in_time = existing_in_time
                
                if existing_out_time:
                    if not latest_out_time or existing_out_time > latest_out_time:
                        latest_out_time = existing_out_time
            
            # 转回字符串格式
            merged_sign_in = earliest_in_time.strftime("%H:%M")
            merged_sign_out = latest_out_time.strftime("%H:%M") if latest_out_time else ""
            
            # 保留第一条记录，删除其他所有记录
            first_record_id = records_to_merge[0][0]
            other_record_ids = [record[0] for record in records_to_merge[1:]]
            
            # 更新第一条记录
            cursor.execute("""
                UPDATE history
                SET sign_in = ?, sign_out = ?
                WHERE id = ?
            """, (merged_sign_in, merged_sign_out, first_record_id))
            
            # 删除其他记录
            if other_record_ids:
                placeholders = ','.join(['?'] * len(other_record_ids))
                cursor.execute(f"""
                    DELETE FROM history
                    WHERE id IN ({placeholders})
                """, other_record_ids)
            
            # 提交事务
            conn.commit()
            
            if len(records_to_merge) > 1:
                return True, f"已将新记录与{len(records_to_merge)}条现有记录合并"
            else:
                return True, "已将新记录合并到现有记录中"
            
        except Exception as e:
            # 出错时回滚事务
            conn.rollback()
            print(f"合并记录时出错: {e}")
            return False, f"合并记录时出错: {e}"
        
    except Exception as e:
        print(f"添加历史记录时出错：{e}")
        return False, f"数据库错误：{str(e)}"
    finally:
        close_sqlite(conn, cursor)

if __name__ == "__main__":
    vec = load_all_face_vector_from_people()[0][1]
    save_ins_to_people(202112135, "刘明宇", 1, face_vector=vec, is_manager=0)