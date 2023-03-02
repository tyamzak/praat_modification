import pandas as pd
import os
from praatio import textgrid

class tgdata:

    def __init__(self, textgrid_file_path:str):

        textgrid_file = textgrid.openTextgrid(textgrid_file_path, includeEmptyIntervals=True)
        self.filename = os.path.basename(textgrid_file_path)
        self.ID = self.filename[0:3]
        self.RECN = self.filename[3:6]
        self.Date = self.filename[6:8]+ "-" + self.filename[8:10] + "-" + self.filename[10:12]
        # ,'ID','RECN','Date'

        self.nsyll = len([x for x in textgrid_file._tierDict['DFauto (English)'].entries if x.label == 'v'])
        # self.nsyll = len(textgrid_file._tierDict['Nuclei'].entries)
        nsounding   = 0
        npause_ps = 0
        npause_psb = 0
        speakingtot = 0
        silenttot_ps = 0
        silenttot_psb = 0
        for interval in textgrid_file._tierDict['Phrases'].entries:
            if interval.label == 'pr':
                nsounding   += 1
                ts = interval.start
                te = interval.end
                speakingtot += te - ts
            elif interval.label == 'ps':
                npause_ps += 1
                ts = interval.start
                te = interval.end
                silenttot_ps += te - ts
            elif interval.label == 'psb':
                npause_psb += 1
                ts = interval.start
                te = interval.end
                silenttot_psb += te - ts
            else:
                # print('想定外のラベル: Phrases   ' + interval.label)
                pass

        self.silenttot = silenttot_ps + silenttot_psb
        self.silenttot_ps = silenttot_ps
        self.silenttot_psb = silenttot_psb

        self.speakingtot = speakingtot
        
        self.asd = self.speakingtot / self.nsyll
        self.nsounding = nsounding
        self.npause = npause_ps + npause_psb
        self.npause_ps = npause_ps
        self.npause_psb = npause_psb

        nrFP = 0
        ts = 0
        te = 0
        tFP = 0.0
        nrRP = 0
        tRP = 0.0
        #個数はTier3からとる
        for start, end, label in textgrid_file._tierDict['DFauto (English)'].entries:
            if label == 'fp':
                nrFP += 1

            elif label == 'rp':
                nrRP += 1

        # 時間はTier2からとる
        for start, end, label in textgrid_file._tierDict['Phrases'].entries:
            if label == 'fp':
                ts = start
                te = end
                tFP += (te - ts)
            elif label == 'rp':
                ts = start
                te = end
                tRP += (te - ts)
        self.nrFP = nrFP
        self.tFP = tFP
        self.nrRP = nrRP
        self.tRP = tRP
        # speechrate(nsyll/dur)
        self.durs = self.tFP + self.tRP + self.speakingtot + self.silenttot_ps + self.silenttot_psb
        # self.speechrate = self.nsyll / self.durs
        #SR = voicedcount / dur * 60；Repair(rp)は含むが、filled pause(fp)は含まない
        self.SR = round((self.nsyll + self.nrRP) / self.durs * 60 ,2)
        #SRP = voicedcount / dur * 60；Repair(rp)もfilled pause(fp)も含まない
        self.SRP = round( (self.nsyll) / self.durs * 60 ,2)

        # articulation_rate(nsyll/phonationtime)
        # self.articulation_rate = self.nsyll / self.phonationtime

        # AR = voicedcount / speakingtot * 60；Repair(rp)は含むが、filled pause(fp)は含まない
        self.AR = round((self.nsyll + self.nrRP) / (self.speakingtot + self.tRP) * 60 ,2)

        # ARP = voicedcount / speakingtot * 60;  Repair(rp)もfilled pause(fp)も含まない
        self.ARP = round((self.nsyll) / self.speakingtot * 60 ,2)

        # Mean Length of Runs ポーズとポーズの間で発話された音節数の平均。
        # 除外されない全てのPhrase番号のところの音節数の平均の値
        # ３番目のtierに、rpか、fpがある時には音節数に加えない。
        try:
            self.MLoR = round((self.nsyll) / (self.nsounding) ,2)
        except ZeroDivisionError:
            self.MLoR = 0

        # PhonRat= speakingtot / dur * 100；発話率（％表示）
        self.PhonRat = format((self.speakingtot + self.tRP) / self.durs * 100, ".2f")

        # SPauseFreq ; １分間に産出されたSilent Pauseの数; 
        # ２番目のtierの番号が入っていない境界部分の数 / dur * 60；発話開始前と開始後の空白を除く。
        self.SPauseFreq = round((self.npause) / self.durs * 60 , 2)

        # SPauseDur =  Silent Pauseのの長さの平均（秒）; 
        # サイレントポーズの長さの平均；２番目のtierの番号が入っていない
        # 部分の長さの平均；発話開始前と開始後の空白を除く。
        try:
            self.SPauseDur = round(self.silenttot / self.npause ,2)
        except ZeroDivisionError:
            self.SPauseDur = 0

        # FPauseFreq ;  １分間に産出されたFilled Pauseの数
        self.FPauseFreq = round(self.nrFP / self.durs * 60 ,2)

        # FPauseDur；１分間に産出されたFilled Pauseの長さの合計（秒）
        self.FPauseDur = round( self.tFP / self.durs * 60 ,2)

        # RpFreq ;  １分間に産出されたRepairの音節数
        self.RpFreq = round( self.nrRP / self.durs * 60 ,2)

        # RpDur；Repairの長さの合計（秒）
        self.RpDur = round(self.tRP / self.durs * 60 ,2)

        # SBPauseFreq ; ２番目のtierに、「"psb"がはいっている境界部分」の数 / dur * 60
        self.SBPauseFreq = round(self.npause_psb / self.durs * 60 ,2)

        # SBPauseDur ; ２番目のtierに、「"psb"がはいっている境界部分」の長さの平均；
        self.SBPauseDur = round( self.silenttot_psb / self.npause_psb ,2)

        # SWPauseFreq ; ２番目のtierに、「"ps"がはいっている境界部分」の数 / dur * 60；
        self.SWPauseFreq = round(self.npause_ps / self.durs * 60 ,2)

        # SWPauseDur ; 2番目のtierに、「"ps"がはいっている境界部分」の長さの平均；
        self.SWPauseDur = round(self.silenttot_ps / self.npause_ps ,2)





