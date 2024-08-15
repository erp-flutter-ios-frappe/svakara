import frappe
from frappe import _
from frappe.utils.file_manager import save_file
import calendar
import time

@frappe.whitelist(allow_guest=True)
def uploadimage(doctype, docname, imagename, imagedata, docfield=None):

	imagename = imagename.replace("_", "")
	imagename = imagename.replace(":", "")
	imagename = imagename.replace(";", "")
	imagename = imagename.replace(" ", "")
	imagename = imagename.replace("*", "")
	imagename = imagename.replace("!", "")
	imagename = imagename.replace("@", "")
	imagename = imagename.replace("#", "")
	imagename = imagename.replace("$", "")
	imagename = imagename.replace("%", "")
	imagename = imagename.replace("^", "")
	imagename = imagename.replace("&", "")
	imagename = imagename.replace("(", "")
	imagename = imagename.replace(")", "")
	imagename = imagename.replace("-", "")
	#imagename = imagename.replace("=", "")
	#imagename = imagename.replace("+", "")
	imagename = imagename.replace("`", "")
	imagename = imagename.replace("~", "")
	#imagename = imagename.replace(",", "")
	#imagename = imagename.replace("<", "")
	#imagename = imagename.replace(">", "")
	imagename = imagename.replace("?", "")
	#imagename = imagename.replace("'", "")
	#imagename = imagename.replace("\"", "")
	

	gmt = time.gmtime()
	ts = calendar.timegm(gmt)
	timstamp = str(str(ts).split(".")[0])


	tempName=str(doctype)+str(docname)+"_"+timstamp+"_"+str(imagename)

	uploadResponse = save_file(fname=tempName,content=imagedata,dt=doctype,dn=docname,df=docfield,decode=True,is_private=0)

	
	if docfield!=None:
		frappe.db.set_value(doctype, docname, docfield, str(uploadResponse.file_url))
		frappe.db.commit()

	return str(uploadResponse.file_url)
	#return uploadResponse.file_url