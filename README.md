# cambiare-gtq
Exchange rate connector for ERPNext based on Guatemalan Central Bank Exchange rates
Conector para tipo de cambio en ERPNext, basado en las tasas de cambio del Banco de Guatemala
#Alpha software version
This software is currently being developed. No connection exists yet with ERPNext.
The python scripts are simply aiming to structure the data to connect to the Guatemalan Central Bank's
web service.
Connection to ERPNext methods and software will follow, at which point these lines for Alpha
will be removed.
Feel free to test the python script!

May 19, 2018: Python script can conenct to web service at http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx
It can pull data directly in XML format.

Pending:
1. Parse XML into usable data chunks
2. Establish a means of connecting to ERPNext
	2.1  Configuration page or app will be necessary
		A button to manually sync latest data
		Setting to MANUAL sync, or PERIODIC sync.: Daily:  Frequency (max of 12x). Start time.   Add rows for specific time sync.
		Weekly: same mechanism, select days. Sync events no more than 84 x per week.
		Data will be stored in specific table.
	2.2  After install, initial configuration is done only once, manually.  Initial configuration will pull all exchange rates for all available currencies
		historically.  Data storage estimate:  ??
3. If data is available on server from initial configuration, it will use this, and not request anything from the server.
4. Parsing data from XML originated chunks and store in database.
5. Update a Currency Exchange entry in ERPNext per day.
6. Timestamp the request and data, keeping a separate record of this. Time stamp will aid when currency exchange rates are important to be measured in seconds.
	6.1 Any invoice entered in foreign currency, with a specific day and time, will obtain the currency exchange rate valid for that time.
	a currency exchange rate is no longer valid from the moment the next currency exchange rate for the same currency appears in the table with a more recent timestamp
	inclusiveness is determined like this: Exchange data 1 timestamp at 07:34:50  Exchange data 2 timestamp at 08:10:23
	Anything after 07:34:50  >= is valid as data 1 rates.  Anything at 8:10:22 >=  but less than 08:10:23 is still data 1 rates
	Anything at 08:10:23 is now data 2.  Process repeats itself for next event.