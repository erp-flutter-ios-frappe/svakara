import frappe
from frappe import throw, _, scrub
import traceback
import json
from frappe.utils import nowdate
import collections
from svakara.globle import appErrorLog,globleLoginUser
from datetime import datetime


@frappe.whitelist(allow_guest=True)
def walletMessage(message,data):
	response={}
	frappe.local.response['http_status_code'] = 200
	response["status_code"]="200"
	response["message"]=message
	response["data"]=data
	return response

@frappe.whitelist(allow_guest=True)
def createWalletEntry(**kwargs):

	parameters=frappe._dict(kwargs)
	allParamKeys = parameters.keys()

	reply={}
	reply['message']=""
	reply['status_code']="200"

	try:
		if parameters['payment_method'] != 'Cash':
			query = "SELECT * from `tabWallet` WHERE `payment_id`='{}' AND `customer`='{}'".format(parameters['payment_id'],parameters['customer'])
			previousEntry = frappe.db.sql(query,as_dict=True)
			if len(previousEntry)!=0:
				return walletMessage("Sucessfully recharge wallet. Your recharge ID: {}".format(previousEntry[0]['name']),previousEntry[0])

			query = "SELECT balance FROM `tabWallet` WHERE `customer`='{}' AND `is_cancelled`='0' AND `docstatus`!=2 ORDER BY `creation` desc LIMIT 1".format(parameters['customer'])
			balancelist=frappe.db.sql(query,as_dict=True)
			
			balance = 0.0
			if len(balancelist)!=0:
				balance = balancelist[0]['balance']

			signature=''
			if 'signature' in allParamKeys:
				if parameters['signature'] not in ['','null',None]:
					signature=parameters['signature']

			reference_document=''
			if 'reference_document' in allParamKeys:
				if parameters['reference_document'] not in ['','null',None]:
					reference_document=parameters['reference_document']

			reference_document_numbre=''
			if 'reference_document_numbre' in allParamKeys:
				if parameters['reference_document_numbre'] not in ['','null',None]:
					reference_document_numbre=parameters['reference_document_numbre']


			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Wallet",
				"name": "New Wallet 1",
				"__islocal": 1,
				"__unsaved": 1,
				"status": "Draft",
				"transaction_date": nowdate(),
				"server_date_and_time": datetime.now(),
				"customer":parameters['customer'],
				"payment_method":parameters['payment_method'],
				"paid_amount":parameters['amount'],
				"payment_id":parameters['payment_id'],
				"balance":float(balance+float(parameters['amount'])),
				"signature":signature,
				"reference_document":reference_document,
				"reference_document_numbre":reference_document_numbre
			})
			d2=d1.insert(ignore_permissions=True)

		frappe.db.commit()

		if parameters['payment_method'] != 'Cash':
			frappe.enqueue(submitWallet,queue='long',job_name="Submit wallet: {}".format(d2.name),timeout=100000,walletID=str(d2.name))

		return walletMessage("Sucessfully recharge wallet. Your recharge ID: {}".format(str(d2.name)),d2)

	except Exception as e:
		response={}
		appErrorLog("Wallet entry",str(e))
		appErrorLog("Wallet entry traceable",str(traceback.format_exc()))
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		response["message_traceable"]=str(traceback.format_exc())
		return response









@frappe.whitelist(allow_guest=True)
def walletHistory(customer):

	query = "SELECT * FROM `tabWallet` WHERE `docstatus`=1 AND `customer`='{}' AND `payment_type` NOT IN ('Reward','Share Wallet Out','Share Wallet In') ORDER BY `transaction_date` DESC".format(customer)
	dataList=frappe.db.sql(query,as_dict=1)
	
	#previousOrder=frappe.get_all("Wallet",filters=[["Wallet","docstatus","=",1],["Wallet","customer","=",customer],["Wallet","payment_type","!=","Reward"],["Wallet","payment_type","!=","Share Wallet Out"],["Wallet","payment_type","!=","Share Wallet In"]],fields=["*"])
	return dataList


@frappe.whitelist(allow_guest=True)
def submitWallet(walletID):

	current_user = frappe.session.user

	loginUser = frappe.session.user
	frappe.set_user(globleLoginUser())

	doc=frappe.get_doc("Wallet",walletID)
	doc.submit()

	d1=frappe.get_doc({
		"docstatus": 0,
		"doctype": "Payment Entry",
		"name": "New Payment Entry 1",
		"__islocal": 1,
		"__unsaved": 1,
		"status": "Draft",
		"posting_date": nowdate(),
		"payment_type": "Receive",
		"party_type":'Customer',
		"party":doc.customer,
		"paid_to":'Bank Account - S',
		"paid_from":'Debtors - S',
		"paid_to_account_currency":"INR",
		"paid_from_account_currency":"INR",
		"received_amount":float(doc.paid_amount),
		"paid_amount":float(doc.paid_amount),
		"remarks":doc.name,
		"reference_no":doc.payment_id,
		"reference_date":doc.transaction_date,
		"reference_doctype":'Wallet',
	})
	d2=d1.insert(ignore_permissions=True)
	d2.submit()

	frappe.set_user(current_user)
	return "Payment entry done"

@frappe.whitelist(allow_guest=True)
def submitWallet2():

	reply = {}
	reply['status_code']="200"
	reply['message']=""

	try:
		current_user = frappe.session.user

		loginUser = frappe.session.user
		frappe.set_user(globleLoginUser())

		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Payment Entry",
			"name": "New Payment Entry 1",
			"__islocal": 1,
			"__unsaved": 1,
			"status": "Draft",
			"posting_date": nowdate(),
			"payment_type": "Receive",
			"party_type":'Customer',
			"party":'1234567890',
			"paid_to":'Bank Account - S',
			"paid_from":'Debtors - S',
			"paid_to_account_currency":"INR",
			"paid_from_account_currency":"INR",
			"paid_amount":float('100'),
			"remarks":'Ravi',
			"reference_doctype":'Wallet',
		})
		d2=d1.insert(ignore_permissions=True)
		frappe.set_user(current_user)
	
	except Exception as e:
		reply["status_code"]=500
		reply["message"]=str(e)
		reply['message_traceable']=traceback.format_exc()

	return reply

