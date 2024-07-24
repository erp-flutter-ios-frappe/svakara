from __future__ import unicode_literals
import requests
import frappe
from frappe import throw, msgprint, _
import frappe.permissions
from frappe.model.document import Document
import traceback
import string
import random

@frappe.whitelist()
def app_error_log(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":str("User:")+str(title+" "+"App Name:Satvars App"),
			"error":traceback.format_exc()
		})
	d = d.insert(ignore_permissions=True)
	return d	

@frappe.whitelist()
def appErrorLog(title,error):
	d = frappe.get_doc({
			"doctype": "App Error Log",
			"title":str("User:")+str(title+" "+"App Name:Salon App"),
			"error":traceback.format_exc()
		})
	d = d.insert(ignore_permissions=True)
	return d

@frappe.whitelist()
def generateResponse(_type,status=None,message=None,data=None,error=None):
	response= {}
	if _type=="S":
		if status:
			response["status"]=status
		else:
			response["status"]="200"
		response["message"]=message
		response["data"]=data
	else:
		error_log=appErrorLog(frappe.session.user,str(error))
		if status:
			response["status"]=status
		else:
			response["status"]="500"
		if message:
			response["message"]=message
		else:
			response["message"]="Something Went Wrong"		
		response["message"]=message
		response["data"]=None
	return response


@frappe.whitelist(allow_guest=True)
def sendSMS(numbers, message):
	
	url = 'https://api.textlocal.in/send/?apikey=ApTmLrwRf9o-0dKuZ53ejDCziNDYNgxJLyJrS3lUmC&numbers='+str(numbers)+'&sender=SATVRS&message='+str(message)
	payload={}
	headers = {'Cookie': 'PHPSESSID=nu28bmlnel7k5ss8ctchib58n6'}
	response = requests.request("POST", url, headers=headers, data=payload)
	return response


@frappe.whitelist(allow_guest=True)
def sendSMSOld(numbers, message):
	import urllib.request
	import urllib.parse

	data =  urllib.parse.urlencode({'apikey': 'ApTmLrwRf9o-0dKuZ53ejDCziNDYNgxJLyJrS3lUmC', 'numbers': '91'+str(numbers), 'message' : str(message), 'sender': 'SATVRS'})
	data = data.encode('utf-8')
	request = urllib.request.Request("https://api.textlocal.in/send/?")
	f = urllib.request.urlopen(request, data)
	fr = f.read()
	return(fr)


	#data =  urllib.urlencode({'username': 'satvaras2020@gmail.com','apikey': 'ApTmLrwRf9o-0dKuZ53ejDCziNDYNgxJLyJrS3lUmC', 'numbers': '91'+str(numbers), 'message' : str(message),'sender': 'SATVRS'})
	#data = data.encode('utf-8')
	#request = urllib2.Request("https://api.textlocal.in/send/")
	#f = urllib2.urlopen(request, data)
	#fr = f.read()
	#return(fr)


@frappe.whitelist(allow_guest=True)
def sendSMS1(numbers, message):
	import urllib
	import urllib2

	data =  urllib.urlencode({'user': 'SATVRS','key': 'b7150d1054XX', 'mobile': '91'+str(numbers), 'message' : str(message),'senderid': 'SATVRS','accusage': 1})
	data = data.encode('utf-8')
	request = urllib2.Request("http://sms.way2send.in/submitsms.jsp")
	f = urllib2.urlopen(request, data)
	fr = f.read()
	return(fr)

@frappe.whitelist()
def id_generator_otp():
   return ''.join(random.choice('0123456789') for _ in range(6))

@frappe.whitelist(allow_guest=True)
def SendOTP(phoneNo):
	try:
		otpobj=frappe.db.get("UserOTP", {"mobile": phoneNo})
		if otpobj:
			frappe.db.sql("""delete from tabUserOTP where mobile='"""+phoneNo+"""'""")

		OTPCODE=id_generator_otp()

		if phoneNo=="1234567890":
			OTPCODE = "123456"

		doc= {"code":OTPCODE,"message":"SMS Sent Successfully","status":200,"phone":phoneNo}
		mess=str(OTPCODE)+" is your OTP for Satvaras App verification code"

		respon = sendSMS(phoneNo,mess)		
		userOTP = frappe.get_doc({
			"doctype":"UserOTP",
			"name":phoneNo,
			"mobile":phoneNo,
			"otp":OTPCODE
		})
		userOTP.flags.ignore_permissions = True
		userOTP.insert()
		return doc
	except Exception as e:
		docex= {"code":OTPCODE,"message":"SMS Not Sent","status":500,"phone":phoneNo}
		return docex
