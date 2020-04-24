import os
import sqlite3
import time

DATABASE = os.getcwd()+'/databases/userInfo.db'
TABLE = 'Users'


def index_replace(text, index=0, replacement=''):
    return '%s%s%s' % (text[:index], replacement, text[index + 1:])


class User:
    def __init__(self, bot, ctx, user=None):
        self.bot = bot
        self.ctx = ctx
        self.user = user if user else ctx.author

        self.conn = None

        try:
            self.conn = sqlite3.connect(DATABASE)
        except sqlite3.Error as e:
            print(e)
        self.cursor = self.conn.cursor()

        self._create_table()
        self._create_user()
        self._get_user_info()

    def close(self):
        self.conn.close()
        del self

    def _create_table(self):
        query = f"""CREATE TABLE IF NOT EXISTS {TABLE} (id BIGINT PRIMARY KEY, last_mod_mail BIGINT, out_going_mail BIGINT, closing_channel BIGINT)"""
        self.cursor.execute(query)
        self.conn.commit()

    def _create_user(self):
        try:
            query = f"""INSERT INTO {TABLE} VALUES (?, ?, ?, ?)"""
            self.cursor.execute(query, (self.user.id, time.time(), 0, 0))
            self.conn.commit()
        except sqlite3.Error:
            pass

    def _get_user_info(self):
        query = f"SELECT * FROM {TABLE} WHERE id = ?"
        self.cursor.execute(query, (self.user.id,))
        info = self.cursor.fetchall()
        if info:
            self.id = info[0][0]
            self.last_mod_mail = info[0][1]
            self.out_going_mail = bool(info[0][2])
            self.closing_channel = bool(info[0][3])
        else:
            self._create_user()
            self._get_user_info()

    def update_value(self, column, value):
        query = f"UPDATE {TABLE} SET {column} = ? WHERE id = ?"
        self.cursor.execute(query, (value, self.user.id,))
        self.conn.commit()
        self._get_user_info()
