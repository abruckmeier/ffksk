from decimal import Decimal

from kiosk.queries import readFromDatabase
from django.utils import timezone
from kiosk.models import Kontostand

from jchart import Chart
from jchart.config import Axes, DataSet, rgba



class Chart_Un_Bezahlt(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):
		data = readFromDatabase('getUmsatzUnBezahlt',[str(timezone.now()),str(timezone.now()),str(timezone.now())])
		for item in data:
			if item['what'] == 'bezahlt': bezahlt = item['preis']
			if item['what'] == 'Dieb': dieb = item['preis']
		data = [bezahlt, dieb]

		return [DataSet(
			data = data,
			backgroundColor = [rgba(0,255,0,0.2), rgba(255,0,0,0.2)]
		)]

	def get_labels(self, **kwargs):
		return( ['bezahlter Warenwert in &#8364;', 'unbezahlter Warenwert in &#8364;'] )


class Chart_UmsatzHistorie(Chart):
	chart_type = 'line'
	responsive = True
	scales = {
		'xAxes': [Axes(type='time', position='bottom')],
		'yAxes': [{'ticks':{'beginAtZero': True}, 'scaleLabel':{'display': True, 'labelString': 'Anteiliger Geldwert in %'}}]
	}

	def get_datasets(self, **kwargs):
		umsatzHistorie = readFromDatabase('getUmsatzHistorie')
		data = []
		for item in umsatzHistorie:
			data.append(round(item['dieb'] / item['allesumsatz']*100,1))
		
		return [DataSet(
			data = data,
			label = 'unbezahlter Geldwert (Entwicklung)',
			backgroundColor = [rgba(0,0,255,0.2)]
		)]

	def get_labels(self, **kwargs):
		umsatzHistorie = readFromDatabase('getUmsatzHistorie')
		data = []
		for item in umsatzHistorie:
			data.append(item['datum'])

		return( data )


class Chart_WeeklyVkValue(Chart):
	chart_type = 'bar'
	responsive = True
	scales = {
		'xAxes': [Axes(type='time', position='bottom')],
		'yAxes': [{'ticks':{'beginAtZero': True}, 'scaleLabel':{'display': True, 'labelString': 'Geldwert in Euro'}}]
	}

	def get_datasets(self, **kwargs):
		weeklyVKValue = readFromDatabase('getWeeklyVKValue')
		data = []
		for item in weeklyVKValue:
			data.append(item['weekly_value'])
		
		return [DataSet(
			data = data,
			label = 'woechentlicher Umsatz im FfE-Kiosk',
			#backgroundColor = [rgba(65,143,190,0.5)]
		)]

	def get_labels(self, **kwargs):
		weeklyVKValue = readFromDatabase('getWeeklyVKValue')
		data = []
		for item in weeklyVKValue:
			data.append(item['week_start'])

		return( data )


class Chart_MonthlyVkValue(Chart):
	chart_type = 'bar'
	responsive = True
	scales = {
		'xAxes': [Axes(type='time', position='bottom')],
		'yAxes': [{'ticks':{'beginAtZero': True}, 'scaleLabel':{'display': True, 'labelString': 'Geldwert in Euro'}}]
	}

	def get_datasets(self, **kwargs):
		monthlyVKValue = readFromDatabase('getMonthlyVKValue')
		data = []
		for item in monthlyVKValue:
			data.append(item['monthly_value'])
		
		return [DataSet(
			data = data,
			label = 'monatlicher Umsatz im FfE-Kiosk',
			#backgroundColor = [rgba(65,143,190,0.5)]
		)]

	def get_labels(self, **kwargs):
		monthlyVKValue = readFromDatabase('getMonthlyVKValue')
		data = []
		for item in monthlyVKValue:
			data.append(item['month_start'])

		return( data )


class Chart_DaylyVkValue(Chart):
	chart_type = 'line'
	responsive = True
	scales = {
		'xAxes': [Axes(type='time', position='bottom')],
		'yAxes': [{'ticks':{'beginAtZero': True}, 'scaleLabel':{'display': True, 'labelString': 'Geldwert in Euro'}}]
	}

	def get_datasets(self, **kwargs):
		daylyVKValue = readFromDatabase('getDaylyVKValue')
		data = []
		for item in daylyVKValue:
			data.append(item['dayly_value'])
		
		return [DataSet(
			data = data,
			label = 'taeglicher Umsatz im FfE-Kiosk',
			backgroundColor = [rgba(65,143,190,0.5)]
		)]

	def get_labels(self, **kwargs):
		daylyVKValue = readFromDatabase('getDaylyVKValue')
		data = []
		for item in daylyVKValue:
			data.append(item['datum'])

		return( data )


