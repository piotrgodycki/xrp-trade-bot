import sqlite3

class OrderDB:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self._init_db()

    def _init_db(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS orders
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      buy_price REAL, amount REAL, sell_price REAL,
                      sell_order_id TEXT UNIQUE, status TEXT)''')
        self.conn.commit()

    def record_order(self, buy_price, amount, sell_price, sell_order_id):
        c = self.conn.cursor()
        c.execute("INSERT INTO orders (buy_price, amount, sell_price, sell_order_id, status) VALUES (?,?,?,?,?)",
                  (buy_price, amount, sell_price, sell_order_id, 'open'))
        self.conn.commit()

    def update_order_status(self, sell_order_id, status):
        c = self.conn.cursor()
        c.execute("UPDATE orders SET status=? WHERE sell_order_id=?", (status, sell_order_id))
        self.conn.commit()

    def get_open_orders(self):
        c = self.conn.cursor()
        c.execute("SELECT sell_order_id FROM orders WHERE status='open'")
        return [row[0] for row in c.fetchall()]
