import logging.handlers
import groople.sql
import groople.http_client
import groople.slurp
import groople.pdf
import io
import argparse
import pprint

parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
parser.add_argument("--db-host", type=str, help="Database Host")
parser.add_argument("--db-user", type=str, help="Database Username")
parser.add_argument("--db-password", type=str, help="Database Password")
parser.add_argument("--db-database", type=str, help="Database Name")
parser.add_argument("--event-no", type=str, help="Event No")
parser.add_argument("--debug", action="store_true", help="debug mode")

args = parser.parse_args()

logger = logging.getLogger(__name__)

loggers = [
    logger,
    logging.getLogger('groople'),
    logging.getLogger('pdf'),
]

log_formatter = logging.Formatter(
    '%(asctime)s %(name)-10s %(levelname)-8s %(message)s')

handler = logging.StreamHandler()
handler.setFormatter(log_formatter)

if args.debug:
    for l in loggers:
        l.addHandler(handler)
        l.setLevel(logging.DEBUG)
else:
    for l in loggers:
        l.addHandler(handler)
        l.setLevel(logging.INFO)


def gen_pdf(main_tex, **kwargs):
    params = dict()
    for key, value in iter(kwargs.items()):
        params[key] = value

    dbConn = groople.sql.DBConnection(
        host=args.db_host,
        username=args.db_user,
        password=args.db_password,
        database=args.db_database,
        event=args.event_no,
    )

    logger.debug("fetching data from {0}".format(args.db_database))
    categories, users = groople.slurp.Slurper(dbConn).data()

    if kwargs['filter'] == "LIGHT":
        pprint.pprint(categories)
        for cat in categories:
            a = list()
            for act in cat['activities']:
                if (len(act['groups'])) == 0:
                    a.append(act)
                else:
                    g = [i for i in act['groups'] if i['maxQuota'] is None or i['maxQuota'] > 100]
                    act['groups'] = g
                    if len(act['groups']) > 0:
                        a.append(act)
            cat['activities'] = a
        categories = [i for i in categories if len(i['activities']) > 0]


    logger.debug("building PDF from LaTeX")
    pdfs = groople.pdf.make(
        categories, users, params,
        doc_src="doc_src",
        main_tex=main_tex,
        templates={
            "inc/activities_j2.tex": "inc/activities.tex"})

    return io.BufferedReader(io.BytesIO(pdfs))

def send_mails(template, **kwargs):
    params = dict()
    for key, value in iter(kwargs.items()):
        params[key] = value

    dbConn = groople.sql.DBConnection(
        host=args.db_host,
        username=args.db_user,
        password=args.db_password,
        database=args.db_database,
        event=args.event_no,
    )

    logger.debug("fetching data")
    categories, users = groople.slurp.Slurper(dbConn).data()

    if kwargs['filter'] == "LIGHT":
        pprint.pprint(categories)
        for cat in categories:
            a = list()
            for act in cat['activities']:
                if (len(act['groups'])) == 0:
                    a.append(act)
                else:
                    g = [i for i in act['groups'] if i['maxQuota'] is None or i['maxQuota'] > 100]
                    act['groups'] = g
                    if len(act['groups']) > 0:
                        a.append(act)
            cat['activities'] = a
        categories = [i for i in categories if len(i['activities']) > 0]


    logger.debug("building PDF from LaTeX")
    pdfs = pdf.make(
        categories, users, params,
        doc_src="doc_src",
        main_tex="pvf2016.tex",
        templates={
            template: "pvf2016.tex"})

    return io.BufferedReader(io.BytesIO(pdfs))


def livret():
    logger.debug("Making livret")
    fd = gen_pdf("template_light.tex", onepage=False, filter=None)
    dst = open("livret.pdf", "wb")
    dst.write(fd.read())
    dst.close()
    fd.close()


def bons_a_tirer():
    logger.debug("Making bons à tirer")
    # fd = gen_pdf("template_orga.tex", onepage=True, users=True, chauffeur=False, xtra=False)
    fd = gen_pdf("pvfr_bat.tex", onepage=True, filter=None, users=False, chauffeur=False, xtra=False)
    dst = open("bons_a_tirer.pdf", "wb")
    dst.write(fd.read())
    dst.close()
    fd.close()


def main():
    # livret()
    bons_a_tirer()


if __name__ == '__main__':
    main()
