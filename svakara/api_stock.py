from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate
import json
import traceback
from frappe.auth import LoginManager, CookieManager
from erpnext.globle import globleUserLogin


@frappe.whitelist(allow_guest=True)
def stockin_rawmaterial(items,dates,mobileNo=None):

	reply={}
	reply["data"] = []
	reply["status_code"] = '500'
	reply["message"] = 'There is issue.'

	try:
		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Stock Entry",
			"name": "New Stock Entry 1",
			"__islocal": 1,
			"__unsaved": 1,
			"naming_series": "MAT-STE-.YYYY.-",
			"stock_entry_type": "Material Receipt",
			# "posting_date": nowdate(),
			# "posting_time": nowdate(),
			"posting_date": dates,
			"set_posting_time":1,
			"to_warehouse": "Stores - SAT",
			"remarks": "Add using app. Login number: {}".format(mobileNo),
			"items":rawMaterialItems(items)
		})
		d2=d1.insert(ignore_permissions=True)
		frappe.local.form_dict = globleUserLogin()
		frappe.local.cookie_manager = CookieManager()
		frappe.local.login_manager = LoginManager()
		temp = d2.submit()
		reply["data"] = temp
		reply["status_code"] = '200'
		reply["message"] = 'Stock entry sucessfully'
		return reply
	except Exception as e:
		reply["message"] = str(e)
		reply["message_traceable"] = str(traceback.format_exc())

	return reply

@frappe.whitelist(allow_guest=True)
def rawMaterialItems(items):
	
	obj_update=[]
	for item in json.loads(items):		
		itemadding={}
		itemadding["item_code"]=item['item_code']
		itemadding["qty"] = float(item['qty'])
		itemadding["basic_rate"] = float(item['rate'])
		#itemadding["allow_zero_valuation_rate"] = 1
		#itemadding["set_basic_rate_manually"] = 1
		obj_update.append(itemadding)
	return obj_update

@frappe.whitelist(allow_guest=True)
def stockout_rawmaterial(**kwargs):

	parameters=frappe._dict(kwargs)
# items,dates,method,mobileNo=None
#"","","",""
	reply={}
	reply["data"] = []
	reply["status_code"] = '500'
	reply["message"] = 'There is issue.'

	from_warehouse = "Stores - SAT"

	to_warehouse = "Used in production - SAT"
	if parameters['method']=="Production":
		to_warehouse = "Used in production - SAT"
	elif parameters['method'] in ["Weight loss","Package weight loss"]:
		to_warehouse = "Weight loss - SAT"
	elif parameters['method']=="Damaged":
		to_warehouse = "Damaged Goods - SAT"

	try:
		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Stock Entry",
			"name": "New Stock Entry 1",
			"__islocal": 1,
			"__unsaved": 1,
			"naming_series": "MAT-STE-.YYYY.-",
			"stock_entry_type": "Material Transfer",
			# "posting_date": nowdate(),
			# "posting_time": nowdate(),
			"posting_date": parameters['dates'],
			"set_posting_time":1,
			"from_warehouse": from_warehouse,
			"to_warehouse": to_warehouse,
			"remarks": "Transfer using app. Login number: {}".format(parameters['mobileNo']),
			"items":transferRawItems(parameters['items'])
		})
		d2=d1.insert(ignore_permissions=True)
		frappe.local.form_dict = globleUserLogin()
		frappe.local.cookie_manager = CookieManager()
		frappe.local.login_manager = LoginManager()
		temp = d2.submit()
		reply["data"] = temp
		reply["status_code"] = '200'
		reply["message"] = 'Stock transfer sucessfully'
		return reply
	except Exception as e:
		reply["message"] = str(e)
		reply["message_traceable"] = str(traceback.format_exc())

	return reply

@frappe.whitelist(allow_guest=True)
def transferRawItems(items):

	obj_update=[]
	for item in json.loads(items):		
		itemadding={}
		itemadding["item_code"]=item['item_code']
		itemadding["qty"] = float(item['qty'])
		obj_update.append(itemadding)
	return obj_update



