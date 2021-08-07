import pymysql
import sys

class DBHepler:
    def __init__(self, host,
                 user,
                 password,
                 db,
                 port,
                 charset):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.port = port
        self.charset = charset
        self.con = pymysql.connect(host=self.host,
                                   user=self.user,
                                   password=self.password,
                                   db=self.db,
                                   port=self.port,
                                   charset=self.charset
                                   )

    def createCur(self, funcName=''):
        if funcName in ['getOne', 'getCol']:
            self.cur = self.con.cursor()
        else:
            self.cur = self.con.cursor(cursor=pymysql.cursors.DictCursor)

    def executeSql(self, sql, params):
        if params:
            result = self.cur.execute(sql, params)
        else:
            result = self.cur.execute(sql)
        return result

    def getSetting(self, params=()):
        self.createCur(sys._getframe().f_code.co_name)
        self.executeSql('select * from settings WHERE name=%s', params)
        results = self.cur.fetchone()
        return results
        
    def updateSetting(self, params=()):
        self.createCur(sys._getframe().f_code.co_name)
        results = self.executeSql('update settings set value=%s where name=%s', params)
        self.con.commit()
        return results

    def insert(self, table, data):
        self.createCur(sys._getframe().f_code.co_name)
        colStr = '(' + ','.join(data.keys()) + ')'
        vDataStr = ''
        for _ in data.keys():
            vDataStr += '%s,'
        vDataStr = vDataStr[:-1]
        vDataStr = '(' + vDataStr + ')'
        sql = 'insert into ' + table + colStr + ' values ' + vDataStr + ' ON DUPLICATE KEY UPDATE user_id=' + data['user_id']
        params = list(data.values())
        results = self.cur.execute(sql, params)
        self.con.commit()
        return results
