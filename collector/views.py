# Date : 2017.01.02 ~
# Author : Jun Yeon

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from configparser import RawConfigParser
from . import protocol as STATE#protocol값 STATE로 import
from collector.models import *
from django.db.models import Max
# from chartit import DataPool, Chart

from plotly.offline import plot
import plotly.graph_objs as go
from plotly.graph_objs import Scatter

import json
import time
import ast
import datetime
import random

import matplotlib
import matplotlib.pyplot as plt

from django.views.decorators.clickjacking import xframe_options_sameorigin


# This web server only manages the device's status, data.
# Not handle the device's state, only bypass the commands.

# for setting the config
def initConfig():
	setConfig(STATE.PARAM_STATE, STATE.STATE_INITIALIZNG)
	setConfig(STATE.PARAM_COMMAND, '')
	setConfig(STATE.PARAM_CHIPINFO, '')
	setConfig(STATE.PARAM_CHANNEL, '')
	setConfig(STATE.PARAM_FREQ, '')
	setConfig(STATE.PARAM_DEADLINE, '')
	setConfig(STATE.PARAM_PERIOD, '')
	setConfig(STATE.PARAM_RESULT, '')
	setConfig(STATE.PARAM_ERROR, '')
	setConfig(STATE.PARAM_RECORD_STATE, '')
	setConfig(STATE.PARAM_COUNTER, '')
	setConfig(STATE.PARAM_START_TIME, '')

# if some_queryset.filter(pk=entry.pk).exists():
def setConfig(key, value):#설정값 만들거나 
	queryResult = Parameter.objects.filter(key=key)#filter() return QuerySet
	if queryResult.exists():
		queryResult.update(value=value)
	else:
		Parameter(key=key, value=value).save()

def getConfig(key):
	queryResult = Parameter.objects.filter(key=key)
	if queryResult.exists():
		return queryResult.get(key=key).value
	else:
		return ''

# Do not check csrf cookies for POST messages
# This function only uses collecting the data. 데이터 모으는 함수
@csrf_exempt
def collector(request):#
	result = {}
	print('Collector called')

	if request.method == 'POST':
		jsonData = json.loads(request.body)#사용자 요청을 json형식으로 로드
		print("---------------jsonData------------------------")
		print(jsonData)
		print("***********************************************")
		menu = jsonData['menu']

		if menu == 'result':
			print("__result__")
			dataCounter = jsonData['dataCounter']
			startTime = jsonData['startTime']
			targetTime = jsonData['targetTime']
			period = jsonData['period']
			freqs = jsonData['freqs']
			channels = jsonData['channels']
			dbData = DwfResultData(dataCounter=dataCounter, startTime = startTime,
				targetTime=targetTime, period=period, freqs=freqs, channels=channels)#DwfResultData 모델로 변환후 저장
			dbData.save()
			result['result'] = True
		elif menu == 'scope':
			print("__scope__")
			dataCounter = jsonData['dataCounter']
			time = jsonData['time']
			timeMin = jsonData['timeMin']
			Z = jsonData['Z']
			R = jsonData['R']
			C = jsonData['C']
			freq = jsonData['freq']
			channel = jsonData['channel']
			for idx in range(len(channel)):
				dbData = DwfMeasureData(dataCounter=dataCounter, time=time, timeMin=timeMin,
					Z=Z[idx], R=R[idx], C=C[idx], freq=freq[idx], channel=channel[idx])
				dbData.save()

			result['result'] = True
		else:
			result['result'] = False

		#for i, (d0, d1, d2) in enumerate(zip(jsonData['freq'], jsonData['gain'], jsonData['phase'])):
		#	data = DwfData(time=time, freq=d0, gain=d1, phase=d2)
		#	data.save()

		# currently alway return to true


	return HttpResponse(json.dumps(result), content_type='application/json')

# This function get/set the parameters.
# The parameter arranged in protocol.py file.
@csrf_exempt
def state(request):
	result = {}

	if request.method == 'POST':
		jsonData = json.loads(request.body)
		menu = jsonData['menu']
		key = jsonData['key']

		if menu == 0: # set menu
			value = jsonData['value']
			result['result'] = True
			setConfig(key, value)
		elif menu == 1: # get menu
			result['result'] = True
			result['value'] = getConfig(key)
	else:
		result['result'] = False
		result['error'] = 'not supported protocol(only POST)'

	return HttpResponse(json.dumps(result), content_type='application/json')

