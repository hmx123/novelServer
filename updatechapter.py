import pymysql


conn = pymysql.Connect(host='localhost', port=3306, user='novels', password='dPNSKNB6XnTyWNMz', db='novels', charset='utf8')
cursor = conn.cursor()

sql = "select content,chapterId from contents"
cursor.execute(sql)
result = cursor.fetchall()
sql = "update chapters set words='%s' where id='%s'"

for res in result:
    cursor.execute(sql % (len(res[0]), res[1]))
    print(res[1])
conn.commit()
