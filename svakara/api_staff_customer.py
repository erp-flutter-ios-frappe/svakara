from __future__ import unicode_literals
from frappe import throw, msgprint, _
import frappe
import traceback
from svakara.globle import appErrorLog,defaultResponseBody,defaultResponseErrorBody
from datetime import datetime
from svakara.account_utils import GetBalance



@frappe.whitelist(allow_guest=True)
def customer_create(**kwargs):

	parameters=frappe._dict(kwargs)

	phoneNo = parameters['phone']
	firstName = parameters['first_name']
	lastName = parameters['last_name']
	city = parameters['city']
	pincode = parameters['pincode']


	reply=defaultResponseBody()
	reply['data']={}

	try:

		query2="SELECT name FROM `tabCustomer` WHERE `name`='{}'".format(str(phoneNo))
		customer_list = frappe.db.sql(query2,as_dict=1)
		if len(customer_list)>0:
			reply["message"]="customer is already created."
			return reply

		customerName = "{} {}".format(firstName,lastName)
		# qury = "INSERT INTO `tabUser` (`name`,`full_name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`,`creation`,`modified`,`modified_by`,`phone`,`mobile_no`) VALUES ('{}','{}', 'Guest', '0', '0', 'Website User', '{}', '1', '{}', '0', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(phoneNo,customerName, lastName,firstName,phoneNo+'@example.com', phoneNo,city,pincode,datetime.now(),datetime.now(),phoneNo,phoneNo,phoneNo)
		# frappe.db.sql(qury)


		# frappe.db.sql("""INSERT INTO `tabUser` (`name`, `owner`, `docstatus`, `idx`, `user_type`, `last_name`, `thread_notify`, `first_name`, `login_after`, `email`, `username`, `location`, `bio`) VALUES ('"""+phoneNo+"""', 'Guest', '0', '0', 'Website User', '"""+lastName+"""', '1', '"""+firstName+"""', '0', '"""+phoneNo+"""@example.com', '"""+phoneNo+"""', '"""+city+"""', '"""+pincode+"""')""")			

		# d = frappe.get_doc({
		# 	"doctype": "User",
		# 	"docstatus": 0,
		# 	"__islocal": 1,
		# 	"__unsaved": 1,
		# 	"name": phoneNo,
		# 	"user_type": 'Website User',
		# 	"last_name": lastName,
		# 	"first_name": firstName,
		# 	"email": "{}@example.com".format(phoneNo),
		# 	"username": phoneNo,
		# 	"location": city,
		# 	"bio": pincode,
		# })
		# d1 = d.insert(ignore_permissions=True)

		# frappe.rename_doc("User", d1.name, phoneNo)

		# return reply

		
		qury = "INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`,`modified_by`,`mobile_no`) VALUES ('{}', '{}', '0',  '0', 'CUST-', '0', '{}', 'India','Individual', 'Individual', '0', '{}', '{}', '{}', '{}', '{}', '{}')".format(phoneNo, phoneNo, customerName, city, pincode,datetime.now(),datetime.now(),phoneNo,phoneNo)
		frappe.db.sql(qury)
		# frappe.db.sql("""INSERT INTO `tabCustomer` (`name`, `owner`, `docstatus`,  `idx`, `naming_series`, `disabled`, `customer_name`, `territory`, `customer_group`, `customer_type`, `is_frozen`, `custom_city`, `custom_pincode`,`creation`,`modified`,`modified_by`) VALUES ('"""+phoneNo+"""', '"""+phoneNo+"""', '0',  '0', 'CUST-', '0', '"""+customerName+"""', 'India','Individual', 'Individual', '0', '"""+city+"""', '"""+pincode+"""')""")		
		# doc_customer = frappe.get_doc({
		# 	"doctype": "Customer",
		# 	"docstatus": 0,
		# 	"__islocal": 1,
		# 	"__unsaved": 1,
		# 	"name": phoneNo,
		# 	"mobile_no":phoneNo,
		# 	"customer_name": "{} {}".format(firstName,lastName),
		# 	"customer_group": 'Individual',
		# 	"customer_type": 'Individual',
		# 	"custom_city": city,
		# 	"custom_pincode": pincode,
		# })
		# doc_customer.insert(ignore_permissions=True)
		# # contactAdd(doc_customer.name,phoneNo,firstName,lastName)
		# frappe.db.commit()

		# sessionuser = frappe.session.user
		# frappe.set_user(globleLoginUser())
		# frappe.rename_doc("Customer",doc_customer.name,phoneNo)
		# frappe.set_user(sessionuser)
		frappe.enqueue(contactAdd,queue='long',job_name="Customer detail update: {}".format(phoneNo),timeout=100000,customer=phoneNo,phoneNo=phoneNo,first_name=firstName,last_name=lastName)

		# d = frappe.get_doc({
		# 	"doctype": "DefaultValue",
		# 	"parent": "" + phoneNo,
		# 	"parenttype": "User Permission",
		# 	"parentfield": "system_defaults",
		# 	"defkey": "Customer",
		# 	"defvalue": phoneNo
		# })
		# d.insert(ignore_permissions=True)

		# p = frappe.get_doc({
		# 	"docstatus":0,
		# 	"doctype":"User Permission",
		# 	"name":"New User Permission 1",
		# 	"__islocal":1,
		# 	"__unsaved":1,
		# 	"apply_for_all_roles":0,
		# 	"__run_link_triggers":0,
		# 	"user":phoneNo,
		# 	"allow":"Customer",
		# 	"for_value":phoneNo})        
		# p.insert(ignore_permissions=True)
		reply["message"]="customer created"

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_staff_customer','create_customer')

	return reply


