import pymysql

conn = pymysql.Connect(host='47.112.22.247', port=3306, user='novels', password='dPNSKNB6XnTyWNMz', db='novels', charset='utf8')
cursor = conn.cursor()
# 获取小说id新增小说章节总数字段
sql = 'select id from novels;'
cursor.execute(sql)
results = cursor.fetchall()
sql_chapter = "select count(id) from chapters where novelId='%s';"
sql_update = "update novels set chaptercount='%s' where id='%s';"
for result in results:
    novelId = result[0]
    cursor.execute(sql_chapter % novelId)
    chapter_count = cursor.fetchone()[0]
    cursor.execute(sql_update % (chapter_count, novelId))
    print(novelId)

# sql = 'insert into monthly_novel(novelId, monthlyId) values ("%s", "%s");'
# for x in range(600, 699):
#     cursor.execute(sql % (x, 6))
conn.commit()
cursor.close()
conn.close()




