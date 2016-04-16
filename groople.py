import logging
import pprint

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class Groople:

    age = "attribute_5"

    def __init__(self, conn):
        self.conn = conn

    def categories(self, event_id):
        with self.conn.cursor() as cursor:
            sql = """
              SELECT distinct category_id, category_label
              FROM activities
              WHERE category_label != 'DUMMY'
              AND event_id = %s
              AND enabled = 1
              ORDER BY category_order;"""
            cursor.execute(sql, (event_id))
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

    @staticmethod
    def aggregate_ages(l):
        gl = sorted([int(i.strip()) for i in l])  # type: list
        input_args = ", ".join([str(i) for i in gl]) # used for logging
        ranges = list()
        while len(gl) > 0:
            min_age = gl.pop(0)
            max_age = min_age
            while len(gl) > 0 and gl[0] == max_age + 1:
                max_age = gl.pop(0)
            ranges.append((min_age, max_age))
        rs = ["{0}-{1}".format(i[0], i[1]) for i in ranges]
        result = None
        if len(rs) > 1:
            rs_last = rs.pop()
            result = " et ".join([", ".join(rs), rs_last])
        else:
            result = rs[0]

        logger.debug("aggreate_ages({0}) = {1}".format(input_args, result))
        return result

    def data(self, event_id = "1277"):
        data = list()
        try:
            # Collecting categories
            for c in self.categories(event_id):
                cat = {
                    'category': c['category_label'].strip(),
                    'activities': list(),
                }
                logger.debug("Category: {0}".format(cat["category"]))

                # Collecting activities
                for a in self.activities(c['category_id']):
                    act = {
                        'titre': a['activity_label'].strip(),
                        'information': a['information'].strip(),
                        'fcfs': a['fcfs'],
                        'attr': dict(),
                        'uattr': dict(),
                        'groups': list(),
                    }
                    logger.debug("Activity: {0}".format(act["titre"]))

                    # Collecting attributes
                    for i in self.attributes(a['activity_id']):
                        k = i['attribute_label'].strip()
                        if k not in act['attr']:
                            act['attr'][k] = {'values': list()}
                        act['attr'][k]['values'].append(i['value'].strip())

                    # Produce joined values
                    for k in act['attr']:
                        act['attr'][k]['c_value'] = ", ".join(act['attr'][k]['values'])

                    # Collecting user_attributes
                    for i in self.user_attributes(a['activity_id']):
                        k = i['attribute_name'].strip()
                        if k not in act['uattr']:
                            act['uattr'][k] = {
                                'label': i['attribute_label'].strip(),
                                'values': list()
                            }
                        act['uattr'][k]['values'].append(i['attribute_value'].strip())

                    # Produce joined values
                    for k in act['uattr']:
                        act['uattr'][k]['c_value'] = ", ".join(act['uattr'][k]['values'])

                    # Aggregates age
                    if Groople.age in act['uattr']:
                        act['uattr'][Groople.age]['a_value'] = Groople.aggregate_ages(act['uattr'][k]['values'])

                    # Collecting groups
                    for g in self.groups(a['activity_id']):
                        group = {
                            'label': g['group_label'].strip(),
                            'minQuota': g['minQuota'],
                            'maxQuota': g['maxQuota'],
                            'fcfs': g['fcfs'],
                            'attr': dict(),
                            'periods': list(),
                        }

                        # Collecting group_attribtes
                        for ga in self.group_attributes(g['group_id']):
                            k = ga['attribute_label'].strip()
                            if k not in group['attr']:
                                group['attr'][k] = {
                                    'values': list()
                                }
                            group['attr'][k]['values'].append(ga['value'].strip())

                        # Produce joined values
                        for k in group['attr']:
                            group['attr'][k]['c_value'] = ", ".join(group['attr'][k]['values'])

                        # Collecting periods
                        for p in self.periods(g['group_id']):
                            group['periods'].append({
                                'name': p['period_name'].strip(),
                                'label': p['label'].strip(),
                                'period_label': p['period_label'].strip(),
                                'parent_period_label': p['parent_period_label'].strip(),
                            })
                        act['groups'].append(group)

                    cat['activities'].append(act)
                data.append(cat)

        finally:
            self.conn.close()

        logger.debug("----- BEGIN DATA -----")
        logger.debug("\n" + pprint.pformat(data, indent=1, width=120))
        logger.debug("----- END DATA -----")
        return data
