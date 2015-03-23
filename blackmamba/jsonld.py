import json
import re

import database
import mamba.task
import mamba.util


class annotations(mamba.task.Request):
	
	def entity_dict(self, qtype, qid):
		if qtype >= 0:
			return {"@id" : "stringdb:%d.%s" % (qtype, qid)}
		elif qtype == -1:
			return {"@id" : "stitchdb:%s" % qid}
		elif qtype == -2:
			return {"@id" : "taxonomy:%s" % qid}
		elif qtype <= -21 and qtype >= -24:
			return {"@id" : "%s" % qid}
		elif qtype == -25:
			return {"@id" : "%s" % qid}
		elif qtype == -26:
			return {"@id" : "%s" % qid}
		elif qtype == -27:
			return {"@id" : "%s" % qid}
		else:
			return {"@id" : qid}
	
	def main(self):
		match = re.match("/document/([0-9]+)/annotations(/([0-9]*))?", self.http.path)
		if match and "JSON-LD" in mamba.setup.config().sections:
			document = int(match.group(1))
			annotation = None
			if match.group(3) != None and match.group(3) != "":
				annotation = int(match.group(3))
			settings = mamba.setup.config().sections["JSON-LD"]
			types = [float(i) for i in settings["types"].split(" ")]
			textmining = database.Connect("textmining")
			sql = "SELECT * FROM documents WHERE document=%d;" % document
			records = textmining.query(sql).dictresult()
			used = set()
			if len(records):
				data = {}
				data["@context"] = "http://nlplab.org/ns/restoa-context-20150307.json"
				sql = "SELECT * FROM matches WHERE document=%d;" % document
				records = textmining.query(sql).dictresult()
				data["@id"] = "/document/%d/annotations" % document
				data["@graph"] = []
				index = -1
				prev_start = None
				for record in records:
					if record["type"] in types:
						start = record["start"]
						stop = record["stop"]+1
						qtype = int(record["type"])
						qid = record["id"]
						if start != prev_start:
							index += 1
							data["@graph"].append({})
							data["@graph"][index]["@id"] = "/document/%d/annotations/%d" % (document, index)
							data["@graph"][index]["target"] = "/document/%d#char=%d,%d" % (document, start, stop)
							data["@graph"][index]["body"] = self.entity_dict(qtype, qid)
							prev_start = start
							used = set()
						elif qtype >= -1 or qtype not in used:
							if type(data["@graph"][index]["body"]) is dict:
								data["@graph"][index]["body"] = [data["@graph"][index]["body"]]
							data["@graph"][index]["body"].append(self.entity_dict(qtype, qid))
						used.add(qtype)
				if annotation == None:
					mamba.http.HTTPResponse(self, json.dumps(data, separators=(',',':'), sort_keys=True), "application/ld+json").send()
				elif annotation < len(data["@graph"]):
					data["@id"] = data["@graph"][annotation]["@id"]
					data["target"] = data["@graph"][annotation]["target"]
					data["body"] = data["@graph"][annotation]["body"]
					del data["@graph"]
					mamba.http.HTTPResponse(self, json.dumps(data, separators=(',',':'), sort_keys=True), "application/ld+json").send()
				else:
					mamba.http.HTTPErrorResponse(self, 404, "Not Found").send()
			else:
				mamba.http.HTTPErrorResponse(self, 404, "Not Found").send()
		else:
			mamba.http.HTTPErrorResponse(self, 400, "Bad Request").send()


class document(mamba.task.Request):
	
	def main(self):
		match = re.match("/document/([0-9]+)", self.http.path)
		if match == None:
			mamba.http.HTTPErrorResponse(self, 400, "Bad Request").send()
		else:
			document = int(match.group(1))
			textmining = database.Connect("textmining")
			sql = "SELECT * FROM documents WHERE document=%d;" % document
			records = textmining.query(sql).dictresult()
			if len(records):
				text = "\n".join(mamba.util.string_to_bytes(records[0]["text"]).split("\t"))
				mamba.http.HTTPResponse(self, text, "text/plain").send()
			else:
				mamba.http.HTTPErrorResponse(self, 404, "Not Found").send()