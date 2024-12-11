import threading
import statistics as stat
from datetime import datetime
import RPi.GPIO as gpio
from pirc522 import RFID
from tinydb import TinyDB, Query
from flask import Flask, Response, send_from_directory
import flask_cors
import json
from time import time, localtime, strftime


### configuracion, inicializacion ###
gpio.setmode(gpio.BOARD)  #para referirnos a los pines por su numero fisico
rf = RFID(bus=0,device=0, speed=500000) #inicializar la libreria pirc522 con una velocidad de bus de 0.5MHz
rf.antenna_gain = 0x04     #ganancia de las antenas de los modulos, 33dB
db = TinyDB("base_datos.json") #inicializar DB
dato = Query() #querys a la db
www = Flask(__name__) #objeto servidor http
flask_cors.CORS(www) #CORS


### globales ###
HOST = "0.0.0.0" #bindear en todas las interfaces
PORT = 8001
BNK_PINS = [3,5] #pines para controlar los CD4066
IRQ_PINS = [40, 38, 36, 37, 35, 33] #pines IRQ de de cada modulo
MAPA     = {40:[1, "ENTRADA"], 38:[2, "SALIDA"], 36:[3, "AL NORTE"],\
	    35:[4, "AL SUR"] , 37:[5, "AL ESTE"],33:[6, "AL OESTE"]}
# PIN   No. MODULO   PROPOSITO
# 40       1        entrada mesa
# 38       2        salida mesa
# 36       3        al NORTE
# 35       4        al SUR
# 37       5        al ESTE
# 33       6        al OESTE
DBG = False # debug con print :)


#objeto para procesar el debouncing de los pines IRQ
class irq_debounce_obj:
	M = 10
	muestrear = False
	conteo = 0
	arr = [-1]*M #guardar pines detectados
	def ready(self):
		if self.conteo>self.M:
			self.conteo = 0
			return True
		return False
	def __init__(self):
		if DBG: print("debounce init")
	def agg(self, val): #agregar pin a la lista y borrar el primero
		if self.muestrear:
			if DBG: print("agg:",val)
			self.arr.pop(0)
			self.arr.append(val)
			self.conteo += 1
	def get_debounced(self): #obtener pin mas activado
		if -1 in self.arr:
			tmp = [x for x in self.arr if -1 not in x]
			return mode(tmp)
		return stat.mode(self.arr)
	def reset(self):
		self.arr = [-1]*self.M


class demux_obj: #controlador demultiplexor
	ff = 0
	def __init__(self):
		if DBG: print("demux init")
	def strobe(self):
		#desahabilitar todos
		for pin in BNK_PINS:
			gpio.output(pin, False)
		#habilitar el pin correspondiente
		gpio.output(BNK_PINS[self.ff], True)
	def switch_bank(self):
		if self.ff:
			self.ff = 0
		else:
			self.ff = 1
		self.strobe()


# inicializar debouncer para los pines IRQ
debounce = irq_debounce_obj()
demuxer    = demux_obj()


#Conversion del ID de list a string hex
def tag_id_str(uid):
	uid_str = ""
	for b in uid:
		uid_str+=format(b,"x")
	if DBG: print("UID:",uid_str)
	return uid_str


# liberar pines
def gpio_cleanup():
	gpio.cleanup()


#configurar como usaremos los pines del GPIO
def setup_pins():
	for pin in IRQ_PINS:
		gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP) # Modo lectura con pull up
		gpio.add_event_detect(pin, gpio.FALLING, callback=debounce.agg) # interrupt activo bajo en cada pin
	for pin in BNK_PINS:
		gpio.setup(pin, gpio.OUT) #Modo salida


#################### HTTP #########################
def actualizar(t):
	info = db.search(dato.tiempo > time()-t) #buscar todos los cambios de hace t seg
	if info: #si hay resultados...
		#yield "data: --INFORMACION--\n\n"
		tmp = ""
		for entry in info:
			tmp = "event: update\ndata: "+json.dumps(entry) + "\n\n"
			yield tmp #...enviarlos
	else:
		yield "data: --skip--\n\n"
	#yield "data: --fin--\n\n"

@www.route("/")
def www_index():
	#enviar index.html
	return send_from_directory("html", "index.html")

@www.route('/eventos')
def www_event():
	#responder eventos del navegador
	return Response(actualizar(15), mimetype='text/event-stream')

www_thread = threading.Thread(target=lambda: www.run(host=HOST, port=PORT, debug=DBG, use_reloader=DBG))
www_thread.daemon = True
############################################

setup_pins()
try:
	www_thread.start() #iniciar servidor http
	while(1): #loop para detectar lecturas
		debounce.reset()
		debounce.muestrear = True
		while(not debounce.ready()):
			demuxer.switch_bank() #intercambiar entre bancos RDID
			rf.wait_for_tag(timeout=0.1)
		debounce.muestrear = False
		(e, t) = rf.request() #iniciar comunicacion con RFID
		if not e:
			(e, uid) = rf.anticoll() #intentar obetner ID
			if not e:
				tiempo = localtime()
				uid__ = tag_id_str(uid)
				dbnc = debounce.get_debounced()
				print(strftime("%H:%M:%S", tiempo),uid__, dbnc)
				db.update({"ubicacion": MAPA[dbnc][0], "tiempo":int(time())}, dato.id == uid__) #actualizar DB

except KeyboardInterrupt:
	db.close() #guardar db
	gpio_cleanup() #liberar pines
	if DBG: print("bye")
