import datetime as dt
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe

#conversion factors
degToCount = 45.5111 
countToDeg = 1/degToCount

streamFreq = 1000
data_log = False  # False means no logs will be saved
shouldAutostream = 1; # This makes the loop run slightly faster
debug_logging_level = 6  # 6 is least verbose, 0 is most verbose

def zeroProcedure(side, port, baud_rate):

	sideMultiplier = 1
	if (side == "left" or side == "l"):
		sideMultiplier = -1
	elif (side == "right" or side == "r"):
		sideMultiplier = 1

	pullCurrent = 1000
	iterations = 0
	holdingCurrent = True
	run_time_total = 1 #seconds
	isMoving = False
	moveVec = np.array([])
	motorAngleVec = np.array([])
	ankleAngleVec = np.array([])
	motorAngleOffset_deg = 0
	ankleAngleOffset_deg = 0
	holdCurrent = pullCurrent * sideMultiplier
	SCALE_FACTOR =  360/16384

	fxs = flex.FlexSEA()
	dev_id = fxs.open(port, baud_rate, debug_logging_level)
	fxs.start_streaming(dev_id, freq=streamFreq, log_en=data_log)
	app_type = fxs.get_app_type(dev_id)
		
	fxs.set_gains(dev_id, 40, 400, 0, 0, 0, 128)
	sleep(0.5)
	startTime = time()
	
	while (holdingCurrent):
		iterations += 1
		currentTime = time()
		timeSec = currentTime - startTime

		fxu.clear_terminal()
		act_pack = fxs.read_device(dev_id)
		
		actCurrent = act_pack.mot_cur
		current_mot_angle = act_pack.mot_ang * countToDeg
		current_ank_angle = act_pack.ank_ang * SCALE_FACTOR

		mot_angle_deg = current_mot_angle
		ank_angle_deg = current_ank_angle

		current_ank_vel = act_pack.ank_vel / 10
		current_mot_vel = act_pack.mot_vel

		desCurrent = holdCurrent

		fxs.send_motor_command(dev_id, fxe.FX_CURRENT, desCurrent)

		print("Ankle Angle: {} deg...".format(current_ank_angle))
		
		if (abs(current_mot_vel)) > 100 or (abs(current_ank_vel) > 1):
			moveVec = np.append(moveVec, True)
		else:
			moveVec = np.append(moveVec, False)

		motorAngleVec = np.append(motorAngleVec, current_mot_angle )
		ankleAngleVec = np.append(ankleAngleVec, current_ank_angle)

		if (timeSec) >= run_time_total:
			if not np.any(moveVec): #if none moved
				motorAngleOffset_deg = np.mean(motorAngleVec)
				ankleAngleOffset_deg = np.mean(ankleAngleVec)
				holdingCurrent = False

			else:
				print("retrying")
				moveVec = np.array([])
				motorAngleVec = np.array([])
				ankleAngleVec = np.array([])
				startTime = time()
				iterations = 0

	#ramp down
	print('Turning off current control...')
	print("Motor Angle offset: {} deg\n".format( (motorAngleOffset_deg) ))
	print("Ankle Angle offset: {} deg\n".format( (ankleAngleOffset_deg) ))
	fxs.send_motor_command(dev_id, fxe.FX_NONE, 0)
	sleep(0.5)

	fxs.close(dev_id)

	return (motorAngleOffset_deg, ankleAngleOffset_deg)

def characterizeCurve(side, port, baud_rate, motorAngleOffset_deg, ankleAngleOffset_deg):

	inProcedure = True
	motorAngleVec = np.array([])
	ankleAngleVec = np.array([])
	interval = 20 #seconds
	iterations = 0
	startTime = time()
	SCALE_FACTOR =  360/16384

	sideMultiplier = 1
	if (side == "left" or side == "l"):
		sideMultiplier = -1
	elif (side == "right" or side == "r"):
		sideMultiplier = 1

	sleep(1)

	pullCurrent = 2000 # magnitude only, not adjusted based on leg side yet
	
	desCurrent = pullCurrent * sideMultiplier

	fxs = flex.FlexSEA()
        
	dev_id = fxs.open(port, baud_rate, debug_logging_level)
	fxs.start_streaming(dev_id, freq=streamFreq, log_en=data_log)
	app_type = fxs.get_app_type(dev_id)
		
	fxs.set_gains(dev_id, 40, 400, 0, 0, 0, 128)
	sleep(0.5)
	dataFile = 'characterizationFunctionData.csv'
	with open(dataFile, "w", newline="\n") as fd:
		writer = csv.writer(fd)
		while(inProcedure):
			iterations += 1
			fxu.clear_terminal()
			act_pack = fxs.read_device(dev_id)
			fxs.send_motor_command(dev_id, fxe.FX_CURRENT, desCurrent)

			current_ank_angle = act_pack.ank_ang * SCALE_FACTOR
			current_ank_vel = act_pack.ank_vel / 10

			current_mot_angle = act_pack.mot_ang
			current_mot_vel = act_pack.mot_vel

			act_current = act_pack.mot_cur

			currentTime = time()
			motorAngle_adj = sideMultiplier * -((current_mot_angle* countToDeg) - motorAngleOffset_deg)
			ankleAngle_adj = sideMultiplier * ((current_ank_angle) - ankleAngleOffset_deg)

			motorAngleVec = np.append(motorAngleVec, motorAngle_adj)
			ankleAngleVec = np.append(ankleAngleVec, ankleAngle_adj)
			print("Motor Angle: {} deg\n".format(motorAngle_adj))
			print("Ankle Angle: {} deg\n".format(ankleAngle_adj))
			
			if (currentTime - startTime) > interval:
				inProcedure = False
				print("Exiting Procedure\n")
				n = 50
				for i in range(0, n):
					fxs.send_motor_command(dev_id, fxe.FX_NONE, pullCurrent * (n-i)/n)
					sleep(0.04)

			writer.writerow([iterations, desCurrent, act_current, motorAngle_adj, ankleAngle_adj])

	p = np.polyfit(ankleAngleVec, motorAngleVec, 3) #fit a polynomial to the ankle and motor angles
	print(p)

	print("Exiting curve characterization procedure")
	fxs.close(dev_id)
	return p

