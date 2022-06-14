import requests
from bs4 import BeautifulSoup
import urllib.request
import os
import zipfile
import shutil
titles = []

def url_create_epub(book_id):
	global titles
	url = 'https://www.shikoto.com/articles/{book_id}.html'.format(book_id=book_id)
	
	book_title = getTitle(url)
	
	createDirectory()
	
	create_cover_page()
	print('Getting Text ...')
	chapter_urls = fatch_index(url)

	for i in range(len(chapter_urls)):
		saveContent(chapter_urls[i],i+1)
		
	
	create_TOC(book_title,0)
	
	create_container()
	
	create_content_opf(book_title,0)
	
	zip_folder(book_title)



def createDirectory():
	global style_sheet
	print('Creating Temp Directory')
	try:
		os.mkdir('temp/')
		os.mkdir('temp/OEBPS')
		os.mkdir('temp/OEBPS/Images')
		os.mkdir('temp/OEBPS/Text')
		os.mkdir('temp/META-INF')
		mimetype = bytes('application/epub+zip',encoding='utf8')
		with open('temp/mimetype','wb') as file:
			file.write(mimetype)
	except Exception as e:
		print(e)
		pass

def getTitle(url):
	#Step 1 : Get Title
	print('Getting Title ...')
	res = requests.get(url,timeout=30)
	soup = BeautifulSoup(res.text,'html.parser')
	title_text = soup.find('h1').text
	return title_text

def fatch_index(url):
	#Step 2 : Fatch URLs Of Content
	print('Fatching Indexesdisc ...')
	res = requests.get(url,timeout=30)
	soup = BeautifulSoup(res.text,'html.parser')
	ls_index = soup.find('ul',attrs={'class':'list-inline chapter-list inline'}).findAll('a')
	result = [f"https://www.shikoto.com{a['href']}" for a in ls_index]
	return result

def saveContent(url,chapter):
	#Step 3 : Get Content
	global titles
	#Get Content Url
	res = requests.get(url,timeout=30)

	soup = BeautifulSoup(res.content,'html.parser')
	chapter_title = soup.find('h1').text
	print(chapter)
	titles.append(chapter_title)
	chapter_content = soup.find('div',attrs={'class':'chapter-content-wrapper'}).find('div')
	ads = chapter_content.findAll('div')
	[ad.decompose() for ad in ads]
	#Change To Html, Clear Coda
	html = '''<?xml version="1.0" encoding="utf-8"?>
	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
  	<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<title>{title}</title>
	</head>
	<body>{body}</body></html>'''.format(title=chapter_title,body=chapter_content)
	html = bytes(html,encoding = "utf8")
	with open('temp/OEBPS/Text/ch_{chapter}.xhtml'.format(chapter=chapter),'wb') as file:
		file.write(html)


def create_cover_page():
	#Create Cover Page
	print('Creating Cover Page...')
	html = '''<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>cover</title>
</head>
<body>
<div>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="100%" height="100%" viewBox="0 0 970 1388" preserveAspectRatio="none">
<image width="970" height="1388" xlink:href=""/>
</svg>
</div>
</body>
</html>'''
	html = bytes(html,encoding = "utf8")
	with open('temp/OEBPS/Text/titlepage.xhtml','wb') as file:
		file.write(html)
 
def create_TOC(book_title,chapter_start):
	# Create Table Of Content
	print('Creating TOC ...')
	global titles
	html = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
<head>
<meta name="dtb:uid" content="0"/>
<meta name="dtb:depth" content="1"/>
<meta name="dtb:totalPageCount" content="0"/>
<meta name="dtb:maxPageNumber" content="0"/>
</head>
<docTitle>
<text>{title}</text>
</docTitle>
<navMap>
<navPoint id="coverpage" playOrder="0"><navLabel><text>封面</text></navLabel><content src="Text/titlepage.xhtml"/></navPoint>'''.format(title=book_title)
	for i in range(len(titles)):
		value = '<navPoint id="ch{i}" playOrder="{i}"><navLabel><text>{title}</text></navLabel><content src="Text/ch_{i}.xhtml"/></navPoint>'.format(i=i+chapter_start,title=titles[i])
		html+=value
	html+='''</navMap></ncx>'''
	html = bytes(html,encoding = "utf8")
	with open('temp/OEBPS/toc.ncx','wb') as file:
		file.write(html)

def create_container():
	print('Creating Container ...')
	xml = '''<?xml version="1.0" encoding="utf-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>'''
	xml = bytes(xml,encoding = "utf8")
	with open('temp/META-INF/container.xml','wb') as file:
		file.write(xml)

def create_content_opf(book_title,chapter_start):
	print('Creating Cotent OPF ...')
	global titles
	length = len(titles)
	# Create manifest
	manifest = '''<item href="toc.ncx" media-type="application/x-dtbncx+xml" id="ncx"/>
				<item href="Images/cover.jpg" id="cover" media-type="image/jpg"/>
				<item href="Text/titlepage.xhtml" id="titlepage" media-type="application/xhtml+xml"/>
				'''
	for i in range(length):
		value = '<item href="Text/ch_{i}.xhtml" id="ch{i}" media-type="application/xhtml+xml"/>'.format(i=i+chapter_start)
		manifest += value

	# Create Spine 
	spine = '<itemref idref="titlepage" linear="no"/>'
	for i in range(length):
		value = '<itemref idref="ch{i}"/>'.format(i=i+chapter_start)
		spine += value

	opf = '''<?xml version="1.0" encoding="UTF-8" ?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id" version="2.0">
<metadata xmlns:opf="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uuid_id" opf:scheme="uuid">0</dc:identifier>
<dc:language>en</dc:language>
<dc:title>{title}</dc:title>
<meta name="cover" content="cover"/>
</metadata><manifest>{manifest}</manifest><spine toc="ncx">{spine}</spine>
</package>'''.format(manifest=manifest,spine=spine,title=book_title)
	opf = bytes(opf,encoding = 'utf8')
	with open('temp/OEBPS/content.opf','wb') as file:
		file.write(opf)

def zip_folder(book_title):
	print('Zipping To Epub ...')
	zipf = zipfile.ZipFile('../ebooks/{title}.epub'.format(title=book_title), 'w', zipfile.ZIP_DEFLATED)
	path = 'temp'
	for root, dirs, files in os.walk(path):
		length = len(path) #string length , used to reduce in path prevent parent path appeared in zip
		for file in files:
			zipf.write(os.path.join(root, file),os.path.join(root[length:], file))
	zipf.close()

def remove_temp():
	print('Removeing Temp ... ')
	shutil.rmtree(os.path.join(os.getcwd(),'temp'))