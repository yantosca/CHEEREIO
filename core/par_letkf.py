from Assimilator import Assimilator
import sys
import time
import settings_interface as si 
import numpy as np
from datetime import datetime,timedelta

data = si.getSpeciesConfig()
path_to_scratch = f"{data['MY_PATH']}/{data['RUN_NAME']}/scratch"
timestamp = str(sys.argv[1]) #Time to assimilate. Expected in form YYYYMMDD_HHMM, UTC time.
DO_RERUN = data["DO_VARON_RERUN"] == "True"

with open(f"{path_to_scratch}/ACTUAL_RUN_IN_PLACE_ASSIMILATION_WINDOW") as f:
    lines = f.readlines()

actual_aw = float(lines[0])
do_rip_aw = False

if not np.isnan(actual_aw):
	actual_aw = int(actual_aw)
	do_rip_aw = True

#Calculate time to use for restart load if we are doing run in place or rerun; different from timestamp
if DO_RERUN:
	delta = timedelta(hours=int(data['ASSIM_TIME']))
	timestamp_datetime = datetime.strptime(timestamp, "%Y%m%d_%H%M")
	timestamp_restart_dt = timestamp_datetime-delta #Restart we are assimilating is one timestep behind current timestamp (because rerunning from one week behind).
	timestamp_restart = timestamp_restart_dt.strftime("%Y%m%d_%H%M") 
elif do_rip_aw:
	ASSIM_TIME = int(data['ASSIM_TIME'])
	backwards = ASSIM_TIME-actual_aw #How many hours backwards should we look from current timestamp for restart to use in building state vector?
	timestamp_datetime = datetime.strptime(timestamp, "%Y%m%d_%H%M")
	delta = timedelta(hours=int(backwards))
	timestamp_restart_dt = timestamp_datetime-delta
	timestamp_restart = timestamp_restart_dt.strftime("%Y%m%d_%H%M")
else:
	timestamp_restart = None

ensnum = int(sys.argv[2])
corenum = int(sys.argv[3])
first_run = str(sys.argv[4])=='true' #If this is the first run, will be true.
just_scale = str(sys.argv[5])=='true' #If this is the first run AND user specifies, we'll just scale (no assimilation); this is calculated in the run_ensemble_simulations script now.
do_amplification = str(sys.argv[6])=='true' #If this is the first run AND user specifies, we'll amplify the spreads of the ensemble member concentrations.
if just_scale:
	label_str = 'scaling'
else:
	label_str = 'LETKF'
dateval = timestamp[0:4]+'-'+timestamp[4:6]+'-'+timestamp[6:8]

if just_scale:
	#Scaling restarts; only ens 1 core 1 will do this.
	if (ensnum == 1) and (corenum==1):
		print(f'Core ({ensnum},{corenum}) is gathering ensemble at time {dateval}.')
		start = time.time()
		print(f'Assimilator call: Assimilator({timestamp},{ensnum},{corenum},timestamp_from_rip={timestamp_restart})')
		a = Assimilator(timestamp,ensnum,corenum,timestamp_from_rip=timestamp_restart)
		end = time.time()
		print(f'Core ({ensnum},{corenum}) gathered ensemble in {end - start} seconds. Begin {label_str} procedure.')
		start = time.time()
		if do_amplification:
			a.amplifySpreads()
		a.scaleRestarts()
		a.saveRestarts()
		with open(f"{path_to_scratch}/ASSIMILATION_COMPLETE", "w") as f:
			f.write("Done.\n") #If so, save flag file to ensemble folder
		end = time.time()
		print(f'Core ({ensnum},{corenum}) completed computation for {dateval} and saved columns in {end - start} seconds.')
	else:
		print(f'Just scaling restarts. Core ({ensnum},{corenum}) is not needed and will hang.')
else:
	print(f'Core ({ensnum},{corenum}) is gathering ensemble at time {dateval}.')
	start = time.time()
	print(f'Assimilator call: Assimilator({timestamp},{ensnum},{corenum},timestamp_from_rip={timestamp_restart})')
	#a = Assimilator('20190108_0000',2,1)
	a = Assimilator(timestamp,ensnum,corenum,timestamp_from_rip=timestamp_restart)
	end = time.time()
	print(f'Core ({ensnum},{corenum}) gathered ensemble in {end - start} seconds. Begin {label_str} procedure.')
	start = time.time()
	if do_amplification:
		a.amplifySpreads()
	a.LETKF()
	end = time.time()
	print(f'Core ({ensnum},{corenum}) completed computation for {dateval} and saved columns in {end - start} seconds.')

print('-------------------END LETKF-------------------')