@csrf_exempt
def init(request):
	if(request.method == 'POST'):
		# initConfig function always succeed.
		initConfig()

		return HttpResponse('{"result":true}')
	else:
		return HttpResponse('{"result":false}')

@csrf_exempt
def command(request):#서버 콘솔창
	if(request.method == 'POST'):
		result = {}
		print(request.body)
		jsonData = json.loads(request.body)
		print('\n')
		print(jsonData)
		command = jsonData['command']

		# waiting 10 sec maximum
		timeout = 50
		counter = 0

		# Make sure the setup command, must be not called in progress.
		if(command == STATE.COMMAND_CHECKCHIP):#setup/control view 메뉴에서 check chip 버튼 눌렀을떄
			# Clear previous chipinfo
			setConfig(STATE.PARAM_CHIPINFO, '')
			setConfig(STATE.PARAM_RESULT, '')

			# setting the parameter with setup
			setConfig(STATE.PARAM_COMMAND, STATE.COMMAND_CHECKCHIP)

			# waiting the parameter changed.
			while(True):
				time.sleep(0.2)

				res = getConfig(STATE.PARAM_RESULT)

				if(res == 'OK'):
					chipInfo = getConfig(STATE.PARAM_CHIPINFO)

					result['result'] = True
					result['value'] = chipInfo
					break
				elif(res == 'FAILED'):
					result['result'] = False
					result['error'] = getConfig(STATE.PARAM_ERROR)
					break

				counter = counter + 1
				if(counter == timeout):
					result['result'] = False
					result['error'] = "No device connected"
					break

			# reset the result
			setConfig(STATE.PARAM_RESULT, '')
		elif(command == STATE.COMMAND_SETUP):#setup/control view 메뉴에서 setup 버튼 눌렀을떄
			freqs = jsonData['freqs']
			period = jsonData['period']
			deadline = jsonData['deadline']
			channels = jsonData['channels']
			counter = 1

			tempCounter = DwfResultData.objects.all().aggregate(Max('dataCounter'))
			if(tempCounter['dataCounter__max'] == None):
				tempCounter = 1
			else:
				counter = int(tempCounter['dataCounter__max']) + 1

			setConfig(STATE.PARAM_RESULT, '')
			setConfig(STATE.PARAM_FREQ, freqs)
			setConfig(STATE.PARAM_PERIOD, period)
			setConfig(STATE.PARAM_DEADLINE, deadline)
			setConfig(STATE.PARAM_CHANNEL, channels)
			setConfig(STATE.PARAM_COUNTER, counter)

			setConfig(STATE.PARAM_COMMAND, STATE.COMMAND_SETUP)

			# waiting the parameter changed.
			while(True):
				time.sleep(0.2)

				res = getConfig(STATE.PARAM_RESULT)
				if(res == 'OK'):
					result['result'] = True
					break
				elif(res == 'FAILED'):
					result['result'] = False
					result['error'] = getConfig(STATE.PARAM_ERROR)
					break

				counter = counter + 1
				if(counter == timeout):
					result['result'] = False
					result['error'] = "No device connected"
					break
		elif(command == STATE.COMMAND_START):
			setConfig(STATE.PARAM_RESULT, '')
			setConfig(STATE.PARAM_COMMAND, STATE.COMMAND_START)

			print('command start received')
			# change the timeout to 20 secs
			timeout = 50*2

			# waiting the parameter changed.
			while(True):
				time.sleep(0.2)

				res = getConfig(STATE.PARAM_RESULT)
				if(res == 'OK'):
					result['result'] = True
					break
				elif(res == 'FAILED'):
					result['result'] = False
					result['error'] = getConfig(STATE.PARAM_ERROR)
					break

				counter = counter + 1
				if(counter == timeout):
					result['result'] = False
					result['error'] = "Timeout"
					break
		elif(command == STATE.COMMAND_STOP):
			setConfig(STATE.PARAM_RESULT, '')
			setConfig(STATE.PARAM_COMMAND, STATE.COMMAND_STOP)

			print('command stop received')

			timeout = 50*2

			# waiting the parameter changed.
			while(True):
				time.sleep(0.2)

				res = getConfig(STATE.PARAM_RESULT)
				if(res == 'OK'):
					initConfig()
					result['result'] = True
					break
				elif(res == 'FAILED'):
					result['result'] = False
					result['error'] = getConfig(STATE.PARAM_ERROR)
					break

				counter = counter + 1
				if(counter == timeout):
					result['result'] = False
					result['error'] = "Timeout"
					break
		elif(command == STATE.COMMAND_CHECKSTATE):
			timeFormat = '%Y-%m-%d %H:%M:%S'

			channel = getConfig(STATE.PARAM_CHANNEL)
			freq = getConfig(STATE.PARAM_FREQ)

			# change the list type
			if(channel != ""):
				channel = ast.literal_eval(channel)
				channel = ", ".join(str(x) for x in channel[:])
			if(freq != ""):
				freq = ast.literal_eval(freq)
				freq = ", ".join(str(x) for x in freq[:])

			result['result'] = True
			result["state"] = getConfig(STATE.PARAM_STATE)
			result["chipInfo"] = getConfig(STATE.PARAM_CHIPINFO)
			result["channel"] = channel
			result["freq"] = freq
			result["deadline"] = getConfig(STATE.PARAM_DEADLINE)
			result["period"] = getConfig(STATE.PARAM_PERIOD)
			result["recordState"] = getConfig(STATE.PARAM_RECORD_STATE)
			result["startTime"] = getConfig(STATE.PARAM_START_TIME)
			if(result["startTime"] != ""):
				endTime = datetime.datetime.strptime(result["startTime"], timeFormat) + datetime.timedelta(days=int(result["deadline"]))
				print(endTime)
				result["endTime"] = endTime.strftime(timeFormat)
		elif(command == STATE.COMMAND_GET_RESULT_LIST):
			datas = DwfResultData.objects.order_by("-dataCounter")[:6]
			result["result"] = True
			result["dataCounter"] = []
			result["timeRange"] = []
			result["period"] = []
			result["freqs"] = []
			result["channels"] = []
			result["state"] = getConfig(STATE.PARAM_STATE)

			for data in datas:
				channels_value = ast.literal_eval(data.channels)
				channels_value = [x+1 for x in channels_value]

				result["dataCounter"].append(data.dataCounter)
				result["timeRange"].append(str(data.startTime) + "~<br>" + str(data.targetTime))
				result["period"].append(data.period)
				result["freqs"].append(data.freqs)
				result["channels"].append(str(channels_value)) # for viewer

			print(result)

		return HttpResponse(json.dumps(result), content_type='application/json')

	else:
		return HttpResponse('{"result":false}')

