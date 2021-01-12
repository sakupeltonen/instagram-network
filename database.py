import sqlite3
from datetime import date

sql_create_account_table = \
    """CREATE TABLE IF NOT EXISTS accounts (
    username varchar(30) PRIMARY KEY,
    private integer,
    post_count varchar(8),
    followers_count varchar(8),
    following_count varchar(8),
    followers_updated_date varchar(15),
    following_updated_date varchar(15),
    name varchar(30),
    bio varchar(30),
    username_changed integer
    );"""
# SQLite does not enforce the size set to varchar

sql_create_follower_table = \
    """CREATE TABLE IF NOT EXISTS followers (
    source varchar(30) NOT NULL,
    target varchar(30) NOT NULL,
    PRIMARY KEY(source, target),
    FOREIGN KEY (source) REFERENCES accounts (username),
    FOREIGN KEY (target) REFERENCES accounts (username)
    );"""

sql_create_picture_table = \
    """CREATE TABLE IF NOT EXISTS pictures (
    id varchar(10) PRIMARY KEY,
    username varchar(30) NOT NULL,
    description varchar(30)
    );"""

accounts_columns = ["private", "post_count", "followers_count", "following_count",
                    "followers_updated_date", "following_updated_date",
                    "name", "bio", "username_changed"]

get_commands = {
    "all_info": """SELECT * FROM accounts WHERE username=?""",
    "unseen": """SELECT username FROM accounts WHERE followers_updated_date IS NULL"""
}


class UserDatabase:
    def __init__(self, path):
        self.path = path
        self.conn = None
        self.cursor = None
        try:
            self.conn = sqlite3.connect(path)
            cursor = self.conn.cursor()
            self.cursor = cursor
            cursor.execute(sql_create_account_table)
            cursor.execute(sql_create_follower_table)
            cursor.execute(sql_create_picture_table)
        except sqlite3.Error as e:
            print(e)

    def close(self):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def simple_query(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def insert_user(self, username):
        """Adds new user(s) without other data"""
        sql_insert_user = \
            """INSERT OR IGNORE INTO accounts(username) VALUES (?);"""
        if isinstance(username, str):
            data = [(username,)]
        else:  # list of user names
            data = [(x,) for x in username]
        self.cursor.executemany(sql_insert_user, data)

    def get(self, task, username):
        """Applies get-type command on username(s) for get_commands[task]"""
        sql = get_commands[task]

        if isinstance(username, str):
            self.cursor.execute(sql, (username,))
            return self.cursor.fetchone()

        assert isinstance(username, list), "Can't perform {} on {}".format(task, username)
        res = []
        for i in range(len(username)):
            self.cursor.execute(sql, (username[i],))
            res.append(self.cursor.fetchone())
        return res

    def set(self, username, data):
        """Sets username(s)'s info according to data dict(s)"""
        if isinstance(username, str):
            username, data = [username], [data]

        columns = data[0].keys()
        assert all([column in accounts_columns for column in columns]), \
            "Error: unknown columns: {}".format(columns)
        _sql = "=?, ".join(columns) + "=?"
        sql = """UPDATE accounts SET {} WHERE username=?""".format(_sql)

        for i in range(len(username)):
            data_list = [data[i][key] for key in accounts_columns if key in columns]
            self.cursor.execute(sql, (*data_list, username[i]))

    def insert_followers(self, target, followers):
        self._update_date(target, "followers")
        self.insert_user(followers)
        target = [target] * len(followers)
        self._insert_foll(followers, target)

    def insert_following(self, source, following):
        self._update_date(source, "following")
        self.insert_user(following)
        source = [source] * len(following)
        self._insert_foll(source, following)

    def _update_date(self, username, foll):
        column_name = foll + "_updated_date"
        date_today = str(date.today())
        self.set(username, {column_name: date_today})

    def _insert_foll(self, source, target):
        sql = """INSERT OR IGNORE INTO followers(source, target) VALUES (?, ?);"""
        pairs = zip(source, target)
        self.cursor.executemany(sql, pairs)

    def insert_post_descriptions(self, username, descriptions):
        sql = """INSERT OR IGNORE INTO pictures(id, username, description) VALUES (?, ?, ?);"""
        triples = [(desc[0], username, desc[1]) for desc in descriptions]
        self.cursor.executemany(sql, triples)

    def get_followers(self, target):
        return self._get_foll(target, "followers")

    def get_following(self, source):
        return self._get_foll(source, "following")

    def _get_foll(self, username, foll):
        if foll == "following":
            sql = """SELECT target FROM followers WHERE source=?"""
        else:
            sql = """SELECT source FROM followers WHERE target=?"""

        self.cursor.execute(sql, (username,))
        records = self.cursor.fetchall()
        usernames = [record[0] for record in records]
        return usernames

    def mark_username_changed(self, username):
        self.set(username, {"username_changed": 1})



