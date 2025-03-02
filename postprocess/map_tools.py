import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import LogNorm,LinearSegmentedColormap
import pickle
from datetime import datetime
from glob import glob

def plotMap(m,lat,lon,flat,labelname,outfile,clim=None,cmap=None,useLog=False,minval = None):
	fig = plt.figure(figsize=(10, 6))
	m.drawcountries(color='lightgray')
	m.drawcoastlines(color='lightgray')
	if cmap is None:
		cmap = plt.cm.jet
	if useLog:
		if minval is not None:
			flat[flat<=minval] = np.nan #user can optionally supply minimum value for log plots; anything below is not shown
		else:
			flat[flat<=0] = np.nan
		mesh = m.pcolormesh(lon, lat, flat,latlon=True,cmap=cmap,norm=LogNorm())
	else:
		mesh = m.pcolormesh(lon, lat, flat,latlon=True,cmap=cmap)
	if clim is not None:
		plt.clim(clim[0],clim[1])
	else:
		plt.clim(np.nanmin(flat), np.nanmax(flat))
	plt.colorbar(label=labelname)
	fig.savefig(outfile)

def plotEmissions(m,lat,lon,ppdir, hemco_diags_to_process,plotWithLogScale=True, min_emis=None,min_emis_std=None, clim=None, clim_std=None,plotcontrol=True,useLognormal = False, aggToMonthly=True,conversion_factor=None):
	hemcodiag = xr.open_dataset(f'{ppdir}/combined_HEMCO_diagnostics.nc')
	if plotcontrol:
		hemcocontroldiag = xr.open_dataset(f'{ppdir}/control_HEMCO_diagnostics.nc')
	dates = hemcodiag['time'].values
	for diag in hemco_diags_to_process:
		hemcofield = hemcodiag[diag].values
		if conversion_factor is not None:
			hemcofield*=conversion_factor
		if plotcontrol:
			ctrlfield = hemcocontroldiag[diag].values
			if conversion_factor is not None:
				ctrlfield*=conversion_factor
		if len(np.shape(hemcofield)) == 5: #we have emissions at higher levels (e.g. aircraft)
			hemcofield = np.sum(hemcofield,axis=2) #ensemble gone, dim 0 is ens, dim 1 is time, dim 2 is lev. Sum up.
			if plotcontrol:
				ctrlfield = np.sum(hemcofield,axis=1) #dim 0 is time, dim 1 is lev.
		if aggToMonthly:
			dates,scalar = agg_to_monthly(dates, hemcofield)
			_,ctrlfield = agg_to_monthly(dates, ctrlfield)
		if useLognormal: 
			hemcofield_std = np.exp(np.std(np.log(hemcofield),axis=0)) #std of log will give the lognormal shape parameter; exponentiate back into emissions space. 
			hemcofield = np.exp(np.mean(np.log(hemcofield),axis=0)) #average across ensemble
		else:
			hemcofield_std = np.std(hemcofield,axis=0) #standard deviation across ensemble
			hemcofield = np.mean(hemcofield,axis=0) #average across ensemble
		#Now hemcofield is of dim time, lat, lon
		timelabels = [str(timeval)[0:13] for timeval in dates]
		#Do the plotting.
		#Get colormaps
		if clim_std is None:
			if min_emis_std is not None:
				clim_std = [min_emis_std,np.max(hemcofield_std)]
			else:
				clim_std = [np.min(hemcofield_std),np.max(hemcofield_std)]
		if clim is None:
			if plotcontrol:
				if min_emis is not None:
					clim  = [min_emis, np.max([np.max(hemcofield),np.max(ctrlfield)])]
				else:
					clim  = [np.min([np.min(hemcofield),np.min(ctrlfield)]), np.max([np.max(hemcofield),np.max(ctrlfield)])]
			else:
				if min_emis is not None:
					clim  = [min_emis, np.max(hemcofield)]
				else:
					clim  = [np.min(hemcofield), np.max(hemcofield)]
		cmap = plt.cm.jet
		for i,dateval in enumerate(timelabels):
			plotMap(m,lat,lon,hemcofield[i,:,:],diag,f'{ppdir}/{diag}_{dateval}_ensemble_mean.png',clim = clim, useLog=plotWithLogScale,minval = min_emis)
			plotMap(m,lat,lon,hemcofield_std[i,:,:],diag,f'{ppdir}/{diag}_{dateval}_ensemble_std.png',clim = clim_std, useLog=plotWithLogScale,minval = min_emis_std)
			if plotcontrol:
				plotMap(m,lat,lon,ctrlfield[i,:,:],diag,f'{ppdir}/{diag}_{dateval}_control.png',clim = clim, useLog=plotWithLogScale,minval = min_emis)


