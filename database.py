# import mysql.connector

# import pymysql

# def connect():
#     return pymysql.connect(
#         host="localhost",
#         user="root",
#         password="",
#         database="multiflex",
#         cursorclass=pymysql.cursors.DictCursor
#     )



# # ✅ SELECT — returns list of dictionaries
# import pymysql
# def select(q):
#     con = pymysql.connect(host="localhost", user="root", password="", db="multiflex", cursorclass=pymysql.cursors.DictCursor)
#     cur = con.cursor()
#     cur.execute(q)
#     result = cur.fetchall()
#     con.close()
#     return result



# # ✅ INSERT — returns inserted row ID
# def insert(query):
#     con = connect()
#     cur = con.cursor()
#     cur.execute(query)
#     con.commit()
#     inserted_id = cur.lastrowid
#     con.close()
#     return inserted_id


# # ✅ UPDATE
# def update(q):
#     con = pymysql.connect(host='localhost', user='root', password='', db='multiflex', charset='utf8')
#     cur = con.cursor()
#     cur.execute(q)
#     con.commit()
#     con.close()
#     return cur.rowcount


# # ✅ DELETE
# def delete(query):
#     con = connect()
#     cur = con.cursor()
#     cur.execute(query)
#     con.commit()
#     con.close()
#     return True
import pymysql

def connect():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',  # leave empty if you didn't set a password in WAMP
        database='multiflex',
        port=3309,  # default WAMP port for MySQL (change if yours is different)
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def select(query):
    con = connect()
    cur = con.cursor()
    cur.execute(query)
    result = cur.fetchall()
    con.close()
    return result

def insert(query):
    con = connect()
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    last_id = cur.lastrowid
    con.close()
    return last_id

def update(query):
    con = connect()
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    con.close()

def delete(query):
    con = connect()
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    con.close()


