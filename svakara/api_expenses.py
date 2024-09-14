from __future__ import unicode_literals
import frappe
from frappe import _
import traceback
from datetime import datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_details
from frappe.utils import today
from svakara.globle import appErrorLog,defaultResponseBody,defaultResponseErrorBody

################# Expenses
#install hrms appliacation on site
# Expense Claim - Add field "custom_month" (Select)
# January
# February
# March
# April
# May
# June
# July
# August
# September
# October
# November
# December

# Expense Claim - Add field "custom_year" (Select)

@frappe.whitelist(allow_guest=True)
def expenses_type(**kwargs):

	parameters=frappe._dict(kwargs)
	reply=defaultResponseBody()
	reply["data"]=[]
	reply["parameters"]=parameters

	try:
		reply["data"]=frappe.get_all("Expense Claim Type",fields=["*"])
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_expenses','expenses_type')

	return reply
	
@frappe.whitelist(allow_guest=True)
def expenses_list(**kwargs):

	parameters=frappe._dict(kwargs)

	reply=defaultResponseBody()
	reply["data"]=[]
	reply["parameters"]=parameters

	try:
		expenseList = frappe.get_all('Expense Claim', filters=[["Expense Claim","custom_month","=",parameters['month']],
												["Expense Claim","custom_year","=",parameters['year']],
												["Expense Claim","employee","=",parameters['employee']],
												], fields=['*'],
												order_by="posting_date")
		if len(expenseList)!=0:
			explist = frappe.get_all('Expense Claim Detail', filters=[["Expense Claim Detail","parent","=",str(expenseList[0]["name"])],
												], fields=['*'],
												order_by="expense_date")
			reply["data"]=explist
		else:
			reply["data"]=[]
		
		return reply
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_expenses','expenses_list')

	return reply

@frappe.whitelist(allow_guest=True)
def expenses_delete_child(**kwargs):

	parameters=frappe._dict(kwargs)

	reply=defaultResponseBody()
	reply["data"]=[]
	reply["parameters"]=parameters

	try:
		expenseChildList = frappe.get_all('Expense Claim Detail', filters=[["Expense Claim Detail","name","=",str(parameters['recordname'])]], fields=['*'])
		if len(expenseChildList)!=0:
			expenseList = frappe.get_all('Expense Claim Detail', filters=[["Expense Claim Detail","parent","=",str(expenseChildList[0]["parent"])]], fields=['*'])

			# for filedelete in expenseList:
			# 	if filedelete['custom_image'] not in [None,""," "]:
			# 		doc = frappe.get_doc(doctype='File', file_url=filedelete['custom_image'])
			# 		if doc:
			# 			dl = frappe.delete_doc(doctype='File',name=doc.name,ignore_permissions=True,delete_permanently=True)


			if len(expenseList)==1:
				# if str(expenseChildList[0]["expense_type"]) in ["Mobile"]:
				# 	reply={}
				# 	frappe.local.response['http_status_code'] = 500
				# 	reply["status_code"]="500"
				# 	reply["message"]="You are not allow to delete this expense."
				# 	return reply
				# else:
				removeOrderquery = """DELETE  FROM `tabExpense Claim` WHERE  name='"""+str(expenseChildList[0]["parent"])+"""'"""
				frappe.db.sql(removeOrderquery)
			else:
				# if str(expenseChildList[0]["expense_type"]) in ["Mobile"]:
				# 	reply={}
				# 	frappe.local.response['http_status_code'] = 500
				# 	reply["status_code"]="500"
				# 	reply["message"]="You are not allow to delete this expense."
				# 	reply["error1"]=traceback.format_exc()
				# 	return reply
				# else:
				removeOrderquery = """DELETE  FROM `tabExpense Claim Detail` WHERE  name='"""+str(parameters['recordname'])+"""'"""
				frappe.db.sql(removeOrderquery)

			frappe.db.commit()
	
			return expenses_list(month=parameters['month'],year=parameters['year'],employee=parameters['employee'])
		
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_expenses','expenses_list')

	return reply

@frappe.whitelist(allow_guest=True)
def expenses_add(**kwargs):

	parameters=frappe._dict(kwargs)

	reply=defaultResponseBody()
	reply["data"]=[]
	reply["parameters"]=parameters

	try:
		expenseList = frappe.get_all('Expense Claim', filters=[["Expense Claim","custom_month","=",parameters['month']],
													["Expense Claim","custom_year","=",parameters['year']],
													["Expense Claim","employee","=",parameters['employee']],
													], fields=['*'],
													order_by="posting_date")
		if len(expenseList)!=0:
			reply = expenses_add_child(str(expenseList[0]["name"]),parameters['month'],parameters['year'],parameters['employee'],parameters['expense_date'],parameters['expensetype'],parameters['expensediscription'],parameters['expenseamount'])
			return reply
		else:
			expenseaprrove=frappe.db.get("Employee",parameters['employee'])
			#la=frappe.get_all("Employee Leave Approver",{"parent":ecode},["leave_approver"])
			childexpenses = []
			childexpenses.append({
				'expense_date': parameters['expense_date'],
				'expense_type': parameters['expensetype'],
				'description': parameters['expensediscription'],
				'amount': parameters['expenseamount'],
				'sanctioned_amount':parameters['expenseamount'],
			})

			d = frappe.get_doc({
				"doctype": "Expense Claim",
				"custom_year":str(parameters['year']),
				"custom_month":str(parameters['month']),
				"employee":str(parameters['employee']),
				"expense_approver":expenseaprrove.expense_approver,
				"expenses":childexpenses
#				"payable_account":"Provision for Salary - BSPL"
			})
			if d.insert(ignore_permissions=True):
				reply = expenses_list(month=parameters['month'],year=parameters['year'],employee=parameters['employee'])
				expenseChildList = frappe.get_all('Expense Claim Detail', filters=[["Expense Claim Detail","parent","=",str(d.name)]], fields=['*'],order_by="creation")
				reply["data2"]=expenseChildList
				return reply
			else:
				frappe.local.response['http_status_code'] = 500
				reply["data"]=[]
				reply["message"]="Expense not created."
				reply["status_code"]="500"
				return reply

	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply = defaultResponseErrorBody(reply,str(e),str(traceback.format_exc()),'api_expenses','expenses_add')

	return reply

@frappe.whitelist(allow_guest=True)
def expenses_add_child(recordname,month,year,employee,expense_date,expensetype,expensediscription,expenseamount):

	reply={}
	parent = frappe.get_doc('Expense Claim', recordname)
	child = frappe.new_doc("Expense Claim Detail")
	child.update({'expense_date': expense_date,
	'expense_type': expensetype,
	'description': expensediscription,
	'amount': expenseamount,
	'sanctioned_amount':expenseamount,
	'parent': parent.name,
	'parenttype': 'Expense Claim',
	'parentfield': 'expenses'})
	parent.expenses.append(child)
	parent.save(ignore_permissions=True)
	frappe.db.commit()

	reply = expenses_list(month=month,year=year,employee=employee)


	expenseChildList = frappe.get_all('Expense Claim Detail', filters=[
		["Expense Claim Detail","expense_date","=",str(expense_date)],
		["Expense Claim Detail","expense_type","=",str(expensetype)],
		["Expense Claim Detail","description","=",str(expensediscription)],
		["Expense Claim Detail","amount","=",str(expenseamount)],
		["Expense Claim Detail","parent","=",str(parent.name)],
	], fields=['*'],order_by="creation desc")

	reply["data2"]=expenseChildList
	return reply