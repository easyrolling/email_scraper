import kickbox, os
import json, pymysql, ConfigParser

kickbox

config = ConfigParser.ConfigParser()
dirname = os.path.dirname(os.path.realpath(__file__))
config.read(dirname+'/config.ini')
kickbox_key = config.get('kickbox', 'key')
conn = pymysql.connect(host=config.get('database', 'host'), user=config.get('database', 'user'), passwd=config.get('database', 'passwd'), db=config.get('database', 'db'))


def check_email(email):
	global kickbox
	
	response = kickbox.verify(email)
	
	result = response.body['result']
	print email, result
	
	if(result == 'valid'):
		return 1
	else:
		if(result == 'unknown'):
			return 2
		else:
			return 0

def get_emails():
	cursor = conn.cursor()
	sql = "select email.id, email.email from email WHERE email.email<>'' and status_id=2 LIMIT 1000"
	cursor.execute(sql)
	
	for email in cursor.fetchall():
		valid = check_email(email[1])
		cursor2 = conn.cursor()
		if(valid > 0):
			query = "UPDATE email SET is_valid=%s, status_id=6 WHERE id=%s"
			cursor2.execute(query, (valid, email[0]))
		else:
			query = "UPDATE email SET status_id=6 WHERE id=%s"
			cursor2.execute(query, (email[0]))
		
		conn.commit()
		cursor2.close()
	cursor.close()
	conn.close()
	
if __name__ == "__main__":
	global kickbox
	client   = kickbox.Client(kickbox_key)
	kickbox  = client.kickbox()
	get_emails()
