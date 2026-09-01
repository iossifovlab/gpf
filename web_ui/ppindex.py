import pathlib

from bs4 import BeautifulSoup

with open("./src/index.html") as html_doc:
    soup = BeautifulSoup(html_doc, "lxml")

pathlib.Path("./src/index.html").write_text(soup.prettify())
