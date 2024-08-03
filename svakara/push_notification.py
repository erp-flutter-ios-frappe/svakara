import frappe
import requests
import json
from frappe import enqueue
import re
from svakara.globle import appErrorLog



@frappe.whitelist(allow_guest=True)
def create_notification(title,body,number):

	reply={}
	reply["status_code"]="200"
	reply["message"]="Sucessfully"
	reply["data"]={}
	
	try:
		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Push Notification",
			"name": "New Push Notification 1",
			"__islocal": 1,
			"__unsaved": 1,
			"mobile_number": number,
			"title": title,
			"body": body,
		})
		if d1.insert(ignore_permissions=True):
			frappe.enqueue(send_notification,queue='default',job_name="Push sending {}".format(d1.name),timeout=50000,doc=d1)
			reply["data"]=d1
			reply["message"]="FCM created."
			return reply
		else:
			frappe.local.response['http_status_code'] = 500
			reply["data"]={}
			reply["message"]="FCM not created."
			reply["status_code"]="500"
			return reply
		
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		reply["message"]=str(e)
		reply['message_traceable']=traceback.format_exc()
		appErrorLog('FCM - create_notification',str(e))
		appErrorLog('FCM - create_notification - traceback',str(traceback.format_exc()))
		return reply


def user_id(doc):
	mobile_number = doc.mobile_number
	user_device_id = frappe.get_all(
		"User Settings", filters={"name": mobile_number}, fields=["token"]
	)
	return user_device_id


@frappe.whitelist()
def send_notification(doc):

	device_ids = user_id(doc)
	for device_id in device_ids:
		enqueue(
			process_notification,
			queue="default",
			now=False,
			device_id=device_id.token,
			notification=doc,
		)

def convert_message(message):
	CLEANR = re.compile("<.*?>")
	cleanmessage = re.sub(CLEANR, "", message)
	# cleantitle = re.sub(CLEANR, "",title)
	return cleanmessage


def process_notification(device_id, notification):

	title = notification.title
	message = notification.body

	if message:
		message = convert_message(message)
	if title:
		title = convert_message(title)

	url = "https://fcm.googleapis.com/fcm/send"
	# url="https://fcm.googleapis.com/v1/projects/gold-freedom-159313/messages:send"

	body = {
		"to": device_id,
		"notification": {"body": message, "title": title},
		"data": {
			# "doctype": notification.document_type,
			# "docname": notification.document_name,
			"doctype": "",
			"docname": "",
		},
	}

	server_key = frappe.db.get_single_value("FCM Notification Settings", "server_key")
	# auth = f"Bearer {server_key}"
	req = requests.post(
		url=url,
		data=json.dumps(body),
		headers={
			"Authorization":'key={}'.format(server_key),
			"Content-Type":"application/json",
			"Accept":"application/json",
		},
	)
	# appErrorLog("Notication Response test",'Ok')


	# appErrorLog("Notication Response Code",str(req.status_code))
	# notificationResponse=req.json()
	# appErrorLog("Notication Response",str(notificationResponse))
	# appErrorLog("Notication Response multicast_id",notificationResponse['multicast_id'])
	# appErrorLog("Notication Response success",notificationResponse['success'])
	# appErrorLog("Notication Response failure",notificationResponse['failure'])
	# appErrorLog("Notication Response canonical_ids",notificationResponse['canonical_ids'])
	# appErrorLog("Notication Response message_id",notificationResponse['results'][0]['message_id'])

	if req.status_code == 200:
		notificationResponse=req.json()
		# appErrorLog("Notication Response",str(notificationResponse))
		# appErrorLog("Notication Response multicast_id",notificationResponse['multicast_id'])
		# appErrorLog("Notication Response success",notificationResponse['success'])
		# appErrorLog("Notication Response failure",notificationResponse['failure'])
		# appErrorLog("Notication Response canonical_ids",notificationResponse['canonical_ids'])
		# appErrorLog("Notication Response message_id",notificationResponse['results'][0]['message_id'])
		
		updateQuery = "UPDATE `tabPush Notification` SET `success`={}, `failure`={}, `multicast_id`='{}', `canonical_ids`='{}', `message_id`='{}' WHERE `name`='{}'".format(notificationResponse['success'],notificationResponse['failure'],notificationResponse['multicast_id'],notificationResponse['canonical_ids'],notificationResponse['results'][0]['message_id'],notification.name)
		# appErrorLog("Notication Update",updateQuery)
		queryResult = frappe.db.sql(updateQuery)
	else:
		updateQuery = "UPDATE `tabPush Notification` SET `failure`=1 WHERE `name`='{}'".format(notification.name)
		queryResult = frappe.db.sql(updateQuery)

	frappe.db.commit()
	return "Notification send"

	# appErrorLog("Notication Response",str(notificationResponse))
	# frappe.log_error(str(notificationResponse))