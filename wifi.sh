#!/bin/bash

# Configuración
SSID="PROYECTO"
PASSPHRASE="PROYECTO"
INTERFACE="wlan0"

# Verificar privilegios
if [[ $EUID -ne 0 ]]; then
    echo "Por favor, ejecuta este script como root."
    exit 1
fi

echo "Configurando el Access Point..."

# Detener servicios que puedan interferir
echo "Deteniendo servicios que puedan causar conflictos..."
systemctl stop NetworkManager
systemctl stop hostapd dnsmasq

# Configurar la interfaz de red
echo "Configurando la interfaz de red..."
ip link set $INTERFACE down
ip addr flush dev $INTERFACE
ip addr add 192.168.50.1/24 dev $INTERFACE
ip link set $INTERFACE up

# Configurar dnsmasq
echo "Creando configuración para dnsmasq..."
cat <<EOF > /etc/dnsmasq.conf
interface=$INTERFACE
dhcp-range=192.168.50.10,192.168.50.100,12h
EOF

# Configurar hostapd
echo "Creando configuración para hostapd..."
cat <<EOF > /etc/hostapd/hostapd.conf
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=6
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSPHRASE
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

# Iniciar dnsmasq
echo "Iniciando dnsmasq..."
systemctl start dnsmasq

# Iniciar hostapd
echo "Iniciando hostapd..."
hostapd /etc/hostapd/hostapd.conf &

# Mostrar el código QR para la conexión Wi-Fi
echo "Generando código QR para la conexión Wi-Fi..."
if command -v qrencode > /dev/null; then
    WIFI_CONFIG="WIFI:T:WPA;S:${SSID};P:${PASSPHRASE};;"
    qrencode -t ansiutf8 "$WIFI_CONFIG"
else
    echo "qrencode no está instalado. Puedes instalarlo con:"
    echo "sudo pacman -S qrencode"
fi

# Mensaje de éxito
echo "Access Point configurado con SSID: $SSID y Contraseña: $PASSPHRASE"

# Opcional: Instrucciones para volver a habilitar NetworkManager
echo -e "\nRecuerda reactivar NetworkManager cuando termines con:"
echo "sudo systemctl start NetworkManager"
