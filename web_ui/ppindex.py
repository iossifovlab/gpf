from bs4 import BeautifulSoup


with open("./src/index.html") as html_doc:
	soup = BeautifulSoup(html_doc, "lxml")

with open("./src/index.html", "w") as html_doc:
	html_doc.write(soup.prettify())
