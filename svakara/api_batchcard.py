from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate
import json
import traceback
from frappe.auth import LoginManager, CookieManager
from erpnext.globle import globleUserLogin




@frappe.whitelist(allow_guest=True)
def item_to_be_manufacting(**kwargs):

	parameters=frappe._dict(kwargs)

	items = parameters['items']
	transaction_date = parameters['transaction_date']
	note = parameters['note']
	mobileNo = parameters['mobileNo']

	reply={}
	reply["data"] = []
	reply["status_code"] = '500'
	reply["message"] = 'There is issue.'

	try:
		# itemListDetail = bomItems(items)
		
		for obj1 in json.loads(items):

			itemListDetail = bomItemsSingle(obj1)

			d1=frappe.get_doc({
				"docstatus": 0,
				"doctype": "Batchcard",
				"name": "New Batchcard 1",
				"__islocal": 1,
				"__unsaved": 1,
				"date": transaction_date,
				"note":note,
				"created_phone": mobileNo,
				"item_to_manufacture":itemListDetail['items'],
				"rmpm":itemListDetail['bom_items'],
			})
			d2=d1.insert(ignore_permissions=True)			
			reply["data"] = d2

		reply["status_code"] = '200'
		reply["message"] = 'Damage stock entry sucessfully.'					

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
		itemadding["qty_to_manufacture"] = float(item['qty'])
		itemadding["item_name"]=item['item_code']
		itemadding["item_display_name"]=item['item_code']

		query = "SELECT * FROM `tabItem` WHERE `item_code`='{}' LIMIT 1".format(item['item_code'])
		itemDetails=frappe.db.sql(query,as_dict=1)

		if len(itemDetails)!=0:
			itemadding["item_name"]=itemDetails[0]['item_name']
			# itemadding["item_display_name"] = stockEntryListProduction(item['item_code'])
			itemadding["item_display_name"] = itemDetails[0]['item_name']

		obj_update.append(itemadding)
	return obj_update

@frappe.whitelist(allow_guest=True)
def bomItemsSingle(item):

	obj_update=[]
	bom_items = []


	itemadding={}
	itemadding["item_code"]=item['item_code']
	itemadding["qty_to_manufacture"] = float(item['qty'])
	itemadding["item_name"]=item['item_code']
	itemadding["item_display_name"]=item['item_code']

	query = "SELECT * FROM `tabItem` WHERE `item_code`='{}' LIMIT 1".format(item['item_code'])
	itemDetails=frappe.db.sql(query,as_dict=1)
	if len(itemDetails)!=0:
		itemadding["item_name"]=itemDetails[0]['item_name']
		# itemadding["item_display_name"] = stockEntryListProduction(item['item_code'])
		itemadding["item_display_name"] = itemDetails[0]['item_name']

	obj_update.append(itemadding)


	#Add BOM items
	queryItemBOM = "SELECT name FROM `tabBOM` WHERE `item`='{}' AND `is_active`='1' AND `is_default`='1'".format(item['item_code'])
	listBOM = frappe.db.sql(queryItemBOM,as_dict=1)
	if len(listBOM)!=0:

		for bom in listBOM:							
			queryItemBOM = "SELECT * FROM `tabBOM Item` WHERE `parent`='{}'".format(bom['name'])
			listBOMItems = frappe.db.sql(queryItemBOM,as_dict=1)
			for bomItem in listBOMItems:
				queryItem = "SELECT * FROM `tabItem` WHERE `name`='{}'".format(bomItem['item_code'])
				listItems = frappe.db.sql(queryItem,as_dict=1)
				if len(listItems)!=0:
					bomItemObj={}
					bomItemObj["item_code"]=listItems[0]['item_code']
					bomItemObj["item_name"]=listItems[0]['item_name']
					bomItemObj["custom_item_type"]=listItems[0]['custom_item_type']
					bomItemObj["item_display_name"]=item_name_converter(listItems[0]['item_code'])
					qtyrequire = float(bomItem['qty'])*float(item['qty'])
					bomItemObj["require_qty"] = float(bomItem['qty'])*float(item['qty'])
					bomItemObj["umo"] = qty_umo_selection(qtyrequire,listItems[0]['custom_item_type'])
					bom_items.append(bomItemObj)
						

	combineItems = []
	for rawitem in bom_items:
		fondItem = False
		for rawitem2 in combineItems:
			if rawitem['item_code']==rawitem2['item_code']:
				rawitem2['require_qty'] += float(rawitem['require_qty'])
				fondItem = True

		if not fondItem:
			combineItems.append(rawitem)


	amountcombineItems = []
	for rawitem in combineItems:
		requqty = str(round(float(rawitem['require_qty']),2)).split(".")
		if len(requqty) >= 1:
			qty = requqty[1]
			if len(qty)==1:
				qty = "{}00".format(qty)
			if len(qty)==2:
				qty = "{}0".format(qty)

			requqty = "{}.{}".format(requqty[0],qty)

		rawitem['require_qty'] = str(requqty)
		amountcombineItems.append(rawitem)



	#Set RM on TOP
	rm=[]
	pm=[]
	for i in amountcombineItems:
		if str(i["custom_item_type"])=="raw":
			rm.append(i)
		else:
			pm.append(i)


	finalreturn = []
	for r in rm:
		finalreturn.append(r)

	for p in pm:
		finalreturn.append(p)		



	reply={}
	reply['items']=obj_update
	reply['bom_items']=finalreturn

	return reply