class Chart_Profits(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):

		vkValueKiosk = readFromDatabase('getKioskValue')
		vkValueKiosk = vkValueKiosk[0]['value']
		vkValueAll = readFromDatabase('getVkValueAll')
		vkValueAll = vkValueAll[0]['value']
		ekValueAll = readFromDatabase('getEkValueAll')
		ekValueAll = ekValueAll[0]['value']
		kioskBankValue = Kontostand.objects.get(nutzer__username='Bank')
		kioskBankValue = Decimal(kioskBankValue.stand / 100)

		gespendet = Kontostand.objects.get(nutzer__username='Gespendet')
		gespendet = Decimal(gespendet.stand / 100)

		# Bargeld "gestohlen"
		bargeld_Dieb = Kontostand.objects.get(nutzer__username='Bargeld_Dieb')
		bargeld_Dieb = Decimal(- bargeld_Dieb.stand / 100)

		theoAlloverProfit = vkValueAll - ekValueAll
		theoProfit = vkValueKiosk + kioskBankValue
		buyersProvision = round(theoAlloverProfit - theoProfit - gespendet,2)
		adminsProvision = 0
		profitHandback = 0
		datum = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
		unBezahlt = readFromDatabase('getUmsatzUnBezahlt',[datum, datum, datum])
		stolenValue = Decimal(0)
		for item in unBezahlt:
			if item['what'] == 'Dieb' and item['preis']: stolenValue = item['preis']
		expProfit = round(theoProfit - stolenValue - bargeld_Dieb - adminsProvision - profitHandback,2)

		data = [buyersProvision, adminsProvision, profitHandback, stolenValue, expProfit, gespendet]

		return [DataSet(
			data = data,
			backgroundColor = [rgba(0,0,255,0.2), rgba(0,0,255,0.4), rgba(0,0,255,0.6), rgba(0,0,255,0.8), rgba(0,255,0,0.6), rgba(255,255,0,0.5)]
		)]

	def get_labels(self, **kwargs):
		return( ['Provision der Eink'+chr(228)+'ufer in '+chr(8364), 'Provision f'+chr(252)+'r Admin und Verwalter', 
			'Gewinnaussch'+chr(252)+'ttung', 'gestohlener Geldwert','erwarteter Gewinn', 'Gespendet'] )


class Chart_ProductsWin(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):
		products = readFromDatabase('getProductsStatistics')
		data = []
		for item in products:
			data.append(round(item['gewinn'],2))

		return [DataSet(
			data = data,
			backgroundColor = rgba(0,255,0,0.2)
		)]

	def get_labels(self, **kwargs):
		products = readFromDatabase('getProductsStatistics')
		data = []
		for item in products:
			data.append(item['name'])

		return( data )

class Chart_ProductsCount(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):
		products = readFromDatabase('getProductsStatistics')
		data = []
		for item in products:
			data.append(round(item['anzahl']))

		return [DataSet(
			data = data,
			backgroundColor = rgba(0,255,0,0.2)
		)]

	def get_labels(self, **kwargs):
		products = readFromDatabase('getProductsStatistics')
		data = []
		for item in products:
			data.append(item['name'])

		return( data )

class Chart_Stolen_ProductsWin(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):
		products = readFromDatabase('getProductsStolenStatistics')
		data = []
		for item in products:
			data.append(round(item['stolen_vk'],2))

		return [DataSet(
			data = data,
			backgroundColor = rgba(0,255,0,0.2)
		)]

	def get_labels(self, **kwargs):
		products = readFromDatabase('getProductsStolenStatistics')
		data = []
		for item in products:
			data.append(item['name'])

		return( data )

class Chart_StolenProductsShare(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):
		products = readFromDatabase('getProductsStolenStatistics')
		data = []
		for item in products:
			data.append(round(item['rel_stolen'],1))

		return [DataSet(
			data = data,
			backgroundColor = rgba(0,255,0,0.2)
		)]

	def get_labels(self, **kwargs):
		products = readFromDatabase('getProductsStolenStatistics')
		data = []
		for item in products:
			data.append(item['name'])

		return( data )