@frappe.whitelist(allow_guest=True)
def stockin(warehouse, items, processMethod,transaction_date, note, mobileNo=None):

	warehouse = "Finished Goods - SAT"

	reply={}
	reply["data"] = []
	reply["status_code"] = '500'
	reply["message"] = 'There is issue.'

	try:
		if processMethod=="Production":
			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Stock Entry",
				"name": "New Stock Entry 1",
				"__islocal": 1,
				"__unsaved": 1,
				"naming_series": "MAT-STE-.YYYY.-",
				"stock_entry_type": "Material Receipt",
				"set_posting_time":1,
				"posting_date": transaction_date,
				#"posting_time": nowdate(),
				"to_warehouse": warehouse,
				"remarks": "Add using app. Login number: {} <br> Note:{}".format(mobileNo,note),
				"items":transferItems(items),
			})
			d2=d1.insert(ignore_permissions=True)
			frappe.local.form_dict = globleUserLogin()
			frappe.local.cookie_manager = CookieManager()
			frappe.local.login_manager = LoginManager()
			temp = d2.submit()
			reply["data"] = temp
			reply["status_code"] = '200'
			reply["message"] = 'New stock entry sucessfully'
		if processMethod=="Expire":
			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Stock Entry",
				"name": "New Stock Entry 1",
				"__islocal": 1,
				"__unsaved": 1,
				"naming_series": "MAT-STE-.YYYY.-",
				"stock_entry_type": "Material Transfer",
				"set_posting_time":1,
				"posting_date": transaction_date,
				#"posting_time": nowdate(),
				"from_warehouse": warehouse,
				"to_warehouse": "Expire Goods - SAT",
				"remarks": "Add using app. Login number: {} <br> Note:{}".format(mobileNo,note),
				"items":transferItems(items),
			})
			d2=d1.insert(ignore_permissions=True)
			frappe.local.form_dict = globleUserLogin()
			frappe.local.cookie_manager = CookieManager()
			frappe.local.login_manager = LoginManager()
			temp = d2.submit()
			reply["data"] = temp
			reply["status_code"] = '200'
			reply["message"] = 'Stock expire sucessfully'
		if processMethod=="Damage":
			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Stock Entry",
				"name": "New Stock Entry 1",
				"__islocal": 1,
				"__unsaved": 1,
				"naming_series": "MAT-STE-.YYYY.-",
				"stock_entry_type": "Material Transfer",
				"set_posting_time":1,
				"posting_date": transaction_date,
				#"posting_time": nowdate(),
				"from_warehouse": warehouse,
				"to_warehouse": "Damaged Goods - SAT",
				"remarks": "Add using app. Login number: {} <br> Note:{}".format(mobileNo,note),
				"items":transferItems(items),
			})
			d2=d1.insert(ignore_permissions=True)
			frappe.local.form_dict = globleUserLogin()
			frappe.local.cookie_manager = CookieManager()
			frappe.local.login_manager = LoginManager()
			temp = d2.submit()
			reply["data"] = temp
			reply["status_code"] = '200'
			reply["message"] = 'Damage stock entry sucessfully.'					
		if processMethod=="Stock remove":
			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Stock Entry",
				"name": "New Stock Entry 1",
				"__islocal": 1,
				"__unsaved": 1,
				"naming_series": "MAT-STE-.YYYY.-",
				"stock_entry_type": "Material Issue",
				"set_posting_time":1,
				"posting_date": transaction_date,
				#"posting_time": nowdate(),
				"from_warehouse": warehouse,
				"remarks": "Add using app. Login number: {} <br> Note:{}".format(mobileNo,note),
				"items":transferItems(items),
			})
			d2=d1.insert(ignore_permissions=True)
			frappe.local.form_dict = globleUserLogin()
			frappe.local.cookie_manager = CookieManager()
			frappe.local.login_manager = LoginManager()
			temp = d2.submit()
			reply["data"] = temp
			reply["status_code"] = '200'
			reply["message"] = 'Stock remove sucessfully'					


		return reply
	except Exception as e:
		reply["message"] = str(e)
		reply["message_traceable"] = str(traceback.format_exc())

	return reply

@frappe.whitelist(allow_guest=True)
def transferItems(items):
	obj_update=[]
	for item in json.loads(items):		
		itemadding={}
		itemadding["item_code"]=item['item_code']
		itemadding["qty"] = float(item['qty'])
		obj_update.append(itemadding)
	return obj_update


