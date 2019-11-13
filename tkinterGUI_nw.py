from tkinter import *
from tkinter import ttk
import tkinter.filedialog as filedialog
from tkinter import messagebox

from PIL import Image,ImageDraw,ImageFont
from PIL import ImageTk,ImageGrab
import cv2
from skimage import filters
#import rasterio
import matplotlib.pyplot as pyplt
from matplotlib.figure import Figure

import numpy as np
import os
import time
import csv

from functools import partial
import sys

import kplus
from sklearn.cluster import KMeans
import tkintercorestat
import tkintercorestat_plot
import tkintercore
import cal_kernelsize
import histograms
import createBins
import axistest

class img():
    def __init__(self,size,bands):
        self.size=size
        self.bands=bands

displayimg={'Origin':None,
            'Gray/NIR':None,
            'ColorIndices':None,
            'Output':None}
cluster=['LabOstu','NDI'] #,'Greenness','VEG','CIVE','MExG','NDVI','NGRDI','HEIGHT']
filenames=[]

Multiimage={}
Multigray={}
Multitype={}
Multiimagebands={}
Multigraybands={}
workbandarray={}
displaybandarray={}
originbandarray={}
clusterdisplay={}
kernersizes={}
multi_results={}
outputimgdict={}
outputimgbands={}

root=Tk()
root.title('GridFree')
root.geometry("")
root.option_add('*tearoff',False)
emptymenu=Menu(root)
root.config(menu=emptymenu)

coinsize=StringVar()
refvar=StringVar()
imgtypevar=StringVar()
edge=StringVar()
kmeans=IntVar()
filedropvar=StringVar()
displaybut_var=StringVar()
bandchoice={}
checkboxdict={}

minipixelareaclass=0

coinbox=None

currentfilename='seedsample.JPG'
currentlabels=None
workingimg=None

boundaryarea=None
outputbutton=None
font=None
reseglabels=None
coindict=None
## Funcitons
refarea=None
originlabels=None
originlabeldict=None
changekmeans=False
convband=None
def distance(p1,p2):
    return np.sum((p1-p2)**2)




def findratio(originsize,objectsize):
    if originsize[0]>objectsize[0] or originsize[1]>objectsize[1]:
        ratio=round(max(originsize[0]/objectsize[0],originsize[1]/objectsize[1]))
    else:
        ratio=round(min(objectsize[0]/originsize[0],objectsize[1]/originsize[1]))
    return ratio


def changedisplayimg(frame,text):
    global displaybut_var
    displaybut_var.set(disbuttonoption[text])
    for widget in frame.winfo_children():
        widget.pack_forget()
    #widget.configure(image=displayimg[text])
    #widget.image=displayimg[text]
    #widget.pack()
    w=displayimg[text]['Size'][1]
    l=displayimg[text]['Size'][0]
    widget.config(width=w,height=l)
    widget.create_image(0,0,image=displayimg[text]['Image'],anchor=NW)
    widget.pack()
    #print('change to '+text)
    #time.sleep(1)