@frappe.whitelist(allow_guest=True)
def contactAdd(customer,phoneNo,first_name,last_name):
	
	reply=defaultResponseBody()
	try:


		filters = [
			["Dynamic Link", "link_doctype", "=", "Customer"],
			["Dynamic Link", "link_name", "=", customer]
		]
		contactList = frappe.get_all("Contact", filters=filters, fields=['*'])

		contactDocument = ''
		if len(contactList)==0:
			d = frappe.get_doc({
					"doctype":"Contact",
					"customer": phoneNo,
					"first_name":first_name,
					"last_name":last_name,
					"docstatus":0,
					"links": [{"link_doctype":"Customer","doctype":"Dynamic Link","idx":1,"parenttype":"Contact","link_name":phoneNo,"docstatus":0,"parentfield":"links"}]
				})
			contactDocument = d.insert(ignore_permissions=True)
		else:
			contactDocument = frappe.get_doc("Contact",contactList[0]['name'])

		child = frappe.new_doc("Contact Phone")
		child.update({'phone': phoneNo,
		'is_primary_phone': 1,
		'is_primary_mobile_no': 1,
		'parent': d.name,
		'parenttype': 'Contact',
		'parentfield': 'phone_nos'})
		contactDocument.phone_nos.append(child)
		contactDocument.save(ignore_permissions=True)
		frappe.db.commit()

		frappe.db.sql("""UPDATE `tabCustomer` SET `customer_primary_contact`='"""+d.name+"""' WHERE `name`='"""+phoneNo+"""' """)

		reply['message']="Contact added sucessfully"
		reply['name']=d.name
		return reply
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_app_user','contactAdd')

	return reply






@frappe.whitelist(allow_guest=True)
def customer_list(**kwargs):

	parameter = frappe._dict(kwargs)

	reply=defaultResponseBody()
	reply["parameters"]=parameter
	reply["data"]=[]

	query = "SELECT * FROM `tabCustomer`"
	reply["data"] = frappe.db.sql(query,as_dict=1)

	return reply

@frappe.whitelist(allow_guest=True)
def customer_detail(**kwargs):

	parameters=frappe._dict(kwargs)
	reply=defaultResponseBody()
	reply['data']={}
	reply["parameters"]=parameters
	reply["data"]={}
	reply['address']=[]
	reply['contact']=[]
	reply['balance']=[]

	allParamKeys = parameters.keys()

	if "name" not in allParamKeys:
		reply["status_code"]="500"
		reply["message"]="Name key parameter is missing."
		return reply
	
	try:
		query = "SELECT * FROM `tabCustomer` WHERE `name`='{}'".format(parameters['name'])
		custmoerDetailList = frappe.db.sql(query,as_dict=1)
		if len(custmoerDetailList)!=0:
			custmoerDetail = custmoerDetailList[0]
			custmoerDetail['address']=[]
			custmoerDetail['contact']=[]
			

			custmoerDetail['balance']=GetBalance(custmoerDetailList[0]['name'])


			address_id=frappe.db.sql("""SELECT `tabAddress`.name FROM `tabAddress` inner join `tabDynamic Link` on `tabAddress`.name=`tabDynamic Link`.parent WHERE `tabDynamic Link`.link_name=%s AND `tabDynamic Link`.link_doctype='Customer' AND `tabDynamic Link`.parenttype='Address' AND `tabAddress`.disabled=0""",custmoerDetail['name'])
			if not len(address_id)==0:
				addresslist = []
				for add in address_id:
					addDetail=frappe.get_doc("Address",add[0])
					addresslist.append(addDetail)

				custmoerDetail['address']=addresslist
				reply['address']=addresslist


			contact_id=frappe.db.sql("""SELECT `tabContact`.name FROM `tabContact` inner join `tabDynamic Link` on `tabContact`.name=`tabDynamic Link`.parent WHERE `tabDynamic Link`.link_name=%s AND `tabDynamic Link`.link_doctype='Customer' AND `tabDynamic Link`.parenttype='Contact'""",custmoerDetail['name'])
			# reply['contact_id']=contact_id
			contact_list = []
			for contac in contact_id:
				query = "SELECT * FROM `tabContact Phone` WHERE `parent`='{}'".format(contac[0])
				# reply['contact_child_query']=query
				allcontact = frappe.db.sql(query,as_dict=1)
				# reply['contact_child_response']=allcontact

				for rec in allcontact:
					contact_list.append(rec)

				# conDetail=frappe.get_doc("Contact",contac[0])
				# contact_list.append(conDetail)

			custmoerDetail['contact']=contact_list
			reply['contact']=contact_list



			reply["data"] = custmoerDetail

		return reply
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_staff_customer','customer_detail')
	
	return reply
