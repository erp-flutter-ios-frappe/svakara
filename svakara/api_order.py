from __future__ import unicode_literals
import frappe
import json
import traceback
from frappe.auth import LoginManager, CookieManager
from erpnext.globle import globleUserLogin
from erpnext.api_dl_auto import delivery_note_auto
from frappe.utils import today
import datetime


@frappe.whitelist(allow_guest=True)
def staff_order(items,discountAmount,totalQty,totalMRP,orderAmount,customerName,paymentMode,transactionDate,note,mobileNo=None):
#Ravi
	reply={}
	reply["data"] = []
	reply["status_code"] = '500'
	reply["message"] = 'There is issue.'

	warehousefinal = 'Finished Goods - SAT'
	if customerName in ['Airport - Ahmedabad']:
		warehousefinal = 'Airport Ahmedabad - SAT'


	try:
		d1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Sales Order",
			"name": "New Sales Order 1",
			"__islocal": 1,
			"__unsaved": 1,
			"items": json.loads(items),
			#"items": salesOrderItems(items,customerName),
			"transaction_date": transactionDate,
			"delivery_date":transactionDate,
			"payment_mode":paymentMode,
			"customer":customerName,
			"set_warehouse":warehousefinal,
			"discount_amount":float(discountAmount),
			"custom_special_note":"Login mobile number {}. Note: {}".format(mobileNo,note),
		})
		d2=d1.insert(ignore_permissions=True)
		frappe.local.form_dict = globleUserLogin()
		frappe.local.cookie_manager = CookieManager()
		frappe.local.login_manager = LoginManager()
		temp = d2.submit()
		delivery_note_auto(temp.name)
		reply["data"] = temp
		reply["status_code"] = '200'
		reply["message"] = 'Sales order place sucessfully'
		return reply
	except Exception as e:
		reply["message"] = str(e)
		reply["message_traceable"] = str(traceback.format_exc())

	return reply

@frappe.whitelist(allow_guest=True)
def customerName(items,customerName):
	obj_update=[]
	#for item in json.loads(items):
	for item in json.loads(items):		
		itemadding={}
		itemadding["item_code"]=item['item_code']
		itemadding["qty"] = int(item['qty'])
		#itemadding["s_warehouse"]=sourcewarehous
		obj_update.append(itemadding)
	return obj_update


@frappe.whitelist(allow_guest=True)
def salesOrderList(allow_guest=True):
	
	query = "SELECT * FROM `tabSales Order` WHERE `docstatus` IN (0,1) AND `customer` IN ('Guest - Office','Airport - Ahmedabad','Swiggy - Office','Zomato - Office') ORDER BY `transaction_date` desc LIMIT 100"
	item_res=frappe.db.sql(query,as_dict=1)

	item_res_response=[]
	for st in item_res:
		
		query = "SELECT * FROM `tabSales Order Item` WHERE `parent`='{}'".format(st['name'])
		item_inner=frappe.db.sql(query,as_dict=1)
		st['items']=item_inner
		item_res_response.append(st)

	return item_res_response



@frappe.whitelist(allow_guest=True)
#def sales_order_qty_datewise(start_date,end_date):
def sales_order_qty_datewise():
	
	reply={}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}


	query = "SELECT * FROM `tabSales Order` WHERE `docstatus`=1 ORDER BY `transaction_date` desc LIMIT 100"
	item_res=frappe.db.sql(query,as_dict=1)

	salesorderlist = frappe.get_all('Sales Order', filters=[
							# ["Sales Order","transaction_date",">=",daterange['first']],
							# ["Sales Order","transaction_date","<=",daterange['last']],
							["Sales Order","delivery_date","=",today()],
							["Sales Order","docstatus","!=",2],
							# ["Sales Order","status","not in",["Closed","Cancelled","Completed","To Bill"]],
							], fields=['name'],
							order_by="transaction_date")

	items={}
	for st in salesorderlist:
		
		query = "SELECT qty,item_code,item_name FROM `tabSales Order Item` WHERE `parent`='{}'".format(st['name'])
		item_inner=frappe.db.sql(query,as_dict=1)

		for item in item_inner:

			allkeys = items.keys()

			match_item = False
			for item_code in allkeys:
				if item_code==item['item_code']:
					match_item = True
					items[item_code]['qty'] = float(items[item_code]['qty']) + float(item['qty'])

			if not match_item:
				query = "SELECT custom_sort_order,custom_item_type,custom_image_thumb,default_bom FROM `tabItem` WHERE `name`='{}'".format(item['item_code'])
				item_detail=frappe.db.sql(query,as_dict=1)



				item['custom_sort_order']=item_detail[0]['custom_sort_order']
				item['custom_item_type']=item_detail[0]['custom_item_type']
				item['custom_image_thumb']=item_detail[0]['custom_image_thumb']
				item['default_bom']=item_detail[0]['default_bom']

				
				items[item['item_code']] = item

