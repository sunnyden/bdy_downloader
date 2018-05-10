import urllib.request
import urllib.parse
import threading
import os
import time
from xml.etree import ElementTree
segmentList = []
taskFinish = []
segmentSize = 500000
maxThreadSize = 400
threadPool = []
fileSize = 0
downUrl = ""
fileName = "G:\\"
fileIOLock = False
writingQueue = []
protocolSwitch = 0
finishSize = 0
startTime = 0
userAgent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
def segmentDownload(contentId):
    global segmentList,taskFinish,fileSize,downUrl,fileName,fileIOLock,writingQueue,protocolSwitch
    try:
        if taskFinish[contentId] == 0:
            taskFinish[contentId] = 1
            fromByte = segmentList[contentId]
            toByte = fromByte + segmentSize
            if contentId +1 == len(segmentList):
                toByte = fileSize
            if protocolSwitch ==0:
                req =  urllib.request.Request("http://"+downUrl)
                protocolSwitch = 1
            else:
                req =  urllib.request.Request("https://"+downUrl)
                protocolSwitch = 0
            req.add_header("User-Agent",userAgent)
            req.add_header('Accept-Range','bytes='+str(fromByte)+'-'+str(toByte))
            req.add_header('Range', 'bytes=' + str(fromByte) + '-' + str(toByte))
            result = urllib.request.urlopen(req)
            buffer = result.read()
            writingQueue.append([fromByte,buffer])
    except IOError:
        taskFinish[contentId]=0
        #print("Thread download failed.",contentId,fromByte,toByte)

def queueFlush():
    global writingQueue,fileName,finishSize
    while True:
        if len(writingQueue) != 0:
            file = open(fileName,"r+b")
            queueObj = writingQueue[0]
            file.seek(queueObj[0])
            file.write(queueObj[1])
            finishSize += len(queueObj[1])
            file.close()
            del writingQueue[0]

def BDYDownload(url):
    global segmentList,taskFinish,downUrl,fileSize,fileName,threadPool,startTime,writingQueue
    downUrl = url
    fn = url.split("fn=")[1].split("&")[0]
    fn = urllib.parse.unquote(fn)
    fileName += fn
    downloadBytes = 0
    req=urllib.request.Request("http://"+url)
    req.add_header("User-Agent",userAgent)
    req.add_header('Accept-Range', 'bytes=-1')
    req.add_header('Range', 'bytes=-1')
    res=urllib.request.urlopen(req)
    fileSize = int(res.info().get("x-bs-file-size"))
    file = open(fileName, 'w')
    file.seek(fileSize)
    file.write('\x00')
    file.close()
    while downloadBytes < fileSize:
        segmentList.append(downloadBytes)
        taskFinish.append(0)
        downloadBytes += segmentSize
    threadPool.append(threading.Thread(target=queueFlush))
    threadPool[0].setDaemon(True)
    threadPool[0].start()
    threadStat = threading.Thread(target=statPrint)
    threadStat.setDaemon(True)
    threadStat.start()
    startTime = time.time()
    print("Downloading...")
    while True:
        if len(threadPool)<maxThreadSize+1:
            i = 0
            for finishFlag in taskFinish:
                if finishFlag == 0 and len(threadPool)<maxThreadSize+1:
                    threadPool.append(threading.Thread(target=segmentDownload,args=[i]))
                    threadPool[len(threadPool)-1].setDaemon(True)
                    threadPool[len(threadPool)-1].start()
                    #time.sleep(0.1)
                i += 1
        i=0
        deadList = []
        for thread in threadPool:
            if not thread.isAlive():
                deadList.append(i)
            i += 1
        i=0
        for deadIndex in deadList:
            del threadPool[deadIndex-i]
            i += 1
        if len(threadPool)==1 and len(writingQueue)==0:
            endTime = time.time()
            print("Download Succeed! AvgSpeed:",(fileSize/(endTime-startTime))/1024,"kb/s")
            break

def statPrint():
    global threadPool,startTime,finishSize
    while True:
        time.sleep(1)
        curTime = time.time()
        print("Downloading(",round(finishSize*100/fileSize,3),"%)...Threads:",len(threadPool)," Current AvgSpeed:", (finishSize / (curTime - startTime)) / 1024, "kb/s")

userAgent = input("Input your UA:")
content = input("Input your link:")
if(content.startswith("http")):
    content = content.split("://")[1]
if(content.__contains__("baidupcs.com/file")):
    BDYDownload(content)
else:
    print("Unsupported Link!")