@frappe.whitelist(allow_guest=True)
def bomItems(items):

	obj_update=[]
	bom_items = []


	for item in json.loads(items):

		itemadding={}
		itemadding["item_code"]=item['item_code']
		itemadding["qty_to_manufacture"] = float(item['qty'])
		itemadding["item_name"]=item['item_code']
		itemadding["item_display_name"]=item['item_code']

		query = "SELECT * FROM `tabItem` WHERE `item_code`='{}' LIMIT 1".format(item['item_code'])
		itemDetails=frappe.db.sql(query,as_dict=1)
		if len(itemDetails)!=0:
			itemadding["item_name"]=itemDetails[0]['item_name']
			# itemadding["item_display_name"] = stockEntryListProduction(item['item_code'])
			itemadding["item_display_name"] = itemDetails[0]['item_name']

		obj_update.append(itemadding)


		#Add BOM items
		queryItemBOM = "SELECT name FROM `tabBOM` WHERE `item`='{}' AND `is_active`='1' AND `is_default`='1'".format(item['item_code'])
		listBOM = frappe.db.sql(queryItemBOM,as_dict=1)
		if len(listBOM)!=0:

			for bom in listBOM:							
				queryItemBOM = "SELECT * FROM `tabBOM Item` WHERE `parent`='{}'".format(bom['name'])
				listBOMItems = frappe.db.sql(queryItemBOM,as_dict=1)
				for bomItem in listBOMItems:
					queryItem = "SELECT * FROM `tabItem` WHERE `name`='{}'".format(bomItem['item_code'])
					listItems = frappe.db.sql(queryItem,as_dict=1)
					if len(listItems)!=0:
						bomItemObj={}
						bomItemObj["item_code"]=listItems[0]['item_code']
						bomItemObj["item_name"]=listItems[0]['item_name']
						bomItemObj["custom_item_type"]=listItems[0]['custom_item_type']
						bomItemObj["item_display_name"]=item_name_converter(listItems[0]['item_code'])
						qtyrequire = float(bomItem['qty'])*float(item['qty'])
						bomItemObj["require_qty"] = float(bomItem['qty'])*float(item['qty'])
						bomItemObj["umo"] = qty_umo_selection(qtyrequire,listItems[0]['custom_item_type'])
						bom_items.append(bomItemObj)
						

	combineItems = []
	for rawitem in bom_items:
		fondItem = False
		for rawitem2 in combineItems:
			if rawitem['item_code']==rawitem2['item_code']:
				rawitem2['require_qty'] += float(rawitem['require_qty'])
				fondItem = True

		if not fondItem:
			combineItems.append(rawitem)

	#Set RM on TOP
	rm=[]
	pm=[]
	for i in combineItems:
		if str(i["custom_item_type"])=="raw":
			rm.append(i)
		else:
			pm.append(i)


	finalreturn = []
	for r in rm:
		finalreturn.append(r)

	for p in pm:
		finalreturn.append(p)		



	reply={}
	reply['items']=obj_update
	reply['bom_items']=finalreturn

	return reply

def qty_umo_selection(qty,item_group):

	if item_group!="raw":
		return "નંગ"

	if qty < 1:
		return "ગ્રામ"

	return "કિલો"

def item_name_converter(item_code):

	if item_code in ['Apple']:
		return "સફરજન"
	if item_code in ['BEETROOT']:
		return "બીટ"
	if item_code in ['WHEATGRASS']:
		return "વીટગ્રાસ્સ"
	if item_code in ['KIWI']:
		return "કીવી"
	if item_code in ['Grape']:
		return "દ્રાક્ષ"
	if item_code in ['Ginger']:
		return "આદુ"
	if item_code in ['Orange']:
		return "સંતરા"
	if item_code in ['Pomegranate']:
		return "દાઢમ"
	if item_code in ['MOSAMBI']:
		return "મોસંબી"
	if item_code in ['CUCUMBER']:
		return "કાકડી"
	if item_code in ['LEMON']:
		return "લીંબુ"
	if item_code in ['CARROT']:
		return "ગાજર"
	if item_code in ['MINT']:
		return "ફુદીનો"
	if item_code in ['AMLA']:
		return "આમળા"
	if item_code in ['SPINACH']:
		return "પાલક"
	if item_code in ['TURMERIC']:
		return "હળદર"
	if item_code in ['CINNAMON']:
		return "તજ"
	if item_code in ['Pineapple']:
		return "પાઈનેઆપ્પલ"






	return item_code







@frappe.whitelist(allow_guest=True)
def stockEntryListProduction(allow_guest=True):
	
	query = "SELECT * FROM `tabBatchcard` ORDER BY `date` desc, `creation` desc LIMIT 35"
	item_res=frappe.db.sql(query,as_dict=1)

	item_res_response=[]
	for st in item_res:
		
		query = "SELECT * FROM `tabBatchcard item child` WHERE `parent`='{}'".format(st['name'])
		item_inner=frappe.db.sql(query,as_dict=1)
		st['items']=item_inner

		queryRMPM = "SELECT * FROM `tabBatchcard RM Child` WHERE `parent`='{}' ORDER BY `idx` asc".format(st['name'])
		RMPMList=frappe.db.sql(queryRMPM,as_dict=1)
		st['items_rmpm']=RMPMList

		item_res_response.append(st)

	return item_res_response