def tg_L4rp_to_L3rp(textgrid_file_path):


    # TextGridを読み込む
    tg = textgrid.openTextgrid(textgrid_file_path,includeEmptyIntervals=True)

    # Tier4に"rp"というラベルのついたintervalを検索する
    rp_intervals = []
    for interval in tg._tierDict["Repair"].entries:
        if interval.label == "rp":
            rp_intervals.append(interval)

    # Tier3に"v"というラベルのついたintervalのラベルを変更する
    tier3 = tg._tierDict['DFauto (English)']
    for interval in tier3.entries:
        for rp_interval in rp_intervals:
            if interval.start >= rp_interval.start and interval.end <= rp_interval.end:
                if interval.label == "v":
                    tier3.insertEntry((interval.start, interval.end, "rp"), collisionMode='replace', collisionReportingMode='silence')

    #  Tier2に"pr"というラベルの付いたintervalのラベルを変更する
    tier2 = tg._tierDict['Phrases']
    for interval in tier2.entries:
        for rp_interval in rp_intervals:
            if interval.start >= rp_interval.start and interval.end <= rp_interval.end:
                if interval.label == "pr":
                    tier2.insertEntry((interval.start, interval.end, "rp"), collisionMode='replace', collisionReportingMode='silence')

    # Tire3で"fp"の部分は、Tier2で"fp"とするプログラム

    # Tier3に"fp"というラベルのついたintervalを検索する
    fp_intervals = []
    for interval in tg._tierDict["DFauto (English)"].entries:
        if interval.label == "fp":
            fp_intervals.append(interval)

    #  Tier2に"pr"というラベルの付いたintervalのラベルを変更する
    tier2 = tg._tierDict['Phrases']
    for interval in tier2.entries:
        for fp_interval in fp_intervals:
            if interval.start >= fp_interval.start and interval.end <= fp_interval.end:
                if interval.label == "pr":
                    tier2.insertEntry((interval.start, interval.end, "fp"), collisionMode='replace', collisionReportingMode='silence')

    # 変更後のTextGridを上書き保存する
    tg.save(textgrid_file_path,format="short_textgrid", includeBlankSpaces=True)

# filename = "Sample_filled_pause_and_long_I_auto_230227_After_Edit_TextGridoutput.TextGrid"

from glob import glob

filelists = glob("./tgfiles/*.TextGrid")

dflist = []
for filename in filelists:
    tg_L4rp_to_L3rp(filename)

    tgd = tgdata(filename)

    df = pd.DataFrame([tgd.__dict__])
    dflist.append(df)

acum_df = pd.concat(dflist)
acum_df.to_csv("output.csv", index=False )
acum_df.to_excel("output.xlsx", index = False)
print('finished')