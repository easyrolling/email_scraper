from bs4 import BeautifulSoup
import time, re, pymysql, html5lib, random, sys, requests, ConfigParser
from requests.exceptions import ConnectionError
from pymysql.err import IntegrityError

config = ConfigParser.ConfigParser()
config.read('config.ini')
chrome_path = config.get('chromedriver', 'path')
conn = pymysql.connect(host=config.get('database', 'host'), user=config.get('database', 'user'), passwd=config.get('database', 'passwd'), db=config.get('database', 'db'))
commit = True

def prepare_source(source):
	source = re.sub('>\W+<', '><', source)
	return source.replace("\n", "")

def find_email(source, current_url):
	prog = re.compile('(mailto:|>|\W)([\w.]+@'+current_url+')', re.I)
	email = prog.search(source)
	
	if(email):
		if(len(email.groups()) > 1):
			print 'Email:', email.group(2)
			return email.group(2)
	else:
		prog = re.compile('(mailto:|>|\W)([\w.]+@[\w.]+)', re.I)
		email = prog.search(source)
		if(email):
			if(len(email.groups()) > 1):
				if('.png' not in email.group(2)):
					if('.' in email.group(2)):
						print 'Email:', email.group(2)
						return email.group(2)
	return False
	
def scrape(biz_id, url):
	try:
		base_url = "http://"
		final_url = base_url+url
		stripped_url = url
		href = url

		time.sleep(1)
		session = requests.session()
		r = session.get(final_url)
		
		print final_url, r.status_code
		if (r.status_code != 200):
			print 'wrong url', url, r.status_code
			status_id = 5
			stripped_url = ''
		else:
			status_id = 4
			time.sleep(1)
			
			if(r.is_redirect):
				print r.url
				url = r.url
				stripped_url = url.replace('www.', '')
			
			
			source = prepare_source(r.text)
			soup = BeautifulSoup(source, 'html5lib')
			anchor = soup.find('a', text=re.compile("contact", re.I))
			
			if(anchor):
				print 'found anchor', anchor.text, anchor.get('href')
				href = anchor.get('href')
				if(href):
					href = href.strip()
					status_id = 3
					if href.startswith('http'):
						r = session.get(href)
					else:
						if href.startswith('/') | href.startswith('#'):
							r = session.get('http://'+url+href)
						else:
							r = session.get('http://'+url+'/'+href)
					
					time.sleep(1)
					
					source = prepare_source(r.text)
					
					email_val = find_email(source, stripped_url)
					if(email_val):
						if(add_email(email_val, biz_id)):
							status_id=2
			else:
				email_val = find_email(source, stripped_url)
				if(email_val):
					if(add_email(email_val, biz_id)):
						status_id=2
						
	except ConnectionError:
		print 'error while connecting', href
		status_id = 5
		stripped_url = ''
	except ChunkEncodingError:
		print 'chunk encoding error', href
		status_id = 1
	
	update_biz(biz_id, status_id, stripped_url)
	session.close()

def find_dup(biz_id, email):
	cursor = conn.cursor()
	query = 'SELECT biz_id FROM email WHERE email=%s'
	cursor.execute(query, (email))
	biz = cursor.fetchone()
	if(biz):
		biz_id2 = biz[0]
		print 'inserting dup', biz_id, biz_id2
		query = 'INSERT INTO biz_dup (biz_id, dup_id) VALUES (%s, %s), (%s, %s)'
		cursor.execute(query, (biz_id, biz_id, biz_id, biz_id2))
		if(commit): conn.commit()
		cursor.close()

def update_biz(biz_id, status_id, web):
	try:
		cursor = conn.cursor()
		print 'updating', biz_id, 'with status', status_id, web
		
		if(web == ''):
			query = 'UPDATE biz SET status_id=%s, web= NULL WHERE id=%s'
			cursor.execute(query, (status_id, biz_id))
		else:
			query = 'UPDATE biz SET status_id=%s, web=%s WHERE id=%s'
			cursor.execute(query, (status_id, web, biz_id))
		
		if commit: conn.commit()
		cursor.close()
	
	except Exception:
		print 'MySQL error'
		pass
		
def add_email(email, biz_id):
	try:
		cursor = conn.cursor()
		query = "INSERT INTO email (email, biz_id) VALUES (%s, %s)"
		print 'adding email', email, 'to', biz_id
		cursor.execute(query, (email, biz_id))
		if commit: conn.commit()
		cursor.close()
		return True
	except IntegrityError:
		print 'Email already exists'
		find_dup(biz_id, email)
		return False
		
def get_links(idd):
	global offset
	i = 0
	print 'offset: ', offset
	
	
	max = 10000 if idd == 0 else 1
	while(i < max):
		cursor = conn.cursor()
		where = "WHERE status_id = 1 AND web is not null" if idd == 0 else "WHERE id = "+idd
		sql = "SELECT id, web FROM biz "+where+" LIMIT 100 OFFSET "+ str(offset)
		cursor.execute(sql)
			
		
		for link in cursor.fetchall():
			print '----------------> scraping ', link[0], link[1]
			scrape(link[0], link[1])
		
		i+=100
		print 'i is at ', i
			
		cursor.close()
	conn.close()
if __name__ == '__main__':
	global offset
	offset = 0 if len(sys.argv) <= 1 else sys.argv[1]
	idd = 0

	get_links(idd)
