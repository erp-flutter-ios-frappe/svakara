from __future__ import unicode_literals
from frappe import throw, msgprint, _
import frappe
import traceback
from svakara.globle import appErrorLog,defaultResponseBody,defaultResponseErrorBody
from datetime import datetime
from svakara.api_app_user import ContactAddNew




@frappe.whitelist(allow_guest=True)
def distributor_create(**kwargs):

	parameters=frappe._dict(kwargs)
	reply=defaultResponseBody()
	

	keysList = list(parameters.keys())


	if 'phone' not in keysList:
		reply["message"]="Phone number not found in parameters."
		return reply

	if 'first_name' not in keysList:
		reply["message"]="First name not found in parameters."
		return reply

	if 'last_name' not in keysList:
		reply["message"]="Last name not found in parameters."
		return reply

	if 'city' not in keysList:
		reply["message"]="City not found in parameters."
		return reply

	if 'pin_code' not in keysList:
		reply["message"]="Pincode not found in parameters."
		return reply		


	phone = parameters['phone']
	first_name = parameters['first_name']
	last_name = parameters['last_name']
	company_name = parameters['company_name']
	city = parameters['city']
	pin_code = parameters['pin_code']


	if company_name in ['',' ',None]:
		company_name = "{} {}".format(first_name,last_name)
	
	reply['data']={}

	try:

		query2="SELECT name FROM `tabDistributor` WHERE `name`='{}'".format(str(phone))
		distribotor_list = frappe.db.sql(query2,as_dict=1)
		if len(distribotor_list)!=0:
			reply["message"]="Distributor is already created. Ditributor ID : {}".format(distribotor_list[0]['name'])
			return reply
		

		##  Customer created
		ditributorUniqueNo = "DIST{}".format(phone)
		query2="SELECT * FROM `tabCustomer` WHERE `name`='{}'".format(ditributorUniqueNo)
		customer_list = frappe.db.sql(query2,as_dict=1)
		if len(customer_list)==0:
			qury = "INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`,`modified_by`,`mobile_no`) VALUES ('{}', '{}', '0',  '0', 'CUST-', '0', '{}', 'India','Individual', 'Individual', '0', '{}', '{}', '{}', '{}', '{}', '{}')".format(ditributorUniqueNo, phone, company_name, city, pin_code,datetime.now(),datetime.now(),phone,phone)
			frappe.db.sql(qury)
			frappe.db.commit()
			query2="SELECT * FROM `tabCustomer` WHERE `name`='{}'".format(ditributorUniqueNo)
			customer_list = frappe.db.sql(query2,as_dict=1)

		if len(customer_list)==0:
			reply["message"]="Customer not found."
			return reply

		customer = customer_list[0]

		#Create Contact
		frappe.enqueue(ContactAddNew,queue='long',job_name="Create contact for customer: {}".format(customer['name']),timeout=100000,phone=phone,customer=customer['name'])
		

		query2="SELECT * FROM `tabWarehouse` WHERE `warehouse_name`='{}'".format(ditributorUniqueNo)
		warehouse_list = frappe.db.sql(query2,as_dict=1)
		if len(warehouse_list)==0:
			
			p = frappe.get_doc({
				"docstatus":0,
				"doctype":"Warehouse",
				"name":"New Warehouse 1",
				"__islocal":1,
				"__unsaved":1,
				"warehouse_name":ditributorUniqueNo,
				"name":ditributorUniqueNo,
				"company":frappe.defaults.get_user_default("Company"),
			})
			war = p.insert(ignore_permissions=True)
			frappe.db.commit()
			query2="SELECT * FROM `tabWarehouse` WHERE `name`='{}'".format(war.name)
			warehouse_list = frappe.db.sql(query2,as_dict=1)

		if len(warehouse_list)==0:
			reply["message"]="Warehouse not found."
			return reply

		warehouse = warehouse_list[0]


		query2="SELECT * FROM `tabDistributor` WHERE `mobile`='{}'".format(phone)
		distributor_list = frappe.db.sql(query2,as_dict=1)
		if len(distributor_list)==0:
			p = frappe.get_doc({
				"docstatus":0,
				"doctype":"Distributor",
				"name":"New Distributor 1",
				"__islocal":1,
				"__unsaved":1,
				"full_name":company_name,
				"mobile":phone,
				"distributor_first_name":first_name,
				"distributor_last_name":last_name,
				"customer":customer['name'],
				"warehouse":warehouse['name'],})
			p.insert(ignore_permissions=True)
			frappe.db.commit()
			query2="SELECT * FROM `tabDistributor` WHERE `mobile`='{}'".format(phone)
			distributor_list = frappe.db.sql(query2,as_dict=1)

		if len(distributor_list)==0:
			reply["message"]="destributor not found/created."
			return reply

		distributor = distributor_list[0]




		query2="SELECT * FROM `tabDelivery Team` WHERE `distributor`='{}' AND `customer`='{}'".format(distributor['name'],customer['name'])
		dl_list = frappe.db.sql(query2,as_dict=1)
		if len(dl_list)==0:
			dl = frappe.get_doc({
				"docstatus":0,
				"doctype":"Delivery Team",
				"name":"New Delivery Team 1",
				"__islocal":1,
				"__unsaved":1,
				"employee_name":company_name,
				"customer":customer['name'],
				"distributor":distributor['name'],
				"mobile":phone
			})
			dl.insert(ignore_permissions=True)
			frappe.db.commit()





		#Page Permission

		query2="SELECT * FROM `tabStaff Page Permission` WHERE `customer`='{}'".format(customer['name'])
		spp_list = frappe.db.sql(query2,as_dict=1)
		if len(spp_list)==0:
			pagePermission = frappe.get_doc({
				"docstatus":0,
				"doctype":"Staff Page Permission",
				"name":"New Staff Page Permission 1",
				"__islocal":1,
				"__unsaved":1,
				"customer":customer['name'],
			})
			pp = pagePermission.insert(ignore_permissions=True)
			frappe.db.commit()
			query2="SELECT * FROM `tabStaff Page Permission` WHERE `customer`='{}'".format(customer['name'])
			spp_list = frappe.db.sql(query2,as_dict=1)

		if len(spp_list)==0:
			reply["message"]="Page permission not found"
			return reply

		spp = spp_list[0]





		pp_doc = frappe.get_doc('Staff Page Permission',spp.name)

		child = frappe.new_doc("Staff Page Permission Child")
		child.update({'page': 'Customer Create',
		'image': 'http://104.197.164.49/files/customer_create_new.gif',
		'title': 'Create Customer',
		'parent': pp_doc.name,
		'parenttype': 'Staff Page Permission',
		'parentfield': 'pages'})
		pp_doc.pages.append(child)
			
		pp_doc.save(ignore_permissions=True)




		reply["message"]="Distributor created."

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_staff_customer','create_customer')

	return reply