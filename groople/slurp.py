import logging
import pprint
import re

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class Slurper:

    age = "attribute_5"
    tel1 = "attribute_6"
    tel2 = "attribute_7"

    def __init__(self, dbConn, httpClient=None):
        self.dbConn = dbConn
        self.httpClient = httpClient

    @staticmethod
    def groupkey(x):
        m = re.search(r'(\d+)\D+(\d+)', x['label'])
        if m:
            return "{0:04d}{1:04d}".format(int(m.group(1)), int(m.group(2)))
        else:
            return x['label']

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

    def data(self):
        categories = list()
        users = dict()

        try:
            for u in self.dbConn.all_users():

                tel1 = u[Slurper.tel1].strip() if u[Slurper.tel1] is not None else None
                tel2 = u[Slurper.tel2].strip() if u[Slurper.tel2] is not None else None

                user = {
                    'user_id': u['user_id'],
                    'username': u['username'].strip(),
                    'firstname': u['firstname'].strip(),
                    'lastname': u['lastname'].strip(),
                    'email': u['email'].strip(),
                    'age': u[Slurper.age],
                    'tel1': tel1 if tel1 is not None else "",
                    'tel2': tel2 if tel2 is not None else "",
                    'tel': " / ".join([i for i in [tel1, tel2] if i is not None]),
                    'active': u['active'],
                    'confirmed': u['confirmed'],
                    'choices': list(),
                    'attributions': list(),
                }

                for p in self.dbConn.choices_by_user(u['user_id']):
                    user['choices'].append({
                        'activity_id': p['activity_id'],
                        'remark': p['remark'],
                        'hasBeenSelected': p['hasBeenSelected'],
                    })

                for p in self.dbConn.attributions_by_user(u['user_id']):
                    user['attributions'].append({
                        'group_id': p['group_id'],
                        'remark': p['remark'],
                        'hasBeenChosen': p['hasBeenChosen'],
                    })

                users[u['user_id']] = user
                logger.debug("User: {0} {1}".format(user['firstname'], user['lastname']))

            # Collecting categories
            for c in self.dbConn.categories():
                cat = {
                    'category': c['category_label'].strip(),
                    'activities': list(),
                }
                logger.debug("Category: {0}".format(cat["category"]))

                # Collecting activities
                for a in self.dbConn.activities(c['category_id']):
                    act = {
                        'titre': a['activity_label'].strip(),
                        'information': a['information'].strip(),
                        'fcfs': a['fcfs'],
                        'attr': dict(),
                        'uattr': dict(),
                        'groups': list(),
                        'choices': list(),
                    }
                    logger.debug("Activity: {0}".format(act["titre"]))

                    # Collecting attributes
                    for i in self.dbConn.attributes(a['activity_id']):
                        k = i['attribute_label'].strip()
                        if k not in act['attr']:
                            act['attr'][k] = {'values': list()}
                        act['attr'][k]['values'].append(i['value'].strip())

                    # Produce joined values
                    for k in act['attr']:
                        act['attr'][k]['c_value'] = ", ".join(act['attr'][k]['values'])

                    # Collecting user_attributes
                    for i in self.dbConn.user_attributes(a['activity_id']):
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
                    if Slurper.age in act['uattr']:
                        act['uattr'][Slurper.age]['a_value'] = Slurper.aggregate_ages(act['uattr'][k]['values'])

                    # Collect choices
                    for p in self.dbConn.choices_by_activity(a['activity_id']):
                        act['choices'].append({
                            'user_id': p['user_id'],
                            'remark': p['remark'],
                            'hasBeenSelected': p['hasBeenSelected'],
                        })

                    # Collecting groups
                    for g in self.dbConn.groups(a['activity_id']):
                        group = {
                            'label': g['group_label'].strip(),
                            'minQuota': g['minQuota'],
                            'maxQuota': g['maxQuota'],
                            'fcfs': g['fcfs'],
                            'attr': dict(),
                            'periods': list(),
                            'users': list(),
                            'attributions': list(),
                        }

                        # Collecting group_attribtes
                        for ga in self.dbConn.group_attributes(g['group_id']):
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
                        for p in self.dbConn.periods(g['group_id']):
                            group['periods'].append({
                                'name': p['period_name'].strip(),
                                'label': p['label'].strip(),
                                'period_label': p['period_label'].strip(),
                                'parent_period_label': p['parent_period_label'].strip(),
                            })

                        # Collecting users
                        for p in self.dbConn.users_by_group(g['group_id']):
                            group['users'].append({
                                'user_id': p['user_id'],
                                'remark': p['remark'],
                            })

                        for p in self.dbConn.attributions_by_group(g['group_id']):
                            group['attributions'].append({
                                'user_id': p['user_id'],
                                'remark': p['remark'],
                                'hasBeenChosen': p['hasBeenChosen'],
                            })

                        act['groups'].append(group)

                    act['groups'].sort(key=self.groupkey)
                    cat['activities'].append(act)
                categories.append(cat)

        finally:
            self.dbConn.conn.close()

        # logger.debug("----- BEGIN DATA -----")
        # logger.debug("\n" + pprint.pformat(categories, indent=1, width=120))
        # logger.debug("----- END DATA -----")
        return categories, users