#Add item which is not in order but present in TRIL Kit
	allkeys = items.keys()
	temp = {}
	for item_code in allkeys:
		if item_code in ['TRIAL']:
			if items[item_code]['default_bom'] not in ['',None,' ']:
				queryItemBOM = "SELECT * FROM `tabBOM Item` WHERE `parent`='{}'".format(items[item_code]['default_bom'])
				listBOMItems = frappe.db.sql(queryItemBOM,as_dict=1)
				for bomItem in listBOMItems:
					if bomItem['item_code'] not in allkeys:
						objectadd = {}
							
						queryItemDetail = "SELECT * FROM `tabItem` WHERE `name`='{}'".format(bomItem['item_code'])
						listItem = frappe.db.sql(queryItemDetail,as_dict=1)
						if len(listItem)!=0:
							objectadd = listItem[0]
							objectadd['qty'] = 0
							temp[bomItem['item_code']] = objectadd

	allkeys = temp.keys()
	for item_code in allkeys:
		items[item_code] = temp[item_code]



#Add trial kit in product List
	allkeys = items.keys()
	for item_code in allkeys:
		if item_code in ['TRIAL']:
			if items[item_code]['default_bom'] not in ['',None,' ']:
				queryItemBOM = "SELECT * FROM `tabBOM Item` WHERE `parent`='{}'".format(items[item_code]['default_bom'])
				listBOMItems = frappe.db.sql(queryItemBOM,as_dict=1)
				for bomItem in listBOMItems:
					for item_code_inner in allkeys:
						if item_code_inner==bomItem['item_code']:
							items[item_code_inner]['qty'] = items[item_code_inner]['qty']+(float(items[item_code]['qty'])*float(bomItem['qty']))


	items_return = []
	allkeys = items.keys()
	for item_code in allkeys:
		if item_code not in ['TRIAL']:
			items_return.append(items[item_code])

	reply['data']=items_return
	return reply



@frappe.whitelist(allow_guest=True)
def sales_order_qty_datewise_v1():
	
	reply={}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}


	query = "SELECT * FROM `tabSales Order` WHERE `docstatus`=1 ORDER BY `transaction_date` desc LIMIT 100"
	item_res=frappe.db.sql(query,as_dict=1)

	salesorderlist = frappe.get_all('Sales Order', filters=[
							# ["Sales Order","transaction_date",">=",daterange['first']],
							# ["Sales Order","transaction_date","<=",daterange['last']],
							["Sales Order","delivery_date","=",today()],
							["Sales Order","docstatus","!=",2],
							# ["Sales Order","status","not in",["Closed","Cancelled","Completed","To Bill"]],
							], fields=['name'],
							order_by="transaction_date")

	items={}
	for st in salesorderlist:
		
		query = "SELECT qty,item_code,item_name FROM `tabSales Order Item` WHERE `parent`='{}'".format(st['name'])
		item_inner=frappe.db.sql(query,as_dict=1)

		for item in item_inner:

			allkeys = items.keys()

			match_item = False
			for item_code in allkeys:
				if item_code==item['item_code']:
					match_item = True
					items[item_code]['qty'] = float(items[item_code]['qty']) + float(item['qty'])

			if not match_item:
				query = "SELECT custom_sort_order,custom_item_type,custom_image_thumb,default_bom FROM `tabItem` WHERE `name`='{}'".format(item['item_code'])
				item_detail=frappe.db.sql(query,as_dict=1)



				item['custom_sort_order']=item_detail[0]['custom_sort_order']
				item['custom_item_type']=item_detail[0]['custom_item_type']
				item['custom_image_thumb']=item_detail[0]['custom_image_thumb']
				item['default_bom']=item_detail[0]['default_bom']

				
				items[item['item_code']] = item

#Add item which is not in order but present in TRIL Kit
	allkeys = items.keys()
	temp = {}
	for item_code in allkeys:
		if item_code in ['TRIAL']:
			if items[item_code]['default_bom'] not in ['',None,' ']:
				queryItemBOM = "SELECT * FROM `tabBOM Item` WHERE `parent`='{}'".format(items[item_code]['default_bom'])
				listBOMItems = frappe.db.sql(queryItemBOM,as_dict=1)
				for bomItem in listBOMItems:
					if bomItem['item_code'] not in allkeys:
						objectadd = {}
							
						queryItemDetail = "SELECT * FROM `tabItem` WHERE `name`='{}'".format(bomItem['item_code'])
						listItem = frappe.db.sql(queryItemDetail,as_dict=1)
						if len(listItem)!=0:
							objectadd = listItem[0]
							objectadd['qty'] = 0
							temp[bomItem['item_code']] = objectadd

	allkeys = temp.keys()
	for item_code in allkeys:
		items[item_code] = temp[item_code]



