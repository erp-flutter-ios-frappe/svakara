import frappe
from frappe import throw, _, scrub
import traceback
import json
from frappe.utils import nowdate
import collections


@frappe.whitelist()
def appErrorLog(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":str("User:")+str(title+" "+"Website Error"),
			"error":traceback.format_exc()
		})
	d = d.insert(ignore_permissions=True)
	return d

@frappe.whitelist()
def generateResponse(_type,status=None,message=None,data=None,error=None):
	response= {}
	if _type=="S":
		if status:
			response["status"]=int(status)
		else:
			frappe.local.response['http_status_code'] = 200
			response["status"]=200
		response["message"]=message
		response["data"]=data
	else:
		error_log=appErrorLog(frappe.session.user,str(error))
		frappe.local.response['http_status_code'] = 500

		if status:
			response["status"]=status
		else:
			response["status"]=500
		response["message"]=str(error)
		response["data"]=None
	return response


@frappe.whitelist(allow_guest=True)
def walletHistory(customer):

	query = "SELECT * FROM `tabWallet` WHERE `docstatus`=1 AND `customer`='{}' AND `payment_type` NOT IN ('Reward','Share Wallet Out','Share Wallet In') ORDER BY `transaction_date` DESC".format(customer)
	dataList=frappe.db.sql(query,as_dict=1)
	
	#previousOrder=frappe.get_all("Wallet",filters=[["Wallet","docstatus","=",1],["Wallet","customer","=",customer],["Wallet","payment_type","!=","Reward"],["Wallet","payment_type","!=","Share Wallet Out"],["Wallet","payment_type","!=","Share Wallet In"]],fields=["*"])
	return dataList


@frappe.whitelist()
def walletMessage(message,data):
	response={}
	frappe.local.response['http_status_code'] = 200
	response["status"]="200"
	response["message"]=message
	response["data"]=data
	return response


@frappe.whitelist()
def submitWallet(walletID):

	from frappe.auth import LoginManager, CookieManager
	frappe.local.form_dict = frappe._dict({
		'cmd': 'login',
		'sid': 'administrator',
		'pwd': 'Satvaras2020*',
		'usr': 'rsp4388@gmail.com'
	})

	frappe.local.cookie_manager = CookieManager()
	frappe.local.login_manager = LoginManager()
	doc=frappe.get_doc("Wallet",walletID)
	doc.submit()

	return ""

@frappe.whitelist()
def createWalletEntry(payment_type,payment_id,amount,customer):

	try:
		if payment_type != 'Cash':
			previousProcess=frappe.get_all("Wallet",filters=[["Wallet","payment_id","=",payment_id]],fields=["*"])
			if len(previousProcess)>0:
				return walletMessage("Wallet entry done",previousProcess[0])

			if payment_id:
				previousProcess1=frappe.get_all("Wallet",filters=[["Wallet","payment_id","=",payment_id]],fields=["*"])
				if len(previousProcess1)>0:
					return walletMessage("Wallet entry done",previousProcess[0])

		d1=frappe.get_doc({
					"docstatus": 0,
					"doctype": "Wallet",
					"name": "New Wallet 1",
					"__islocal": 1,
					"__unsaved": 1,
					"status": "Draft",
					"transaction_date": nowdate(),
					"payment_type":"Payment",
					"payment_method":payment_type,
					"payable_amount":amount,
					"wallet_balance":amount,
					"customer":customer,
					"owner":customer,
					"payment_id":payment_id,
				})
		d2=d1.insert(ignore_permissions=True)

		if payment_type != 'Cash':
			d2.submit()

		frappe.db.commit()


		if float(amount)>=3000:
			frappe.db.sql("""update tabCustomer SET custom_subscription_days=30 WHERE name= '""" + customer +"""'  """)	

		return walletMessage("Wallet entry done",d2)

	except Exception as e:
		response={}
		error_log=appErrorLog(frappe.session.user,e)
		frappe.local.response['http_status_code'] = 500
		response["status"]="500"
		response["message"]=str(e)
		return response