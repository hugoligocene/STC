#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

This script provides statistics of the forward runs of the FORWBox-meanhigh family

It is based on the output of ageStat.py and is a variant of plotAgeStat
In plotAgeStat, the diagnostics are shown for all streams for a given supertype

This version is a special version of plotAgeStatComposit for the 2019 STC final meeting
It differs by removing the plots for the Return runs, rescaling due to change of
time unit from hour to day and accounting for the output step and beautifying
the figures, and improving the printed version.
It differs from plotAgeStatComposit4ACP by changing spatial units from degree to km

Version derived from plotAgeStatComposit4ACP for the benefit of some confs in 
2019 but which is also now the official version for the paper.
A number of modifications and additions have been made.

core: possibility to use cloud core analysis (for EAD only)
New scaling of the impact (final)
New diagnostic of the impact: integrated impact (in pt) as a function of time, 
probability of hiting the level as a function of pt (integral in age)
Corrected mean age using the formula of Scheele
Proportion of parcels above a given level relative to the same proportion in 
the sources

Here we show the results for the whole summer 2017 and as a comparison
between the supertypes in the FullAMA domain (EAZ, EAD, EIZ, EID, EIZ-Return and EID-Return)

It generates for both sh and mh hightypes 4  figures which are
(actually mh not plotted)

1) The 2d histogram of parcels as a function of age and potential temperature
1ACP) The version for ACP
1 bis) Integrated impact

2) The same histogram normalized per level to better see the vertical propagation
2ACP) The version for ACP
2Corr) The mean age with and without age correction

3) The mean age and the modal age for each level (discarded)

4) The number of active parcels as a function of age

5) Plot of the vertical distribution of sources at (age 0 parcels) (discarded)

6) Plot for each of the supertype of the normalized age histogram at 370 K, 380 K and 400 K ,
that is positions 94, 104, 124
Show mean and modal peak

7) Comparison of the histograms for EAZ, EAD, EID, EIZ, EID-Return, EIZ-Return
superimposed to the source curve

7bis) Plot of the proportion of parcels above a given level relative to the same
proportion in the sources

8) Analysis of diffusion

This is made for each of the 9 decades and can be called for all the runs

EAZ, EAD, EIZ, EID are showing statistics of parcels in the FullAMA domain with the rule that a particle that exits
once is discarded.
EIZ-FULL, EID-FULL show the statistics of parcels in the global domain
EIZ-Return, EID-Return show the statistics of parcels in the FullAMA domain by applying a simple mask to the FULL runs,
that is parcels that leave the domain are counted if they return.

Created on Sat 23 Feb 2019

@author: Bernard Legras

Created on Sat 23 Feb 2019

