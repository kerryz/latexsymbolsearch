# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import os
from bs4 import BeautifulSoup
import requests
import json

from global_constants import STORED_PRE, COMMANDS, KEYWORDS, IMG_SRCS, CONTENT, HTML

WIKIPEDIA_ROOT_URL = "http://en.wikipedia.org/wiki/List_of_mathematical_symbols"
WIKIBOOKS_ROOT_URL = "http://en.wikibooks.org/wiki/LaTeX/Mathematics"
WIKIPEDIA_FILEPATH = os.path.join(
    "..", "data", "html",
    "List of mathematical symbols - Wikipedia, the free encyclopedia.html")
WIKIBOOKS_FILEPATH = os.path.join(
    "..", "data", "html",
    "LaTeX_Mathematics - Wikibooks, open books for an open world.html")
# HTML_PATH_FROM_SERVER = os.path.join("..", "data", "html")
HTML_PATH_FROM_SERVER = "/static"

# https://www.sharelatex.com/learn/Spacing_in_math_mode
LATEX_SPACE_CMDS = [
    "\\quad",
    "\\,",
    "\\:",
    "\\;",
    "\\!",
    "\\ ",
    "\\qquad"
]


def main():
    documents = get_documents()


class LatexDocumentModel(object):
    def __init__(self, img_srcs=None, commands=None, keywords=None, content=None, html=None):
        """
        Parameters
        ----------
        img_srcs : list
            list of file paths to the latex symbol images that represent this document
        commands : list
            list of latex commands that represent this document, e.g. [u"\\empty", u"\\varnothing"]
        content : str
            the description of the symbol as a string
            this is the string that will be indexed
        html :
            the html representation of `content`.
            This is what is stored and later retrieved by the searcher.
        """
        self.img_srcs = img_srcs
        self.commands = commands
        self.keywords = keywords
        self.content = content
        self.html = html

    def get_kwargs(self):
        """
        The kwargs that the whoosh writer will store, use as:
            kwargs = latexDocumentModelInstance.get_kwargs()
            writer.add_document(**kwargs)
        """
        # index commands without start \ to better match query
        indexed_commands = []
        for cmd in self.commands:
            if cmd and cmd[0] == "\\":
                indexed_commands.append(cmd[1:])
            else:
                indexed_commands.append(cmd)
        return {
            IMG_SRCS: " ".join(self.img_srcs),
            STORED_PRE+IMG_SRCS: json.dumps(self.img_srcs),
            COMMANDS: indexed_commands,
            STORED_PRE+COMMANDS: " ".join(self.commands),
            KEYWORDS: self.keywords,
            STORED_PRE+COMMANDS: json.dumps(self.commands),
            CONTENT: self.content,
            HTML: self.html
        }

    def __str__(self):
        return " ".join(self.commands)

    def __repr__(self):
        return " ".join(self.commands)


def get_documents():
    documents_list = []
    found_commands = set()
    get_wikipedia_documents(documents_list, found_commands)
    get_wikibooks_documents(documents_list, found_commands)
    return documents_list


