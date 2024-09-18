from __future__ import unicode_literals
from frappe import throw, msgprint, _
import frappe
import traceback
from svakara.globle import appErrorLog,defaultResponseBody,defaultResponseErrorBody,globleLoginUser



@frappe.whitelist(allow_guest=True)
def item_list(**kwargs):
	
	parameters=frappe._dict(kwargs)
	reply=defaultResponseBody()
	keysList = list(parameters.keys())

	if 'distributor' not in keysList:
		reply["message"]="Distributor not found in parameters."
		return reply
	
	query2="SELECT * FROM `tabItem` WHERE `item_code` IN (SELECT item_code FROM `tabDistributor Item` WHERE `parent`='{}')".format(parameters['distributor'])
	item_list_previous = frappe.db.sql(query2,as_dict=1)

	reply['data']=item_list_previous


	return reply





@frappe.whitelist(allow_guest=True)
def item_create(**kwargs):

	parameters=frappe._dict(kwargs)
	reply=defaultResponseBody()
	

	keysList = list(parameters.keys())


	if 'item_name' not in keysList:
		reply["message"]="Item name not found in parameters."
		return reply

	if 'item_group' not in keysList:
		reply["message"]="Item group not found in parameters."
		return reply

	if 'item_type' not in keysList:
		reply["message"]="Item type not found in parameters."
		return reply

	if 'uom' not in keysList:
		reply["message"]="UOM not found in parameters."
		return reply

	if 'rate' not in keysList:
		reply["message"]="Rate not found in parameters."
		return reply
	
	if 'distributor' not in keysList:
		reply["message"]="Distributor not found in parameters."
		return reply	

	nameKey = ""
	if 'name' in keysList:
		nameKey = parameters['name']





	query2="SELECT name FROM `tabDistributor Item` WHERE `parent`='{}'".format(parameters['distributor'])
	item_list_previous = frappe.db.sql(query2,as_dict=1)


	item_co = ""
	for i in parameters['item_name'].split(' '):
		item_co="{}{}".format(item_co,i[0].upper())

	item_code = "{}{}{}".format(parameters['distributor'],item_co,len(item_list_previous)+1)


	query2="SELECT name FROM `tabItem` WHERE `item_code`='{}'".format(item_code)
	item_list = frappe.db.sql(query2,as_dict=1)
	if len(item_list)!=0:
		reply['message']="Item is already present."
		return reply

	sessionuser = frappe.session.user
	frappe.set_user(globleLoginUser())


	if nameKey!="":
		frappe.db.sql("""UPDATE `tabItem` SET `description`='"""+parameters['description']+"""',`standard_rate`='"""+parameters['rate']+"""',`custom_pack_size`='"""+parameters['custom_pack_size']+"""',`stock_uom`='"""+parameters['uom']+"""',`item_name`='"""+parameters['item_name']+"""',`item_group`='"""+parameters['item_group']+"""',`custom_item_type`='"""+parameters['item_type']+"""' WHERE `name`='"""+nameKey+"""' """)
		reply["message"]="Item updated."
		reply['data']=frappe.get_doc('Item',nameKey)

		return reply




	try:

		p = frappe.get_doc({
			"docstatus":0,
			"doctype":"Item",
			"name":"New Item 1",
			"__islocal":1,
			"__unsaved":1,
			"item_code":item_code,
			"item_name":parameters['item_name'],
			"company":frappe.defaults.get_user_default("Company"),
			"item_group":parameters['item_group'],
			"custom_item_type":parameters['item_type'],
			"stock_uom":parameters['uom'],
			"valuation_rate":parameters['rate'],
			"standard_rate":parameters['rate'],
			"custom_subscriber_rate":parameters['rate'],
			"description":parameters['description'],
			"custom_pack_size":parameters['custom_pack_size'],
			"is_stock_item":0,
			"is_sales_item":1
		})
		itemAdded = p.insert(ignore_permissions=True)
		reply['data']=itemAdded
		

		doc_distributor = frappe.get_doc('Distributor',parameters['distributor'])
		
		child = frappe.new_doc("Distributor Item")
		child.update({
			'item_code': itemAdded.name,
			'item_name': itemAdded.item_name,
			'parent': doc_distributor.name,
			'parenttype': 'Distributor',
			'parentfield': 'item'
		})
		doc_distributor.item.append(child)
		doc_distributor.save(ignore_permissions=True)


		frappe.db.sql("""UPDATE `tabItem Default` SET `default_warehouse`='"""+doc_distributor.warehouse+"""' WHERE `parent`='"""+itemAdded.name+"""' """)
		frappe.db.commit()
		reply["message"]="Item created."

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_distributor','distributor_create')


	if sessionuser not in [None,'',"","None"]:
		frappe.set_user(sessionuser)
	
	return reply