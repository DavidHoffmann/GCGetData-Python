GCGetData
=========

Tool zur Erstellung von GPX Dateien mit deren Hilfe das Geocachen mit Garmin GPS Geräten ermöglicht wird.

Voraussetzung
-------------
Python
Version: 2.7 (wurde für die Entwicklung und den Test verwendet)
Pythonmodul: mechanize

Beispiele
---------

### nearest
python GCGetData.py -u GCUSERNAME -p GCPASSWORT -c 10 52.000000,10.000000 > /tmp/gc-52.000000-10.000000.gpx

Mit dem Parameter -c können die Anzahl der gesuchten caches angegeben werden. Mysteries werden bei der Suche nicht berücksichtigt, da man die Rätsel selten Unterwegs lösen kann.

Die Caches werden im Umkreis der angegeben Koordinaten gesucht. Das Format der Koordinaten entspricht dem Format: "Normal GPS Coordinates (WGS84 Datum) - Decimal".
Die Ausgabe der GPX Datei erfolgt in die Konsole von der das Programm aufgerufen wurde. Es empfiehlt sich daher die Umleitung in eine Datei (hier: "/tmp/gc-52.000000-10.000000.gpx") die anschließend einfach auf das Navigationsgerät kopiert werden kann. 

### mystery
python GCGetData.py -u GCUSERNAME -p GCPASSWORT -m 51.000000,9.000000 52.000000,10.000000 > /tmp/gc-myst-52.000000-10.000000.gpx

Bei der "Mystery-Suche" wird ausschließlich ein einziger cache mit den Koordinaten (hier: "52.000000,10.000000") gesucht. Bei dem gefundenen Cache werden nach dem Download die Koordinaten auf (hier: "51.000000,9.000000") korrigiert. So kann man dann auch die gelösten Rätsel einfach auf dem Navigationsgerät nutzen.

Betriebssysteme
---------------
Das Programm sollte auf allen gängigen Plattformen laufen, auf denen Python lauffähig ist. Getestet habe ich die aktuelle Version nur nur mit Ubuntu Linux 12.04 und dem Garmin Oregon 450t. 
Sollte es zu schwierigkeiten kommen, würde ich mich über eine Rückmeldung bzw. einen Patch freuen.


