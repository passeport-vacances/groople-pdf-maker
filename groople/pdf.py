# Copyright 2016 Jacques Supcik / Passeport Vacances Fribourg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import jinja2
import os
import re
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

LATEX_SUBS = (
    (re.compile(r'\\'), r'\\textbackslash'),
    (re.compile(r'([{}_#%&$])'), r'\\\1'),
    (re.compile(r'~'), r'\~{}'),
    (re.compile(r'\^'), r'\^{}'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\.\.\.+'), r'\\ldots{} '),
    (re.compile(r'\x92'), r"'"),
    (re.compile(r'\x85'), r'\ldots{} '),
    (re.compile(r'\x96'), r'--'),
)


def escape_tex(value):
    newval = value
    for pattern, replacement in LATEX_SUBS:
        newval = pattern.sub(replacement, newval)
    return newval


def cell_break(value):
    value = re.sub(r'\n', r'\\newline{}', value)
    return value


def line_break(value):
    value = re.sub(r'\n', r'\\\n', value)
    return value


def make(categories, users, params, doc_src, main_tex, templates):
    logger.debug("Building template")
    cur_dir = os.getcwd()
    logger.debug("Current working directory : {0}".format(cur_dir))
    tmp_dir = tempfile.mkdtemp()
    logger.debug("Temp directory : {0}".format(tmp_dir))
    shutil.copytree(doc_src, os.path.join(tmp_dir, "tex"))
    os.chdir(os.path.join(tmp_dir, "tex"))

    texenv = jinja2.Environment(
        extensions=['jinja2.ext.do'],
        line_statement_prefix="#",
        line_comment_prefix="##",
        loader=jinja2.FileSystemLoader("."))
    texenv.block_start_string = '((*'
    texenv.block_end_string = '*))'
    texenv.variable_start_string = '((('
    texenv.variable_end_string = ')))'
    texenv.comment_start_string = '((='
    texenv.comment_end_string = '=))'
    texenv.filters['escape_tex'] = escape_tex
    texenv.filters['cell_break'] = cell_break
    texenv.filters['line_break'] = line_break

    logger.debug("Rendering")
    for k, v in templates.items():
        logger.debug("{0} -> {1}".format(k, v))
        template = texenv.get_template(k)
        f = open(v, mode="w", encoding="utf-8")
        f.write(template.render(data=categories, users=users, params=params))
        f.close()

    logger.debug("compiling latex")

    cmd = "latexmk -silent -f -pdf -pdflatex='xelatex' {0}".format(main_tex)
    logger.debug("> {0}".format(cmd))
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = p.communicate(timeout=300)
        logger.debug("return code: {0}".format(p.returncode))
        logger.debug("----- BEGIN STDOUT -----")
        logger.debug("\n" + out.decode("utf-8"))
        logger.debug("----- END STDOUT / BEGIN STDERR -----")
        logger.debug("\n" + err.decode("utf-8"))
        logger.debug("----- END STDERR -----")
    except Exception as e:
        logger.error(type(e))
        logger.error(e)
        return None

    cmd = "latexmk -silent -f -pdf -pdflatex='xelatex' -c {0}".format(main_tex)
    logger.debug("> {0}".format(cmd))
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = p.communicate(timeout=300)
        logger.debug("return code: {0}".format(p.returncode))
        logger.debug("----- BEGIN STDOUT -----")
        logger.debug("\n" + out.decode("utf-8"))
        logger.debug("----- END STDOUT / BEGIN STDERR -----")
        logger.debug("\n" + err.decode("utf-8"))
        logger.debug("----- END STDERR -----")
    except Exception as e:
        logger.error(type(e))
        logger.error(e)
        return None

    res = open(os.path.splitext(main_tex)[0] + ".pdf", "rb").read()
    os.chdir(cur_dir)

    logger.debug("Cleaning up {0}".format(tmp_dir))
    shutil.rmtree(tmp_dir)
    return res