def plotScaleFactor(m,lat,lon,ppdir, useLognormal = False, aggToMonthly=True,plot_on_log_scale=False,clim = None):
	files = glob(f'{ppdir}/*_SCALEFACTOR.nc')
	files.sort()
	sf_names = [pts.split('/')[-1][0:-15] for pts in files]
	for file,name in zip(files,sf_names):
		ds = xr.load_dataset(file)
		dates = ds['time'].values
		scalar = ds['Scalar'].values
		if aggToMonthly:
			dates,scalar = agg_to_monthly(dates, scalar)
		if useLognormal:
			scalar = np.exp(np.mean(np.log(scalar),axis=0)) #average across ensemble
		else:
			scalar = np.mean(scalar,axis=0) #average across ensemble
		timelabels = [str(timeval)[0:13] for timeval in dates]
		if plot_on_log_scale:
			cmap = plt.cm.bwr #Let user supplied clim and plotMap do the rest.
		else:
			#Make custom blue-white-red colorbar centered at one
			cvals  = [0.0, 1.0, np.max([np.max(scalar),1.1])]
			colors = ["blue","white","red"]
			pltnorm=plt.Normalize(min(cvals),max(cvals))
			tuples = list(zip(map(pltnorm,cvals), colors))
			cmap = LinearSegmentedColormap.from_list("", tuples)
			if clim is None:
				clim = [0,np.max([np.max(scalar),1.1])]
		for i,dateval in enumerate(timelabels):
			plotMap(m,lat,lon,scalar[i,:,:],'Scaling factor',f'{ppdir}/{name}_{dateval}_scalefactor.png',clim=clim,cmap=cmap,useLog=plot_on_log_scale)

def regridBigYdata(bigy,gclat,gclon,timeperiod=None):
	dates = bigy["dates"]
	datevals = [datetime.strptime(dateval,'%Y%m%d_%H%M') for dateval in dates]
	specieslist = bigy["species"]
	total_satellite_obs=bigy["obscount"]
	true_obs = bigy["obs"]
	sim_obs = bigy["sim_obs"]
	ctrl_obs = bigy["control"]
	if timeperiod is not None: #Slice data down to timeperiod
		inds = [i for i, e in enumerate(datevals) if (e >= timeperiod[0]) & (e < timeperiod[1])]
		total_satellite_obs=total_satellite_obs[inds,:,:,:]
		true_obs = true_obs[inds,:,:,:]
		sim_obs = sim_obs[inds,:,:,:]
		ctrl_obs = ctrl_obs[inds,:,:,:]
	#Arrays to return
	total_obs_in_period = np.sum(total_satellite_obs,axis=0)
	total_weighted_mean_true_obs = np.zeros(np.shape(total_obs_in_period))
	assim_minus_obs = np.zeros(np.shape(total_obs_in_period))*np.nan
	ctrl_minus_obs = np.zeros(np.shape(total_obs_in_period))*np.nan
	#loop through and fill.
	for i,species in enumerate(specieslist):
		for j in range(len(gclat)):
			for k in range(len(gclon)):
				if np.sum(~np.isnan(true_obs[:,i,j,k]))>0:
					assim_minus_obs[i,j,k] = np.nanmean(sim_obs[:,i,j,k]-true_obs[:,i,j,k])
					ctrl_minus_obs[i,j,k] = np.nanmean(ctrl_obs[:,i,j,k]-true_obs[:,i,j,k])
				if np.sum(total_satellite_obs[:,i,j,k]) == 0:
					total_weighted_mean_true_obs[i,j,k] = np.nan
				else:
					indices = np.where(np.logical_not(np.isnan(true_obs[:,i,j,k])))[0]
					total_weighted_mean_true_obs[i,j,k] = np.average(true_obs[indices,i,j,k],weights=total_satellite_obs[indices,i,j,k])
	return [total_obs_in_period,total_weighted_mean_true_obs,assim_minus_obs,ctrl_minus_obs]


def agg_to_monthly(dates, to_agg):
	agg_dim = len(np.shape(to_agg))
	years = dates.astype('datetime64[Y]').astype(int) + 1970
	months = dates.astype('datetime64[M]').astype(int) % 12 + 1
	ym = (years*100) + months
	_, ind = np.unique(ym,return_index = True)
	dates = dates[ind]
	shape = np.array(np.shape(to_agg))
	if agg_dim == 3:
		shape[0] = len(ind)
	else:
		shape[1] = len(ind)
	to_return = np.zeros(shape)
	for i in range(len(ind)):
		if agg_dim == 3:
			if i == len(ind)-1:
				subset = to_agg[ind[i]:,:,:]
			else:
				subset = to_agg[ind[i]:ind[i+1],:,:]
			to_return[i,:,:] = np.mean(subset,axis=0)
		else:
			if i == len(ind)-1:
				subset = to_agg[:,ind[i]:,:,:]
			else:
				subset = to_agg[:,ind[i]:ind[i+1],:,:]
			to_return[:,i,:,:] = np.mean(subset,axis=1)
	return [dates,to_return]
