import psycopg2
from postgresConfig import *

# Подгружаем БД
conn = psycopg2.connect(
    user=user,
    password=password,
    host=host,
    database=db_name
)

cursor = conn.cursor()

for line in open("res/data/OriginCSV/UTF8/encoded-Сompetencies.csv", encoding='utf-8'):
    if "sphere" not in line:
        cursor.execute("""INSERT INTO "Сompetencies" (sphere, name) VALUES (%s, %s)""",
                       line[:-1].split(";"))

conn.commit()
conn.close()
