# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 20:14:01 2023

@author: bilal
"""

from serial import *
from time import sleep
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as wgt
import os


def InitializeGUI(acquisition_time):
    
    plt.rcParams.update({
    "lines.color": "0.5",
    "patch.edgecolor": "0.5",
    "text.color": "0.95",
    "axes.facecolor": "0.5",
    "axes.edgecolor": "0.5",
    "axes.labelcolor": "0.5",
    "xtick.color": "white",
    "ytick.color": "white",
    "grid.color": "lightgray",
    "figure.facecolor": "0.1",
    "figure.edgecolor": "0.1",
    "savefig.facecolor": "0.1",
    "savefig.edgecolor": "0.1"})
    
    fig, ((ax1, ax2),(ax3, ax4)) = plt.subplots(nrows = 2, ncols = 2, figsize = (14,8), sharex = True)
    
    b1ax = plt.axes([0.02, 0.93, 0.12, 0.045])
    screenshot_button = wgt.Button(b1ax, "Capture Screen", color="grey", hovercolor="#05b5fa")
    screenshot_button.on_clicked(ScreenCapture)
    
    b2ax = plt.axes([0.15, 0.93, 0.06, 0.045])
    stop_button = wgt.Button(b2ax, "Stop", color="grey", hovercolor="#05b5fa")
    stop_button.on_clicked(Stop)
    
    b3ax = plt.axes([0.22, 0.93, 0.14, 0.045])
    acquire_button = wgt.Button(b3ax, "Acquire data: "+str(acquisition_time)+"s", color="grey", hovercolor="#05b5fa")
    acquire_button.on_clicked(AcquireTrigger)
    
    axes = [ax1, ax2, ax3, ax4]
    buttons = [screenshot_button, stop_button, acquire_button] 
    
    return axes, buttons

def GetCounts(s, exp_rate = 40000):
    data = s.read(10)
    # print(s.in_waiting)
    counts = np.array([data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8]])
    for i in range(exp_rate-1):
        data = s.read(10)
        counts = counts + np.array([data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8]])
    return counts

def CollectData(s, acquisition_time, acq_rate):
    
    print('\nData collection request accepted. Collecting data for ' + str(acquisition_time) + ' seconds.')
    
    data = np.zeros((acquisition_time * acq_rate, 9)) # Empty array for data storage
    first_ack = True
    
    global stop_flag
    
    for j in range(acquisition_time * acq_rate):
        
        if stop_flag:
            raise Exception
        
        if first_ack:     
            b3ax = plt.axes([0.22, 0.93, 0.14, 0.045])
            acquire_button = wgt.Button(b3ax, "Acquiring data", color="blue", hovercolor="grey")
            first_ack = False
            plt.pause(0.0001)
            
        if (j == acquisition_time * acq_rate - 1):
            
            data[j] = GetCounts(s, int(40000/acq_rate))
            global acquire
            acquire = 0
            continue
            
        if j % acq_rate == 0:
            print("Buffer:", s.in_waiting, "Time:", j/acq_rate)
            
        data[j] = GetCounts(s, int(40000/acq_rate))
        
    return data

def FindHeader(s):
    for i in range(1000):
        try_head = s.read(1)
        if try_head[0] == 47:
            print("\nHeader found, initiating GUI.")
            return True
    print("\nHeader not found. Exiting.")
    return False

# def DisplayAcqSuccess(acquisition_time, acquisition_number):    

#     b4ax = plt.axes([0.37, 0.93, 0.16, 0.045])
#     display = wgt.Button(b4ax, "  "+str(acquisition_time)+"s | data"+str(acquisition_number)+" saved", color="0.2", hovercolor="0.2")
#     b3ax = plt.axes([0.22, 0.93, 0.14, 0.045])
#     acquire_button = wgt.Button(b3ax, "Acquire data: "+str(acquisition_time)+"s", color="grey", hovercolor="#05b5fa")
#     acquire_button.on_clicked(AcquireTrigger)
#     print("\nAcquisition no.", acquisition_number, "completed.")
#     plt.pause(0.001)

def UpdateGUI(indiv_counts, axes, time_axis): 
    
    axes[0].cla()
    axes[1].cla()
    axes[2].cla()
    axes[3].cla()
    
    axes[0].plot(time_axis, indiv_counts["A"], color = "#45fc03", label = "A")
    axes[0].plot(time_axis, indiv_counts["AP"], color = "#05b5fa", label = "A'")
    axes[0].text(time_axis[-1], indiv_counts["A"][-1], indiv_counts["A"][-1], fontsize = 20)
    axes[0].text(time_axis[-1], indiv_counts["AP"][-1], indiv_counts["AP"][-1], fontsize = 20)

    axes[1].plot(time_axis, indiv_counts["B"], color = "#45fc03", label = "B")
    axes[1].plot(time_axis, indiv_counts["BP"], color = "#05b5fa", label = "B'")
    axes[1].text(time_axis[-1], indiv_counts["B"][-1], indiv_counts["B"][-1], fontsize = 20)
    axes[1].text(time_axis[-1], indiv_counts["BP"][-1], indiv_counts["BP"][-1], fontsize = 20)

    axes[2].plot(time_axis, indiv_counts["AB"], color = "#701c8c", label = "AB")
    axes[2].plot(time_axis, indiv_counts["ABP"], color = "#FFD700", label = "AB'")
    axes[2].text(time_axis[-1], indiv_counts["AB"][-1], indiv_counts["AB"][-1], fontsize = 20) # - indiv_counts["AB"][-1]*0.018 + indiv_counts["APBP"][-1]*0.077
    axes[2].text(time_axis[-1], indiv_counts["ABP"][-1], indiv_counts["ABP"][-1], fontsize = 20)

    axes[3].plot(time_axis, indiv_counts["APB"], color = "#701c8c", label = "A'B")
    axes[3].plot(time_axis, indiv_counts["APBP"], color = "#FFD700", label = "A'B'")
    axes[3].plot(time_axis, indiv_counts["ABBP"], color = "#FD0E35", label = "ABB'")        
    axes[3].text(time_axis[-1], indiv_counts["APB"][-1], indiv_counts["APB"][-1], fontsize = 20)
    axes[3].text(time_axis[-1], indiv_counts["APBP"][-1], indiv_counts["APBP"][-1], fontsize = 20) # + indiv_counts["AB"][-1]*0.018 - indiv_counts["APBP"][-1]*0.077 
    
    axes[0].legend(loc = 'upper left')
    axes[0].set_title("Counts against time")
    axes[0].set_ylabel("Counts")

    axes[1].legend(loc = 'upper left')
    axes[1].set_title("Counts against time")

    axes[2].legend(loc = 'upper left')
    axes[2].set_xlabel("Time(s)")
    axes[2].set_ylabel("Counts")

    axes[3].legend(loc = 'upper left')
    axes[3].set_xlabel("Time(s)")
    
    plt.pause(0.001)

def ScreenCapture(val): # Button-triggered function to save the current screen.
    plt.savefig("screenshot")
    
def Stop(val):  # Button-triggered function to safely close the program.
    global stop_flag
    stop_flag = True

def AcquireTrigger(val): # Button-triggered function to start data collection. 
    global acquire    
    acquire = True

def RawDataToDict(counts): # Helper function.
    
    indiv_counts = {}
    
    indiv_counts["A"] = counts[:, 0]
    indiv_counts["B"] = counts[:, 1]
    indiv_counts["BP"] = counts[:, 2]
    indiv_counts["AP"] = counts[:, 3]
    indiv_counts["AB"] = counts[:, 4]
    indiv_counts["ABP"] = counts[:, 5]
    indiv_counts["APB"] = counts[:, 6]
    indiv_counts["APBP"] = counts[:, 7]
    indiv_counts["ABBP"] = counts[:, 8]
    
    return indiv_counts

def PhotoDetectionCounter(s, acquisition_time, acquisition_number, acq_rate, step_size): # The main function.

    global acquire
    global stop_flag
    stop_flag = False
    acquire = False        

    
        
    if FindHeader(s) == False:
        return
    
    time_axis = np.array([1])
    tic = 1
    
    acq_rate = 100 # Collecting this many data samples per second while saving data.    
    
    axes, buttons = InitializeGUI(acquisition_time)
    
    counts = [GetCounts(s, 40000)]
    
    for i in range(120):
        
        if stop_flag:
            raise Exception
        
        tic += 1
        time_axis= np.append(time_axis, tic)
    
        counts = np.append(counts, [GetCounts(s, 40000)], axis = 0)
        indiv_counts = RawDataToDict(counts)
        
        if acquire:
            
            data = CollectData(s, acquisition_time, acq_rate)
            
            b4ax = plt.axes([0.37, 0.93, 0.16, 0.045])
            display = wgt.Button(b4ax, "  "+str(acquisition_time)+"s | data"+str(acquisition_number)+" saved", color="0.2", hovercolor="0.2")
            b3ax = plt.axes([0.22, 0.93, 0.14, 0.045])
            acquire_button = wgt.Button(b3ax, "Acquire data: "+str(acquisition_time)+"s", color="grey", hovercolor="#05b5fa")
            acquire_button.on_clicked(AcquireTrigger)
            print("\nAcquisition no.", acquisition_number, "completed.")
            plt.pause(0.001)
            
            np.savetxt("data"+str(acquisition_number)+".txt", data)
            acquisition_number += step_size
            
            acquire = False
            
        UpdateGUI(indiv_counts, axes, time_axis)


    while True:
        
        if stop_flag:
            plt.close('all')
            s.close()
            return
        
        tic += 1
        time_axis= np.delete(time_axis, 0)
        time_axis= np.append(time_axis, tic)
        
        counts = np.delete(counts, 0, axis = 0)
        counts = np.append(counts, [GetCounts(s, 40000)], axis = 0)
        indiv_counts = RawDataToDict(counts)
        
        if acquire:
            
            data = CollectData(s, acquisition_time, acq_rate)
            
            b4ax = plt.axes([0.37, 0.93, 0.16, 0.045])
            display = wgt.Button(b4ax, "  "+str(acquisition_time)+"s | data"+str(acquisition_number)+" saved", color="0.2", hovercolor="0.2")
            b3ax = plt.axes([0.22, 0.93, 0.14, 0.045])
            acquire_button = wgt.Button(b3ax, "Acquire data: "+str(acquisition_time)+"s", color="grey", hovercolor="#05b5fa")
            acquire_button.on_clicked(AcquireTrigger)
            print("\nAcquisition no.", acquisition_number, "completed.")
            plt.pause(0.001)
            
            np.savetxt("data"+str(acquisition_number)+".txt", data)
            acquisition_number += step_size
                                  
            acquire = False
            
        UpdateGUI(indiv_counts, axes, time_axis)
       
    return

try:
    
    acquisition_time = 20 # Time interval for data collction.
    acquisition_number = 0 # "acquisition_number".txt will be saved as the first file.
    acq_rate = 1 # Precision of data collection. "acq_rate" times per second.
    step_size = 1
    
    s = Serial("COM5", 4000000)
    s.set_buffer_size(10000000)
    print("\nSerial connection established.")
    sleep(0.1)
    if s.in_waiting == 0:
        print("\nNo data incoming. Closing port.")
        raise Exception("\nNo data incoming. COM connection terminated.")
    
    PhotoDetectionCounter(s, acquisition_time, acquisition_number, acq_rate, step_size)
    
except Exception:
    print("\nStop request called. Exitting.")
    plt.close('all')
    s.close()
else:
    print("\nAn error caused program termination.")
    plt.close('all')
    s.close()