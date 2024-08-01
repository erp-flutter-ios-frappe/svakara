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