# Dummy SQL module for external SQL queries
import MySQLdb

class DataBaseConnection(object):
  def __init__(self, db, cursor):
    super(DataBaseConnection, self).__init__()

    self.db		= db
    self.cursor		= cursor

  def commit(self):
    self.query('COMMIT')

  def rollback(self):
    self.query('ROLLBACK')

  def query(self, q):
    self.cursor.execute(q)
    return self.cursor.fetchall()

  def close(self):
    self.cursor.close()

class DataBase(object):
  def __init__(self, **kwargs):
    super(DataBase, self).__init__()

    self.conn		= None
    self.kwargs		= kwargs

  def open(self):
    self.conn = MySQLdb.connect(charset = 'utf8', use_unicode = True, **self.kwargs)

  def connect(self):
    c = DataBaseConnection(self, self.conn.cursor())

    c.query('SET AUTOCOMMIT = 0')
    c.query('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    c.query('START TRANSACTION')

    return c

  def start_transaction(self):
    pass

  def commit(self):
    pass

  def rollback(self):
    pass
