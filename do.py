import os
import sys
from mimetypes import guess_extension
import re

from bs4 import BeautifulSoup
import requests

data_image_id_key = 'data-image-id'
data_original_key = 'data-original'
content_type_key = 'Content-Type'
episode_item_key = 'episode_item'

def login(sess, nicoId, nicoPw):
    loginUrl = "https://secure.nicovideo.jp/secure/login?site=niconico&mail=%s&password=%s" % (nicoId, nicoPw)
    response = sess.post(loginUrl)
    soup = BeautifulSoup(response.text, 'html.parser')
    return len(soup.select("div.notice.error")) <= 0

def get_episode_urls(sess, comic_id):
	response = sess.get('http://seiga.nicovideo.jp/comic/%s' % comic_id)
	soup = BeautifulSoup(response.text, 'html.parser')

	return [re.findall('mg[0-9]+', episode_item.select('div.title')[0].find('a')['href'])[0] for episode_item in soup.select('li.episode_item') if len(episode_item.select('div.purchase_type')) == 0]

def create_and_get_manga_directory(seiga_soup):
	title = seiga_soup.select('span.manga_title')[0].text
	episode = seiga_soup.select('span.episode_title')[0].text
	path = os.path.join(title, episode)
	if not os.path.exists(path):
		os.makedirs(path)

	return path

def save_images(mg_id):
	host_seiga = 'http://seiga.nicovideo.jp/watch/%s' % mg_id
	seiga_response = sess.get(host_seiga)
	seiga_soup = BeautifulSoup(seiga_response.text, 'html.parser')
	directory = create_and_get_manga_directory(seiga_soup)
	imgs = seiga_soup.select('img.lazyload')
	if len(imgs) == 0:
		print "No seiga named %s" % mg_id
	else:
		imgs = [img for img in imgs if data_original_key in img.attrs and data_image_id_key in img.attrs]
		for img in imgs:
			img_url = img[data_original_key]
			data_image_id = img[data_image_id_key]
			r = requests.get(img_url)

			extension = None
			if content_type_key in r.headers:
				extension = guess_extension(r.headers[content_type_key])
			if extension is None:
				extension = ".jpg"

			with open(os.path.join(directory, data_image_id + extension), "wb") as file:
				file.write(r.content)

if __name__ == "__main__":
	if len(sys.argv) < 5:
		print "Usage:\n\t- python do.py id pw c c_id\n\t- python do.py id pw m mg_id [mg_id]"
		sys.exit()
	id = sys.argv[1]
	pw = sys.argv[2]
	mode = sys.argv[3]
	args = sys.argv[4:]

	with requests.session() as sess:
		if login(sess, id, pw):
			mg_ids = None
			if mode == 'c':
				mg_ids = get_episode_urls(sess, args[0])
			elif mode == 'm':
				mg_ids = args

			if mg_ids is None:
				print "Wrong param. See usage."
				sys.exit()

			for mg_id in mg_ids:
				save_images(mg_id)
