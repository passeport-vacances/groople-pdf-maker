import pymysql


class DBConnection:

    def __init__(self, host, username, password, database, event):
        self.conn = pymysql.connect(
            host=host,
            user=username,
            passwd=password,
            db=database,
            cursorclass=pymysql.cursors.DictCursor,
        )
        self.event = event

    def all_users(self):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM users_full
              ORDER BY lastname, firstname"""
            cursor.execute(sql)
            return cursor.fetchall()

    def categories(self):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT distinct category_id, category_label
              FROM activities
              WHERE category_label != 'DUMMY'
              AND event_id = %s
              AND enabled = 1
              ORDER BY category_order;"""
            cursor.execute(sql, self.event)
            return cursor.fetchall()

    def activities(self, cat_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT *
              FROM activities
              WHERE category_id = %s
              AND enabled = 1
              ORDER BY activity_label;"""
            cursor.execute(sql, (cat_id))
            return cursor.fetchall()

    def attributes(self, activity_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT *
              FROM activities_attributes
              WHERE activity_id = %s"""
            cursor.execute(sql, (activity_id))
            return cursor.fetchall()

    def user_attributes(self, activity_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM _user_attributes, activities_users_attributes_values
              WHERE _user_attributes.attribute_id = activities_users_attributes_values.user_attribute_id
              AND activities_users_attributes_values.activity_id = %s
              ORDER BY order_field;"""
            cursor.execute(sql, (activity_id))
            return cursor.fetchall()

    def groups(self, activity_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM groups
              WHERE activity_id = %s"""
            cursor.execute(sql, (activity_id))
            return cursor.fetchall()

    def group_attributes(self, group_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM groups_attributes
              WHERE group_id = %s"""
            cursor.execute(sql, (group_id))
            return cursor.fetchall()

    def periods(self, group_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM groups_periods, periods
              WHERE groups_periods.period_id = periods.period_id
              AND group_id = %s"""
            cursor.execute(sql, (group_id))
            return cursor.fetchall()

    def users_by_group(self, group_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM users_groups, users_full
              WHERE users_groups.user_id = users_full.user_id
              AND group_id = %s
              ORDER BY lastname, firstname"""
            cursor.execute(sql, (group_id))
            return cursor.fetchall()

    def choices_by_user(self, user_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM choices
              WHERE user_id = %s
              ORDER BY id"""
            cursor.execute(sql, (user_id))
            return cursor.fetchall()

    def choices_by_activity(self, activity_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM choices
              WHERE activity_id = %s
              ORDER BY id"""
            cursor.execute(sql, (activity_id))
            return cursor.fetchall()

    def attributions_by_user(self, user_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM attributions
              WHERE user_id = %s
              ORDER BY id"""
            cursor.execute(sql, (user_id))
            return cursor.fetchall()

    def attributions_by_group(self, group_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT * FROM attributions
              WHERE group_id = %s
              ORDER BY id"""
            cursor.execute(sql, (group_id))
            return cursor.fetchall()
