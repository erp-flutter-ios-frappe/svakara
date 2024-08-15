from __future__ import unicode_literals
import frappe
from frappe import _
import traceback
from datetime import datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_details
from frappe.utils import today


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
	reply={}
	reply["message"]="list found."
	reply["status_code"]="200"
	reply["data"]=[]

	try:
		listExpensesType=frappe.get_all("Expense Claim Type",fields=["*"])

		data = []
		expenseaprrove=frappe.db.get("Employee",parameters['employee'])

		if expenseaprrove:
			if expenseaprrove.allowance_structure not in ["",None,"none","None"]:
				allowancestructure=frappe.db.get("Allowance Structure",str(expenseaprrove.allowance_structure))
				if allowancestructure:
					for expensestype in listExpensesType:
						expensestype["amount"] = "0"
						expensestype["readonly"] = "0"
						expensestype["hidden"] = "0"
						
						if expensestype["name"] in ["HQ DA"]:
							expensestype["amount"] = allowancestructure.hq_da
							expensestype["readonly"] = "1"
						elif expensestype["name"] in ["Ex HQ DA"]:
							expensestype["amount"] = allowancestructure.ex_hq_da
							expensestype["readonly"] = "1"
						elif expensestype["name"] in ["Ex HQ Metro DA"]:
							expensestype["amount"] = allowancestructure.ex_hq_metro_da
							expensestype["readonly"] = "1"
						elif expensestype["name"] in ["Hotel N Food"]:
							expensestype["amount"] = allowancestructure.hotel_n_food
							expensestype["readonly"] = "0"
						elif expensestype["name"] in ["Intercity"]:
							expensestype["amount"] = allowancestructure.intercity
							expensestype["readonly"] = "0"													
						elif expensestype["name"] in ["Mobile"]:
							expensestype["amount"] = allowancestructure.mobile_bill_reimbursement_actual_or_upto
							expensestype["readonly"] = "1"	
							#expensestype["hidden"] = "1"
							expensestype["hidden"] = "0"


						if expensestype["hidden"]=="0":
							data.append(expensestype)


		reply["data"]=data

		return reply
	except Exception as e:
		frappe.local.response['http_status_code'] = 500
		reply["status_code"]="500"
		errotext="{} param: {} /n error: {}".format(str(frappe.session.user),str(e))
		# appErrorLogGloble("Expenses - expenses_list",errotext)
		# appErrorLogGloble("Expenses - expenses_list",traceback.format_exc())
		reply["error"]=errotext
		reply["message"]=str(e)
		reply["error1"]=traceback.format_exc()
		return reply
	
@frappe.whitelist(allow_guest=True)
def expenses_list(**kwargs):

	parameters=frappe._dict(kwargs)

	reply={}
	reply["message"]="list found."
	reply["status_code"]="200"
	reply["data"]=[]

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
		reply["status_code"]="500"
		# errotext="{} param: {} /n error: {}".format(str(frappe.session.user),str(e))
		# appErrorLogGloble("Expenses - expenses_list",errotext)
		# appErrorLogGloble("Expenses - expenses_list",traceback.format_exc())
		# reply["error"]=errotext
		reply["message"]=str(e)
		reply["error1"]=traceback.format_exc()
		return reply

@frappe.whitelist(allow_guest=True)
def expenses_delete_child(**kwargs):

	parameters=frappe._dict(kwargs)

	expenseChildList = frappe.get_all('Expense Claim Detail', filters=[["Expense Claim Detail","name","=",str(parameters['recordname'])]], fields=['*'])
	if len(expenseChildList)!=0:
		expenseList = frappe.get_all('Expense Claim Detail', filters=[["Expense Claim Detail","parent","=",str(expenseChildList[0]["parent"])]], fields=['*'])
		if len(expenseList)==1:
			if str(expenseChildList[0]["expense_type"]) in ["Mobile"]:
				reply={}
				frappe.local.response['http_status_code'] = 500
				reply["status_code"]="500"
				reply["message"]="You are not allow to delete this expense."
				return reply
			else:
				removeOrderquery = """DELETE  FROM `tabExpense Claim` WHERE  name='"""+str(expenseChildList[0]["parent"])+"""'"""
				frappe.db.sql(removeOrderquery)
		else:
			if str(expenseChildList[0]["expense_type"]) in ["Mobile"]:
				reply={}
				frappe.local.response['http_status_code'] = 500
				reply["status_code"]="500"
				reply["message"]="You are not allow to delete this expense."
				reply["error1"]=traceback.format_exc()
				return reply
			else:
				removeOrderquery = """DELETE  FROM `tabExpense Claim Detail` WHERE  name='"""+str(parameters['recordname'])+"""'"""
				frappe.db.sql(removeOrderquery)

		frappe.db.commit()
	
	return expenses_list(month=parameters['month'],year=parameters['year'],employee=parameters['employee'])

@frappe.whitelist(allow_guest=True)
def expenses_add(**kwargs):

	parameters=frappe._dict(kwargs)

	#month,year,employee,expense_date,expensetype,expensediscription,expenseamount

	reply={}
	reply["message"]="list found."
	reply["status_code"]="200"
	reply["data"]=[]
	try:

		expenseList = frappe.get_all('Expense Claim', filters=[["Expense Claim","month","=",parameters['month']],
													["Expense Claim","year","=",parameters['year']],
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
			})

			d = frappe.get_doc({
				"doctype": "Expense Claim",
				"year":str(parameters['year']),
				"month":str(parameters['month']),
				"employee":str(parameters['employee']),
				"expense_approver":expenseaprrove.expense_approver,
				"expenses":childexpenses
#				"payable_account":"Provision for Salary - BSPL"
			})
			if d.insert(ignore_permissions=True):
				reply = expenses_list(parameters['month'],parameters['year'],parameters['employee'])
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
		reply["status_code"]="500"
		# errotext="param: {} /n error: {}".format(str(employee),str(e))
		# appErrorLogGloble("Expenses - expenses_add",errotext)
		# appErrorLogGloble("Expenses - expenses_add",traceback.format_exc())
		# reply["error"]=errotext
		reply["message"]=str(e)
		reply["error1"]=traceback.format_exc()
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