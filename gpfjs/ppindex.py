from bs4 import BeautifulSoup


with open("dist/index.html") as html_doc:
	soup = BeautifulSoup(html_doc, "lxml")

with open("dist/index.html", "w") as html_doc:
	html_doc.write(soup.prettify())