def get_wikipedia_documents(documents_list, found_commands):
    """documents_list is a list of LatexDocumentModel"""
    # get webpage
    # r = requests.get(WIKIPEDIA_ROOT_URL)
    # html_page = r.text

    # get webpage file
    with open(WIKIPEDIA_FILEPATH) as f:
        html_page = f.read()

    soup = BeautifulSoup(html_page)

    # replace all image src
    imgs = soup.find_all("img")
    for img in imgs:
        img["src"] = HTML_PATH_FROM_SERVER + img["src"][1:]

    # extract data
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")[3:]  # removing table headers
        # print len(rows)
        i = 0
        while i < len(rows):
            # find the table rows that belong to one symbol
            row_span = int(rows[i].find("td")["rowspan"])
            symbol_rows = rows[i:i+row_span]
            # extract the text from "name / read as / category" and use as keywords
            keywords_list = []
            for r_idx, sr in enumerate(symbol_rows):
                name_cell_idx = 2 if r_idx == 0 else 0
                name_cell = sr.find_all("td")[name_cell_idx]
                keywords_list += [word for word in list(name_cell.stripped_strings)]
                # remove semi colon from keywords
                for w_idx, word in enumerate(keywords_list):
                    if word and word[-1] == ";":
                        keywords_list[w_idx] = word[:-1]
            keywords_str = " ".join(keywords_list)
            # remove html tags to get a string to index
            symbol_idx_str = ""
            for sr in symbol_rows:  # type(sr) == Tag
                for s in sr.stripped_strings:  # type(sr.strippedstrings) == generator
                    symbol_idx_str += " " + s
            # add the latex commands used to produce the equation images
            symbol_rows_str = "<table>" +\
                "\n".join([unicode(row) for row in symbol_rows]) + "</table>"
            symbol_rows_soup = BeautifulSoup(symbol_rows_str)
            # symbol_rows_soup = BeautifulSoup(
            #     "".join([unicode(row) for row in symbol_rows]), 'html5lib')
            table_cells = symbol_rows_soup.find_all("td")
            for td in table_cells:
                for img in reversed(td.find_all("img")):
                    img_cmd_raw = img["alt"].strip()
                    img_cmd = strip_latex_spaces(img_cmd_raw)
                    cmd_html = symbol_rows_soup.new_tag("code", **{"class": "eqn-cmd"})
                    cmd_html.string = img_cmd
                    img_clone = BeautifulSoup(unicode(img)).body.contents[0]
                    wrapper = symbol_rows_soup.new_tag("span", **{"class": "eqn-wrapper"})
                    wrapper.insert(0, img_clone)
                    wrapper.insert(0, cmd_html)
                    img.replace_with(wrapper)
                    # img.insert_after(cmd_html)
                    # img.insert_after(symbol_rows_soup.new_tag("br"))
            # symbol images
            symbol_imgs = symbol_rows[0].find_all("td")[1].find_all("img")
            if not symbol_imgs:
                # no latex symbol, skip this
                i += row_span
                continue
            symbol_cmds = []
            symbol_img_srcs = []
            already_collected = False
            for symbol_img in symbol_imgs:
                symbol_cmd_raw = symbol_img["alt"].strip()
                symbol_cmd = strip_latex_spaces(symbol_cmd_raw)
                if symbol_cmd in found_commands and len(symbol_imgs) == 1:
                    already_collected = True
                    break
                # if symbol_cmd and symbol_cmd[0] == "\\":
                #     symbol_cmd = symbol_cmd[1:]
                symbol_cmds.append(symbol_cmd)
                found_commands.add(symbol_cmd)
                symbol_img_src = symbol_img["src"].strip()  # .split(os.path.sep)[-1]
                symbol_img_srcs.append(symbol_img_src)
            if already_collected:
                i += row_span
                continue
            # get the html table rows of the symbol: <tr>...</tr><tr>...</tr>
            # symbol_rows_soup = BeautifulSoup("".join([unicode(row) for row in symbol_rows]))
            tds = symbol_rows_soup.find("tr").find_all("td")
            """
            td0 = symbol_rows_soup.new_tag("td", rowspan=row_span, align="center")
            for sym_idx in reversed(xrange(len(symbol_imgs))):
                td0.insert(0, symbol_imgs[sym_idx])
                if sym_idx != 0:
                    td0.insert(0, symbol_rows_soup.new_tag("br"))
                    td0.insert(0, symbol_rows_soup.new_tag("br"))
            tds[0].replace_with(td0)
            """
            img_cell_clone = BeautifulSoup(
                "<table><tr>" + unicode(tds[1]) + "</tr></td>").find("td")
            tds[0].replace_with(img_cell_clone)
            [e.extract() for e in tds[1].find_all()]
            for cmd_idx, cmd in enumerate(reversed(symbol_cmds)):
                code_tag = symbol_rows_soup.new_tag("code")
                code_tag.string = cmd
                tds[1].insert(0, code_tag)
                if len(symbol_cmds) > 1 and cmd_idx > 0:
                    tds[1].insert(1, symbol_rows_soup.new_tag("br"))
                    tds[1].insert(2, symbol_rows_soup.new_tag("br"))
            trs = symbol_rows_soup.find_all("tr")
            symbol_html = "\n".join([unicode(tr) for tr in trs])

            documents_list.append(LatexDocumentModel(
                img_srcs=symbol_img_srcs,
                commands=symbol_cmds,
                keywords=keywords_str,
                content=symbol_idx_str,
                html=symbol_html
            ))

            i += row_span
        # end while(i < len(rows))
    # end for table in tables
    return documents_list