@author: Bernard Legras
"""
import numpy as np
#from datetime import datetime,timedelta
import pickle,gzip
import matplotlib.pyplot as plt
import matplotlib.colors as colors
#import matplotlib.ticker as ticker
from matplotlib.colors import LogNorm
import argparse
import socket
import os

# Color list with 20 colors
listcolors=['#161d58','#253494','#2850a6','#2c7fb8','#379abe','#41b6c4',
            '#71c8bc','#a1dab4','#d0ecc0','#ffffcc','#fef0d9','#fedeb1',
            '#fdcc8a','#fdac72','#fc8d59','#ef6b41','#e34a33','#cb251a',
            '#b30000','#7f0000']
mymap=colors.ListedColormap(listcolors)
dpi = 300

parser = argparse.ArgumentParser()
parser.add_argument("-t","--type",type=str,choices=["EAD","EAZ","EIZ","EID","EIZ-Return","EID-Return","EIZ-FULL","EID-FULL"],help="type")
#parser.add_argument("-d","--date",type=str,choices=["Jun-01","Jun-11","Jun-21","Jul-01","Jul-11","Jul-21","Aug-01","Aug-11","Aug-21"],help='run_date')

supertypes = ["EAZ","EIZ","EIZ-Return","EIZ-FULL","EAD","EID","EID-Return","EID-FULL"]
#hightypes = ['sh','mh']
hightypes = ['sh',]

# parameter for  using core clouds and core analysis (only for EAD at the moment)
core = False
if core:
    cc = 'core'
else:
    cc = ''

step = 6
hmax = 1728
# 62 days
age_max = 1488
nstep  =  int(hmax/step)
figsave = False
figpdf = False
nbins = 425
theta = np.arange(275.5,700,1)
ages = np.arange(0,age_max+1,6)/24
ageaxis = np.arange(0.,62.25,0.25)
thetaxis = np.arange(275.5,700)

fs = 16
trea = {'EAZ':'ERA5 kinematic','EAD':'ERA5 diabatic',
        'EIZ':'ERA-I kinematic','EID':'ERA-I diabatic'}
trea_short = {'EAZ':'ERA5 kin','EAD':'ERA5 dia',
        'EIZ':'ERA-I kin','EID':'ERA-I dia'}
#plt.rc('text', usetex=True)
#plt.rc('font', family='serif')
dpi = 300

args = parser.parse_args()
if args.type is not None: supertype = args.type

dates = ["Jun-01","Jun-11","Jun-21","Jul-01","Jul-11","Jul-21","Aug-01","Aug-11","Aug-21"]
#dates = ["Jun-01","Jun-11","Jun-21"]
#dates = ['Aug-21']

# Find the main work dir according to the computer
if socket.gethostname() == 'gort':
    forw_dir =  '/home/legras/data/STC/STC-forw'
    out_dir = '/home/legras/data/STC/STC-FORWBox-meanhigh-OUT'
elif 'ciclad' in socket.gethostname():
    forw_dir =  '/home/legras/STC/STC-forw'
    out_dir = '/data/legras/STC/STC-FORWBox-meanhigh-OUT'
elif 'satie' in socket.gethostname():
    forw_dir =  '/home/legras/data/STC/STC-forw'
    out_dir = '/home/legras/data/STC/STC-FORWBox-meanhigh-OUT'
elif 'Graphium' in socket.gethostname():
    forw_dir = "C:\\cygwin64\\home\\berna\\data\\STC\\STC-forw"
    out_dir = "C:\\cygwin64\\home\\berna\\data\\STC\\STC-FORWBox-meanhigh-OUT"

result = {}
result['sh'] = {}
result['mh'] = {}
for supertype in supertypes:
    for hightype in hightypes:
        result[hightype][supertype] = {}
        result[hightype][supertype]['histog'] = np.zeros(shape=(nstep,nbins))
    for date in dates:
        print('')
        print('Processing '+date+' for '+supertype)
        # get the histograms and mean data calculated by ageStat.py from the part files
        file_out = os.path.join(out_dir,'ageStat-'+supertype+'-2017-'+date)
        if core & (supertype == 'EAD'):
            file_out = os.path.join(out_dir,'ageStat-'+supertype+'-Core-2017-'+date)
        print('reading',file_out )
        with gzip.open(file_out,'rb') as f:
           [_,histog,_,_] = pickle.load(f)
        for hightype in hightypes:
            result[hightype][supertype]['histog'] += histog[hightype]
    for hightype in hightypes:
        result[hightype][supertype]['nactiv'] = np.sum(result[hightype][supertype]['histog'],axis=1)

#%%
# need to load the true source distribution
with gzip.open(os.path.join(forw_dir,'source_dist_updated.pkl'),'rb') as f:
        source_dist = pickle.load(f)

# insert the source distribution
for hightype in hightypes:
    for supertype in ['EAZ','EAD','EIZ','EID']:
        result[hightype][supertype]['histog'] = np.insert(result[hightype][supertype]['histog'],0,source_dist['sh'+cc],axis=0)

#%% 1ACP) Plot of the age/thet histogram
# normalization : conversion of time into days and degree in km
# The factor Delta theta is 1 here (1K layer)
degree = 6372 * 2 * np.pi / 360
ff_s = (1/24) * degree**2
fst = 16
fs  =20
show_slope = True
lt1 = 94   # index for theta = 369.5 K
lt2 = 144  # index for theta = 419.5 K

for hightype in hightypes:
    fig = plt.figure(figsize=(9,9))
    #fig.suptitle(hightype+' age theta histogram',fontsize=fs )
    n = 1
    for supertype in ['EAZ','EAD','EIZ','EID']:
        plt.subplot(2,2,n)
        #im = plt.imshow(np.log10(ff_s*result[hightype][supertype]['histog'][0:248,:]).T,
        #           extent=(0.25,62,275,700),origin='lower',aspect='auto',cmap=mymap,clim=(-3,3))
        im = plt.imshow(ff_s*result[hightype][supertype]['histog'][0:249,:].T,
                   extent=(0.,62,275,700),origin='lower',aspect='auto',cmap=mymap,
                   norm = LogNorm(vmin=10,vmax=5e7))
        if show_slope:
            hh = result[hightype][supertype]['histog'][0:249,:].copy()
            # factor 0.25 because the sampling step is 6h
            ss = 0.25*np.sum(hh,axis=0)
            hh = hh / ss[np.newaxis,:]
            # 0.25 is 6h
            # The offset 30 is here to avoid capturing a wrong max at high altitude in EAD and EIZ
            [slope,org] = np.polyfit(ages[30+np.argmax(hh[30:,lt1:lt2+1],axis=0)],theta[lt1:lt2+1],1)
            age1 = (theta[lt1] - org)/slope
            age2 = (theta[lt2] - org)/slope
            plt.plot([age1,age2],[theta[lt1],theta[lt2]])
        plt.ylim(320,420)
        plt.xlim(0,62)
        plt.tick_params(labelsize=fst)
        #plt.colorbar()
        plt.title(trea[supertype],fontsize=fs)
        if n in [1,3]: plt.ylabel(r'Potential temperature (K)',fontsize=fs)
        if n in [3,4]: plt.xlabel(r'Age (day)',fontsize=fs)
        n += 1
    cax = fig.add_axes([0.17,-0.04,0.67,0.05])
    cbar = fig.colorbar(im,cax,orientation='horizontal')
    cbar.set_label(r'Cumulative impact per age (day km$^2$ K$^{-1}$)',labelpad=-1,size=fs)
    cbar.ax.tick_params(labelsize=fs)
    if figpdf:
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agethethist-composit-ACP.png'),bbox_inches='tight',dpi=dpi)
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agethethist-composit-ACP.pdf'),bbox_inches='tight',dpi=dpi)
    plt.show()

#%% 1 bis ACP) diagnostics on this histogram
    # integral of source dist over the potential temperature
    d_theta = 5
    SS = ff_s*np.sum(source_dist['sh'+cc]) * d_theta
    tc = 140
    for hightype in hightypes:
        impact = {}
        impact_age = {}
        impact_theta = {}
        for supertype in supertypes:
            impact[supertype] = ff_s*result[hightype][supertype]['histog'][0:249,:].T
            # integral of impact over theta as a function of age
            impact_age[supertype] = np.sum(impact[supertype],axis=0) * d_theta
            # proba to each the level theta
            impact_theta[supertype] = np.sum(impact[supertype],axis=1)*d_theta/SS
        fig = plt.figure(figsize=(12,6))
        plt.subplot(1,2,1)
        ages = np.arange(0.,62.1,0.25)
        plt.semilogy(ages,impact_age['EIZ'],'--r',
                            ages,impact_age['EID'],'r',
                            ages,impact_age['EAZ'],'--b',
                            ages,impact_age['EAD'],'b',linewidth=6)
        plt.legend(('EIZ 17 days','EID 15 days','EAZ 13.3 days','EAD 13.3 days'),fontsize=fs,loc='upper right')
        # fit slope for ages > 35 days
        for supertype in ['EIZ','EID','EAZ','EAD']:
            [slope,i0] = np.polyfit(ages[tc:],np.log(impact_age[supertype][tc:]),1)
            print ('decay time and anchor',supertype,1/slope,np.exp(i0))
            plt.semilogy(ages[tc:],np.exp(i0 + slope*ages[tc:]),'k',linewidth=12,alpha=0.3)
        plt.xlabel('ages (day)',fontsize=fs)
        plt.ylabel('integrated impact',fontsize=fs)
        plt.tick_params(labelsize=fst)
        plt.subplot(1,2,2)
        thetas = np.arange(275.5,700,1)
        plt.semilogx(impact_theta['EIZ'],thetas,'--r',
                            impact_theta['EID'],thetas,'r',
                            impact_theta['EAZ'],thetas,'--b',
                            impact_theta['EAD'],thetas,'b',linewidth=6)
        plt.legend(('EIZ 10.6 K','EID 20.1 K','EAZ 14.7 K','EAD 15.4 K'),fontsize=fs,loc='lower left')
        # fit slope for lveles between 370K and 410K
        for supertype in ['EIZ','EID','EAZ','EAD']:
            [slope,pp] = np.polyfit(thetas[95:136],np.log(impact_theta[supertype][95:136]),1)
            print('proba theta time and anchor',supertype,1/slope,np.exp(pp))
            plt.semilogx(np.exp(pp + slope*thetas[95:136]),thetas[95:136],'k',linewidth=12,alpha=0.3)
        plt.xlabel('probability of hiting the level',fontsize=fs)
        plt.ylabel('potential temperature (K)',fontsize=fs)
        plt.tick_params(labelsize=fs)
        plt.ylim(320,420)
        plt.xlim(1.e-3,2)
        plt.show()

#%% 2ACP) Plot of the age/thet histogram, normalized for each level by integrating in time
lt1 = 94   # index for theta = 369.5 K
lt2 = 144  # index for theta = 419.5 K
for hightype in hightypes:
    fig = plt.figure(figsize=(9,9))
    #fig.suptitle(hightype+' age theta normalized histogram' )
    n = 1
    for supertype in ['EAZ','EAD','EIZ','EID']:
        plt.subplot(2,2,n)
        hh = result[hightype][supertype]['histog'][0:249,:].copy()
        # factor 0.25 because the sampling step is 6h
        # therefore we normalize to 1 if the correct integration is used
        ss = 0.25*np.sum(hh,axis=0)
        hh = hh / ss[np.newaxis,:]
        im = plt.imshow(hh.T,norm = LogNorm(vmin=1e-6,vmax=0.1),
                   extent=(0.,62,275,700),origin='lower',aspect='auto',cmap=mymap)
        # Fit a line to the age crest as a function of potential temperature
        # 0.25 is 6h
        # The offset 30 is here to avoid capturing a wrong max at high altitude in EAD and EIZ
        [slope,org] = np.polyfit(ages[30+np.argmax(hh[30:,lt1:lt2+1],axis=0)],theta[lt1:lt2+1],1)
        age1 = (theta[lt1] - org)/slope
        age2 = (theta[lt2] - org)/slope
        plt.plot([age1,age2],[theta[lt1],theta[lt2]])
        plt.ylim(320,420)
        plt.xlim(0.,62)
        plt.tick_params(labelsize=fst)
        plt.title(trea[supertype],fontsize=fs)
        print(supertype,slope)

        if n in [1,3]: plt.ylabel(r'Potential temperature (K)',fontsize=fs)
        if n in [3,4]: plt.xlabel(r'Age (day)',fontsize=fs)
        n += 1
    cax = fig.add_axes([0.17,-0.04,0.67,0.05])
    cbar = fig.colorbar(im,cax,orientation='horizontal')
    cbar.set_label(r'Normalized age spectrum per level (day$^{-1}$)',labelpad=-1,size=fs)
    cbar.ax.tick_params(labelsize=fs)
    if figpdf:
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agethetnormhist-composit-ACP.png'),bbox_inches='tight',dpi=dpi)
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agethetnormhist-composit-ACP.pdf'),bbox_inches='tight',dpi=dpi)
    plt.show()

#%% 2Corr) MEAN AGE (WITH TAIL CORRECTION )
# Use the method of Scheele
# calculation of the tail decay for large age
#% first plot every 5K between 320 and 420K for ERA5 diabatic
fig = plt.figure(figsize=(5,5))
hightype = 'sh'
supertype = 'EID'
hh = result[hightype][supertype]['histog'][0:249,:].copy()
# Here we normalize such that the discrete integral of hh is 1 for each theta
# In this way hh is the discrete version of the continuous distribution F
# (see note about age correction in manus/method)
ss = 0.25*np.sum(hh,axis=0)
hh = hh / ss[np.newaxis,:]
# l1 and l2 bounds for theta limiting following calculations to the 320K-420K range
l1 = np.where(theta>320)[0][0]
l2 = np.where(theta<420)[0][-1]+1
l3 = np.where(theta<400)[0][-1]+1
l4 = np.where(theta>330)[0][0]
# aL find index of age = 50 day (assumig oldest age is about 60)
aL = np.where(ages>50)[0][0]-1
for l in range(l1+10,l2+1,5):
    plt.plot(ages[aL:],hh[aL:,l])
plt.yscale('log')
plt.show()
fig = plt.figure(figsize=(5,5))
# fit a log-linear law over the interval
slope = np.empty(l2-l1+1)
pp = np.empty(l2-l1+1)
i = 0
for l in range(l1,l2+1):
    [slope[i],pp[i]] = np.polyfit(ages[aL:]-ages[-1],np.log(hh[aL:,l]),1)
    i += 1
pp = np.exp(pp)
plt.plot(slope,theta[l1:l2+1])
mslope = np.mean(slope[l4-l1:l3-l1])
# get slopes of the slope
# here we select sub-intervals (actually 330K-355K and 355K-385K) to fit
# straight lines to the slope variation with theta
s1 = np.mean(slope[10:36])
[m2,s20] = np.polyfit(theta[l1+35:l1+65],slope[35:65],1)
plt.plot([s1,s1],[330,355],'m',s20+m2*theta[l1+35:l1+65],theta[l1+35:l1+65],'m')
plt.show()
print('s1',s1)
print('s20, m2',s20,m2)
#%%
# Mean age and correction of the mean age
# uncorrected mean age
fig,axs = plt.subplots(2,2,figsize=(7,7),sharex=True,sharey=True)
axs = axs.flatten()
k = 0
for supertype in ['EAD','EAZ','EID','EIZ']:
    hh = result[hightype][supertype]['histog'][0:249,:].copy()
    ss = 0.25*np.sum(hh,axis=0)
    hh = hh / ss[np.newaxis,:]
    # corrected mean age (see formula )
    slope = np.empty(l2-l1+1)
    pp = np.empty(l2-l1+1)
    i = 0
    for l in range(l1,l2+1):
        [slope[i],pp[i]] = np.polyfit(ages[aL:]-ages[-1],np.log(hh[aL:,l]),1)
        i += 1
    pp = np.exp(pp)
    slope = np.ma.masked_invalid(slope)
    mslope = np.mean(slope[l4-l1:l3-l1])
    hh = hh[:,l1:l2+1]
    meanAges = 0.25*np.sum(hh*ages[:,np.newaxis],axis=0)
    corrAges = (meanAges - (hh[-1,:]/slope)*(-1/slope + ages[-1]))/(1 - hh[-1,:]/slope)
    corrAges2 = (meanAges - (hh[-1,:]/mslope)*(-1/mslope + ages[-1]))/(1 - hh[-1,:]/mslope)

    # plot uncorrected and corrected age together

    #plt.plot(meanAges,theta[l1:l2+1],corrAges,theta[l1:l2+1],corrAges2,theta[l1:l2+1])
    axs[k].plot(meanAges,theta[l1:l2+1],corrAges2,theta[l1:l2+1],linewidth=3)
    axs[k].set_xlim(0,60)
    if k in [2,3]: axs[k].set_xlabel('Age (day)')
    if k in [0,2]: axs[k].set_ylabel('Potential temperature (K)')
    #plt.legend(['Uncorrected mean age','Corrected mean age'],loc='center right')
    axs[k].set_title('Mean age for '+supertype)
    k += 1
if figpdf:
    plt.savefig(os.path.join(forw_dir,'figs',hightype+'-age-correction-ACP.png'),bbox_inches='tight',dpi=dpi)
    plt.savefig(os.path.join(forw_dir,'figs',hightype+'-age-correction-ACP.pdf'),bbox_inches='tight',dpi=dpi)
plt.show()

#%% 4ACP) Plot of the number of active parcels as a function of age in three separate
# vertical bands of theta (and total)
# The rescaling factor is here due to converting from hour to day in tau, multiplying
# by the integration factor Delta t = 6h and converting dedree in km
ff = (1/24) * (1/4) * degree**2
for hightype in hightypes:
    fig = plt.figure(figsize=(9,9))
    #fig.suptitle(hightype+' nactiv as a function of age  per range tot(k) top(r) bot(b) mid(g)')
    n = 1
    for supertype in ['EAZ','EAD','EIZ','EID']:
        plt.subplot(2,2,n)
        # 65 is first thetaxis above 340 K and 95 is first thetaxis above 370 K
        total = np.sum(ff*result[hightype][supertype]['histog'][0:249,:],axis=1)
        toprange = np.sum(ff*result[hightype][supertype]['histog'][0:249,95:],axis=1)
        botrange = np.sum(ff*result[hightype][supertype]['histog'][0:249,0:65],axis=1)
        midrange = np.sum(ff*result[hightype][supertype]['histog'][0:249,65:95],axis=1)
        plt.semilogy(ageaxis,total,'k',ageaxis,toprange,'r',
                     ageaxis,botrange,'b',ageaxis,midrange,'g',linewidth=4)

        if n in [1,3]: plt.ylabel(r'Cumulative impact (day$^2$ km$^2$)',fontsize=fs)
        if n in [3,4]: plt.xlabel(r'Age (day)',fontsize=fs)
        plt.tick_params(labelsize=fst)
        plt.ylim(1000,3e8)
        # Calculate the slope of the curves during the second half and fit a curve
        tc = 140
        [total_slope,total_y0] = np.polyfit(ageaxis[tc:],np.log(total[tc:]),1)
        [toprange_slope,toprange_y0] = np.polyfit(ageaxis[tc:],np.log(toprange[tc:]),1)
        [midrange_slope,midrange_y0] = np.polyfit(ageaxis[tc:],np.log(midrange[tc:]),1)
        [botrange_slope,botrange_y0] = np.polyfit(ageaxis[tc:],np.log(botrange[tc:]),1)
        print('decay',supertype)
        print('total   ',[total_slope,total_y0])
        print('toprange',[toprange_slope,toprange_y0])
        print('midrange',[midrange_slope,midrange_y0])
        print('botrange',[botrange_slope,botrange_y0])
        tc2 = 124
        plt.semilogy(ageaxis[tc2:],np.exp(total_y0)*np.exp(total_slope*ageaxis[tc2:]),'k',
                     ageaxis[tc2:],np.exp(midrange_y0)*np.exp(midrange_slope*ageaxis[tc2:]),'g',
                     ageaxis[tc2:],np.exp(botrange_y0)*np.exp(botrange_slope*ageaxis[tc2:]),'b',
                     linewidth=12,alpha=0.3)
        #if n in [1,3]: plt.ylim(1,2*10**6)
        #else:
        #    plt.ylim(5*10**3,2*10**6)

        plt.title(r'{} t:{:3.1f} m:{:3.1f} b:{:3.1f}'.format(trea_short[supertype],-1/total_slope,-1/midrange_slope,-1/botrange_slope),fontsize=fs)
        n += 1

    if figpdf:
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agenactiv-composit-ACP.png'),bbox_inches='tight',dpi=dpi)
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agenactiv-composit-ACP.pdf'),bbox_inches='tight',dpi=dpi)
    plt.show()

#%% 6ACP) Plot the supertypes EAZ, EAD, EIZ, EID of the normalized age histogram at 370 K, 380 K and 400 K ,
# that is positions 94, 104, 124
# show mean and modal peak
fs = 16
for hightype in hightypes:
    fig = plt.figure(figsize=(9,9))
    #fig.suptitle(hightype+' normalized age histogram at 370 k (b), 380 K (r) and 400 K (k)')
    n = 1
    for supertype in ['EAZ','EAD','EIZ','EID']:
        plt.subplot(2,2,n)
        hh = result[hightype][supertype]['histog'][0:249,:].copy()
        ss = 0.25*np.sum(hh,axis=0)
        hh = hh / ss[np.newaxis,:]
        agemean = 0.25*np.sum(hh*ageaxis[:,np.newaxis],axis=0)
        agemode = ageaxis[np.argmax(hh,axis=0)]
        plt.plot(ageaxis,hh[:,94],'b',ageaxis,hh[:,104],'r',ageaxis,hh[:,124],'k',linewidth=5)
        # to have the vertical axis in log scale
        plt.yscale('log')
        plt.scatter(agemean[94],0.065,c='b',marker='v',s=128)
        plt.scatter(agemean[104],0.065,c='r',marker='v',s=128)
        plt.scatter(agemean[124],0.065,c='k',marker='v',s=128)
        plt.scatter(agemode[94],0.053,c='b',marker='D',s=96)
        plt.scatter(agemode[104],0.053,c='r',marker='D',s=96)
        plt.scatter(agemode[124],0.053,c='k',marker='D',s=96)
        #plt.plot([agemean[94],],[0.015,],'bv',[agemean[104],],[0.015,],'rv',[agemean[124],],[0.015,],'kv',linewidth=12)
        plt.title(trea[supertype],fontsize=fs)
        plt.tick_params(labelsize=fst)
        plt.ylim(0,0.07)
        if n in [1,3]: plt.ylabel('Normalized age spectrum (day$^{-1}$)',fontsize=fs)
        if n in [3,4]: plt.xlabel('Age (day)',fontsize=fs)
        n += 1
    if figpdf:
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agehistog3levels-composit-ACP.png'),bbox_inches='tight',dpi=dpi)
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-agehistog3levels-composit-ACP.pdf'),bbox_inches='tight',dpi=dpi)
    plt.show()

#%% 7ACP) Comparison of the histograms for EAZ, EAD, EID, EIZ, EID-Return, EIZ-Return
# superimposed to the source curve
# Set TeX to write the labels and annotations
plt.rc('text', usetex=False)
#plt.rc('font', family='sansserif')

# normalization factor 1/24 * 1/4 (to convert units of previous time factor in
# day and to multiply per the time integration interval 6h and the inverse of the layer
# thickness (no factor for this later since layer thickness is 1 K)
ff = (1/24) * (1/4) * degree**2
# for the source distribution, the Delta t factor is not used
ff_s = (1/24)  * degree**2
fs = 14
for hightype in hightypes:
    hightcore = hightype+cc
    fig,ax = plt.subplots(figsize=(5,5))
    ax.semilogx(ff*np.sum(result[hightype]['EIZ']['histog'][0:249,:],axis=0),thetaxis,'--r',
                ff*np.sum(result[hightype]['EID']['histog'][0:249,:],axis=0),thetaxis,'r',
                ff*np.sum(result[hightype]['EAZ']['histog'][0:249,:],axis=0),thetaxis,'--b',
                ff*np.sum(result[hightype]['EAD']['histog'][0:249,:],axis=0),thetaxis,'b',
                linewidth=5)
    ax.set_ylabel(r'Potential temperature $\theta$ (K)',fontsize=fs)
    ax.set_xlabel(r'Target cumulative impact (day$^2$ km$^2$ K$^{-1}$)',fontsize=fs)
    ax.set_ylim(320,420)
    ax.set_xlim(1e5,5e8)
    ax.tick_params(labelsize=fs)
    # calculation of a fit for the EAD and EID curves between 370 and 480 K and addition of this fitto the figure
    slope1,x01 = np.polyfit(thetaxis[95:135],np.log(ff*np.sum(result[hightype]['EAD']['histog'][0:249,95:135],axis=0)),1)
    slope2,x02 = np.polyfit(thetaxis[95:135],np.log(ff*np.sum(result[hightype]['EID']['histog'][0:249,95:135],axis=0)),1)
    print('slopes',1/slope1,1/slope2)
    ax.semilogx(np.exp(x01)*np.exp(slope1*thetaxis[95:135]),thetaxis[95:135],'b',
                        np.exp(x02)*np.exp(slope2*thetaxis[95:135]),thetaxis[95:135],'r',
                        linewidth = 24, alpha = 0.3)
    # superimpose the source curve in separate axis (same log range)
    ax2 = ax.twiny()
    ax2.set_xlabel(r'High cloud distribution (day km$^2$ K$^{-1}$)',fontsize=fs,color='g')
    ax2.semilogx(ff_s*source_dist[hightcore],thetaxis,'g',linewidth=8,alpha=0.5)
    ax2.tick_params(axis='x',labelcolor='g',labelsize=fs)
    ax2.set_xlim(1e4,5e8)
    ax.legend([r'$\it ERA$-$\itI~kin$',r'$\bf ERA$-$\bfI~dia$',
               r'${\it ERA5~kin}$',r'${\bf ERA5~dia}$'],
               fontsize=fs,loc='centerleft')
    # plt.title('Cumulative impact in the AMA region as a function of altitude',fontsize=fs)
    # plot horizontal line at modal max of sources
    ax2.plot([1e4,5e8],[thetaxis[np.argmax(source_dist[hightcore])],
                    thetaxis[np.argmax(source_dist[hightcore])]],'g')
    ax2.annotate(r'$\theta$ = 349.5 K',(1.50e4,344),fontsize=fs)
    print('theta for max source',thetaxis[np.argmax(source_dist[hightcore])])

    if figpdf:
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-age-compar-impact-profile-composit-ACP.png'),bbox_inches='tight',dpi=dpi)
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-age-compar-impact-profile-composit-ACP.pdf'),bbox_inches='tight',dpi=dpi)
    plt.show()

#%% 7bisACP) Plot of the proportion of parcels above a given level relative to 
#the same proportion in the sources
# Calculation of the proportion for the sources
fs = 22
plt.rc('text', usetex=True)

for hightype in hightypes:
    hightcore = hightype+cc
    source_above = np.flip(np.cumsum(np.flip(source_dist[hightcore]))/np.sum(source_dist[hightcore]))
    source_below = np.cumsum(source_dist[hightcore])/np.sum(source_dist[hightcore])
    target_above = {}
    target_below = {}
    fig,ax = plt.subplots(figsize=(9,9))
    for supertype in supertypes:
        target_sum = np.sum(result[hightype][supertype]['histog'][0:249,:])
        target_above[supertype] = np.flip(np.cumsum(np.flip(np.sum(result[hightype][supertype]['histog'][0:249,:],axis=0))))\
            / (target_sum * source_above)
        target_below[supertype] = np.cumsum(np.sum(result[hightype][supertype]['histog'][0:249,:],axis=0))\
            / (target_sum * source_below)
    ax.plot(target_above['EIZ']*target_below['EAZ'],thetaxis,'--r',
            target_above['EID']*target_below['EAD'],thetaxis,'r',
            target_above['EAZ']*target_below['EIZ'],thetaxis,'--b',
            target_above['EAD']*target_below['EID'],thetaxis,'b',
            linewidth=6)
    # plot a vertical line for the unit ratio
    ax.plot(np.ones(len(thetaxis)),thetaxis,'k')
    ax.set_ylabel('target potential temperature (K)',fontsize=fs)
    ax.set_xlabel('target/source cumulative ratio distribution',fontsize=fs)
    ax.set_ylim(320,420)
    ax.set_xlim(0,150)
    ax.tick_params(labelsize=fs)
    # superimpose the source curve
    ax2 = ax.twiny()
    ax2.semilogx(ff_s*source_dist[hightcore],thetaxis,'g',linewidth=8,alpha=0.5)
    ax2.tick_params(axis='x',labelcolor='g',labelsize=fs)
    ax2.set_xlabel('source distribution (day km$^2$ K$^{-1}$)',fontsize=fs,color='g')
    ax2.set_xlim(1e4,5e8)
    ax2.plot([1e4,5e8],[thetaxis[np.argmax(source_dist[hightcore])],
                    thetaxis[np.argmax(source_dist[hightcore])]],'g')
    ax2.annotate(r'$\theta$ = 349.5 K',(15e4,351),fontsize=fs)
    ax.legend([r'\textbf{ERA5 kin}',r'\textit{ERA5 dia}',
                r'\textbf{ERA-I kin}',r'\textit{ERA-I dia}'],
                fontsize=fs,loc='upper right')
    #plt.title(hightype+' cumulative impact ratio as a function of age',fontsize=fs)
    # plot horizontal line at modal max of sources
    #ax.plot([0,14],[thetaxis[np.argmax(source_dist[hightype])],
    #                thetaxis[np.argmax(source_dist[hightype])]],'g')
    if figpdf:
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-age-compar-impact-ratio-composit-ACP.png'),bbox_inches='tight',dpi=dpi)
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-age-compar-impact-ratio-composit-ACP.pdf'),bbox_inches='tight',dpi=dpi)
    plt.show()

#%% 8) analysis of diffusion
alpha = 1/13.3
AA = {'EAD':1.07,'EAZ':1.11,'EIZ':0.98,'EID':1.35}
for supertype in['EAD','EAZ','EID','EIZ']:
    # analysis as a function of the vertical coordinate theta by summing over time
    # Consider the histogram with temperatures between 349.5 and 414.5 K
    hht = result['sh'][supertype]['histog'][0:249,74:140].copy()
    thets = thetaxis[74:140]
    # sum over time
    sst = np.sum(hht,axis=0)
    # max impact along the time axis (plotted below)
    hhtmax = np.max(hht,axis=0) 
    # normalizing each histogram for a given theta
    hht /= sst[np.newaxis,:]
    fig = plt.figure(figsize=(12,6))
    plt.subplot(2,4,1)
    # mean age for theta values
    agemean = np.sum(hht*ageaxis[:,np.newaxis],axis=0)
    agemode = ageaxis[np.argmax(hht,axis=0)]
    plt.plot(agemean,thets,agemode,thets)
    plt.ylim(370,400)
    plt.title(supertype+' mean age and mode (t)')
    plt.subplot(2,4,2)
    # variance of the age and linear fit
    var2age = np.sum(hht*ageaxis[:,np.newaxis]**2,axis=0) - agemean**2
    [b,a] = np.polyfit(agemean[10:30],var2age[10:30],1)
    dcor = (0.5*AA[supertype]**2 * b)/(1 - 2*alpha*b)
    print('diff1 '+supertype,0.5*b,dcor)
    plt.plot(agemean,var2age,agemean,a + b*agemean)
    plt.title(supertype+' age: var vs mean' )
    plt.subplot(2,4,3)
    tags=[5,10,15,20,25,30,35,40]
    for tag in tags:
        plt.plot(ageaxis,hht[:,tag])
    plt.subplot(2,4,4)
    plt.plot(hhtmax[20:50]*np.exp(alpha*agemode[20:50])*np.sqrt(agemode[20:50]),thets[20:50])

    # analysis as a function of time by summing over theta
    # this method does not work possibly for lack of separation in kinematic
    hhp = result['sh'][supertype]['histog'][0:249,74:140].copy()
    thets = thetaxis[74:140]
    ssp = np.sum(hhp,axis=1)
    hhpmax = np.max(hhp,axis=1)
    hhp /= ssp[:,np.newaxis]
    plt.subplot(2,4,5)
    thetmean = np.sum(hhp*thets[np.newaxis,:],axis=1)
    thetmode = thets[np.argmax(hh,axis=1)]
    plt.plot(ageaxis,thetmean,ageaxis,thetmode)
    plt.title(supertype+' mean and mode (thet)')
    plt.subplot(2,4,6)
    var2thet = np.sum(hhp*thets[np.newaxis,:]**2,axis=1) - thetmean**2
    [b,a] = np.polyfit(ageaxis[10:60],var2thet[10:60],1)
    print('diff2 '+supertype,0.5*b)
    plt.plot(ageaxis,var2thet,ageaxis,a + b*ageaxis)
    plt.subplot(2,4,7)
    tags=[5,10,20,30,40,50,60,70,80,100,140,160,180,200,220,240]
    for tag in tags:
        plt.plot(hhp[tag,:],thets)
    plt.subplot(2,4,8)
    print('hhpmax0 '+supertype,hhpmax[0])
    plt.plot(ageaxis,hhpmax*np.exp(alpha*ageaxis)*np.sqrt(ageaxis))
    if figpdf:
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-'+supertype+'-diffus-anal-ACP.png'),bbox_inches='tight',dpi=dpi)
        plt.savefig(os.path.join(forw_dir,'figs',hightype+'-'+supertype+'-diffus-anal-ACP.pdf'),bbox_inches='tight',dpi=dpi)
    plt.show()