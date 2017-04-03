import logging.handlers
import groople
import io
import pymysql
import argparse
import pdf

parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
parser.add_argument("--db-host", type=str, help="Database Host")
parser.add_argument("--db-user", type=str, help="Database Username")
parser.add_argument("--db-password", type=str, help="Database Password")
parser.add_argument("--db-database", type=str, help="Database Name")
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


def gen_pdf(**kwargs):
    params = dict()
    for key, value in iter(kwargs.items()):
        params[key] = value

    conn = pymysql.connect(
        host=args.db_host,
        user=args.db_user,
        passwd=args.db_password,
        db=args.db_database,
        cursorclass=pymysql.cursors.DictCursor,
    )

    logger.debug("fetching data")
    data = groople.Groople(conn).data()

    logger.debug("building PDF from LaTeX")
    pdfs = pdf.make(
        data, params,
        doc_src="doc_src",
        main_tex="pvf2016.tex",
        templates={
            "template.tex": "pvf2016.tex"})

    return io.BufferedReader(io.BytesIO(pdfs))


def livret():
    logger.debug("Making livret")
    fd = gen_pdf(onepage=False)
    dst = open("livret-light.pdf", "wb")
    dst.write(fd.read())
    dst.close()
    fd.close()


def bons_a_tirer():
    logger.debug("Making bons à tirer")
    fd = gen_pdf(onepage=True, users=True, chauffeur=True, xtra=False)
    dst = open("participants.pdf", "wb")
    dst.write(fd.read())
    dst.close()
    fd.close()


def main():
    bons_a_tirer()


if __name__ == '__main__':
    main()





c = groople.http_client.HttpClient('passvac.fribourg@bluewin.ch', '15GDsasF34', '1277')
c.login()
print (c.userInfo("207795"))
print (c.initialChoices("207795"))
