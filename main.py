import statistics as stat
from datetime import datetime
import RPi.GPIO as gpio
from pirc522 import RFID
from time import localtime, strftime

### globales ###
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
	def ready(self): #regresar True si hubo suficientes detecciones
		if self.conteo>self.M:
			self.conteo = 0
			return True
		return False
	def __init__(self):
		if DBG: print("obj init")
	def agg(self, val): #agregar pin a la lista y borrar el primero
		if self.muestrear:
			if DBG: print("agg:",val)
			self.arr.pop(0)
			self.arr.append(val)
			self.conteo += 1
	def get_debounced(self): # regresar el pin con mas detecciones
		if -1 in self.arr:
			tmp = [x for x in self.arr if -1 not in x]
			return mode(tmp)
		return stat.mode(self.arr)
	def reset(self): #reiniciar array
		self.arr = [-1]*self.M


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


### solo para referencia
#def test(rf, gpio):
#	print("--test")
#	(err, tpe) = rf.request()
#	print("a")
#	if not err:
#		print("detectado " + format(tpe,"02x") + str(type(tpe)) )
#		print("b")
#		(err, uid) = rf.anticoll()
#		if not err:
#			print(str(uid) + str(type(uid)))
#			if not rf.select_tag(uid):
#				############
#				if not rf.card_auth(rf.auth_a,10,[0xFF,0xFF,0xFF,0xFF,0xFF,0xFF], uid):
#					data = rf.read(10)
#					print("leyendo block 10: "+str(data) +str(type(data)))
#					rf.stop_crypto()
#	gpio.cleanup()



### configuracion, inicializacion ###
gpio.setmode(gpio.BOARD)  #para referirnos a los pines por su numero fisico
setup_pins()
rf = RFID(bus=0,device=0) #inicializar la libreria pirc522
#rf2 = RFID(bus=1,device=0)
rf.antenna_gain = 0x4     #ganancia de las antenas de los modulos, 33dB
debounce = irq_debounce_obj() # inicializar debouncer para los pines IRQ
try:
	while(1): #loop para detectar lecturas
		debounce.reset()
		debounce.muestrear = True
		while(not debounce.ready()):
			rf.wait_for_tag(timeout=0.15)
		debounce.muestrear = False
		(e, t) = rf.request() #iniciar comunicacion con RFID
		if not e:
			(e, uid) = rf.anticoll() #intentar obetner ID
			if not e:
				tiempo = localtime()
				print(strftime("%H:%M:%S", tiempo),tag_id_str(uid), debounce.get_debounced())
except KeyboardInterrupt:
	if DBG: print("bye")
	gpio_cleanup() #liberar pines
