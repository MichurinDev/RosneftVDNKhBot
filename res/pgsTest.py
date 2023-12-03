import psycopg2
from psycopg2 import Error
from data.postgresConfig import *

try:
    # Подключение к существующей базе данных
    connection = psycopg2.connect(user="postgres",
                                  password="420506",
                                  host="localhost",
                                  database="RosneftVDNKh")

    # Курсор для выполнения операций с базой данных
    cursor = connection.cursor()
    # Распечатать сведения о PostgreSQL
    print("Информация о сервере PostgreSQL")
    print(connection.get_dsn_parameters(), "\n")
    # Выполнение SQL-запроса
    cursor.execute("""SELECT * FROM "UsersInfo";""")
    # Получить результат
    record = cursor.fetchone()
    print(record)

except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL", error)

finally:
    if connection:
        cursor.close()
        connection.close()
        print("Соединение с PostgreSQL закрыто")