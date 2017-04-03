import logging.handlers
import os

import groople.sql
import groople.http_client
import groople.slurp
import groople.pdf
import io
import argparse
import flask

app = flask.Flask(__name__)

parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
parser.add_argument(
    "--db-host", type=str,
    default=os.getenv("GROOPLE_DB_HOST", "phpmyadmin.groople.me"),
    help="Database Host"
)

parser.add_argument(
    "--db-user", type=str,
    default=os.getenv("GROOPLE_DB_USERNAME"),
    help="Database Username"
)

parser.add_argument(
    "--db-password", type=str,
    default=os.getenv("GROOPLE_DB_PASSWORD"),
    help="Database Password"
)

parser.add_argument(
    "--db-database", type=str,
    default=os.getenv("GROOPLE_DB_NAME"),
    help="Database Name"
)

parser.add_argument(
    "--event-no", type=str,
    default=os.getenv("GROOPLE_DB_EVENT_NO"),
    help="Event No"
)

parser.add_argument(
    "--debug", action="store_true",
    help="debug mode"
)

parser.add_argument(
    "--no-cleanup", action="store_true",
    help="do not remove temp directory"
)


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

    logger.debug("building PDF from LaTeX")
    pdfs = groople.pdf.make(
        categories, users, params,
        doc_src="doc_src",
        main_tex=main_tex,
        templates={
            "inc/activities_j2.tex": "inc/activities.tex"
        },
        cleanup=not args.no_cleanup,
    )

    return io.BufferedReader(io.BytesIO(pdfs))


@app.route("/livret")
def livret():
    logger.debug("Making livret")
    fd = gen_pdf("template_light.tex", onepage=False, filter=None)
    dst = open("livret.pdf", "wb")
    dst.write(fd.read())
    dst.close()
    fd.close()


@app.route("/bons-a-tirer")
def bons_a_tirer():
    logger.debug("Making bons à tirer")
    fd = gen_pdf("pvfr_bat.tex", onepage=True, filter=None, users=False, chauffeur=False, xtra=False)
    return flask.send_file(fd, mimetype="application/pdf", as_attachment=True, attachment_filename="bon-a-tirer.pdf")
#    fd.close()
#    return res

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)