#https://stackoverflow.com/questions/33267383/how-to-configure-x-frame-options-in-django-to-allow-iframe-embedding-of-one-view
@xframe_options_sameorigin
def graph(request):
	dataCounter = request.GET.get('dataCounter', '')#request.GET.get(key[, default])
	channels = request.GET.get('channels', '')
	freqs = request.GET.get('freqs', '')
	dataSelection = request.GET.get('dataSelection', '')

	print("dataCounter %s, channels %s, freqs %s" % (dataCounter, channels, freqs))

	if dataCounter != '' and channels != '' and freqs != '' and dataSelection != '':
		channels = ast.literal_eval("[" + channels + "]")#문자 그대로 evaluate
		freqs = ast.literal_eval("[" + freqs + "]")
		series = []
		series_options_terms = {}

		dateTime = DwfMeasureData.objects.filter(dataCounter=dataCounter, channel=channels[0], freq=freqs[0]).values("time")

		# print dateTime.get()
		# dateTime.update("")

		scatter_arr = []

		for channel in channels:
			queryData = DwfMeasureData.objects.filter(dataCounter=dataCounter, channel=channel, freq__in=freqs)
			impedences_qs = queryData.values(dataSelection)
			impedences = [qd[dataSelection] for qd in impedences_qs]

			print("--------------impedences----------------------")
			print(impedences)
			time_min_qs = queryData.values('timeMin')
			time_min = [qd['timeMin'] for qd in time_min_qs]

			scatter_arr.append(Scatter(x=time_min, y=impedences,
					mode='lines+markers', name=channel + 1,
					opacity=0.8))

		fig = {
			"data": scatter_arr,
			"layout": go.Layout(title="impedanceGraph", xaxis = go.layout.XAxis(title = "time(min)"), yaxis = go.layout.YAxis(title = dataSelection)),
		}

		plot_div = plot(fig, output_type='div')

		return render(request, "graph.html", context={'plot_div': plot_div})

def error(request):
	return render(request, 'error.html')

def main(request):
	return render(request, 'index.html')