def returnMasterCharCurve(side):

	if (side == "left" or side == "l"):
		# p_master = np.array([-0.00424264234777545,-0.06889812445373765,15.130443127922279,-19.645263553974758])
		p_master = np.array([-4.720759145733847e-05,0.006536093248930683,11.081964828396627,-20.28684280598441])
		# -0.0006898396269644869,0.04493335231208463,17.121016947809473,-23.05164502008648
	elif (side == "right" or side == "r"):
		# p_master = np.array([-0.0031984892460558243,-0.05622770666577403,13.225066430545905,-5.280853747360638])
		p_master = np.array([8.177242465556683e-05,0.0064357221142148455,10.222595790957813,-28.841301246984546])
	return p_master

def returnMasterZero(side): # currently not correct
	if (side == "left" or side == "l"):
		zero_master = np.array([516.2000353445956,  39.56368571428572])
	elif (side == "right" or side == "r"):
		zero_master = np.array([-131.07188938982958, 39.440765027322406])

	return zero_master	

def calibrateWrapper(side, port, baud_rate, recalibrateZero=True, recalibrateCurve = True):
	if (side == "left" or side == "l"):
		filename = 'offsets_ExoLeft.csv'
	elif (side == "right" or side == "r"):
		filename = 'offsets_ExoRight.csv'

	if (recalibrateZero):
		# input('Plug in {0} exo and hit ENTER once you''ve done so'.format(side.upper()))

		with open(filename,'w') as file:

			print(side)
			print("Starting homing procedure...\n")
			(motorAngleOffset_deg, ankleAngleOffset_deg) = zeroProcedure(side, port, baud_rate)
			print ('succesfully obtained offsets')

			writer = csv.writer(file, delimiter=',')

			writer.writerow([motorAngleOffset_deg, ankleAngleOffset_deg])

			file.close()
		
	else:
		
		zero_poly_fit = returnMasterZero(side)
		print('reading offsets for {0}'.format(side.upper()))
		with open(filename,'r') as file:

			reader = csv.reader(file, delimiter=',')
			i = 0

			for row in reader:
				i+=1
				if i == 1:
					line1 = np.asarray(row,dtype=np.float64)
				elif i == 2:
					line2 = np.asarray(row,dtype=np.float64)
				elif i == 3:
					line3 = np.asarray(row,dtype=np.float64)
			file.close()

		motorAngleOffset_deg = line1[0]
		ankleAngleOffset_deg = line1[1]

		# motorAngleOffset_deg = zero_poly_fit[0]
		# ankleAngleOffset_deg = zero_poly_fit[1]		


	if (recalibrateCurve):
		# input('hit ENTER to recalibrate curve')
		filename2 = 'char_curve_{0}_{1}.csv'.format(side,strftime("%Y%m%d-%H%M%S"))
		charCurve_poly_fit = characterizeCurve(side, port, baud_rate, motorAngleOffset_deg, ankleAngleOffset_deg)
		TR_poly_fit = np.polyder(charCurve_poly_fit)

		with open(filename2,'w') as file:

			writer = csv.writer(file, delimiter=',')

			writer.writerow(charCurve_poly_fit)
			writer.writerow(TR_poly_fit)


	else:
		charCurve_poly_fit = returnMasterCharCurve(side)
		TR_poly_fit = np.polyder(charCurve_poly_fit)


	print('Motor angle offset')
	print(str(motorAngleOffset_deg))
	print('Ankle angle offset')
	print(str(ankleAngleOffset_deg))	

	return motorAngleOffset_deg, ankleAngleOffset_deg, charCurve_poly_fit, TR_poly_fit


if __name__ == '__main__':

	try: # only works for a single exo
		port_cfg_path = '/home/pi/Actuator-Package/Python/flexsea_demo/ports.yaml'
		ports, baud_rate = fxu.load_ports_from_file(port_cfg_path)

		port = ports[0]

		side = "left"
		#side = "right"

		input("Did you check for the correct leg side?\n")
		
		with open(filename, "w", newline="\n") as fd:
			writer = csv.writer(fd)

		motorAngleOffset_deg, ankleAngleOffset_deg, charCurve_poly_fit, TR_poly_fit = calibrateWrapper(side, recalibrateZero=True, recalibrateCurve=True)

		print(f'Motor Angle Offset: {motorAngleOffset_deg}')
		print(f'Ankle Angle Offset: {ankleAngleOffset_deg}')
		print(f'Char Curve: {charCurve_poly_fit}')
		print(f'TR Curve: {TR_poly_fit}')
		
	except Exception as e:
		print("broke: " + str(e))
		print(traceback.format_exc())
		pass