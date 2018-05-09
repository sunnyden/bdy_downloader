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

#BDYDownload("http://nj01ct01.baidupcs.com/file/a6022851d521a66b30ea953b523115a5?bkt=p3-000075f51fc3b043fb46fcdbad24fb7b3527&fid=3405821062-250528-703859121264326&time=1525776955&sign=FDTAXGERLQBHSKa-DCb740ccc5511e5e8fedcff06b081203-KfVpuvFSdFSbRuyUk3Tu7W%2FOKro%3D&to=63&size=7884632&sta_dx=7884632&sta_cs=0&sta_ft=rar&sta_ct=5&sta_mt=5&fm2=MH%2CYangquan%2CAnywhere%2C%2Cguangdong%2Cct&vuk=3405821062&iv=0&newver=1&newfm=1&secfm=1&flow_ver=3&pkey=000075f51fc3b043fb46fcdbad24fb7b3527&sl=76480590&expires=8h&rt=pr&r=975115165&mlogid=2963783697017339122&vbdid=1920632986&fin=evidence.rar&fn=evidence.rar&rtype=1&dp-logid=2963783697017339122&dp-callid=0.1.1&hps=1&tsl=80&csl=80&csign=QLiowAUlNe51BGVx12f0T0%2FyEko%3D&so=0&ut=6&uter=4&serv=0&uc=4212678354&ic=3630465345&ti=26fa64dbec288224e83a0ba19a4d944005d21fd880f81096305a5e1275657320&by=themis")
#BDYDownload("nj01ct01.baidupcs.com/file/6a3f15e685ac90ef09be53483ccd458d?bkt=p3-00001b50100f315cb71d4451f155cf2976c2&fid=3405821062-250528-692000515586167&time=1525771574&sign=FDTAXGERLQBHSKa-DCb740ccc5511e5e8fedcff06b081203-B2%2B%2FruQgb%2BLKrI4o4fzv%2BTcxsqc%3D&to=63&size=27301965&sta_dx=27301965&sta_cs=0&sta_ft=flac&sta_ct=5&sta_mt=0&fm2=MH%2CYangquan%2CAnywhere%2C%2Cguangdong%2Cct&vuk=3405821062&iv=0&newver=1&newfm=1&secfm=1&flow_ver=3&pkey=00001b50100f315cb71d4451f155cf2976c2&sl=76480590&expires=8h&rt=pr&r=796018404&mlogid=2962339104915394514&vbdid=1920632986&fin=03+The+Shower.flac&fn=03+The+Shower.flac&rtype=1&dp-logid=2962339104915394514&dp-callid=0.1.1&hps=1&tsl=80&csl=80&csign=QLiowAUlNe51BGVx12f0T0%2FyEko%3D&so=0&ut=6&uter=4&serv=0&uc=4212678354&ic=3630465345&ti=220620fd8d32b115b861e7af9d8d84ad6473c279875fa1ea&by=themis")
#BDYDownload("nj01ct01.baidupcs.com/file/4f26c80d2c4807b0023e4b427d8c0d8d?bkt=p3-00005834cc4011c2f729b33fdd520246b657&fid=3405821062-250528-19247043127462&time=1525779828&sign=FDTAXGERLQBHSKa-DCb740ccc5511e5e8fedcff06b081203-ZWt83qRjawPVqP3wFsWCTLVDmsc%3D&to=63&size=30084294&sta_dx=30084294&sta_cs=4&sta_ft=flac&sta_ct=5&sta_mt=0&fm2=MH%2CYangquan%2CAnywhere%2C%2Cguangdong%2Cct&vuk=3405821062&iv=0&newver=1&newfm=1&secfm=1&flow_ver=3&pkey=00005834cc4011c2f729b33fdd520246b657&sl=76480590&expires=8h&rt=pr&r=156523937&mlogid=2964554932512991765&vbdid=1920632986&fin=01+%E3%83%89%E3%83%A9%E3%81%88%E3%82%82%E3%82%93.flac&fn=01+%E3%83%89%E3%83%A9%E3%81%88%E3%82%82%E3%82%93.flac&rtype=1&dp-logid=2964554932512991765&dp-callid=0.1.1&hps=1&tsl=80&csl=80&csign=QLiowAUlNe51BGVx12f0T0%2FyEko%3D&so=0&ut=6&uter=4&serv=0&uc=4212678354&ic=3630465345&ti=7f2851a6839322b822e909b8c735b719ab586856fc0babcd&by=themis")
#BDYDownload("www.baidupcs.com/rest/2.0/pcs/file?method=batchdownload&app_id=250528&zipcontent=%7B%22fs_id%22%3A%5B%22921197101616171%22%5D%7D&sign=DCb740ccc5511e5e8fedcff06b081203:C1tw89LYqD3itdPJoMwsGQI2eCo%3D&uid=692560905&time=1525931648&dp-logid=2982116022717788305&dp-callid=0&vuk=3405821062&from_uk=692560905")
userAgent = input("Input your UA:")
content = input("Input your link:")
if(content.startswith("http")):
    content = content.split("://")[1]
if(content.__contains__("baidupcs.com/file")):
    BDYDownload(content)
else:
    print("Unsupported Link!")
