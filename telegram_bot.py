from telegram.ext import Updater
import logging
import logging.handlers
import groople
import io
import pymysql
import argparse
import pdf

parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
parser.add_argument("--bot-token", type=str, help="Bot secret Token")
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
    logging.getLogger('telegram'),
]

log_formatter = logging.Formatter(
    '%(asctime)s %(name)-10s %(levelname)-8s %(message)s')

if args.debug:
    handler = logging.StreamHandler()
    handler.setFormatter(log_formatter)
    for l in loggers:
        l.addHandler(handler)
        l.setLevel(logging.DEBUG)
else:
    handler = logging.handlers.RotatingFileHandler(
        "/var/log/groople-pdf-maker.log",
        mode='a', maxBytes=32 * 1024 * 1024, backupCount=5, encoding="UTF-8")
    handler.setFormatter(log_formatter)
    for l in loggers:
        l.addHandler(handler)
        l.setLevel(logging.INFO)


def gen_pdf(one_page = False):
    conn = pymysql.connect(
        host=args.db_host,
        user=args.db_user,
        passwd=args.db_password,
        db=args.db_database,
        cursorclass=pymysql.cursors.DictCursor,
    )

    logger.debug("fetching data")
    data = groople.Groople(conn).data()

    params = {'onepage': 0}
    if one_page:
        params['onepage'] = 1

    logger.debug("building PDF from LaTeX")
    pdfs = pdf.make(
        data, params,
        doc_src="doc_src",
        main_tex="pvf2016.tex",
        templates={
            "template.tex": "pvf2016.tex"})

    return io.BufferedReader(io.BytesIO(pdfs))


def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Bonjour')


def livret(bot, update):
    logger.debug("Making livret")
    bot.sendMessage(update.message.chat_id, text='Je prépare le livret... patience.')
    fd = gen_pdf(one_page=False)
    bot.sendDocument(update.message.chat_id, fd, filename="livret_2016.pdf")


def bons_a_tirer(bot, update):
    logger.debug("Making bons à tirer")
    bot.sendMessage(update.message.chat_id, text='Je prépare les bons à tirer... patience.')
    fd = gen_pdf(one_page=True)
    bot.sendDocument(update.message.chat_id, fd, filename="bons_a_tirer_2016.pdf")


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(args.bot_token)
    dp = updater.dispatcher
    dp.addTelegramCommandHandler("start", start)
    dp.addTelegramCommandHandler("livret", livret)
    dp.addTelegramCommandHandler("bons_a_tirer", bons_a_tirer)

    dp.addErrorHandler(error)

    logger.info("Bot ready")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
