# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
from bs4 import BeautifulSoup


def main():
    img_parse()

html_tr = """
<tr>
<td rowspan="2" bgcolor="#D0F0D0" align="center">
<div style="font-size:200%;" class="nounderlines"><a href="http://en.wikipedia.org/wiki/Plus_sign" title="Plus sign" class="mw-redirect">+</a></div>
</td>
<td rowspan="2" bgcolor="#FFFFFF" align="center"><img class="mwe-math-fallback-image-inline tex" alt="+ \!\," src="./List of mathematical symbols - Wikipedia, the free encyclopedia_files/5ba4c96940454c4d05519d2374d34bc0.png"></td>
<td style="padding:0px;">
<div style="padding:2px;text-align:left;border-bottom:1px #aaa solid;"><a href="http://en.wikipedia.org/wiki/Addition" title="Addition">addition</a></div>
<div style="padding:2px;text-align:center;border-bottom:1px #aaa solid;"><a href="http://en.wikipedia.org/wiki/Plus_and_minus_signs" title="Plus and minus signs">plus</a>;<br>
add</div>
<div style="padding:2px;text-align:right;"><a href="http://en.wikipedia.org/wiki/Arithmetic" title="Arithmetic">arithmetic</a></div>
</td>
<td>4 + 6 means the sum of 4 and 6.</td>
<td>2 + 7 = 9</td>
</tr>
<tr>
<td style="padding:0px;">
<div style="padding:2px;text-align:left;border-bottom:1px #aaa solid;"><a href="http://en.wikipedia.org/wiki/Disjoint_union" title="Disjoint union">disjoint union</a></div>
<div style="padding:2px;text-align:center;border-bottom:1px #aaa solid;">the disjoint union of ... and ...</div>
<div style="padding:2px;text-align:right;"><a href="http://en.wikipedia.org/wiki/Naive_set_theory" title="Naive set theory">set theory</a></div>
</td>
<td><i>A</i><sub>1</sub> + <i>A</i><sub>2</sub> means the disjoint union of sets <i>A</i><sub>1</sub> and <i>A</i><sub>2</sub>.</td>
<td><i>A</i><sub>1</sub> = {3, 4, 5, 6} ∧ <i>A</i><sub>2</sub> = {7, 8, 9, 10} ⇒<br>
<i>A</i><sub>1</sub> + <i>A</i><sub>2</sub> = {(3,1), (4,1), (5,1), (6,1), (7,2), (8,2), (9,2), (10,2)}</td>
</tr>
"""

def table_parse():
    rows_soup = BeautifulSoup(html_tr)
    tds = rows_soup.find_all("tr")[0].find_all("td")

    wrapper = rows_soup.new_tag("div", **{"class": "eqn-wrapper"})
    tds[2].insert(0, wrapper)

    img_cell_clone = BeautifulSoup(unicode(tds[1]))#.body.contents[0]
    tds[0].replace_with(img_cell_clone)
    [e.extract() for e in tds[1].find_all()]
    tds[1].insert(0, "asdf")
    print rows_soup.prettify()
    """

    rows_soup = BeautifulSoup(unicode(rows_soup))
    table_rows = rows_soup.find_all("tr")
    row0 = table_rows[0]
    tds = row0.find_all("td")
    print tds[0]
    print "*"*40
    for e in tds[1].find_all():
        print e
        print
    [e.extract() for e in tds[1].find_all()]
    tds[1].insert(0, "asdf")
    # print rows_soup.prettify()
    """


def img_parse():
    html = """
    <tr>
    <td>
    before: <img src="/img1.png"> afterwards: <img src="/img2.png">
    </td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html5lib')
    print soup.prettify()
    img_tags = soup.find_all('img')
    for img_tag in img_tags:
        print
        print img_tag.prettify()

if __name__ == "__main__":
    main()
