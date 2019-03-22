import pandas
import random


def GetDownloadTime(throughput, chunksize):
    return chunksize / throughput


class SimVideo:
    def __init__(self):
        self.length = 180.0 + 120.0 * random.random()
        self.debug = []
        self.chunks = []
        countdown = self.length
        while countdown > 0:
            temp = .6 + .3 * random.random()
            temp = round(temp, 5)
            if countdown < temp:
                temp = countdown
                countdown = 0
            else:
                countdown -= temp
            self.chunks.append(temp)
            self.debug.append(self.length - countdown)
        self.NumChunks = len(self.chunks)
        self.arrRet = [[], [], [], [], [], [], []]

        self.secBuffer = 0
        self.fCurrentTime = 0
        self.underruns = 0
        self.downtime = 0
        self.chunkIndex = 0
        self.videotime = 0
        self.partialDownload = 0
        self.subSecond = 0
        self.bufferLimit = 5
        self.throughput = -1
        self.bitrate = -1

    def generate_chunks(self, length, standard, variation):
        self.length = length
        self.chunks = []
        countdown = self.length
        while countdown > 0:
            temp = standard - variation + variation * random.random()
            temp = round(temp, 5)
            if countdown < temp:
                temp = countdown
                countdown = 0
            else:
                countdown -= temp
            self.chunks.append(temp)
            self.debug.append(self.length - countdown)
        self.NumChunks = len(self.chunks)

    def update(self, videotime, throughput, bitrate, secbuffer, underruns, downtime, fcurrenttime):
        self.arrRet[0].append(videotime)
        self.arrRet[1].append(throughput)
        self.arrRet[2].append(bitrate)
        self.arrRet[3].append(secbuffer)
        self.arrRet[4].append(underruns)
        self.arrRet[5].append(downtime)
        self.arrRet[6].append(fcurrenttime)

    def start_watch(self):
        self.fCurrentTime = 0
        self.underruns = 0
        self.downtime = 0
        self.chunkIndex = 0
        self.videotime = 0
        self.partialDownload = 0
        self.subSecond = 0

    def status(self):
        temp = [self.throughput, self.bitrate]
        for subarr in self.arrRet:
            if len(subarr) >= 1:
                temp.append(subarr[len(subarr)-1])
        return temp

    def step(self, throughput, bitrate, throughput_duration):
        self.throughput = throughput
        self.bitrate - bitrate
        try:
            # print("Iteration", fCurrentTime, videotime, secBuffer, self.debug[chunkIndex],
            # videotime + secBuffer + self.chunks[chunkIndex])
            chunk = self.chunks[self.chunkIndex]
        except IndexError:
            # print("Last Iteration", fCurrentTime, videotime, secBuffer, self.debug[chunkIndex-1],
            #      videotime + secBuffer)
            self.videotime += self.length - self.secBuffer - self.videotime
            self.fCurrentTime += self.length - self.secBuffer - self.videotime
            return True, self.status()
        fChunkSize = 1.0 * bitrate * chunk
        downloadTime = fChunkSize / throughput
        if self.secBuffer + chunk > self.bufferLimit:
            waitTime = self.secBuffer - (self.bufferLimit - chunk)
            if waitTime + self.subSecond >= 1:
                # print("Full Buffer", secBuffer, bufferLimit - chunk, chunk)
                self.videotime += 1 - self.subSecond
                self.secBuffer -= 1 - self.subSecond
                self.fCurrentTime += 1 - self.subSecond
                self.fCurrentTime = round(self.fCurrentTime)
                self.subSecond = 0
                self.update(self.videotime, throughput, bitrate,
                            self.secBuffer, self.underruns, self.downtime, self.fCurrentTime)
                self.step(throughput, bitrate)
                return False, self.status()
            else:
                # print("too far ahead", waitTime, subSecond, videotime, secBuffer, chunk)
                self.secBuffer -= waitTime
                self.subSecond += waitTime
                self.videotime += waitTime
                self.fCurrentTime += waitTime
                self.step(throughput, bitrate)
                return False, self.status()
        if self.subSecond + downloadTime > 1:
            timePassed = 1 - self.subSecond
            self.partialDownload = timePassed * throughput / bitrate
            self.chunks[self.chunkIndex] -= self.partialDownload

            # print("Partial download", subSecond, downloadTime, subSecond + downloadTime, chunk,
            #      self.chunks[chunkIndex], partialDownload)
            self.secBuffer -= timePassed
            self.videotime += timePassed
            self.fCurrentTime += timePassed
            self.fCurrentTime = round(self.fCurrentTime)

            if self.secBuffer < 0:
                self.videotime += self.secBuffer
                self.downtime -= self.secBuffer
                self.underruns += 1
                self.secBuffer = 0
            self.subSecond = 0
            self.update(self.videotime, throughput, bitrate,
                        self.secBuffer, self.underruns, self.downtime, self.fCurrentTime)
            self.step(throughput, bitrate)
            return False, self.status()
        self.chunkIndex += 1
        self.subSecond += downloadTime
        self.secBuffer -= downloadTime
        self.videotime += downloadTime
        self.fCurrentTime += downloadTime
        # print("moved on", subSecond)

        if self.secBuffer < 0:
            self.videotime += self.secBuffer
            self.downtime -= self.secBuffer
            self.underruns += 1
            self.secBuffer = 0
        self.secBuffer += chunk + self.partialDownload
        self.partialDownload = 0
        if self.subSecond == 1.0:
            self.subSecond = 0
            self.update(self.videotime, throughput, bitrate,
                        self.secBuffer, self.underruns, self.downtime, self.fCurrentTime)
        return False, self.status()

    def finish_watch(self):
        while round(self.videotime, 8) < round(self.length, 8):
            # print("i tried", videotime, self.length, secBuffer)
            if self.subSecond > 0 and self.secBuffer > 1:
                self.secBuffer -= 1-self.subSecond
                self.videotime += 1-self.subSecond
                self.fCurrentTime += 1-self.subSecond
                self.subSecond = 0
            elif self.secBuffer > 1:
                self.secBuffer -= 1
                self.videotime += 1
                self.fCurrentTime += 1
            else:
                self.videotime += self.secBuffer
                self.fCurrentTime += self.secBuffer
                self.secBuffer = 0
            throughput = "download finished"
            bitrate = "download finished"
            self.update(self.videotime, throughput, bitrate, self.secBuffer, self.underruns,
                        self.downtime, round(self.fCurrentTime, 5))
        return self.arrRet

    def simWatch(self, throughputs, bitrates, bufferLimit=5):
        secBuffer = 0
        fCurrentTime = 0
        underruns = 0
        downtime = 0
        chunkIndex = 0
        videotime = 0
        partialDownload = 0
        subSecond = 0
        while videotime + secBuffer < self.length:
            try:
                # print("Iteration", fCurrentTime, videotime, secBuffer, self.debug[chunkIndex],
                # videotime + secBuffer + self.chunks[chunkIndex])
                chunk = self.chunks[chunkIndex]
            except:
                # print("Last Iteration", fCurrentTime, videotime, secBuffer, self.debug[chunkIndex-1],
                #      videotime + secBuffer)
                videotime += self.length - secBuffer - videotime
                fCurrentTime += self.length - secBuffer - videotime
                continue
            throughput = float(throughputs[int(fCurrentTime) % len(throughputs)])
            bitrate = float(bitrates[int(chunkIndex) % len(bitrates)])

            fChunkSize = bitrate * chunk
            downloadTime = fChunkSize / throughput
            if secBuffer + chunk > bufferLimit:
                waitTime = secBuffer - (bufferLimit - chunk)
                if waitTime + subSecond >= 1:
                    # print("Full Buffer", secBuffer, bufferLimit - chunk, chunk)
                    videotime += 1 - subSecond
                    secBuffer -= 1 - subSecond
                    fCurrentTime += 1 - subSecond
                    fCurrentTime = round(fCurrentTime)
                    subSecond = 0
                    self.update(videotime, throughput, bitrate, secBuffer, underruns, downtime, fCurrentTime)
                    continue
                else:
                    # print("too far ahead", waitTime, subSecond, videotime, secBuffer, chunk)
                    secBuffer -= waitTime
                    subSecond += waitTime
                    videotime += waitTime
                    fCurrentTime += waitTime
                    continue
            if subSecond + downloadTime > 1:
                timePassed = 1 - subSecond
                partialDownload = timePassed * throughput / bitrate
                self.chunks[chunkIndex] -= partialDownload

                # print("Partial download", subSecond, downloadTime, subSecond + downloadTime, chunk,
                #      self.chunks[chunkIndex], partialDownload)
                secBuffer -= timePassed
                videotime += timePassed
                fCurrentTime += timePassed
                fCurrentTime = round(fCurrentTime)

                if secBuffer < 0:
                    videotime += secBuffer
                    downtime -= secBuffer
                    underruns += 1
                    secBuffer = 0
                subSecond = 0
                self.update(videotime, throughput, bitrate, secBuffer, underruns, downtime, fCurrentTime)
                continue
            chunkIndex += 1
            subSecond += downloadTime
            secBuffer -= downloadTime
            videotime += downloadTime
            fCurrentTime += downloadTime
            # print("moved on", subSecond)

            if secBuffer < 0:
                videotime += secBuffer
                downtime -= secBuffer
                underruns += 1
                secBuffer = 0
            secBuffer += chunk + partialDownload
            partialDownload = 0
            if subSecond == 1.0:
                subSecond = 0
                self.update(videotime, throughput, bitrate, secBuffer, underruns, downtime, fCurrentTime)
                continue
        '''
        for chunkIndex in range(len(self.chunks)):
            # TODO: DOESNT PROPERLY ACCOUNT STOPPING TO BUFFER
            # TODO: GO SEC BY SEC INSTEAD OF CHUNK BY CHUNK
            chunk = self.chunks[chunkIndex]
            throughput = throughputs[chunkIndex]
            bitrate = bitrates[chunkIndex]
            LastTime = fCurrentTime
            fChunkSize = bitrate*chunk
            downloadTime = fChunkSize/throughput
            fCurrentTime += downloadTime
            bufferLeft = secBuffer
            secBuffer -= downloadTime
            if secBuffer < 0:
                underrruns += 1
                downtime -= secBuffer
                secBuffer = 0
            secBuffer += chunk
            if secBuffer > bufferLimit:
                fCurrentTime += secBuffer - bufferLimit
                secBuffer -= secBuffer - bufferLimit

            #print(chunk, downloadTime, (fCurrentTime),(fCurrentTime-downloadTime), secBuffer)
            #print(int(LastTime), int(fCurrentTime))
            for temp in range(int(LastTime), int(fCurrentTime)):
                sec = temp+1
                delta = float(sec) - (fCurrentTime-downloadTime)
                if delta > 1:
                    delta = 1
                bufferLeft -= delta
                if bufferLeft < 0:
                    bufferLeft = 0
                arrRet[0].append(throughput)
                arrRet[1].append(bitrate)
                arrRet[2].append(bufferLeft)
                arrRet[3].append(underrruns)
                arrRet[4].append(downtime)
        for temp in range(int(fCurrentTime), int(self.length)):
            sec = temp + 1
            delta = float(sec) - (fCurrentTime - downloadTime)
            if delta > 1:
                delta = 1
            bufferLeft -= delta
            if bufferLeft < 0:
                bufferLeft = 0
            arrRet[0].append(throughput)
            arrRet[1].append(bitrate)
            arrRet[2].append(bufferLeft)
            arrRet[3].append(underrruns)
            arrRet[4].append(downtime)
        '''
        # print("Finished downloading", videotime, secBuffer, videotime+secBuffer, self.length)

        while round(videotime, 8) < round(self.length, 8):
            # print("i tried", videotime, self.length, secBuffer)
            if subSecond > 0 and secBuffer > 1:
                secBuffer -= 1-subSecond
                videotime += 1-subSecond
                fCurrentTime += 1-subSecond
                subSecond = 0
            elif secBuffer > 1:
                secBuffer -= 1
                videotime += 1
                fCurrentTime += 1
            else:
                videotime += secBuffer
                fCurrentTime += secBuffer
                secBuffer = 0
            throughput = float(throughputs[int(fCurrentTime) % len(throughputs)])
            bitrate = float(bitrates[int(fCurrentTime) % len(bitrates)])
            self.update(videotime, throughput, bitrate, secBuffer, underruns, downtime, round(fCurrentTime,5))
        return self.arrRet


if __name__ == '__main__':
    video = SimVideo()

    # print(video.chunks)

    Throughputs = []
    Bitrates = []

    for x in range(int(video.length) * 10):
        Throughputs.append(10*random.random())
        Bitrates.append(10*random.random())

    # step by step
    video.start_watch()
    done = False
    while(not done):
        done, msg = video.step(4*random.random()+2, 2+4*random.random())
        print(msg)
    var = video.finish_watch()

    # var = video.simWatch(Throughputs, Bitrates)
    print("Videotime: ")
    print(var[0])
    print("BufferLeft: ")
    print(var[3])
    print("Downtime: ")
    print(var[5])
    print("Current Time: ")
    print(var[6])

    print(video.length)
    print(var[6][len(var[0]) - 1])
