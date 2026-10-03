from multiprocessing import connection
import os

import pymysql
from dotenv import load_dotenv

import sqlglot
from sqlglot import exp

load_dotenv()


def get_connection():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

    return connection

def validate_sql(sql):
    try: 
        statements=sqlglot.parse(
            sql,
            read="mysql"
        )
    except Exception as e:
        raise ValueError(f"SQL语法解析失败: {e}")
    if len(statements)!=1:
        raise ValueError("只允许执行一条SQL语句")
    statement=statements[0]

    if not isinstance(statement,(exp.Select,exp.Union)):
        raise ValueError("只允许执行只读Select查询")
    return True

def execute_sql(sql):
    validate_sql(sql)
    
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()

        return result

    finally:
        connection.close()

def get_database_schema():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            schema_text = ""

            for table in tables:
                table_name = list(table.values())[0]

                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()

                schema_text += f"Table: {table_name}\n"

                for column in columns:
                    schema_text += (
                        f"- {column['Field']} "
                        f"{column['Type']}\n"
                    )

                schema_text += "\n"

        return schema_text

    finally:
        connection.close()

if __name__ == "__main__":
    result = get_database_schema()

    print(result)