from flask import Flask, Response, render_template, request
from time import time
import flask_cors, json

PORT = 8001
HOST = "0.0.0.0"
www = Flask(__name__)
flask_cors.CORS(www)


db = { # :)
	"1": {"id": "1", "ubicacion":"1","tiempo":None,   "nombre":"Rafael<br/>(empleado#1)"},
	"2": {"id": "2", "ubicacion":"2","tiempo":None,  "nombre":"Josafat<br/>(empleado#2)"},
	"3": {"id": "3", "ubicacion":"3","tiempo":None,  "nombre":"Ignacio<br/>(empleado#3)"},
	"4": {"id": "4", "ubicacion":"4","tiempo":None, "nombre":"Carolina<br/>(empleado#4)"},
	"5": {"id": "5", "ubicacion":"5","tiempo":None, "nombre":"Samantha<br/>(empleado#5)"},
	"6": {"id": "6", "ubicacion":"6","tiempo":None,   "nombre":"Amelia<br/>(empleado#6)"},
	"7": {"id": "7", "ubicacion":"1","tiempo":None,"nombre":"El Bogueto<br/>(empleado#7)"}, # :)))
	"8": {"id": "8", "ubicacion":"2","tiempo":None,   "nombre":"Mostaza<br/>(prod#345f)"},
	"9": {"id": "9", "ubicacion":"3","tiempo":None,    "nombre":"Catsun<br/>(prod#7436)"},
	"10":{"id":"10", "ubicacion":"4","tiempo":None,    "nombre":"Plato<br/>(prod#84a23)"},
	"11":{"id":"11", "ubicacion":"5","tiempo":None, "nombre":"Producto<br/>(prod#73c12)"},
	"12":{"id":"12", "ubicacion":"6","tiempo":None, "nombre":"Producto<br/>(prod#7b2b7)"},
	"13":{"id":"13", "ubicacion":"1","tiempo":None, "nombre":"Producto<br/>(prod#c35cf)"},
	"14":{"id":"14", "ubicacion":"2","tiempo":None, "nombre":"Producto<br/>(prod#a12de)"}
}

def init():
	for k in db.keys(): db[k]["tiempo"] = time()

def actualizar(t):
	tt = time()-t
	for k in db.keys():
		if db[k]["tiempo"] >= tt:
			yield "event: update\ndata: "+json.dumps(db[k]) + "\n\n"
	return "data: --skip--\n\n"

@www.route("/edit", methods=["GET", "POST"])
def www_edit():
	# [item seleccionado, pos] ()-> mover a [N,S,E,O,sal,entr]
	if request.method == 'POST':
		obj=request.form.get('obj')
		pos=request.form.get('pos')
		if obj and pos:
			db[obj]["ubicacion"] = pos
			db[obj]["tiempo"] = time()
	tmp = []
	for k in db.keys(): tmp.append(db[k])

	return render_template("index.html", edit=1, data=tmp, objetos=[valor for valor in db.values()])

@www.route("/")
def www_index():
	return render_template("index.html", edit=0)

@www.route('/eventos')
def www_event():
	return Response(actualizar(7), mimetype='text/event-stream')

init()
www.run(host=HOST, port=PORT, debug=False, use_reloader=False)