#Add trial kit in product List
	allkeys = items.keys()
	for item_code in allkeys:
		if item_code in ['TRIAL']:
			if items[item_code]['default_bom'] not in ['',None,' ']:
				queryItemBOM = "SELECT * FROM `tabBOM Item` WHERE `parent`='{}'".format(items[item_code]['default_bom'])
				listBOMItems = frappe.db.sql(queryItemBOM,as_dict=1)
				for bomItem in listBOMItems:
					for item_code_inner in allkeys:
						if item_code_inner==bomItem['item_code']:
							items[item_code_inner]['qty'] = items[item_code_inner]['qty']+(float(items[item_code]['qty'])*float(bomItem['qty']))


	items_return = []
	allkeys = items.keys()
	for item_code in allkeys:
		if item_code not in ['TRIAL']:
			items_return.append(items[item_code])

	reply['data']=items_return
	return reply





@frappe.whitelist(allow_guest=True)
def sales_order_qty_datewise_v2(**kwargs):
	
	reply={}
	reply['status_code']=200
	reply['message']=''
	reply['data']={}

	parameters=frappe._dict(kwargs)

	parametersKeys = parameters.keys()
	if 'start_date' not in parametersKeys:
		reply['status_code']=500
		reply['message']='Start date parameter is not found.'
		return reply

	if 'end_date' not in parametersKeys:
		reply['status_code']=500
		reply['message']='End date parameter is not found.'
		return reply


	format = '%Y-%m-%d'
	datetime_start_date = datetime.datetime.strptime(parameters['start_date'], format)
	start_date = datetime_start_date.date()
	reply['start_date']=start_date

	datetime_end_date = datetime.datetime.strptime(parameters['end_date'], format)
	end_date = datetime_end_date.date()
	reply['end_date']=end_date
	
	if start_date != end_date:
		if start_date > end_date:
			reply['status_code']=500
			reply['message']='Start date is not before end date.'
			return reply

	items={}

	query = "SELECT name FROM `tabSales Order` WHERE `delivery_date`>='{}' AND `delivery_date`<='{}' AND `docstatus`!=2".format(start_date, end_date)
	item_inner_so=frappe.db.sql(query,as_dict=1)

	item_inner=[]
	for so in item_inner_so:
		query = "SELECT qty,item_code,item_name FROM `tabSales Order Item` WHERE `parent`='{}'".format(so['name'])
		so_items=frappe.db.sql(query,as_dict=1)
		for soi in so_items:
			item_inner.append(soi)


	for item in item_inner:

		allkeys = items.keys()

		match_item = False
		for item_code in allkeys:
			if item_code==item['item_code']:
				match_item = True
				items[item_code]['qty'] = float(items[item_code]['qty']) + float(item['qty'])

		if not match_item:
			query = "SELECT custom_sort_order,custom_item_type,custom_image_thumb,default_bom FROM `tabItem` WHERE `name`='{}'".format(item['item_code'])
			item_detail=frappe.db.sql(query,as_dict=1)



			item['custom_sort_order']=item_detail[0]['custom_sort_order']
			item['custom_item_type']=item_detail[0]['custom_item_type']
			item['custom_image_thumb']=item_detail[0]['custom_image_thumb']
			item['default_bom']=item_detail[0]['default_bom']

			
			items[item['item_code']] = item


	reply['before_trial_kit']=items
	
#Add trial kit in product List
	allkeys = items.keys()
	for item_code in allkeys:
		if item_code in ['TRIAL']:
			if items[item_code]['default_bom'] not in ['',None,' ']:
				queryItemBOM = "SELECT * FROM `tabBOM Item` WHERE `parent`='{}'".format(items[item_code]['default_bom'])
				listBOMItems = frappe.db.sql(queryItemBOM,as_dict=1)
				for bomItem in listBOMItems:
					for item_code_inner in allkeys:
						if item_code_inner==bomItem['item_code']:
							items[item_code_inner]['qty'] = items[item_code_inner]['qty']+(float(items[item_code]['qty'])*float(bomItem['qty']))

	items_return = []
	allkeys = items.keys()
	for item_code in allkeys:
		if item_code not in ['TRIAL']:
			items_return.append(items[item_code])

	reply['data']=items_return
	return reply