def get_wikibooks_documents(documents_list, found_commands):
    # get webpage file
    with open(WIKIBOOKS_FILEPATH) as f:
        html_page = f.read()

    soup = BeautifulSoup(html_page)

    # replace all image src and add <code>
    imgs = soup.find_all("img")
    for img in imgs:
        img["src"] = HTML_PATH_FROM_SERVER + img["src"][1:]
        try:
            img_cmd_raw = img["alt"].strip()
            img_cmd = strip_latex_spaces(img_cmd_raw)
            cmd_html = soup.new_tag("code", **{"class": "eqn-cmd"})
            cmd_html.string = img_cmd
            img_clone = BeautifulSoup(unicode(img)).body.contents[0]
            wrapper = soup.new_tag("span", **{"class": "eqn-wrapper"})
            wrapper.insert(0, img_clone)
            wrapper.insert(0, cmd_html)
            img.replace_with(wrapper)
        except KeyError:
            pass
    for td in soup.find_all("td"):
        print
        print td.prettify()
        pass

    # extract data
    tables = soup.find_all("table")
    correct_captions = set([
        "Relation Symbols",
        "Binary Operations",
        "Set and/or Logic Notation",
        "Delimiters",
        "Greek Letters",
        "Other symbols",
        "Trigonometric Functions"
    ])
    for table in tables:
        caption = table.find("caption")
        if caption is None:
            continue
        caption_str = caption.string.strip()
        if caption_str in correct_captions:
            rows = table.find_all("tr")[1:]  # skip header
            for row in rows:
                cells = row.find_all("td")
                i = 0
                while i < len(cells):
                    symbol_cmds = []
                    img_cell = cells[i]
                    # get commands from the command table cell
                    cmd_cell = cells[i+1]
                    cmds = list(cmd_cell.stripped_strings)
                    if not cmds:
                        i += 2
                        continue
                    if len(cmds) > 1:
                        cmds = [cmd for cmd in cmds if cmd != "and" and cmd != "or"]
                    already_collected = False
                    for cmd in cmds:
                        if cmd in found_commands:
                            already_collected = True
                    if already_collected and len(cmds) == 1:
                        i += 2
                        continue
                    for cmd in cmds:
                        symbol_cmds.append(cmd)
                        found_commands.add(cmd)
                    # get image info from the image cel
                    symbol_imgs = img_cell.find_all("img")
                    symbol_img_srcs = []
                    for symbol_img in symbol_imgs:
                        symbol_img_src = symbol_img["src"].strip()  # .split(os.path.sep)[-1]
                        symbol_img_srcs.append(symbol_img_src)

                    # the html for this symbol row
                    symbol_html = "<tr align=\"center\">"\
                        + unicode(img_cell) + unicode(cmd_cell) + "<td colspan=\"3\">"\
                        + "</tr>"

                    documents_list.append(LatexDocumentModel(
                        img_srcs=symbol_img_srcs,
                        commands=symbol_cmds,
                        html=symbol_html
                    ))
                    i += 2


def strip_latex_spaces(raw_cmd):
    old_raw_cmd = raw_cmd
    stripped = False
    while not stripped:
        for space_cmd in LATEX_SPACE_CMDS:
            if raw_cmd.endswith(space_cmd):
                raw_cmd = raw_cmd[:-len(space_cmd)]
        if raw_cmd == old_raw_cmd:
            stripped = True
        else:
            old_raw_cmd = raw_cmd
    return raw_cmd.strip()


if __name__ == "__main__":
    main()
