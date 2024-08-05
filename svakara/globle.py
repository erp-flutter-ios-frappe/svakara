from __future__ import unicode_literals
import frappe
from frappe import _



@frappe.whitelist(allow_guest=True)
def globleUserLogin(allow_guest=True):
	return frappe._dict({
		'cmd': 'login',
		'sid': 'Desk',
		'pwd': 'svakara@2024*',
		'usr': 'svakara@gmail.com'
	})

@frappe.whitelist(allow_guest=True)
def globleLoginUser(allow_guest=True):
	return "svakara@gmail.com"

@frappe.whitelist(allow_guest=True)
def defaultResponseBody():
	reply = {}
	reply['status_code']='200'
	reply['message']=''
	return reply

@frappe.whitelist(allow_guest=True)
def defaultResponseErrorBody(reply,error,error_traceable,file_name,method_name):
	appErrorLog("{} - {}".format(file_name,method_name),error)
	appErrorLog("{} - {} traceable".format(file_name,method_name),error_traceable)
	reply["status_code"]="500"
	reply["message"]=error
	reply["message_traceable"]=error_traceable
	return reply



@frappe.whitelist(allow_guest=True)
def run_query_inDB_select(query):
	test = frappe.db.sql(query,as_dict=1)
	return test

@frappe.whitelist(allow_guest=True)
def appErrorLog(title,error):
	d = frappe.get_doc({
			"doctype": "Error Log",
			"method":title,
			"error":error
		})
	d = d.insert(ignore_permissions=True)
	return d