def generatedisplayimg(filename):
    firstimg=Multiimagebands[filename]
    height,width=firstimg.size
    ratio=findratio([height,width],[850,850])
    if height*width<850*850:
        resize=cv2.resize(Multiimage[filename],(int(width*ratio),int(height*ratio)),interpolation=cv2.INTER_LINEAR)
    else:
        resize=cv2.resize(Multiimage[filename],(int(width/ratio),int(height/ratio)),interpolation=cv2.INTER_LINEAR)
    rgbimg=ImageTk.PhotoImage(Image.fromarray(resize.astype('uint8')))
    tempdict={}
    tempdict.update({'Size':resize.shape})
    tempdict.update({'Image':rgbimg})
    displayimg['Origin']=tempdict
    if height*width<850*850:
        resize=cv2.resize(Multigray[filename],(int(width*ratio),int(height*ratio)),interpolation=cv2.INTER_LINEAR)
    else:
        resize=cv2.resize(Multigray[filename],(int(width/ratio),int(height/ratio)),interpolation=cv2.INTER_LINEAR)
    grayimg=ImageTk.PhotoImage(Image.fromarray(resize.astype('uint8')))
    tempdict={}
    tempdict.update({'Size':resize.shape})
    tempdict.update({'Image':grayimg})
    displayimg['Gray/NIR']=tempdict
    tempdict={}
    tempdict.update({'Size':resize.shape})
    if height*width<850*850:
        tempdict.update({'Image':ImageTk.PhotoImage(Image.fromarray(np.zeros((int(height*ratio),int(width*ratio))).astype('uint8')))})
    else:
        tempdict.update({'Image':ImageTk.PhotoImage(Image.fromarray(np.zeros((int(height/ratio),int(width/ratio))).astype('uint8')))})
    displayimg['Output']=tempdict
    tempband=np.zeros((displaybandarray[filename]['LabOstu'].shape))
    tempband=tempband+displaybandarray[filename]['LabOstu']
    ratio=findratio([tempband.shape[0],tempband.shape[1]],[850,850])
    if tempband.shape[0]*tempband.shape[1]<850*850:
        tempband=cv2.resize(ratio,(int(tempband.shape[1]*ratio),int(tempband.shape[0]*ratio)),interpolation=cv2.INTER_LINEAR)
    else:
        tempband=cv2.resize(ratio,(int(tempband.shape[1]/ratio),int(tempband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
    pyplt.imsave('displayimg.png',tempband)
    indimg=cv2.imread('displayimg.png')
    tempdict={}
    tempdict.update({'Size':tempband.shape})
    tempdict.update({'Image':ImageTk.PhotoImage(Image.fromarray(indimg))})
    displayimg['ColorIndices']=tempdict


def Open_File(filename):   #add to multi-image,multi-gray  #call band calculation
    global Multiimage,Multigray,Multitype,Multiimagebands,Multigraybands
    try:
        Filersc=cv2.imread(filename,flags=cv2.IMREAD_ANYCOLOR)
        height,width,channel=np.shape(Filersc)
        Filesize=(height,width)
        RGBfile=cv2.cvtColor(Filersc,cv2.COLOR_BGR2RGB)
        Multiimage.update({filename:RGBfile})
        Grayfile=cv2.cvtColor(Filersc,cv2.COLOR_BGR2Lab)
        Grayfile=cv2.cvtColor(Grayfile,cv2.COLOR_BGR2GRAY)
        #Grayfile=cv2.GaussianBlur(Grayfile,(3,3),cv2.BORDER_DEFAULT)
        #ostu=filters.threshold_otsu(Grayfile)
        #Grayfile=Grayfile.astype('float32')
        #Grayfile=Grayfile/ostu
        Grayimg=img(Filesize,Grayfile)
        RGBbands=np.zeros((channel,height,width))
        for j in range(channel):
            band=RGBfile[:,:,j]
            band=np.where(band==0,1e-6,band)
            #ostu=filters.threshold_otsu(band)
            #band=band/ostu
            RGBbands[j,:,:]=band
        RGBimg=img(Filesize,RGBbands)
        tempdict={filename:RGBimg}
        Multiimagebands.update(tempdict)
        tempdict={filename:Grayfile}
        Multigray.update(tempdict)
        tempdict={filename:0}
        Multitype.update(tempdict)
        tempdict={filename:Grayimg}
        Multigraybands.update(tempdict)

    except:
        messagebox.showerror('Invalid Filename','Cannot open '+filename)
        return
    filenames.append(filename)

def commentoutrasterio():
    '''
    except:
        try:
            Filersc=rasterio.open(filename)
            height=Filersc.height
            width=Filersc.width
            channel=Filersc.count
            print(Filersc)
            Filebands=np.zeros((3,height,width))
            imagebands=np.zeros((height,width,3))
            grayimg=np.zeros((height,width,3))
            graybands=np.zeros((3,height,width))
            Filesize=(height,width)
            for j in range(channel):
                band=Filersc.read(j+1)
                if j<3:
                    imagebands[:,:,j]=band
                    band = np.where((band == 0)|(band==-10000) | (band==-9999), 1e-6, band)
                    Filebands[j,:,:]=band
                else:
                    grayimg[:,:,j-3]=band
                    band = np.where((band == 0)|(band==-10000) | (band==-9999), 1e-6, band)
                    graybands[j-3,:,:]=band

            Fileimg=img(Filesize,Filebands)
            tempdict={filename:imagebands}
            Multiimage.update(tempdict)
            tempdict={filename:Fileimg}
            Multiimagebands.update(tempdict)
            tempdict={filename:2}
            Multitype.update(tempdict)
            Grayim=img(Filesize,graybands)
            tempdict={filename:grayimg}
            Multigray.update(tempdict)
            tempdict={filename:Grayim}
            Multigraybands.update(tempdict)
            print(Filebands)
    '''
    pass

def Open_Multifile():
    global Multiimage,Multigray,Multitype,Multiimagebands,changefileframe,imageframe,Multigraybands,filenames
    global changefiledrop,filedropvar,originbandarray,displaybandarray,clusterdisplay,currentfilename,resviewframe
    global refsubframe,outputbutton,reseglabels,refbutton,figcanvas,loccanvas,originlabels,changekmeans,refarea
    global originlabeldict,convband

    MULTIFILES=filedialog.askopenfilenames()
    if len(MULTIFILES)>0:
        Multiimage={}
        Multigray={}
        Multitype={}
        Multiimagebands={}
        Multigraybands={}
        filenames=[]
        originbandarray={}
        displaybandarray={}
        clusterdisplay={}
        reseglabels=None
        originlabels=None
        originlabeldict=None
        changekmeans=True
        convband=None
        refvar.set('0')
        kmeans.set('2')
        refarea=None
        if 'NDI' in bandchoice:
            bandchoice['NDI'].set('1')
        if 'NDVI' in bandchoice:
            bandchoice['NDVI'].set('1')
        refbutton.config(state=DISABLED)
        figcanvas.delete(ALL)
        #loccanvas=None
        for widget in refsubframe.winfo_children():
            widget.config(state=DISABLED)
        #for widget in resviewframe.winfo_children():
        #    widget.config(state=DISABLED)
        if outputbutton is not None:
            outputbutton.config(state=DISABLED)
        for i in range(len(MULTIFILES)):
            Open_File(MULTIFILES[i])
            singleband(MULTIFILES[i])
        for widget in changefileframe.winfo_children():
            widget.pack_forget()
        filedropvar.set(filenames[0])
        changefiledrop=OptionMenu(changefileframe,filedropvar,*filenames,command=partial(changeimage,imageframe))
        changefiledrop.pack()
        #singleband(filenames[0])
        generatedisplayimg(filenames[0])
        currentfilename=filenames[0]
        for i in range(len(cluster)):
            bandchoice[cluster[i]].set('')
        #changedisplayimg(imageframe,'Origin')
        kmeans.set(2)
        reshapemodified_tif=np.zeros((displaybandarray[currentfilename]['LabOstu'].shape[0]*displaybandarray[currentfilename]['LabOstu'].shape[1],1))
        colordicesband=kmeansclassify(['LabOstu'],reshapemodified_tif)
        generateimgplant(colordicesband)
        changedisplayimg(imageframe,'Origin')
        bandchoice['LabOstu'].set('1')




def workbandsize(item):
    pass

def singleband(file):
    global displaybandarray,originbandarray
    bands=Multigraybands[file].bands
    bandsize=Multigraybands[file].size
    try:
        channel,height,width=bands.shape
    except:
        channel=0
    if channel>1:
        bands=bands[0,:,:]
    bands=cv2.GaussianBlur(bands,(3,3),cv2.BORDER_DEFAULT)
    ostu=filters.threshold_otsu(bands)
    bands=bands.astype('float32')
    bands=bands/ostu
    #display purpose
    if imgtypevar.get()=='0':
        if bandsize[0]*bandsize[1]>2000*2000:
            ratio=findratio([bandsize[0],bandsize[1]],[2000,2000])
        else:
            ratio=1
    if imgtypevar.get()=='1':
        if bandsize[0]*bandsize[1]>1000*1000:
            ratio=findratio([bandsize[0],bandsize[1]],[600,600])
        else:
            #ratio=findratio([bandsize[0],bandsize[1]],[500,500])
            #ratio=float(1/ratio)
            ratio=1
    originbands={}
    displays={}
    if 'LabOstu' not in originbands:
        originbands.update({'LabOstu':bands})
        displaybands=cv2.resize(bands,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #displaybands=displaybands.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        #kernel=np.ones((2,2),np.float32)/4
        #displaybands=np.copy(bands)
        displays.update({'LabOstu':displaybands})
        #displaybandarray.update({'LabOstu':cv2.filter2D(displaybands,-1,kernel)})
    bands=Multiimagebands[file].bands
    for i in range(3):
        bands[i,:,:]=cv2.GaussianBlur(bands[i,:,:],(3,3),cv2.BORDER_DEFAULT)
    NDI=128*((bands[1,:,:]-bands[0,:,:])/(bands[1,:,:]+bands[0,:,:])+1)
    tempdict={'NDI':NDI}
    if 'NDI' not in originbands:
        originbands.update(tempdict)
        displaybands=cv2.resize(NDI,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #displaybands=np.copy(NDI)
        #kernel=np.ones((2,2),np.float32)/4
        #displaydict={'NDI':cv2.filter2D(displaybands,-1,kernel)}
        displaydict={'NDI':displaybands}
        #displaydict=displaydict.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        displays.update(displaydict)

    Red=bands[0,:,:]
    Green=bands[1,:,:]
    Blue=bands[2,:,:]
    tempdict={'Band1':Red}
    if 'Band1' not in originbands:
        originbands.update(tempdict)
        image=cv2.resize(Red,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        displaydict={'Band1':image}
        displays.update(displaydict)
    tempdict={'Band2':Green}
    if 'Band2' not in originbands:
        originbands.update(tempdict)
        image=cv2.resize(Red,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        displaydict={'Band2':image}
        displays.update(displaydict)
    tempdict={'Band3':Blue}
    if 'Band3' not in originbands:
        originbands.update(tempdict)
        image=cv2.resize(Red,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        displaydict={'Band3':image}
        displays.update(displaydict)
    Greenness = bands[1, :, :] / (bands[0, :, :] + bands[1, :, :] + bands[2, :, :])
    tempdict = {'Greenness': Greenness}
    if 'Greenness' not in originbandarray:
        originbands.update(tempdict)
        image=cv2.resize(Greenness,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #image=image.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        displaydict={'Greenness':image}
        #displaybandarray.update(worktempdict)
        displays.update(displaydict)
    VEG=bands[1,:,:]/(np.power(bands[0,:,:],0.667)*np.power(bands[2,:,:],(1-0.667)))
    tempdict={'VEG':VEG}
    if 'VEG' not in originbandarray:
        originbands.update(tempdict)
        image=cv2.resize(VEG,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        kernel=np.ones((4,4),np.float32)/16
        #displaybandarray.update({'LabOstu':})
        #image=image.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        worktempdict={'VEG':cv2.filter2D(image,-1,kernel)}
        displays.update(worktempdict)
    CIVE=0.441*bands[0,:,:]-0.811*bands[1,:,:]+0.385*bands[2,:,:]+18.78745
    tempdict={'CIVE':CIVE}
    if 'CIVE' not in originbandarray:
        originbands.update(tempdict)
        image=cv2.resize(CIVE,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #image=image.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        worktempdict={'CIVE':image}
        displays.update(worktempdict)
    MExG=1.262*bands[1,:,:]-0.884*bands[0,:,:]-0.311*bands[2,:,:]
    tempdict={'MExG':MExG}
    if 'MExG' not in originbandarray:
        originbands.update(tempdict)
        image=cv2.resize(MExG,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #image=image.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        worktempdict={'MExG':image}
        displays.update(worktempdict)
    NDVI=(bands[0,:,:]-bands[2,:,:])/(bands[0,:,:]+bands[2,:,:])
    tempdict={'NDVI':NDVI}
    if 'NDVI' not in originbandarray:
        originbands.update(tempdict)
        image=cv2.resize(NDVI,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #image=image.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        worktempdict={'NDVI':image}
        displays.update(worktempdict)
    NGRDI=(bands[1,:,:]-bands[0,:,:])/(bands[1,:,:]+bands[0,:,:])
    tempdict={'NGRDI':NGRDI}
    if 'NGRDI' not in originbandarray:
        originbands.update(tempdict)
        image=cv2.resize(NGRDI,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #image=image.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        worktempdict={'NGRDI':image}
        displays.update(worktempdict)
    if channel>=1:
        nirbands=Multigraybands[file].bands
        NDVI=(nirbands[0,:,:]-bands[1,:,:])/(nirbands[0,:,:]+bands[1,:,:])
        tempdict={'NDVI':NDVI}
        #if 'NDVI' not in originbandarray:
        originbands.update(tempdict)
        image=cv2.resize(NDVI,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        #image=image.reshape((int(bandsize[1]/ratio),int(bandsize[0]/ratio),3))
        worktempdict={'NDVI':image}
        displays.update(worktempdict)
    if channel==3:
        bands=Multigraybands[file].bands
        Height=bands[2,:,:]
        tempdict={'HEIGHT':Height}
        if 'HEIGHT' not in originbandarray:
            originbands.update(tempdict)
            image=cv2.resize(Height,(int(bandsize[1]/ratio),int(bandsize[0]/ratio)),interpolation=cv2.INTER_LINEAR)
            worktempdict={'HEIGHT':image}
            displays.update(worktempdict)
    else:
        originbandarray.update({'HEIGHT':np.zeros(bandsize)})
        image=np.zeros((int(bandsize[0]/ratio),int(bandsize[0]/ratio)))
        worktempdict.update({'HEIGHT':image})
        displays.update(worktempdict)


    displaybandarray.update({file:displays})
    originbandarray.update({file:originbands})







def Band_calculation():
    global originbandarray,workbandarray
    originbandarray={}
    workbandarray={}
    for file in filenames:
        singleband(file)




def changeimage(frame,filename):
    global clusterdisplay,currentfilename,resviewframe
    clusterdisplay={}
    currentfilename=filename
    print(filename)
    generatedisplayimg(filename)
    changedisplayimg(frame,'Origin')
    for key in cluster:
        tuplist=[]
        for i in range(len(cluster)):
            tuplist.append('')
        tup=tuple(tuplist)
        bandchoice[key].set(tup)
    #for key in cluster:
    #    ch=ttk.Checkbutton(contentframe,text=key,variable=bandchoice[key],command=changecluster)#,command=partial(autosetclassnumber,clusternumberentry,bandchoice))
    #    ch.pack()

    if filename in multi_results.keys():
        for widget in resviewframe.winfo_children():
            widget.pack_forget()
        iternum=len(list(multi_results[filename][0].keys()))
        itervar=IntVar()
        itervar.set(iternum)
        resscaler=Scale(resviewframe,from_=1,to=iternum,tickinterval=1,length=220,orient=HORIZONTAL,variable=itervar,command=partial(changeoutputimg,filename))
        resscaler.pack()
        outputbutton=Button(resviewframe,text='Export Results',command=partial(export_result,itervar))
        outputbutton.pack()


def generateplant(checkbox,bandchoice):
    keys=bandchoice.keys()
    choicelist=[]
    imageband=np.zeros((displaybandarray['LabOstu'].shape))
    for key in keys:
        tup=bandchoice[key].get()
        if '1' in tup:
            choicelist.append(key)
            imageband=imageband+displaybandarray[key]
    if len(choicelist)==0:
        messagebox.showerror('No Indices is selected',message='Please select indicies to do KMeans Classification.')

        return

    if int(kmeans.get())==1:
        ratio=findratio([imageband.shape[0],imageband.shape[1]],[850,850])
        imageband=cv2.resize(imageband,(int(imageband.shape[1]/ratio),int(imageband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        imageband=np.where(imageband==1,2,imageband)
        temprgb=np.zeros((imageband.shape[0],imageband.shape[1],3))
        pyplt.imsave('displayimg.png',imageband)
        indimg=cv2.imread('displayimg.png')
        displayimg['ColorIndices']['Image']=ImageTk.PhotoImage(Image.fromarray(indimg))
        changedisplayimg(imageframe,'ColorIndices')

    else:
        if ''.join(choicelist) in clusterdisplay:
            tempdict=clusterdisplay[''.join(choicelist)]
            if kmeans.get() in tempdict:
                displaylabels=tempdict[kmeans.get()]
            else:
                reshapemodified_tif=np.zeros((displaybandarray['LabOstu'].shape[0]*displaybandarray['LabOstu'].shape[1],len(choicelist)))
                displaylabels=kmeansclassify(choicelist,reshapemodified_tif)
            generateimgplant(displaylabels)
            return
        else:
            reshapemodified_tif=np.zeros((displaybandarray['LabOstu'].shape[0]*displaybandarray['LabOstu'].shape[1],len(choicelist)))
            displaylabels=kmeansclassify(choicelist,reshapemodified_tif)
            generateimgplant(displaylabels)


def generatecheckbox(frame,classnum):
    global checkboxdict
    for widget in frame.winfo_children():
        widget.pack_forget()
    checkboxdict={}
    for i in range(10):
        dictkey=str(i+1)
        tempdict={dictkey:Variable()}
        tempdict[dictkey].set('0')
        checkboxdict.update(tempdict)
        ch=Checkbutton(checkboxframe,text=dictkey,variable=checkboxdict[dictkey],command=partial(changecluster,''))
        if i+1>int(kmeans.get()):
            ch.config(state=DISABLED)
        ch.pack(side=LEFT)
        #if i==0:
        #    ch.invoke()
    #for i in range(int(classnum)):
    #    dictkey='class '+str(i+1)
    #    tempdict={dictkey:Variable()}
    #    checkboxdict.update(tempdict)
        #ch=ttk.Checkbutton(frame,text=dictkey,command=partial(generateplant,checkboxdict,bandchoice,classnum),variable=checkboxdict[dictkey])
    #    ch=ttk.Checkbutton(frame,text=dictkey,command=changecluster,variable=checkboxdict[dictkey])
    #    ch.grid(row=int(i/3),column=int(i%3))
    #    if i==minipixelareaclass:
    #        ch.invoke()

def generateimgplant(displaylabels):
    global currentlabels,changekmeans
    keys=checkboxdict.keys()
    plantchoice=[]
    for key in keys:
        plantchoice.append(checkboxdict[key].get())
    tempdisplayimg=np.zeros((displaybandarray[currentfilename]['LabOstu'].shape))
    for i in range(len(plantchoice)):
        tup=plantchoice[i]
        if '1' in tup:
            tempdisplayimg=np.where(displaylabels==i,1,tempdisplayimg)
    currentlabels=np.copy(tempdisplayimg)
    ratio=findratio([tempdisplayimg.shape[0],tempdisplayimg.shape[1]],[850,850])
    if tempdisplayimg.shape[0]*tempdisplayimg.shape[1]<850*850:
        tempdisplayimg=cv2.resize(tempdisplayimg,(int(tempdisplayimg.shape[1]*ratio),int(tempdisplayimg.shape[0]*ratio)))
    else:
        tempdisplayimg=cv2.resize(tempdisplayimg,(int(tempdisplayimg.shape[1]/ratio),int(tempdisplayimg.shape[0]/ratio)))
    pyplt.imsave('displayimg.png',tempdisplayimg)
    #bands=Image.fromarray(tempdisplayimg)
    #bands=bands.convert('L')
    #bands.save('displayimg.png')
    indimg=cv2.imread('displayimg.png')
    tempdict={}
    tempdict.update({'Size':tempdisplayimg.shape})
    tempdict.update({'Image':ImageTk.PhotoImage(Image.fromarray(indimg))})
    displayimg['ColorIndices']=tempdict
    changedisplayimg(imageframe,'ColorIndices')
    changekmeans=True


def kmeansclassify(choicelist,reshapedtif):
    global clusterdisplay,minipixelareaclass
    if int(kmeans.get())==0:
        return
    for i in range(len(choicelist)):
            tempband=displaybandarray[currentfilename][choicelist[i]]
            #tempband=cv2.resize(tempband,(450,450),interpolation=cv2.INTER_LINEAR)
            reshapedtif[:,i]=tempband.reshape(tempband.shape[0]*tempband.shape[1],1)[:,0]
    clf=KMeans(n_clusters=int(kmeans.get()),init='k-means++',n_init=10,random_state=0)
    tempdisplayimg=clf.fit_predict(reshapedtif)
    displaylabels=tempdisplayimg.reshape(displaybandarray[currentfilename]['LabOstu'].shape)
    pixelarea=1.0
    for i in range(int(kmeans.get())):
        pixelloc=np.where(displaylabels==i)
        pixelnum=len(pixelloc[0])
        temparea=float(pixelnum/(displaylabels.shape[0]*displaylabels.shape[1]))
        if temparea<pixelarea:
            minipixelareaclass=i
            pixelarea=temparea
    if kmeans.get() not in displaylabels:
        tempdict={kmeans.get():displaylabels}
        clusterdisplay.update({''.join(choicelist):tempdict})
    return displaylabels

def changecluster(event):
    keys=bandchoice.keys()
    choicelist=[]
    imageband=np.zeros((displaybandarray[currentfilename]['LabOstu'].shape))
    for key in keys:
        tup=bandchoice[key].get()
        if '1' in tup:
            choicelist.append(key)
            imageband=imageband+displaybandarray[currentfilename][key]
    if len(choicelist)==0:
        messagebox.showerror('No Indices is selected',message='Please select indicies to do KMeans Classification.')
        tempband=np.copy(displaybandarray[currentfilename]['LabOstu'])
        ratio=findratio([tempband.shape[0],tempband.shape[1]],[850,850])
        tempband=cv2.resize(tempband,(int(tempband.shape[1]/ratio),int(tempband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        pyplt.imsave('displayimg.png',tempband)
        indimg=cv2.imread('displayimg.png')
        #indimg=Image.open('displayimg.png')
        tempdict={}
        tempdict.update({'Size':tempband.shape})
        tempdict.update({'Image':ImageTk.PhotoImage(Image.fromarray(indimg))})
        displayimg['ColorIndices']=tempdict
        changedisplayimg(imageframe,'ColorIndices')
        return
    if int(kmeans.get())==1:
        tempband=np.copy(imageband)
        ratio=findratio([tempband.shape[0],tempband.shape[1]],[850,850])
        tempband=cv2.resize(tempband,(int(tempband.shape[1]/ratio),int(tempband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        pyplt.imsave('displayimg.png',tempband)
        #bands=Image.fromarray(tempband)
        #bands=bands.convert('RGB')
        #bands.save('displayimg.png')
        indimg=cv2.imread('displayimg.png')
        tempdict={}
        tempdict.update({'Size':tempband.shape})
        tempdict.update({'Image':ImageTk.PhotoImage(Image.fromarray(indimg))})
        displayimg['ColorIndices']=tempdict
        changedisplayimg(imageframe,'ColorIndices')
    else:
        if ''.join(choicelist) in clusterdisplay:
            tempdict=clusterdisplay[''.join(choicelist)]
            if kmeans.get() in tempdict:
                displaylabels=tempdict[kmeans.get()]
            else:
                reshapemodified_tif=np.zeros((displaybandarray[currentfilename]['LabOstu'].shape[0]*displaybandarray[currentfilename]['LabOstu'].shape[1],len(choicelist)))
                displaylabels=kmeansclassify(choicelist,reshapemodified_tif)
            generateimgplant(displaylabels)
            return
        else:
            reshapemodified_tif=np.zeros((displaybandarray[currentfilename]['LabOstu'].shape[0]*displaybandarray[currentfilename]['LabOstu'].shape[1],len(choicelist)))
            displaylabels=kmeansclassify(choicelist,reshapemodified_tif)
            generateimgplant(displaylabels)




    print(kmeans.get())
    print(refvar.get())
    print(edge.get())
    print(bandchoice)
    print(checkboxdict)

def showinitcounting(tup):
    global multi_results,kernersizes
    labels=tup[0]
    counts=tup[1]
    colortable=tup[2]
    coinparts=tup[3]
    filename=tup[4]

def showcounting(tup):
    global multi_results,kernersizes#,pixelmmratio,kernersizes
    global font
    labels=tup[0]
    counts=tup[1]
    colortable=tup[2]
    #labeldict=tup[0]
    coinparts=tup[3]
    filename=tup[4]
    #currlabeldict=labeldict['iter'+str(int(itervar)-1)]
    #print(currlabeldict)
    #labels=currlabeldict['labels']
    #counts=currlabeldict['counts']
    #colortable=currlabeldict['colortable']
    uniquelabels=list(colortable.keys())
    originfile,extension=os.path.splitext(filename)
    image=Image.open(filename)
    image=image.resize([labels.shape[1],labels.shape[0]],resample=Image.BILINEAR)
    draw=ImageDraw.Draw(image)
    #font=ImageFont.load_default()
    if labels.shape[1]<850:
        font=ImageFont.truetype('cmb10.ttf',size=16)
    else:
        font=ImageFont.truetype('cmb10.ttf',size=28)
    if len(coinparts)>0:
        tempband=np.zeros(labels.shape)
        coinkeys=coinparts.keys()
        for coin in coinkeys:
            coinlocs=coinparts[coin]
            tempband[coinlocs]=1

    global recborder
    for uni in uniquelabels:
        if uni!=0:
            pixelloc = np.where(labels == uni)
            try:
                ulx = min(pixelloc[1])
            except:
                continue
            uly = min(pixelloc[0])
            rlx = max(pixelloc[1])
            rly = max(pixelloc[0])
            midx = ulx + int((rlx - ulx) / 2)
            midy = uly + int((rly - uly) / 2)
            print(ulx, uly, rlx, rly)
            draw.polygon([(ulx,uly),(rlx,uly),(rlx,rly),(ulx,rly)],outline='red')
            if uni in colortable:
                canvastext = str(colortable[uni])
            else:
                canvastext = 'No label'
            if imgtypevar.get()=='0':
                draw.text((midx-1, midy+1), text=canvastext, font=font, fill='black')
                draw.text((midx+1, midy+1), text=canvastext, font=font, fill='black')
                draw.text((midx-1, midy-1), text=canvastext, font=font, fill='black')
                draw.text((midx+1, midy-1), text=canvastext, font=font, fill='black')
                draw.text((midx,midy),text=canvastext,font=font,fill=(141,2,31,0))


    '''   kernelsize computation
    for uni in uniquelabels:
        if uni !=0:
            pixelloc = np.where(labels == uni)
            try:
                ulx = min(pixelloc[1])
            except:
                continue
            uly = min(pixelloc[0])
            rlx = max(pixelloc[1])
            rly = max(pixelloc[0])
            print(ulx, uly, rlx, rly)
            midx = ulx + int((rlx - ulx) / 2)
            midy = uly + int((rly - uly) / 2)
            length={}
            currborder=tkintercore.get_boundaryloc(labels,uni)
            for i in range(len(currborder[0])):
                for j in range(i+1,len(currborder[0])):
                    templength=float(((currborder[0][i]-currborder[0][j])**2+(currborder[1][i]-currborder[1][j])**2)**0.5)
                    length.update({(i,j):templength})
            sortedlength=sorted(length,key=length.get,reverse=True)
            try:
                topcouple=sortedlength[0]
            except:
                continue
            kernellength=length[topcouple]
            i=topcouple[0]
            j=topcouple[1]
            x0=currborder[1][i]
            y0=currborder[0][i]
            x1=currborder[1][j]
            y1=currborder[0][j]
            #slope=float((y0-y1)/(x0-x1))
            linepoints=[(currborder[1][i],currborder[0][i]),(currborder[1][j],currborder[0][j])]
            #draw.line(linepoints,fill='yellow')
            #points=linepixels(currborder[1][i],currborder[0][i],currborder[1][j],currborder[0][j])

            lengthpoints=cal_kernelsize.bresenhamline(x0,y0,x1,y1)  #x0,y0,x1,y1
            for point in lengthpoints:
                if imgtypevar.get()=='0':
                    draw.point([int(point[0]),int(point[1])],fill='yellow')
            tengentaddpoints=cal_kernelsize.tengentadd(x0,y0,x1,y1,rlx,rly,labels,uni)
            #for point in tengentaddpoints:
                #if int(point[0])>=ulx and int(point[0])<=rlx and int(point[1])>=uly and int(point[1])<=rly:
            #    draw.point([int(point[0]),int(point[1])],fill='green')
            tengentsubpoints=cal_kernelsize.tengentsub(x0,y0,x1,y1,ulx,uly,labels,uni)
            #for point in tengentsubpoints:
            #    draw.point([int(point[0]),int(point[1])],fill='green')
            width=1e10
            pointmatch=[]
            for i in range(len(tengentaddpoints)):
                point=tengentaddpoints[i]
                try:
                    templabel=labels[int(point[1]),int(point[0])]
                except:
                    continue
                if templabel==uni:
                    for j in range(len(tengentsubpoints)):
                        subpoint=tengentsubpoints[j]
                        tempwidth=float(((point[0]-subpoint[0])**2+(point[1]-subpoint[1])**2)**0.5)
                        if tempwidth<width:
                            pointmatch[:]=[]
                            pointmatch.append(point)
                            pointmatch.append(subpoint)
                            width=tempwidth
            if len(pointmatch)>0:
                x0=int(pointmatch[0][0])
                y0=int(pointmatch[0][1])
                x1=int(pointmatch[1][0])
                y1=int(pointmatch[1][1])
                if imgtypevar.get()=='0':
                    draw.line([(x0,y0),(x1,y1)],fill='yellow')
                print('kernelwidth='+str(width*pixelmmratio))
                print('kernellength='+str(kernellength*pixelmmratio))
                #print('kernelwidth='+str(kernelwidth*pixelmmratio))
                tempdict.update({uni:[kernellength,width,kernellength*pixelmmratio,width*pixelmmratio]})


            #print(event.x, event.y, labels[event.x, event.y], ulx, uly, rlx, rly)

            #recborder = canvas.create_rectangle(ulx, uly, rlx, rly, outline='red')
            #drawcontents.append(recborder)
                draw.polygon([(ulx,uly),(rlx,uly),(rlx,rly),(ulx,rly)],outline='red')
                if uni in colortable:
                    canvastext = str(colortable[uni])
                else:
                    canvastext = 'No label'
                #rectext = canvas.create_text(midx, midy, fill='black', font='Times 8', text=canvastext)
                #drawcontents.append(rectext)
                if imgtypevar.get()=='0':
                    draw.text((midx,midy),text=canvastext,font=font,fill='black')
                #trainingdataset.append([originfile+'-training'+extension,'wheat',str(ulx),str(rlx),str(uly),str(rly)])

    kernersizes.update({filename:tempdict})
    '''
    content='item count:'+str(len(uniquelabels))+'\n File: '+filename
    contentlength=len(content)+50
    #rectext=canvas.create_text(10,10,fill='black',font='Times 16',text=content,anchor=NW)
    draw.text((10-1, 10+1), text=content, font=font, fill='black')
    draw.text((10+1, 10+1), text=content, font=font, fill='black')
    draw.text((10-1, 10-1), text=content, font=font, fill='black')
    draw.text((10+1, 10-1), text=content, font=font, fill='black')
    draw.text((10,10),text=content,font=font,fill=(141,2,31,0))
    #image.save(originfile+'-countresult'+extension,"JPEG")
    firstimg=Multigraybands[currentfilename]
    height,width=firstimg.size
    ratio=findratio([height,width],[850,850])
    #if labels.shape[0]*labels.shape[1]<850*850:
    #    disimage=image.resize([int(labels.shape[1]*ratio),int(labels.shape[0]*ratio)],resample=Image.BILINEAR)
    #else:
    #    disimage=image.resize([int(labels.shape[1]/ratio),int(labels.shape[0]/ratio)],resample=Image.BILINEAR)
    if height*width<850*850:
        disimage=image.resize([int(width*ratio),int(height*ratio)],resample=Image.BILINEAR)
    else:
        disimage=image.resize([int(width/ratio),int(height/ratio)],resample=Image.BILINEAR)
    displayoutput=ImageTk.PhotoImage(disimage)
    return displayoutput,image
    #displayimg['Output']=displayoutput
    #changedisplayimg(imageframe,'Output')
    #time.sleep(5)
    #image.show()



def changeoutputimg(file,intnum):
    outputimg=outputimgdict[file]['iter'+str(int(intnum)-1)]
    tempdict={}
    tempdict.update({'Size':displayimg['ColorIndices']['Size']})
    tempdict.update({'Image':outputimg})
    displayimg['Output']=tempdict
    changedisplayimg(imageframe,'Output')

def export_result(iterver):
    files=multi_results.keys()
    path=filedialog.askdirectory()
    for file in files:
        labeldict=multi_results[file][0]
        totalitervalue=len(list(labeldict.keys()))
        #itervalue='iter'+str(int(iterver.get())-1)
        #itervalue='iter'+str(totalitervalue-1)
        #itervalue=int(iterver.get())
        itervalue='iter'+iterver
        print(itervalue)
        print(labeldict)
        labels=labeldict[itervalue]['labels']
        counts=labeldict[itervalue]['counts']
        colortable=labeldict[itervalue]['colortable']

        head_tail=os.path.split(file)
        originfile,extension=os.path.splitext(head_tail[1])
        if len(path)>0:
            imageband=outputimgbands[file][itervalue]
            draw=ImageDraw.Draw(imageband)
            uniquelabels=list(colortable.keys())
            tempdict={}
            for uni in uniquelabels:
                if uni !=0:
                    pixelloc = np.where(labels == uni)
                    try:
                        ulx = min(pixelloc[1])
                    except:
                        continue
                    uly = min(pixelloc[0])
                    rlx = max(pixelloc[1])
                    rly = max(pixelloc[0])
                    print(ulx, uly, rlx, rly)
                    midx = ulx + int((rlx - ulx) / 2)
                    midy = uly + int((rly - uly) / 2)
                    length={}
                    currborder=tkintercore.get_boundaryloc(labels,uni)
                    for i in range(len(currborder[0])):
                        for j in range(i+1,len(currborder[0])):
                            templength=float(((currborder[0][i]-currborder[0][j])**2+(currborder[1][i]-currborder[1][j])**2)**0.5)
                            length.update({(i,j):templength})
                    sortedlength=sorted(length,key=length.get,reverse=True)
                    try:
                        topcouple=sortedlength[0]
                    except:
                        continue
                    kernellength=length[topcouple]
                    i=topcouple[0]
                    j=topcouple[1]
                    x0=currborder[1][i]
                    y0=currborder[0][i]
                    x1=currborder[1][j]
                    y1=currborder[0][j]
                    #slope=float((y0-y1)/(x0-x1))
                    linepoints=[(currborder[1][i],currborder[0][i]),(currborder[1][j],currborder[0][j])]
                    #draw.line(linepoints,fill='yellow')
                    #points=linepixels(currborder[1][i],currborder[0][i],currborder[1][j],currborder[0][j])

                    lengthpoints=cal_kernelsize.bresenhamline(x0,y0,x1,y1)  #x0,y0,x1,y1
                    for point in lengthpoints:
                        if imgtypevar.get()=='0':
                            draw.point([int(point[0]),int(point[1])],fill='yellow')
                    tengentaddpoints=cal_kernelsize.tengentadd(x0,y0,x1,y1,rlx,rly,labels,uni)
                    #for point in tengentaddpoints:
                        #if int(point[0])>=ulx and int(point[0])<=rlx and int(point[1])>=uly and int(point[1])<=rly:
                    #    draw.point([int(point[0]),int(point[1])],fill='green')
                    tengentsubpoints=cal_kernelsize.tengentsub(x0,y0,x1,y1,ulx,uly,labels,uni)
                    #for point in tengentsubpoints:
                    #    draw.point([int(point[0]),int(point[1])],fill='green')
                    width=1e10
                    pointmatch=[]
                    for i in range(len(tengentaddpoints)):
                        point=tengentaddpoints[i]
                        try:
                            templabel=labels[int(point[1]),int(point[0])]
                        except:
                            continue
                        if templabel==uni:
                            for j in range(len(tengentsubpoints)):
                                subpoint=tengentsubpoints[j]
                                tempwidth=float(((point[0]-subpoint[0])**2+(point[1]-subpoint[1])**2)**0.5)
                                if tempwidth<width:
                                    pointmatch[:]=[]
                                    pointmatch.append(point)
                                    pointmatch.append(subpoint)
                                    width=tempwidth
                    if len(pointmatch)>0:
                        x0=int(pointmatch[0][0])
                        y0=int(pointmatch[0][1])
                        x1=int(pointmatch[1][0])
                        y1=int(pointmatch[1][1])
                        if imgtypevar.get()=='0':
                            draw.line([(x0,y0),(x1,y1)],fill='yellow')
                        print('kernelwidth='+str(width*pixelmmratio))
                        print('kernellength='+str(kernellength*pixelmmratio))
                        #print('kernelwidth='+str(kernelwidth*pixelmmratio))
                        tempdict.update({uni:[kernellength,width,kernellength*pixelmmratio,width*pixelmmratio]})


                    #print(event.x, event.y, labels[event.x, event.y], ulx, uly, rlx, rly)

                    #recborder = canvas.create_rectangle(ulx, uly, rlx, rly, outline='red')
                    #drawcontents.append(recborder)

            kernersizes.update({file:tempdict})
            originheight,originwidth=Multigraybands[file].size
            image=imageband.resize([originwidth,originheight],resample=Image.BILINEAR)
            image.save(path+'/'+originfile+'-countresult'+'.png',"PNG")
            originrestoredband=labels
            restoredband=originrestoredband.astype('float32')
            restoredband=cv2.resize(src=restoredband,dsize=(originwidth,originheight),interpolation=cv2.INTER_LINEAR)
            print(restoredband.shape)
            currentsizes=kernersizes[file]
            indicekeys=list(originbandarray[file].keys())
            indeclist=[ 0 for i in range(len(indicekeys)*3)]
            datatable={}
            origindata={}
            for key in indicekeys:
                data=originbandarray[file][key]
                data=data.tolist()
                tempdict={key:data}
                origindata.update(tempdict)
                print(key)
            for uni in colortable:
                print(uni,colortable[uni])
                uniloc=np.where(restoredband==float(uni))
                if len(uniloc)==0 or len(uniloc[1])==0:
                    continue
                smalluniloc=np.where(originrestoredband==uni)
                ulx,uly=min(smalluniloc[1]),min(smalluniloc[0])
                rlx,rly=max(smalluniloc[1]),max(smalluniloc[0])
                width=rlx-ulx
                length=rly-uly
                print(width,length)
                subarea=restoredband[uly:rly+1,ulx:rlx+1]
                subarea=subarea.tolist()
                amount=len(uniloc[0])
                print(amount)
                sizes=currentsizes[uni]
                #templist=[amount,length,width]
                templist=[amount,sizes[0],sizes[1],sizes[2],sizes[3]]
                tempdict={colortable[uni]:templist+indeclist}  #NIR,Redeyes,R,G,B,NDVI,area
                print(tempdict)
                for ki in range(len(indicekeys)):
                    originNDVI=origindata[indicekeys[ki]]
                    print(len(originNDVI),len(originNDVI[0]))
                    pixellist=[]
                    for k in range(len(uniloc[0])):
                        #print(uniloc[0][k],uniloc[1][k])
                        try:
                            tempdict[colortable[uni]][5+ki*3]+=originNDVI[uniloc[0][k]][uniloc[1][k]]
                        except IndexError:
                            print(uniloc[0][k],uniloc[1][k])
                        tempdict[colortable[uni]][6+ki*3]+=originNDVI[uniloc[0][k]][uniloc[1][k]]
                        pixellist.append(originNDVI[uniloc[0][k]][uniloc[1][k]])
                    tempdict[colortable[uni]][ki*3+5]=tempdict[colortable[uni]][ki*3+5]/amount
                    tempdict[colortable[uni]][ki*3+7]=np.std(pixellist)
                datatable.update(tempdict)
            filename=path+'/'+originfile+'-outputdata.csv'
            with open(filename,mode='w') as f:
                csvwriter=csv.writer(f)
                rowcontent=['Index','Plot','Area(#pixel)','Length(#pixel)','Width(#pixel)','Length(mm)','Width(mm)']
                for key in indicekeys:
                    rowcontent.append('avg-'+str(key))
                    rowcontent.append('sum-'+str(key))
                    rowcontent.append('std-'+str(key))
                #csvwriter.writerow(['ID','NIR','Red Edge','Red','Green','Blue','NIRv.s.Green','LabOstu','area(#of pixel)'])
                #csvwriter.writerow(['Index','Plot','Area(#pixels)','avg-NDVI','sum-NDVI','std-NDVI','Length(#pixel)','Width(#pixel)'])#,'#holes'])
                csvwriter.writerow(rowcontent)
                i=1
                for uni in datatable:
                    row=[i,uni]
                    for j in range(len(datatable[uni])):
                        row.append(datatable[uni][j])
                    #row=[i,uni,datatable[uni][0],datatable[uni][1],datatable[uni][2],datatable[uni][5],datatable[uni][3],datatable[uni][4]]#,
                         #datatable[uni][5]]
                    i+=1
                    print(row)
                    csvwriter.writerow(row)
    messagebox.showinfo('Saved',message='Results are saved to '+path)

def single_kmenas(singlebandarray):
    numindec=0
    keys=bandchoice.keys()
    for key in keys:
        tup=bandchoice[key].get()
        if '1' in tup:
            numindec+=1
    reshapeworkimg=np.zeros((singlebandarray[cluster[0]].shape[0]*singlebandarray[cluster[0]].shape[1],numindec))
    j=0
    for i in range(len(cluster)):
        tup=bandchoice[cluster[i]].get()
        if '1' in tup:
            tempband=singlebandarray[cluster[i]]
            reshapeworkimg[:,j]=tempband.reshape(tempband.shape[0]*tempband.shape[1],1)[:,0]
            j+=1
    clusternumber=int(kmeans.get())
    clf=KMeans(n_clusters=clusternumber,init='k-means++',n_init=10,random_state=0)
    labels=clf.fit_predict(reshapeworkimg)
    temptif=labels.reshape(singlebandarray[cluster[0]].shape[0],singlebandarray[cluster[0]].shape[1])
    keys=checkboxdict.keys()
    plantchoice=[]
    for key in keys:
        plantchoice.append(checkboxdict[key].get())
    tempdisplayimg=np.zeros((singlebandarray[cluster[0]].shape))
    #for i in range(len(plantchoice)):
    #    tup=plantchoice[i]
    #    if '1' in tup:
    #        tempdisplayimg=np.where(temptif==i,1,tempdisplayimg)

    pixelarea=1.0
    minipixelareaclass=0
    for i in range(int(kmeans.get())):
        pixelloc=np.where(temptif==i)
        pixelnum=len(pixelloc[0])
        temparea=float(pixelnum/(temptif.shape[0]*temptif.shape[1]))
        if temparea<pixelarea:
            minipixelareaclass=i
            pixelarea=temparea
    tempdisplayimg=np.where(temptif==minipixelareaclass,1,tempdisplayimg)
        #clusterdisplay.update({''.join(choicelist):tempdict})
    #return displaylabels
    return tempdisplayimg



def batchextraction():
    global multi_results
    for file in filenames:
        if file!=currentfilename:
            tempdisplaybands=displaybandarray[file]
            displayband=single_kmenas(tempdisplaybands)
            coin=refvar.get()=='1'
            edgevar=edge.get()=='1'
            if edgevar:
                displayband=removeedge(displayband)
            nonzeros=np.count_nonzero(displayband)
            nonzeroloc=np.where(displayband!=0)
            ulx,uly=min(nonzeroloc[1]),min(nonzeroloc[0])
            rlx,rly=max(nonzeroloc[1]),max(nonzeroloc[0])
            nonzeroratio=float(nonzeros)/((rlx-ulx)*(rly-uly))
            print(nonzeroratio)
            if coin:
                boundaryarea=tkintercorestat.boundarywatershed(displayband,1,'inner')
                boundaryarea=np.where(boundaryarea<1,0,boundaryarea)
                coindict,miniarea=tkintercorestat.findcoin(boundaryarea)
                coinarea=0
                topkey=list(coindict.keys())[0]
                coinarea=len(coindict[topkey][0])
                displayband[coindict[topkey]]=0
                nocoinarea=float(np.count_nonzero(displayband))/(displayband.shape[0]*displayband.shape[1])
                #ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1000,1000])
                print('nocoinarea',nocoinarea)
                coinratio=coinarea/(displayband.shape[0]*displayband.shape[1])
                print('coinratio:',coinratio)
                time.sleep(3)
                ratio=float(nocoinarea/coinratio)
                print('ratio:',ratio)
                if nonzeroratio<0.20:
                    #if coinratio**0.5<=0.2:# and nonzeroratio>=0.1:
                    ratio=findratio([displayband.shape[0],displayband.shape[1]],[1600,1600])
                    workingimg=cv2.resize(displayband,(int(displayband.shape[1]/ratio),int(displayband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
                else:
                    ratio=findratio([displayband.shape[0],displayband.shape[1]],[1000,1000])
                    workingimg=cv2.resize(displayband,(int(displayband.shape[1]/ratio),int(displayband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
            else:
                if nonzeroratio<=0.20:# and nonzeroratio>=0.1:
                    ratio=findratio([displayband.shape[0],displayband.shape[1]],[1600,1600])
                    workingimg=cv2.resize(displayband,(int(displayband.shape[1]/ratio),int(displayband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
                else:
                    #workingimg=np.copy(displayband)
                    #if nonzeroratio>0.15:
                    ratio=findratio([displayband.shape[0],displayband.shape[1]],[1000,1000])
                    workingimg=cv2.resize(displayband,(int(displayband.shape[1]/ratio),int(displayband.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
                    #else:
                    #    if nonzeroratio<0.1:
                    #        ratio=findratio([displayband.shape[0],displayband.shape[1]],[1503,1503])
                    #        workingimg=cv2.resize(displayband,(int(displayband.shape[1]*ratio),int(displayband.shape[0]*ratio)),interpolation=cv2.INTER_LINEAR)


            labels,border,colortable,greatareas,tinyareas,coinparts,labeldict=tkintercorestat.init(workingimg,workingimg,'',workingimg,10,coin)
            multi_results.update({file:(labeldict,coinparts)})
            tempimgdict={}
            tempimgbands={}
            for key in labeldict:
                tup=(labeldict[key]['labels'],labeldict[key]['counts'],labeldict[key]['colortable'],coinparts,file)
                outputdisplay,outputimg=showcounting(tup)
                tempimgdict.update({key:outputdisplay})
                tempimgbands.update({key:outputimg})
            outputimgdict.update({file:tempimgdict})
            outputimgbands.update({file:tempimgbands})
    pass

maxx=0
minx=0
bins=None
loccanvas=None
linelocs=[0,0,0,0]

def resegment():
    global loccanvas,maxx,minx,maxy,miny,linelocs,bins,ybins,reseglabels,figcanvas,refvar,refsubframe,panelA
    figcanvas.unbind('<Any-Enter>')
    figcanvas.unbind('<Any-Leave>')
    figcanvas.unbind('<Button-1>')
    figcanvas.unbind('<B1-Motion>')
    figcanvas.delete(ALL)
    panelA.unbind('<Button-1>')
    refvar.set('0')
    for widget in refsubframe.winfo_children():
        widget.config(state=DISABLED)
    thresholds=[cal_xvalue(linelocs[0]),cal_xvalue(linelocs[1])]
    minthres=min(thresholds)
    maxthres=max(thresholds)
    lwthresholds=[cal_yvalue(linelocs[2]),cal_yvalue(linelocs[3])]
    maxlw=max(lwthresholds)
    minlw=min(lwthresholds)
    print(minthres,maxthres)
    labels=np.copy(reseglabels)
    #if reseglabels is None:
    #    reseglabels,border,colortable,labeldict=tkintercorestat.resegmentinput(labels,minthres,maxthres,minlw,maxlw)

    if refarea is not None:
        labels[refarea]=0
    reseglabels,border,colortable,labeldict=tkintercorestat.resegmentinput(labels,minthres,maxthres,minlw,maxlw)
    multi_results.update({currentfilename:(labeldict,{})})
    iterkeys=list(labeldict.keys())
    iternum=len(iterkeys)
    print(labeldict)
    #iternum=3
    tempimgdict={}
    tempimgbands={}
    for key in labeldict:
        tup=(labeldict[key]['labels'],labeldict[key]['counts'],labeldict[key]['colortable'],{},currentfilename)
        outputdisplay,outputimg=showcounting(tup)
        tempimgdict.update({key:outputdisplay})
        tempimgbands.update({key:outputimg})
    outputimgdict.update({currentfilename:tempimgdict})
    outputimgbands.update({currentfilename:tempimgbands})
    changeoutputimg(currentfilename,'1')
    '''
    data=np.asarray(border[1:])
    hist,bin_edges=np.histogram(data,density=False)
    #figcanvas=Canvas(frame,width=400,height=350,bg='white')
    #figcanvas.pack()
    restoplot=createBins.createBins(hist.tolist(),bin_edges.tolist(),len(bin_edges))

    minx,maxx=histograms.plot(restoplot,hist.tolist(),bin_edges.tolist(),figcanvas)
    bins=bin_edges.tolist()
    loccanvas=figcanvas
    linelocs=[minx,maxx]
    '''
    data=[]
    uniquelabels=list(colortable.keys())
    lenwid=[]
    for uni in uniquelabels:
        if uni!=0:
            pixelloc = np.where(reseglabels == uni)
            try:
                ulx = min(pixelloc[1])
            except:
                continue
            uly = min(pixelloc[0])
            rlx = max(pixelloc[1])
            rly = max(pixelloc[0])
            length=rly-uly
            width=rlx-ulx
            lenwid.append((length+width))
            data.append(len(pixelloc[0]))
    miny=min(lenwid)
    maxy=max(lenwid)
    minx=min(data)
    maxx=max(data)
    binwidth=(maxx-minx)/10
    ybinwidth=(maxy-miny)/10
    bin_edges=[]
    y_bins=[]
    for i in range(0,11):
        bin_edges.append(minx+i*binwidth)
    for i in range(0,11):
        y_bins.append(miny+i*ybinwidth)
    #bin_edges.append(maxx)
    #bin_edges.append(maxx+binwidth)
    #y_bins.append(maxy)
    #y_bins.append(maxy+ybinwidth)
    plotdata=[]
    for i in range(len(data)):
        plotdata.append((data[i],lenwid[i]))
    scaledDatalist=[]
    x_scalefactor=300/(maxx-minx)
    y_scalefactor=250/(maxy-miny)
    for (x,y) in plotdata:
        xval=50+(x-minx)*x_scalefactor
        yval=300-(y-miny)*y_scalefactor
        scaledDatalist.append((xval,yval))

    axistest.drawdots(25,325,375,25,bin_edges,y_bins,scaledDatalist,figcanvas)


    #loccanvas=figcanvas
    #minx=25
    #maxx=375
    #maxy=325
    #miny=25
    #linelocs=[25+12,375-12,325-12,25+12]
    linelocs=[25+12,375-12,25+12,325-12]
    bins=bin_edges
    ybins=y_bins

    figcanvas.bind('<Any-Enter>',item_enter)
    figcanvas.bind('<Any-Leave>',item_leave)
    figcanvas.bind('<Button-1>',item_start_drag)
    figcanvas.bind('<B1-Motion>',item_drag)
    if refarea is not None:
        reseglabels[refarea]=65535

def cal_yvalue(y):
    y_scalefactor=250/(maxy-miny)
    yval=(300-y)/y_scalefactor+miny
    return yval

def cal_xvalue(x):
    #print(maxx,minx,max(bins),min(bins))
    #binwidth=(maxx-minx)/(max(bins)-min(bins))
    #binwidth=(max(bins)-min(bins))/12
    #print(x,minx,binwidth)
    #xloc=((x-minx)/binwidth)
    #print(xloc,min(bins))
    #value=min(bins)+xloc*binwidth
    #print(value)
    x_scalefactor=300/(maxx-minx)
    xval=(x-50)/x_scalefactor+minx

    #print(x,xval)
    return xval



def item_enter(event):
    global figcanvas
    figcanvas.config(cursor='hand2')
    figcanvas._restorItem=None
    figcanvas._restoreOpts=None
    itemType=figcanvas.type(CURRENT)
    #print(itemType)

    pass

def item_leave(event):
    global figcanvas
    pass

def item_start_drag(event):
    global figcanvas,linelocs
    itemType=figcanvas.type(CURRENT)
    print(itemType)
    if itemType=='line':
        fill=figcanvas.itemconfigure(CURRENT,'fill')[4]
        if fill=='red':
            figcanvas._lastX=event.x
            #loccanvas._lastY=event.y
            linelocs[0]=event.x
        if fill=='orange':
            figcanvas._lastX=event.x
            #loccanvas._lastY=event.y
            linelocs[1]=event.x
        if fill=='blue':
            figcanvas._lastY=event.y
            linelocs[2]=event.y
            #print('blue')
        if fill=='purple':
            figcanvas._lastY=event.y
            linelocs[3]=event.y
            #print('purple')
        if fill!='red' and fill!='orange':
            figcanvas._lastX=None
        if fill!='blue' and fill!='purple':
            figcanvas._lastY=None
    else:
        tup=figcanvas.find_all()
        print(tup)
        tup=list(tup)
        redarrow=tup[-4]
        orangearrow=tup[-3]
        bluearrow=tup[-2]
        purplearrow=tup[-1]
        currx=event.x
        curry=event.y
        if currx<25:
            currx=25
        if currx>375:
            currx=375
        if curry<25:
            curry=25
        if curry>325:
            curry=325
        dist=[abs(linelocs[0]-currx),abs(linelocs[1]-currx),abs(linelocs[2]-curry),abs(linelocs[3]-curry)]
        print(dist)
        #print(loccanvas.bbox(redarrow),loccanvas.bbox(orangearrow),loccanvas.bbox(bluearrow),loccanvas.bbox(purplearrow))
        mindist=min(dist)
        mindistind=dist.index(mindist)
        if mindistind==0:
            figcanvas.move(redarrow,currx-linelocs[0],0)
            figcanvas._lastX=currx
            linelocs[0]=currx
        if mindistind==1:
            figcanvas.move(orangearrow,currx-linelocs[1],0)
            figcanvas._lastX=currx
            linelocs[1]=currx
        if mindistind==2:
            figcanvas.move(bluearrow,0,curry-linelocs[2])
            linelocs[2]=curry
            figcanvas._lastY=curry
        if mindistind==3:
            figcanvas.move(purplearrow,0,curry-linelocs[3])
            linelocs[3]=curry
            figcanvas._lastY=curry

        #print(tup)
        #loccanvas._lastX=None
        #loccanvas._lastY=None
    pass

def item_drag(event):
    global figcanvas,linelocs,xvalue
    x=event.x
    y=event.y
    if x<25:
        x=25
    if x>375:
        x=375
    if y<25:
        y=25
    if y>325:
        y=325
    try:
        fill=figcanvas.itemconfigure(CURRENT,'fill')[4]
        print(fill)
    except:
        return
    #itemType=loccanvas.type(CURRENT)
    #try:
    #    test=0-loccanvas._lastX
    #    test=0-loccanvas._lastY
    #except:
    #    return

    if fill=='red' or fill=='orange':
        figcanvas.move(CURRENT,x-figcanvas._lastX,0)
    if fill=='blue' or fill=='purple':
        figcanvas.move(CURRENT,0,y-figcanvas._lastY)
    figcanvas._lastX=x
    figcanvas._lastY=y
    if fill=='red':
        linelocs[0]=x
    if fill=='orange':
        linelocs[1]=x
    if fill=='blue':
        linelocs[2]=y
    if fill=='purple':
        linelocs[3]=y
            #print(line_a)
    #print(minline)
    #print(maxline)
    print(cal_xvalue(linelocs[0]),cal_xvalue(linelocs[1]),cal_yvalue(linelocs[2]),cal_yvalue(linelocs[3]))
    pass


def extraction(frame):
    global kernersizes,multi_results,workingimg,outputimgdict,outputimgbands,pixelmmratio
    global currentlabels,panelA,outputbutton,reseglabels,refbutton,figcanvas,resegbutton,refvar
    global refsubframe,loccanvas,originlabels,changekmeans,originlabeldict,refarea
    if int(kmeans.get())==1:
        messagebox.showerror('Invalid Class #',message='#Class = 1, try change it to 2 or more, and refresh Color-Index.')
        return
    refarea=None
    multi_results.clear()
    kernersizes.clear()
    itervar=IntVar()
    outputimgdict.clear()
    outputimgbands.clear()
    #for widget in frame.winfo_children():
    #    widget.pack_forget()
    coin=refvar.get()=='1'
    edgevar=edge.get()=='1'
    if edgevar:
        currentlabels=removeedge(currentlabels)
    nonzeros=np.count_nonzero(currentlabels)
    nonzeroloc=np.where(currentlabels!=0)
    try:
        ulx,uly=min(nonzeroloc[1]),min(nonzeroloc[0])
    except:
        messagebox.showerror('Invalid Colorindices',message='Need to process colorindicies')
        return
    rlx,rly=max(nonzeroloc[1]),max(nonzeroloc[0])
    nonzeroratio=float(nonzeros)/((rlx-ulx)*(rly-uly))
    print(nonzeroratio)

    '''
    if coin:
        #boundaryarea=tkintercorestat.boundarywatershed(currentlabels,1,'inner')
        #boundaryarea=np.where(boundaryarea<1,0,boundaryarea)
        #coindict,miniarea=tkintercorestat.findcoin(boundaryarea)
        #coinarea=0
        #if coinsize.get()=='1' or coinsize.get()=='2':
        #    topkey=list(coindict.keys())[0]
        #    coinarea=len(coindict[topkey][0])
        #    currentlabels[coindict[topkey]]=0

        #for key in coinkeys:
        #    coinarea+=len(coindict[key][0])
        #    currentlabels[coindict[key]]=0

        coinarea=len(refarea[0])
        nocoinarea=float(np.count_nonzero(currentlabels))/(currentlabels.shape[0]*currentlabels.shape[1])
        print('nocoinarea',nocoinarea)
        coinratio=coinarea/(currentlabels.shape[0]*currentlabels.shape[1])
        print('coinratio:',coinratio**0.5)
        time.sleep(3)
        ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1000,1000])
        #print('miniarea:',miniarea)
        print('coinarea:',coinarea)
        print('ratio:',ratio)
        currentlabels[refarea]=0
        if nonzeroratio<0.2:
            #if coinratio**0.5<=0.2:# and nonzeroratio>=0.1:
            #if coinarea<3000:
            print('cond1')
            ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1600,1600])
            #ratio=float(16/miniarea)
            #ratio=1.5
            workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]/ratio),int(currentlabels.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        else:
            print('cond2')
            ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1000,1000])
            #ratio=float(16/miniarea)
            workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]/ratio),int(currentlabels.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
            #workingimg=np.copy(currentlabels)

        #else:
        #    if miniarea<=10:
        #        print('cond3')
        #        ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1500,1500])
        #        workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]*ratio),int(currentlabels.shape[0]*ratio)),interpolation=cv2.INTER_LINEAR)
        #    else:
        #        print('cond2')
        #        ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1000,1000])
        #        workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]/ratio),int(currentlabels.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)

        if ratio<1:
            print('1500x1500')
            ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1600,1600])
            print('1500x1500 ratio:',ratio)
            workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]*ratio),int(currentlabels.shape[0]*ratio)),interpolation=cv2.INTER_LINEAR)
        else:
            workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]*ratio),int(currentlabels.shape[0]*ratio)),interpolation=cv2.INTER_LINEAR)

        #workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]*ratio),int(currentlabels.shape[0]*ratio)),interpolation=cv2.INTER_LINEAR)
        #coinarea=coindict[topkey]
        coinulx=min(refarea[1])
        coinuly=min(refarea[0])
        coinrlx=max(refarea[1])
        coinrly=max(refarea[0])
        coinlength=coinrly-coinuly
        coinwidth=coinrlx-coinulx
        if coinsize.get()=='1' or coinsize.get()=='2':
            pixelmmratio=19.05**2/(coinlength*coinwidth)
        if coinsize.get()=='3':
            refsize=int(sizeentry.get())
            pixelmmratio=refsize/(coinlength*coinwidth)
        copyboundaryarea=np.copy(boundaryarea)
        copyboundaryarea[refarea]=0
        labels,border,colortable,labeldict=tkintercorestat.coinlabels(copyboundaryarea)
    else:
    '''
    #nonzeroratio=float(nonzeros)/(currentlabels.shape[0]*currentlabels.shape[1])
    if nonzeroratio<=0.2:# and nonzeroratio>=0.1:
        ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1600,1600])
        workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]/ratio),int(currentlabels.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
    else:
        #if nonzeroratio>0.16:
        if imgtypevar.get()=='0':
            print('imgtype',imgtypevar.get())
            if currentlabels.shape[0]*currentlabels.shape[1]>1000*1000:
                ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1000,1000])
                workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]/ratio),int(currentlabels.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
            else:
                ratio=1
                workingimg=np.copy(currentlabels)
        if imgtypevar.get()=='1':
            print('imgtype',imgtypevar.get())
            if currentlabels.shape[0]*currentlabels.shape[1]>1000*1000:
                ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[620,620])
                workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]/ratio),int(currentlabels.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
            else:
                ratio=1
                workingimg=np.copy(currentlabels)

    pixelmmratio=1.0
        #else:
        #    if nonzeroratio<0.1:
        #        print('using 1500x1500')
        #        ratio=findratio([currentlabels.shape[0],currentlabels.shape[1]],[1553,1553])
        #        workingimg=cv2.resize(currentlabels,(int(currentlabels.shape[1]*ratio),int(currentlabels.shape[0]*ratio)),interpolation=cv2.INTER_LINEAR)

    #cv2.imshow('workingimg',workingimg)
    coin=False
    print('ratio:',ratio)
    print('workingimgsize:',workingimg.shape)
    #if imgtypevar.get()=='0':
#<<<<<<< HEAD
        #labels,border,colortable,greatareas,tinyareas,coinparts,labeldict=tkintercorestat.init(workingimg,workingimg,'',workingimg,10,coin)
    #    labels,border,colortable,labeldict=tkintercorestat.init(workingimg,workingimg,'',workingimg,10,coin)
    #if imgtypevar.get()=='1':
        #labels,border,colortable,coinparts,labeldict=tkintercorestat_plot.init(workingimg,workingimg,'',workingimg,10,coin)
    if originlabels is None:
        originlabels,border,colortable,originlabeldict=tkintercorestat.init(workingimg,workingimg,'',workingimg,10,coin)
    else:
        if changekmeans==True:
            originlabels,border,colortable,originlabeldict=tkintercorestat.init(workingimg,workingimg,'',workingimg,10,coin)
            changekmeans=False
    multi_results.update({currentfilename:(originlabeldict,{})})

    reseglabels=originlabels
    labeldict=originlabeldict
    colortable=originlabeldict['iter0']['colortable']
#=======
    #labels,border,colortable,greatareas,tinyareas,coinparts,labeldict=tkintercorestat.init(workingimg,workingimg,'',workingimg,10,coin)
    #if imgtypevar.get()=='1':
        
    #multi_results.update({currentfilename:(labeldict,coinparts)})
#>>>>>>> 8af175b92d858c2523ccaf7db7238be6fbec0c8b
    iterkeys=list(labeldict.keys())
    iternum=len(iterkeys)
    print(labeldict)
    #iternum=3
    itervar.set(len(iterkeys))
    tempimgdict={}
    tempimgbands={}
    for key in labeldict:
        tup=(labeldict[key]['labels'],labeldict[key]['counts'],labeldict[key]['colortable'],{},currentfilename)
        outputdisplay,outputimg=showcounting(tup)
        tempimgdict.update({key:outputdisplay})
        tempimgbands.update({key:outputimg})
    outputimgdict.update({currentfilename:tempimgdict})
    outputimgbands.update({currentfilename:tempimgbands})
    #time.sleep(5)
    #tup=(labeldict,coinparts,currentfilename)
    #resscaler=Scale(frame,from_=1,to=iternum,tickinterval=1,length=220,orient=HORIZONTAL,variable=itervar,command=partial(changeoutputimg,currentfilename))
    #resscaler.pack()
    changeoutputimg(currentfilename,'1')

    '''
    data=np.asarray(border[1:])
    hist,bin_edges=np.histogram(data,density=False)
    figcanvas=Canvas(frame,width=400,height=350,bg='white')
    figcanvas.pack()
    restoplot=createBins.createBins(hist.tolist(),bin_edges.tolist(),len(bin_edges))
    global minx,maxx,bins,loccanvas,linelocs
    minx,maxx=histograms.plot(restoplot,hist.tolist(),bin_edges.tolist(),figcanvas)
    bins=bin_edges.tolist()
    loccanvas=figcanvas
    linelocs=[minx,maxx]
    '''
    global loccanvas,maxx,minx,maxy,miny,linelocs,bins,ybins,figcanvas
    data=[]
    uniquelabels=list(colortable.keys())
    lenwid=[]
    figcanvas.delete(ALL)
    for uni in uniquelabels:
        if uni!=0:
            pixelloc = np.where(originlabels == uni)
            try:
                ulx = min(pixelloc[1])
            except:
                continue
            uly = min(pixelloc[0])
            rlx = max(pixelloc[1])
            rly = max(pixelloc[0])
            length=rly-uly
            width=rlx-ulx
            lenwid.append((length+width))
            data.append(len(pixelloc[0]))
    miny=min(lenwid)
    maxy=max(lenwid)
    minx=min(data)
    maxx=max(data)
    binwidth=(maxx-minx)/10
    ybinwidth=(maxy-miny)/10
    bin_edges=[]
    y_bins=[]
    for i in range(0,11):
        bin_edges.append(minx+i*binwidth)
    for i in range(0,11):
        y_bins.append(miny+i*ybinwidth)
    #bin_edges.append(maxx)
    #bin_edges.append(maxx+binwidth)
    #y_bins.append(maxy)
    #y_bins.append(maxy+ybinwidth)
    plotdata=[]
    for i in range(len(data)):
        plotdata.append((data[i],lenwid[i]))
    scaledDatalist=[]
    x_scalefactor=300/(maxx-minx)
    y_scalefactor=250/(maxy-miny)
    for (x,y) in plotdata:
        xval=50+(x-minx)*x_scalefactor
        yval=300-(y-miny)*y_scalefactor
        scaledDatalist.append((xval,yval))

    axistest.drawdots(25,325,375,25,bin_edges,y_bins,scaledDatalist,figcanvas)


    #loccanvas=figcanvas
    #minx=25
    #maxx=375
    #maxy=325
    #miny=25
    #[25,375,325,25]
    linelocs=[25+12,375-12,25+12,325-12]
    #linelocs=[25+12,375-12,325-12,25+12]
    bins=bin_edges
    ybins=y_bins

    figcanvas.bind('<Any-Enter>',item_enter)
    figcanvas.bind('<Any-Leave>',item_leave)
    figcanvas.bind('<Button-1>',item_start_drag)
    figcanvas.bind('<B1-Motion>',item_drag)

    #reseg=Button(frame,text='Re-process',command=partial(resegment,labels,figcanvas),padx=5,pady=5)
    #reseg.pack()

    #if outputbutton is None:
    #    outputbutton=Button(control_fr,text='Export Results',command=partial(export_result,'0'),padx=5,pady=5)
    #    outputbutton.pack()
    #batchextraction()
    #else:
    #    outputbutton.pack_forget()
    #    outputbutton.pack()
    refbutton.config(state=NORMAL)
    refvar.set('0')
    for widget in refsubframe.winfo_children():
        widget.config(state=DISABLED)
    outputbutton.config(state=NORMAL)
    resegbutton.config(state=NORMAL)

    pass

def onFrameConfigure(inputcanvas):
    '''Reset the scroll region to encompass the inner frame'''
    inputcanvas.configure(scrollregion=inputcanvas.bbox(ALL))




def removeedge(bands):
    global pointcontainer,displayorigin
    copyband=np.copy(bands)
    size=copyband.shape
    for i in range(20):
        copyband[i,:]=0  #up
        copyband[:,i]=0  #left
        copyband[:,size[1]-1-i]=0 #right
        copyband[size[0]-1-i,:]=0
    img=ImageTk.PhotoImage(Image.fromarray(copyband.astype('uint8')))
    displayimg['ColorIndices']['Image']=img
    changedisplayimg(imageframe,'ColorIndices')
    return copyband

def clustercontent(var):
    global cluster,bandchoice,contentframe
    bandchoice={}
    if var=='0':
        cluster=['LabOstu','NDI']
    if var=='1':
        cluster=['Greenness','VEG','CIVE','MExG','NDVI','NGRDI','HEIGHT','Band1','Band2','Band3']
    for widget in contentframe.winfo_children():
        widget.pack_forget()
    for key in cluster:
        tempdict={key:Variable()}
        bandchoice.update(tempdict)
        ch=ttk.Checkbutton(contentframe,text=key,variable=bandchoice[key])#,command=changecluster)#,command=partial(autosetclassnumber,clusternumberentry,bandchoice))
        #if filedropvar.get()=='seedsample.JPG':
        #    if key=='NDI':
        #        ch.invoke()
        ch.pack(fill=X)

def findtempbandgap(locs):
    xloc=list(locs[1])
    yloc=list(locs[0])
    sortedx=sorted(xloc)
    gaps={}
    last=0
    for i in range(len(sortedx)):
        if sortedx[i]==sortedx[last]:
            continue
        isone = sortedx[i]-sortedx[last]==1
        if isone == False:
            gaps.update({(last,i-1):i-1-last+1})
        last=i
    print('xgaps',gaps,'len',len(sortedx))
    gaps={}
    last=0
    sortedy=sorted(yloc)
    for i in range(len(sortedy)):
        if sortedy[i]==sortedy[last]:
            continue
        isone = sortedy[i]-sortedy[last]==1
        if isone == False:
            gaps.update({(last,i-1):i-1-last+1})
        last=i
    print('ygaps',gaps,'len',len(sortedy))



def customcoin(event,processlabels,tempband):
    global panelA,refarea,coinbox
    x=event.x
    y=event.y
    panelA.delete(coinbox)
    #ratio=findratio([processlabels.shape[0],processlabels.shape[1]],[850,850])
    #tempband=cv2.resize(processlabels.astype('float32'),(int(processlabels.shape[1]/ratio),int(processlabels.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
    #if processlabels.shape[0]*processlabels.shape[1]>850*850
    #    tempband=
    #tempband=tempband.astype('uint8')
    print(tempband.shape)
    coinlabel=tempband[y,x]
    print('coinlabel',coinlabel,'x',x,'y',y)
    if coinlabel==0:
        #messagebox.showerror('Invalid',message='Please pick areas have items.')
        return
    else:
        refarea=np.where(processlabels==coinlabel)
        coinarea=np.where(tempband==coinlabel)
        #findtempbandgap(coinarea)
        ulx,uly=min(coinarea[1]),min(coinarea[0])
        rlx,rly=max(coinarea[1]),max(coinarea[0])
        #copytempband=np.copy(tempband)
        #temparea=copytempband[uly:rly+1,ulx:rlx+1]
        #copytempband[uly:rly+1,ulx:rlx+1]=tkintercorestat.tempbanddenoice(temparea,coinlabel,len(refarea[0])/(ratio**2))
        #coinarea=np.where(copytempband==coinlabel)
        unix=np.unique(coinarea[1]).tolist()
        uniy=np.unique(coinarea[0]).tolist()
        if len(unix)==1:
            ulx,rlx=unix[0],unix[0]
        else:
            ulx,rlx=min(coinarea[1]),max(coinarea[1])
        if len(uniy)==1:
            uly,rly=uniy[0],uniy[0]
        else:
            uly,rly=min(coinarea[0]),max(coinarea[0])
        '''
        try:
            ulx,uly=min(coinarea[1]),min(coinarea[0])
            rlx,rly=max(coinarea[1]),max(coinarea[0])
        except:
            coinarea=np.where(tempband==coinlabel)
            ulx,uly=min(coinarea[1]),min(coinarea[0])
            rlx,rly=max(coinarea[1]),max(coinarea[0])
        '''
        coinbox=panelA.create_rectangle(ulx,uly,rlx+1,rly+1,outline='yellow')
        #panelA.unbind('<Button-1>')


def magnify(event):
    global panelA
    x=event.x
    y=event.y
    grabimg=ImageGrab.grab((x-2,y-2,x+2,y+2))
    subimg=grabimg.resize((10,10))
    magnifier=panelA.create_image(x-3,y-3,image=ImageTk.PhotoImage(subimg))
    panelA.update()


#def highlightcoin(processlabel,coindict,miniarea):
def highlightcoin():
    global coinbox,panelA,refarea
    if convband is None:
        return
    tempband=np.copy(convband)
    #uniquel=np.unique(tempband)
    #print(uniquel)
    processlabel=np.copy(reseglabels)
    coinarea=0
    panelA.delete(coinbox)
    unique,counts=np.unique(processlabel,return_counts=True)
    hist=dict(zip(unique[1:],counts[1:]))
    sortedlist=sorted(hist,key=hist.get,reverse=True)
    if coinsize.get()=='3':
        panelA.bind('<Button-1>',lambda event,arg=processlabel:customcoin(event,processlabel,tempband))
        panelA.config(cursor='hand2')
        #panelA.bind('<Motion>',magnify)
    else:
        if coinsize.get()=='1':
            topkey=sortedlist[0]
        if coinsize.get()=='2':
            topkey=sortedlist[-1]
            coinarea=np.where(tempband==topkey)
            i=2
            while(len(coinarea[0])==0):
                topkey=sortedlist[-i]
                coinarea=np.where(tempband==topkey)
                i+=1
            #copyboundary=np.copy(processlabel)
        refarea=np.where(processlabel==topkey)
        print(topkey)
        coinarea=np.where(tempband==topkey)
        print(coinarea)
        ulx,uly=min(coinarea[1]),min(coinarea[0])
        rlx,rly=max(coinarea[1]),max(coinarea[0])
        #copytempband=np.copy(tempband.astype('int64'))
        #temparea=copytempband[uly:rly+1,ulx:rlx+1]
        #copytempband[uly:rly+1,ulx:rlx+1]=tkintercorestat.tempbanddenoice(temparea,topkey,len(refarea[0])/(ratio**2))
        #coinarea=np.where(copytempband==topkey)
        '''
        try:
            ulx,uly=min(coinarea[1]),min(coinarea[0])
            rlx,rly=max(coinarea[1]),max(coinarea[0])
        except:
            coinarea=np.where(tempband==topkey)
            ulx,uly=min(coinarea[1]),min(coinarea[0])
            rlx,rly=max(coinarea[1]),max(coinarea[0])
        '''
        unix=np.unique(coinarea[1]).tolist()
        uniy=np.unique(coinarea[0]).tolist()
        if len(unix)==1:
            ulx,rlx=unix[0],unix[0]
        else:
            ulx,rlx=min(coinarea[1]),max(coinarea[1])
        if len(uniy)==1:
            uly,rly=uniy[0],uniy[0]
        else:
            uly,rly=min(coinarea[0]),max(coinarea[0])
        coinbox=panelA.create_rectangle(ulx,uly,rlx+2,rly+2,outline='yellow')



def refchoice(refsubframe):
    global coinsize,sizeentry,coinbox,panelA,boundaryarea,coindict,convband
    #refsubframe.grid_forget()
    #for widget in refsubframe.winfo_children():
    #    widget.pack_forget()
    panelA.delete(coinbox)
    if refvar.get()=='1':
        if type(currentlabels)==type(None):
            messagebox.showerror('Invalid Option',message='Should get # class >=2 color index image first.')
            return
        #refsubframe.pack(side=BOTTOM)
        #refsubframe.grid(row=1,column=0,columnspan=4)
        #refoption=[('Use Maximum','1'),('Use Minimum','2'),('User Specify','3')]
        for widget in refsubframe.winfo_children():
            widget.config(state=NORMAL)
        if reseglabels is None:
            return
        processlabel=np.copy(reseglabels)
        ratio=findratio([processlabel.shape[0],processlabel.shape[1]],[850,850])
        #tempband=cv2.resize(processlabel.astype('float32'),(int(processlabel.shape[1]/ratio),int(processlabel.shape[0]/ratio)),interpolation=cv2.INTER_LINEAR)
        print(ratio)
        if int(ratio)>1:
            convband,cache=tkintercorestat.pool_forward(processlabel,{"f":int(ratio),"stride":int(ratio)})
        else:
            convband=processlabel
        highlightcoin()
        #if reseglabels is None:
        #    boundaryarea=tkintercorestat.boundarywatershed(currentlabels,1,'inner')
        #    boundaryarea=np.where(boundaryarea<1,0,boundaryarea)
        #    coindict,miniarea=tkintercorestat.findcoin(boundaryarea)
        #    processlabels=np.copy(boundaryarea)
        #else:
        #coindict,miniarea=tkintercorestat.findcoin(reseglabels)
        #processlabels=np.copy(reseglabels)
    if refvar.get()=='0':
        for widget in refsubframe.winfo_children():
            widget.config(state=DISABLED)
        #panelA.unbind('<Button-1>')




## ----Interface----


## ----Display----
display_fr=Frame(root,width=640,height=640)
control_fr=Frame(root,width=320,height=320)
display_fr.pack(side=LEFT)
control_fr.pack(side=LEFT)
#display_label=Text(display_fr,height=1,width=100)
#display_label.tag_config("just",justify=CENTER)
#display_label.insert(END,'Display Panel',"just")
#display_label.configure(state=DISABLED)
#display_label.pack(padx=10,pady=10)

imgtypevar.set('0')
Open_File('seedsample.JPG')
singleband('seedsample.JPG')
#cal indices
generatedisplayimg('seedsample.JPG')



imageframe=LabelFrame(display_fr,bd=0)
imageframe.pack()

#panelA=Label(imageframe,text='Display Panel',image=displayimg['Origin']) #620 x 620
l=displayimg['Origin']['Size'][0]
w=displayimg['Origin']['Size'][1]
panelA=Canvas(imageframe,width=w,height=l,bg='white')
panelA.create_image(0,0,image=displayimg['Origin']['Image'],anchor=NW)
panelA.pack(padx=20,pady=20,expand=YES)


buttondisplay=LabelFrame(display_fr,bd=0)
buttondisplay.config(cursor='hand2')
buttondisplay.pack()

#disbuttonoption={'Origin':'1','Gray/NIR':'2','ColorIndices':'3','Output':'4'}
disbuttonoption={'Origin':'1','ColorIndices':'3','Output':'4'}
for text in disbuttonoption:
    b=Radiobutton(buttondisplay,text=text,variable=displaybut_var,value=disbuttonoption[text],command=partial(changedisplayimg,imageframe,text))
    b.pack(side=LEFT,padx=20,pady=5)
    if disbuttonoption[text]=='1':
        b.invoke()
### ---open file----
openfilebutton=Button(buttondisplay,text='Open',command=Open_Multifile,cursor='hand2')
openfilebutton.pack(side=LEFT,padx=20,pady=5)
outputbutton=Button(buttondisplay,text='Export',command=partial(export_result,'0'))
outputbutton.pack(side=LEFT,padx=20,pady=5)
outputbutton.config(state=DISABLED)
## ----Control----
#control_label=Text(control_fr,height=1,width=50)
#control_label.tag_config("just",justify=CENTER)
#control_label.insert(END,'Control Panel',"just")
#control_label.configure(state=DISABLED)
#control_label.pack()

filter_fr=LabelFrame(control_fr,bd=0)
filter_fr.pack()
imgtypeframe=LabelFrame(filter_fr,text='Image type',bd=0)
imgtypeframe.pack()
imgtypeoption=[('Crop plots','1'),('Grain kernel','0')]
for text,mode in imgtypeoption:
    b=Radiobutton(imgtypeframe,text=text,variable=imgtypevar,value=mode,command=partial(clustercontent,mode))
    b.pack(side=LEFT,padx=6)

### ---change file---
changefileframe=LabelFrame(filter_fr,text='Change Files',cursor='hand2')
#changefileframe.pack()

filedropvar.set(filenames[0])
changefiledrop=OptionMenu(changefileframe,filedropvar,*filenames,command=partial(changeimage,imageframe))
changefiledrop.pack()
### ---choose color indices---
chframe=LabelFrame(filter_fr,text='Select indicies below',cursor='hand2',bd=0)
chframe.pack()
chcanvas=Canvas(chframe,width=200,height=60,scrollregion=(0,0,400,400))
chcanvas.pack(side=LEFT)
chscroller=Scrollbar(chframe,orient=VERTICAL)
chscroller.pack(side=RIGHT,fill=Y,expand=True)
chcanvas.config(yscrollcommand=chscroller.set)
chscroller.config(command=chcanvas.yview)
contentframe=LabelFrame(chcanvas)
chcanvas.create_window((4,4),window=contentframe,anchor=NW)
contentframe.bind("<Configure>",lambda event,arg=chcanvas:onFrameConfigure(arg))

for key in cluster:
    tempdict={key:Variable()}
    bandchoice.update(tempdict)
    ch=ttk.Checkbutton(contentframe,text=key,variable=bandchoice[key])#,command=changecluster)#,command=partial(autosetclassnumber,clusternumberentry,bandchoice))
    if filedropvar.get()=='seedsample.JPG':
        if key=='LabOstu':
            ch.invoke()
    ch.pack(fill=X)

### ----Class NUM----
kmeansgenframe=LabelFrame(filter_fr,text='Select # of class',cursor='hand2',bd=0)
kmeansgenframe.pack()
kmeanslabel=LabelFrame(kmeansgenframe,bd=0)
checkboxframe=LabelFrame(kmeansgenframe,cursor='hand2',bd=0)#,text='Select classes',cursor='hand2')
kmeanslabel.pack()

kmeans.set(2)
#kmeansbar=Scale(kmeanslabel,from_=1,to=10,tickinterval=1,length=270,showvalue=0,orient=HORIZONTAL,variable=kmeans,command=partial(generatecheckbox,checkboxframe))
kmeansbar=ttk.Scale(kmeanslabel,from_=1,to=10,length=350,orient=HORIZONTAL,variable=kmeans,cursor='hand2',command=partial(generatecheckbox,checkboxframe))
kmeansbar.pack()

kmeansbar.bind('<ButtonRelease-1>',changecluster)

checkboxframe.pack()
for i in range(10):
    dictkey=str(i+1)
    tempdict={dictkey:Variable()}
    if i==1:
        tempdict[dictkey].set('1')
    else:
        tempdict[dictkey].set('0')
    checkboxdict.update(tempdict)
    ch=Checkbutton(checkboxframe,text=dictkey,variable=checkboxdict[dictkey],command=partial(changecluster,''))
    if i+1>int(kmeans.get()):
        ch.config(state=DISABLED)
    ch.pack(side=LEFT)

reshapemodified_tif=np.zeros((displaybandarray[currentfilename]['LabOstu'].shape[0]*displaybandarray[currentfilename]['LabOstu'].shape[1],1))
colordicesband=kmeansclassify(['LabOstu'],reshapemodified_tif)
generateimgplant(colordicesband)
changedisplayimg(imageframe,'Origin')
#generatecheckbox(checkboxframe,2)

#refreshebutton=Button(filter_fr,text='Refresh ColorIndices',cursor='hand2',command=changecluster)
#refreshebutton.pack()
### --- ref and edge settings ---

#for text,mode in refoption:
#    b=Radiobutton(refframe,text=text,variable=refvar,value=mode,command=partial(refchoice,refsubframe))
    #b.pack(side=LEFT,padx=15)
#    b.grid(row=0,column=column)
#    column+=1

edgeframe=LabelFrame(filter_fr,text='Edge remove setting')
#edgeframe.pack()
edgeoption=[('Remove edge','1'),('Keep same','0')]

edge.set('0')
for text,mode in edgeoption:
    b=Radiobutton(edgeframe,text=text,variable=edge,value=mode)
    b.pack(side=LEFT,padx=6)

### ---start extraction---
extractionframe=LabelFrame(control_fr,cursor='hand2',bd=0)
extractionframe.pack(padx=5,pady=5)
resviewframe=LabelFrame(control_fr,cursor='hand2')
figcanvas=Canvas(resviewframe,width=400,height=350,bg='white')
figcanvas.pack()
extractbutton=Button(extractionframe,text='Segment Origin',command=partial(extraction,resviewframe))
extractbutton.pack(side=LEFT)
resegbutton=Button(extractionframe,text='Re-Segment',command=resegment)
resegbutton.pack(side=LEFT)
resegbutton.config(state=DISABLED)
resviewframe.pack()
refframe=LabelFrame(control_fr,cursor='hand2',bd=0)
refframe.pack()

refoption=[('Use Ref','1'),('No Ref','0')]
refvar.set('0')
refsubframe=LabelFrame(refframe,bd=0)
column=0
refbutton=Checkbutton(refframe,text='Ref',variable=refvar,command=partial(refchoice,refsubframe))
refbutton.pack(side=LEFT)
refbutton.config(state=DISABLED)
refsubframe.pack(side=LEFT)
refoption=[('Max','1'),('Min','2'),('Spec','3')]
for text,mode in refoption:
    b=Radiobutton(refsubframe,text=text,variable=coinsize,value=mode,command=highlightcoin)#,command=partial(highlightcoin,processlabels,coindict,miniarea))
    b.pack(side=LEFT,padx=5)
    if mode=='1':
        b.invoke()
sizeentry=Entry(refsubframe,width=5)
sizeentry.insert(END,10)
sizeentry.pack(side=LEFT,padx=5)
sizeunit=Label(refsubframe,text='mm^2')
sizeunit.pack()
for widget in refsubframe.winfo_children():
    widget.config(state=DISABLED)
root.mainloop()