###########################################################
########################   Air-port #######################
###########################################################

@frappe.whitelist(allow_guest=True)
def stockinAirport(warehouse, items, method, dates,mobileNo=None):

	warehouse = "Airport Ahmedabad - SAT"

	reply={}
	reply["data"] = []
	reply["status_code"] = '500'
	reply["message"] = 'There is issue.'

	to_warehouse = warehouse
	from_warehouse = "Finished Goods - SAT"

	if method=="Out":
		to_warehouse = "Finished Goods - SAT"
		from_warehouse = warehouse

	try:
		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Stock Entry",
			"name": "New Stock Entry 1",
			"__islocal": 1,
			"__unsaved": 1,
			"naming_series": "MAT-STE-.YYYY.-",
			"stock_entry_type": "Material Transfer",
			# "posting_date": nowdate(),
			"posting_date": dates,
			"set_posting_time":1,
			# "posting_time": nowdate(),
			# "posting_time": '00:01:00',
			"from_warehouse": from_warehouse,
			"to_warehouse": to_warehouse,
			"remarks": "Transfer using app. Login number: {}".format(mobileNo),
			"items":transferItems(items)
		})
		d2=d1.insert(ignore_permissions=True)
		frappe.local.form_dict = globleUserLogin()
		frappe.local.cookie_manager = CookieManager()
		frappe.local.login_manager = LoginManager()
		temp = d2.submit()
		reply["data"] = temp
		reply["status_code"] = '200'
		reply["message"] = 'Stock transfer sucessfully'
		return reply
	except Exception as e:
		reply["message"] = str(e)
		reply["message_traceable"] = str(traceback.format_exc())

	return reply




@frappe.whitelist(allow_guest=True)
def stockEntryListAirport(allow_guest=True):
	
	#item_res=[]
	#item_list=frappe.get_all("Stock Entry",filters=[["Stock Entry","from_warehouse","in",["Airport Ahmedabad - SAT"]],["Stock Entry","to_warehouse","in",["Airport Ahmedabad - SAT"]]],fields=['*'],order_by="posting_date")

	query = "SELECT * FROM `tabStock Entry` WHERE (`from_warehouse`='Airport Ahmedabad - SAT' OR `to_warehouse`='Airport Ahmedabad - SAT') AND `docstatus`=1 ORDER BY `posting_date` desc, `posting_time` desc LIMIT 50"
	item_res=frappe.db.sql(query,as_dict=1)

	item_res_response=[]
	for st in item_res:
		
		query = "SELECT * FROM `tabStock Entry Detail` WHERE `parent`='{}'".format(st['name'])
		item_inner=frappe.db.sql(query,as_dict=1)
		st['items']=item_inner
		item_res_response.append(st)

	return item_res_response

@frappe.whitelist(allow_guest=True)
def stockEntryListProduction(allow_guest=True):
	
	query = "SELECT * FROM `tabStock Entry` WHERE (`from_warehouse`='Finished Goods - SAT' OR `to_warehouse`='Finished Goods - SAT') AND `docstatus`=1 ORDER BY `posting_date` desc, `posting_time` desc LIMIT 100"
	item_res=frappe.db.sql(query,as_dict=1)

	item_res_response=[]
	for st in item_res:
		
		query = "SELECT * FROM `tabStock Entry Detail` WHERE `parent`='{}'".format(st['name'])
		item_inner=frappe.db.sql(query,as_dict=1)
		st['items']=item_inner
		item_res_response.append(st)

	return item_res_response

@frappe.whitelist(allow_guest=True)
def stockEntryListRawMaterial(allow_guest=True):
	
	query = "SELECT * FROM `tabStock Entry` WHERE (`from_warehouse`='Stores - SAT' OR `to_warehouse`='Stores - SAT') AND `docstatus`=1 ORDER BY `posting_date` desc, `posting_time` desc LIMIT 100"
	item_res=frappe.db.sql(query,as_dict=1)

	item_res_response=[]
	for st in item_res:
		
		query = "SELECT * FROM `tabStock Entry Detail` WHERE `parent`='{}'".format(st['name'])
		item_inner=frappe.db.sql(query,as_dict=1)
		st['items']=item_inner
		item_res_response.append(st)

	return item_res_response