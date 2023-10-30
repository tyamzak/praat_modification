import pandas as pd
import os
import math
from praatio import textgrid

from typing import Tuple, List
import shutil


class tgdata:
    def __init__(self, textgrid_file_path: str):
        textgrid_file = textgrid.openTextgrid(
            textgrid_file_path, includeEmptyIntervals=True
        )
        self.filename = os.path.basename(textgrid_file_path)

        textgrid_file = self.calc_1(textgrid_file)

        # - Tier4に”rp”が入っている境界内の、Tier3の”v”を”rp”に置き換える
        textgrid_file = self.T4rp_T3v2rp(textgrid_file)

        # - Tier2の境界がfpであるTier3のvをfpに変える(Speech rateの計算前に実行する)
        textgrid_file = self.T2fp_T3v2fp(textgrid_file)

        textgrid_file = self.calc_2(textgrid_file)

        # - Tier4に”rp”が入っている境界と同じ境界をTier2に作り、”rp”を入れる
        textgrid_file = self.T4rp_T2rp(textgrid_file)

        textgrid_file = self.calc_3(textgrid_file)

        self.textgrid_file = textgrid_file

    def save(
        self,
        output_path: str,
        format: str = "short_textgrid",
        includeBlankSpaces: bool = True,
    ):
        """Save the Textgrid to the specified output path."""
        self.textgrid_file.save(
            output_path, format=format, includeBlankSpaces=includeBlankSpaces
        )

    def calc_1(self, textgrid_file: textgrid) -> textgrid:
        """Phonation Rate (%)
            PhonRat=speakingtot(Tier2: pr)/dur (Tier2: ps+psb+pr+fp)* 100
             Frequency of Silent Pause per minute
            SPauseFreq=Tier2: # (the number) of “ps” or “psb”/dur (Tier2: ps+psb+pr+fp)*60
             Mean Duration of Silent Pause
            SPauseDur =Tier2: Mean duration of “ps” and “psb”
             Frequency of Between-Clause Silent Pause per minute
            SBPauseFreq=Tier2: # of “psb”/ dur (Tier2: ps+psb+pr+fp)*60
             Mean Duration of Between-Clause Silent Pause
            SBPauseDur =Tier2: Mean duration of “psb”
             Frequency of Within-Clause Silent Pause per minute
            SWPauseFreq=Tier2: # of “ps”/ dur (Tier2: ps+psb+pr+fp)*60
             Mean Duration of Within-Clause Silent Pause
            SWPauseDur=Tier2: Mean duration of “ps”
             Frequency of Filled Pause per minute
            FPauseFreq=Tier2: # of “fp”/ dur (Tier2: ps+psb+pr+fp)*60
            Mean Duration of Filled Pause per minute
            FPauseDur=Tier2: Mean duration of “fp”

        Args:
            textgrid_file (textgrid): _description_

        Returns:
            textgrid: _description_
        """

        self.ID = self.filename[0:3]
        self.RECN = self.filename[3:6]
        self.Date = (
            self.filename[6:8] + "-" + self.filename[8:10] + "-" + self.filename[10:12]
        )
        # ,'ID','RECN','Date'

        # self.nsyll = len(textgrid_file._tierDict['Nuclei'].entries)
        nsounding = 0
        npause_ps = 0
        npause_psb = 0
        speakingtot = 0
        silenttot_ps = 0
        silenttot_psb = 0
        t2_pr_dur = 0
        t2_ps_dur = 0
        t2_psb_dur = 0
        for interval in textgrid_file._tierDict["Phrases"].entries:
            if interval.label == "pr":
                nsounding += 1
                ts = interval.start
                te = interval.end
                speakingtot += te - ts
                t2_pr_dur += te - ts
            elif interval.label == "ps":
                npause_ps += 1
                ts = interval.start
                te = interval.end
                silenttot_ps += te - ts
                t2_ps_dur += te - ts
            elif interval.label == "psb":
                npause_psb += 1
                ts = interval.start
                te = interval.end
                silenttot_psb += te - ts
                t2_psb_dur += te - ts
            else:
                # print('想定外のラベル: Phrases   ' + interval.label)
                pass

        self.t2_pr_dur = t2_pr_dur
        self.t2_ps_dur = t2_ps_dur
        self.t2_psb_dur = t2_psb_dur
        self.silenttot = silenttot_ps + silenttot_psb
        self.silenttot_ps = silenttot_ps
        self.silenttot_psb = silenttot_psb

        self.speakingtot = speakingtot

        # self.asd = self.speakingtot / self.nsyll
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

        # 個数はTier2からとる
        for start, end, label in textgrid_file._tierDict["Phrases"].entries:
            if label == "fp":
                nrFP += 1

            elif label == "rp":
                nrRP += 1

        # 時間はTier2からとる
        for start, end, label in textgrid_file._tierDict["Phrases"].entries:
            if label == "fp":
                ts = start
                te = end
                tFP += te - ts
            elif label == "rp":
                ts = start
                te = end
                tRP += te - ts

        self.nrFP = nrFP
        self.tFP = tFP
        self.nrRP = nrRP
        self.tRP = tRP
        # speechrate(nsyll/dur)
        self.durs = (
            self.tFP
            + self.tRP
            + self.speakingtot
            + self.silenttot_ps
            + self.silenttot_psb
        )

        #############################################
        # PhonRat= speakingtot / dur * 100；発話率（％表示）
        # self.PhonRat = format((self.speakingtot + self.tRP) / self.durs * 100, ".2f")
        #############################################

        # 1 Phonation Rate (%) PhonRat=speakingtot(Tier2: pr)/dur (Tier2: ps+psb+pr+fp)* 100
        self.PhonRat = format(
            (self.t2_pr_dur)
            / (self.t2_ps_dur + self.t2_psb_dur + self.t2_pr_dur + self.tFP)
            * 100,
            ".2f",
        )

        # SPauseFreq ; １分間に産出されたSilent Pauseの数;
        # ２番目のtierの番号が入っていない境界部分の数 / dur * 60；発話開始前と開始後の空白を除く。
        # self.npause = npause_ps + npause_psb
        self.SPauseFreq = round((self.npause) / self.durs * 60, 2)

        #  Frequency of Silent Pause per minute
        # SPauseFreq=Tier2: # (the number) of “ps” or “psb”/dur (Tier2: ps+psb+pr+fp)*60

        # SPauseDur =  Silent Pauseのの長さの平均（秒）;
        # サイレントポーズの長さの平均；２番目のtierの番号が入っていない
        # 部分の長さの平均；発話開始前と開始後の空白を除く。
        # Mean Duration of Silent Pause
        # SPauseDur =Tier2: Mean duration of “ps” and “psb”
        try:
            # self.SPauseDur = round(self.silenttot / self.npause, 2) # 表現変更
            self.SPauseDur = round((self.t2_ps_dur + self.t2_psb_dur) / self.npause, 2)
        except ZeroDivisionError:
            self.SPauseDur = 0

        # SBPauseFreq ; ２番目のtierに、「"psb"がはいっている境界部分」の数 / dur * 60
        # Frequency of Between-Clause Silent Pause per minute
        # SBPauseFreq=Tier2: # of “psb”/ dur (Tier2: ps+psb+pr+fp)*60
        # self.SBPauseFreq = round(self.npause_psb / self.durs * 60, 2)
        self.SBPauseFreq = round(
            self.npause_psb
            / (self.t2_ps_dur + self.t2_psb_dur + self.t2_pr_dur + self.tFP)
            * 60,
            2,
        )

        # SBPauseDur ; ２番目のtierに、「"psb"がはいっている境界部分」の長さの平均；
        # Mean Duration of Between-Clause Silent Pause
        # SBPauseDur =Tier2: Mean duration of “psb”
        if self.npause_psb == 0:
            self.SBPauseDur = 0
        else:
            self.SBPauseDur = round(self.silenttot_psb / self.npause_psb, 2)

        # SWPauseFreq ; ２番目のtierに、「"ps"がはいっている境界部分」の数 / dur * 60；
        # Frequency of Within-Clause Silent Pause per minute
        # SWPauseFreq=Tier2: # of “ps”/ dur (Tier2: ps+psb+pr+fp)*60
        # self.SWPauseFreq = round(self.npause_ps / self.durs * 60, 2)
        self.SWPauseFreq = round(
            self.npause_ps
            / (self.t2_psb_dur + self.t2_pr_dur + self.t2_ps_dur + self.tFP)
            * 60,
            2,
        )

        # Mean Duration of Within-Clause Silent Pause
        # SWPauseDur=Tier2: Mean duration of “ps”
        try:
            # SWPauseDur ; 2番目のtierに、「"ps"がはいっている境界部分」の長さの平均；
            self.SWPauseDur = round(self.silenttot_ps / self.npause_ps, 2)
        except ZeroDivisionError:
            self.SWPauseDur = 0

        #  Frequency of Filled Pause per minute
        # FPauseFreq=Tier2: # of “fp”/ dur (Tier2: ps+psb+pr+fp)*60
        self.FPauseFreq = round(
            self.nrFP
            / (self.t2_psb_dur + self.t2_pr_dur + self.t2_ps_dur + self.tFP)
            * 60,
            2,
        )

        # Mean Duration of Filled Pause ###perminuteを省いた　20230829
        # FPauseDur=Tier2: Mean duration of “fp”

        # TODO: zero division error を全てに適用するか確認する
        try:
            self.FPauseDur = round(
                self.tFP / self.nrFP,
                2,
            )
        except ZeroDivisionError:
            self.FPauseDur = 0

        return textgrid_file

    def calc_2(self, textgrid_file: textgrid) -> textgrid:
        """
        Speech rate
        SR = Tier3: v+rp/ dur (Tier2: ps+psb+pr+fp)* 60
        Articulation rate
        AR = (Tier3: v+rp) / speakingtot (Tier2: pr) * 60
        Mean Length of Runs
        MLoR = Tier2: prの境界内にあるTier3のvの数を、全てのprの境界内で平均する
        (もともとTier3でvだったが、Tier2のfp境界内、Tier4のrp境界内のvは、上の処理14), 15)で、それぞれfp, rpに置き換わっている)。

                Args:
                    textgrid_file (textgrid): _description_

                Returns:
                    textgrid: _description_
        """

        nsyll = len(
            [
                x
                for x in textgrid_file._tierDict["DFauto (English)"].entries
                if x.label == "v"
            ]
        )

        # self.nsyll = len(textgrid_file._tierDict['Nuclei'].entries)
        nsounding = 0
        npause_ps = 0
        npause_psb = 0
        speakingtot = 0
        silenttot_ps = 0
        silenttot_psb = 0
        t2_pr_dur = 0
        t2_ps_dur = 0
        t2_psb_dur = 0
        for interval in textgrid_file._tierDict["Phrases"].entries:
            if interval.label == "pr":
                nsounding += 1
                ts = interval.start
                te = interval.end
                speakingtot += te - ts
                t2_pr_dur += te - ts
            elif interval.label == "ps":
                npause_ps += 1
                ts = interval.start
                te = interval.end
                silenttot_ps += te - ts
                t2_ps_dur += te - ts
            elif interval.label == "psb":
                npause_psb += 1
                ts = interval.start
                te = interval.end
                silenttot_psb += te - ts
                t2_psb_dur += te - ts
            else:
                # print('想定外のラベル: Phrases   ' + interval.label)
                pass

        T3nrFP = 0
        T3nrRP = 0
        ts = 0
        te = 0
        tFP = 0.0
        tRP = 0.0
        # 個数はTier3からとる
        for start, end, label in textgrid_file._tierDict["DFauto (English)"].entries:
            if label == "fp":
                T3nrFP += 1

            elif label == "rp":
                T3nrRP += 1

        # 時間はTier2からとる
        for start, end, label in textgrid_file._tierDict["Phrases"].entries:
            if label == "fp":
                ts = start
                te = end
                tFP += te - ts
            elif label == "rp":
                ts = start
                te = end
                tRP += te - ts

        self.T3nrFP = T3nrFP
        self.tFP = tFP
        self.T3nrRP = T3nrRP

        # SR = voicedcount / dur * 60；Repair(rp)は含むが、filled pause(fp)は含まない
        self.SR = round(
            (nsyll + T3nrRP) / (t2_ps_dur + t2_psb_dur + t2_pr_dur + tFP) * 60, 2
        )

        # AR = voicedcount / speakingtot * 60；Repair(rp)は含むが、filled pause(fp)は含まない
        self.AR = round((nsyll + T3nrRP) / (speakingtot) * 60, 2)

        # Mean Length of Runs
        # MLoR = Tier2: prの境界内にあるTier3のvの数を、全てのprの境界内で平均する
        # (もともとTier3でvだったが、Tier2のfp境界内、Tier4のrp境界内のvは、
        # 上の処理14), 15)で、それぞれfp, rpに置き換わっている)。

        count_T3v_in_T2pr = 0

        for t3start, t3end, t3label in textgrid_file.tiers[2].entries:
            if t3label == "v":
                for t2start, t2end, t2label in textgrid_file.tiers[1].entries:
                    if t2label == "pr":
                        if t2start <= t3start and t3end <= t2end:
                            count_T3v_in_T2pr += 1

        # そこで、MLoRの計算に、次の条件を加えていただけないでしょうか。
        # 「一つのTier2"pr"の範囲内のTier3の記号に一つも"v"がない場合、MLoRの計算の"pr"とカウントしない。」
        # この時点でのTier3には、"v", "rp", "fp"しか存在しませんので、
        # 「一つのTier2"pr"の範囲内のTier3の記号に"rp"また"fp"しかない場合、MLoRの計算の"pr"とカウントしない。」
        # と同義となるはずです。

        count_T2pr = 0
        for t2start, t2end, t2label in textgrid_file.tiers[1].entries:
            if t2label == "pr":
                vexist = False
                for t3start, t3end, t3label in textgrid_file.tiers[2].entries:
                    if t2start <= t3start and t3end <= t2end and t3label == "v":
                        vexist = True
                        break

                if vexist:
                    count_T2pr += 1
                    # print(f"t2start:{t2start} t2end:{t2end}")

        try:
            self.MLoR = round((count_T3v_in_T2pr) / (count_T2pr), 2)
        except ZeroDivisionError:
            self.MLoR = 0

        return textgrid_file

    def calc_3(self, textgrid_file: textgrid) -> textgrid:
        """
        Speech rate pruned
        SRP = Tier3 (# of “v”) / dur (Tier2: ps+psb+fp+pr)*60
        Articulation rate pruned
        ARP = Tier3 (# of “v”) / dur (Tier2: pr)*60
        Frequency of Repair per minute; １分間に産出されたRepairの音節数。
        RpFreq = Tier3: # of “rp”/dur (Tier 2: ps+psb+pr+fp+rp)*60
        Summed Duration of Repair per minute; １分間に産出されたRepairの長さ。
        RpDur = Tier2: summed duration of “rp”/dur (Tier 2: ps+psb+pr+fp+rp)*60

                        Args:
                            textgrid_file (textgrid): _description_

                        Returns:
                            textgrid: _description_
        """

        self.ID = self.filename[0:3]
        self.RECN = self.filename[3:6]
        self.Date = (
            self.filename[6:8] + "-" + self.filename[8:10] + "-" + self.filename[10:12]
        )
        # ,'ID','RECN','Date'

        self.nsyll = len(
            [
                x
                for x in textgrid_file._tierDict["DFauto (English)"].entries
                if x.label == "v"
            ]
        )

        # self.nsyll = len(textgrid_file._tierDict['Nuclei'].entries)
        nsounding = 0
        npause_ps = 0
        npause_psb = 0
        speakingtot = 0
        silenttot_ps = 0
        silenttot_psb = 0
        t2_pr_dur = 0
        t2_ps_dur = 0
        t2_psb_dur = 0
        for interval in textgrid_file._tierDict["Phrases"].entries:
            if interval.label == "pr":
                nsounding += 1
                ts = interval.start
                te = interval.end
                speakingtot += te - ts
                t2_pr_dur += te - ts
            elif interval.label == "ps":
                npause_ps += 1
                ts = interval.start
                te = interval.end
                silenttot_ps += te - ts
                t2_ps_dur += te - ts
            elif interval.label == "psb":
                npause_psb += 1
                ts = interval.start
                te = interval.end
                silenttot_psb += te - ts
                t2_psb_dur += te - ts
            else:
                # print('想定外のラベル: Phrases   ' + interval.label)
                pass

        self.t2_pr_dur = t2_pr_dur
        self.t2_ps_dur = t2_ps_dur
        self.t2_psb_dur = t2_psb_dur
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
        T3nrFP = 0
        T3nrRP = 0

        # 個数はTier2からとる
        for start, end, label in textgrid_file._tierDict["Phrases"].entries:
            if label == "fp":
                nrFP += 1

            elif label == "rp":
                nrRP += 1

        # 個数はTier3からとる
        for start, end, label in textgrid_file._tierDict["DFauto (English)"].entries:
            if label == "fp":
                T3nrFP += 1

            elif label == "rp":
                T3nrRP += 1

        # 時間はTier2からとる
        for start, end, label in textgrid_file._tierDict["Phrases"].entries:
            if label == "fp":
                ts = start
                te = end
                tFP += te - ts
            elif label == "rp":
                ts = start
                te = end
                tRP += te - ts
        self.nrFP = nrFP
        self.tFP = tFP
        self.nrRP = nrRP
        self.tRP = tRP
        # speechrate(nsyll/dur)
        self.durs = (
            self.tFP
            + self.tRP
            + self.speakingtot
            + self.silenttot_ps
            + self.silenttot_psb
        )

        # SRP = voicedcount / dur * 60；Repair(rp)もfilled pause(fp)も含まない
        # Speech rate pruned
        # SRP = Tier3 (# of “v”) / dur (Tier2: ps+psb+fp+pr)*60

        self.SRP = round(
            (self.nsyll) / (t2_psb_dur + t2_ps_dur + t2_pr_dur + tFP) * 60, 2
        )

        # Frequency of Repair per minute; １分間に産出されたRepairの音節数。
        # RpFreq = Tier3: # of “rp”/dur (Tier 2: ps+psb+pr+fp+rp)*60
        # Summed Duration of Repair per minute; １分間に産出されたRepairの長さ。
        # RpDur = Tier2: summed duration of “rp”/dur (Tier 2: ps+psb+pr+fp+rp)*60

        # Articulation rate pruned
        # ARP = Tier3 (# of “v”) / dur (Tier2: pr)*60

        # ARP = voicedcount / speakingtot * 60;  Repair(rp)もfilled pause(fp)も含まない
        self.ARP = round((self.nsyll) / t2_pr_dur * 60, 2)

        # Frequency of Repair per minute; １分間に産出されたRepairの音節数。
        # RpFreq = Tier3: # of “rp”/dur (Tier 2: ps+psb+pr+fp+rp)*60

        # RpFreq ;  １分間に産出されたRepairの音節数
        self.RpFreq = round(
            T3nrRP / (t2_psb_dur + t2_ps_dur + t2_pr_dur + tFP + tRP) * 60, 2
        )

        # RpDur；Repairの長さの合計（秒）
        self.RpDur = round(
            self.tRP / (t2_psb_dur + t2_ps_dur + t2_pr_dur + tFP + tRP) * 60, 2
        )

        textgrid_file = self.vl_jp_modification(textgrid_file)

        self.calculate_duration(textgrid_file)

        return textgrid_file

    def T2fp_T3v2fp(self, textgrid_file: textgrid) -> textgrid:
        # - Tier2の境界がfpであるTier3のvをfpに変える(Speech rateの計算前に実行する)

        # - Tier2の境界がfpであるTier3のvをfpに変える(Speech rateの計算前に実行する)
        for t3start, t3end, t3label in textgrid_file.tiers[2].entries:
            if t3label == "v":
                for t2start, t2end, t2label in textgrid_file.tiers[1].entries:
                    if t2label == "fp":
                        if t2start <= t3start and t3end <= t2end:
                            textgrid_file.tiers[2].insertEntry(
                                (t3start, t3end, "fp"),
                                collisionMode="replace",
                                collisionReportingMode="silence",
                            )

        return textgrid_file

    def T4rp_T3v2rp(self, textgrid_file: textgrid) -> textgrid:
        """Tier4に”rp”が入っている境界内の、Tier3の”v”を”rp”に置き換える

        Args:
            textgrid_file (textgrid): _description_

        Returns:
            textgrid: _description_
        """

        for t3start, t3end, t3label in textgrid_file.tiers[2].entries:
            if t3label == "v":
                for t4start, t4end, t4label in textgrid_file.tiers[3].entries:
                    if t4label == "rp":
                        if t4start <= t3start and t3end <= t4end:
                            textgrid_file.tiers[2].insertEntry(
                                (t3start, t3end, "rp"),
                                collisionMode="replace",
                                collisionReportingMode="silence",
                            )

        return textgrid_file

    def T4rp_T2rp(self, textgrid_file: textgrid) -> textgrid:
        """- Tier4に”rp”が入っている境界と同じ境界をTier2に作り、”rp”を入れる

        Returns:
            _type_: textgrid
        """

        for t4start, t4end, t4label in textgrid_file.tiers[3].entries:
            if t4label == "rp":
                # if t4start <= t3start and t3end <= t4end:
                textgrid_file.tiers[1].insertEntry(
                    (t4start, t4end, "rp"),
                    collisionMode="replace",
                    collisionReportingMode="silence",
                )
        # 一番簡単な解決法は、処理追加の４番目を行ったあとに、最初と最後の空白を除いた空白に、
        # すべて"pr"を入れる、というものだと思います
        lastend = 0
        endindex = len(textgrid_file.tiers[1].entries) - 1
        for i, item in enumerate(textgrid_file.tiers[1].entries):
            start = item[0]
            end = item[1]
            label = item[2]

            if lastend != 0 and start != lastend:
                textgrid_file.tiers[1].insertEntry(
                    (lastend, start, "pr"),
                    collisionMode="replace",
                    collisionReportingMode="silence",
                )

            if i != 0 and i != endindex:
                if label == "":
                    textgrid_file.tiers[1].insertEntry(
                        (start, end, "pr"),
                        collisionMode="replace",
                        collisionReportingMode="silence",
                    )
            lastend = end
        return textgrid_file

    def vl_jp_modification(self, tg: textgrid) -> textgrid:
        """
        fluencyの処理の後に行う
        Tier5 jpがある範囲において、Tier3のv:labelをjp:labelに変更する
        長さが500ms以上の母音であれば、Tier3の”v”を”vl”に書き換える
        Args:
            tg (textgrid): _description_
        """

        # Tier5に"jp"というラベルのついたintervalを検索する
        jp_intervals = []
        if "Japanese" in tg._tierDict.keys():
            for interval in tg._tierDict["Japanese"].entries:
                if interval.label == "jp":
                    jp_intervals.append(interval)

        # Tier3に"v"というラベルのついたintervalのラベルを変更する
        tier3 = tg._tierDict["DFauto (English)"]
        for interval in tier3.entries:
            for jp_interval in jp_intervals:
                if (
                    interval.start >= jp_interval.start
                    and interval.end <= jp_interval.end
                ):
                    if interval.label == "v":
                        tier3.insertEntry(
                            (interval.start, interval.end, "jp"),
                            collisionMode="replace",
                            collisionReportingMode="silence",
                        )

            if interval.label == "v":
                if (interval.end - interval.start) >= 0.5:
                    tier3.insertEntry(
                        (interval.start, interval.end, "vl"),
                        collisionMode="replace",
                        collisionReportingMode="silence",
                    )

        return tg

    def calculate_duration(self, tg: textgrid) -> (float, float):
        # 「Tier2の"pr"の直後に"fp"また"rp"が来る場合は、その"pr"の最後の"v"を"vf"としない。」
        # 言い換えると、
        # 「"pr"の最後の"v"を"vf"とするのは、そのあとが、"ps", "psb", また最終行のみとする。」
        total_v_entries = []
        max_and_min_in_prs = []
        max_and_min_in_PitRangeAv = []
        max_and_min_in_IntRangeAv = []
        undefined = 0

        v_entries = []
        for l3index, v in enumerate(tg._tierDict["DFauto (English)"].entries):
            dfeng_entry = v
            is_v = False
            is_inPR = False

            # 空白は無視
            if dfeng_entry.label == "":
                continue

            # labelがvかvfの場合
            if dfeng_entry.label in ["v", "vf"]:
                is_v = True

            for l2index, ph_entry in enumerate(tg._tierDict["Phrases"].entries):
                is_nextl2_fp = False

                # Tier2 Phrases で　PRの開始と終了を取得する pr_start, pr_end,
                if ph_entry.label == "pr":
                    pr_start = ph_entry.start
                    pr_end = ph_entry.end

                    # l2indexがlen(tg._tierDict["Phrases"].entries)-1ではないとき
                    if l2index != len(tg._tierDict["Phrases"].entries):
                        if tg._tierDict["Phrases"].entries[l2index + 1].label == "fp":
                            is_nextl2_fp = True

                    if pr_start <= dfeng_entry.start and dfeng_entry.end <= pr_end:
                        is_inPR = True
                        break

            # Pitch用の計算###########################
            f0 = tg._tierDict["Pitch"].entries[l3index].label

            # Intensity用の計算########################
            dB = tg._tierDict["Intensity"].entries[l3index].label

            # f0が--undefined--だった場合、一つ前のPitch_PPD_validを無効にする
            if f0 == "--undefined--" and l3index != 0:
                Mel = "--undefined--"
                v_entries[-1]["Pitch_PPD_valid"] = False
                undefined += 1
            else:
                Mel = 2595 * math.log10(1 + float(f0) / 700)

            dict_entry = {
                "start": dfeng_entry.start,
                "end": dfeng_entry.end,
                "duration": dfeng_entry.end - dfeng_entry.start,
                "duration_valid": True,
                "others_valid": True,
                "is_inPR": is_inPR,
                "is_lastv_inPR": False,
                "is_nextl2_fp": is_nextl2_fp,
                "dB": float(dB),
                "is_v": is_v,
                "f0": f0,
                "Mel": Mel,
            }

            v_entries.append(dict_entry)

        # Tier2 pr 内の最後のTier3vの判定を追加する
        for l2index, ph_entry in enumerate(tg._tierDict["Phrases"].entries):
            # Tier2 Phrases で　PRの開始と終了を取得する pr_start, pr_end,
            if ph_entry.label == "pr":
                pr_start = ph_entry.start
                pr_end = ph_entry.end
                last_index = None
                for i in range(0, len(v_entries)):
                    if (
                        pr_start <= v_entries[i]["start"]
                        and v_entries[i]["end"] <= pr_end
                        and v_entries[i]["is_v"]
                    ):
                        last_index = i

                if last_index is not None:
                    v_entries[last_index]["is_lastv_inPR"] = True

        # 絶対値と平均を取得していく
        for i in range(0, len(v_entries)):
            # vじゃなかったら計算対象から外す
            if v_entries[i]["is_v"] == False:
                v_entries[i]["duration_valid"] = False
                v_entries[i]["others_valid"] = False
                if i > 0:
                    # 前のペアも計算対象から外す
                    v_entries[i - 1]["duration_valid"] = False

            # Tier2のPR内でなかった場合
            if v_entries[i]["is_inPR"] == False:
                # 計算対象から外す
                v_entries[i]["duration_valid"] = False
                v_entries[i]["others_valid"] = False

            # PR内の最後のvだった場合、
            if i > 0 and v_entries[i]["is_lastv_inPR"] == True:
                # durtion_validをFalseにする
                v_entries[i]["duration_valid"] = False

                # もし次がfpのpr内の最後のvじゃなかったら
                if (
                    i > 0
                    and v_entries[i]["is_nextl2_fp"] == False
                    and v_entries[i - 1]["is_inPR"] == True
                ):
                    # さらにもう１つ前のduration_validをFalseにする
                    v_entries[i - 1]["duration_valid"] = False

                    # others_validをFalseにする
                    v_entries[i]["others_valid"] = False

            if i == len(v_entries) - 1:
                # 最後の一つ前から最後までの範囲を無効にする
                v_entries[i - 1]["duration_valid"] = False
                v_entries[i]["duration_valid"] = False

                # others_validは最後のみ無効にする
                v_entries[i]["others_valid"] = False

            # 最後のデータではなかった場合
            else:
                # 隣り合う母音(Pair)の長さの差（絶対値）
                v_entries[i]["abs"] = abs(
                    v_entries[i + 1]["duration"] - v_entries[i]["duration"]
                )
                # 隣り合う母音(Pair)の長さの平均
                v_entries[i]["avg"] = (
                    v_entries[i + 1]["duration"] + v_entries[i]["duration"]
                ) / 2

                # absをabgで割ったもの
                v_entries[i]["abs_divided_by_avg"] = (
                    v_entries[i]["abs"] / v_entries[i]["avg"]
                )
                # 隣り合うMelの長さの差（絶対値）
                try:
                    v_entries[i]["abs_Mel"] = abs(
                        v_entries[i + 1]["Mel"] - v_entries[i]["Mel"]
                    )
                except TypeError:
                    pass

                # 隣り合うdBの差(絶対値)
                v_entries[i]["abs_dB"] = abs(
                    float(v_entries[i + 1]["dB"]) - float(v_entries[i]["dB"])
                )

        for item in v_entries:
            total_v_entries.append(item)

        # absにNaNがある行を削除
        df = pd.DataFrame(total_v_entries).dropna(subset=["abs"])

        # print(df)
        # "duration_valid"がTrueのみのものを抽出する
        duration_df = df[df["duration_valid"] == True]

        nPVI = duration_df["abs_divided_by_avg"].sum() / len(duration_df) * 100
        nPVIn = len(duration_df)
        self.nPVI = nPVI
        self.nPVIn = nPVIn

        # absにNaNがある行を削除
        df = pd.DataFrame(total_v_entries).dropna(subset=["abs"])
        # "others_valid"がTrueのみのものを抽出する
        others_df = df[df["others_valid"] == True]
        # Pitch #########################################################
        # nVarPco : 母音のピッチの標準偏差を平均で割ったものに100をかけたもの。
        # ”vf”, ”fp”, “rp”, “vl”, “jp”, “--undefined—"を除く
        dfmel = others_df[others_df["Mel"] != "--undefined--"]["Mel"]
        nVarPco = dfmel.std() / dfmel.mean() * 100
        self.nVarPco = nVarPco

        # nVarPcon : nVarPconの計算に使われたペアの数。
        nVarPcon = len(dfmel)
        self.nVarPcon = nVarPcon

        # PitAllAv : Melの平均
        PitAllAv = dfmel.mean()
        self.PitAllAv = PitAllAv

        # nVarDco 母音の長さの標準偏差を平均で割ったものに100をかけたもの。
        nVarDco = others_df["duration"].std() / others_df["duration"].mean() * 100
        self.nVarDco = nVarDco
        # nVarDcon上記3．で、nVarcoの計算に使われた”v”の数。
        nVarDcon = len(others_df)
        self.nVarDcon = nVarDcon
        # DurAllAv 全ての”v”（”vf”は除く）の長さの平均。
        DurAllAv = others_df["duration"].mean()
        self.DurAllAv = DurAllAv

        # Intensity #####################################################
        # nVarIco : 母音のIntensityの標準偏差を平均で割ったものに100をかけたもの。
        # ”vf”, ”fp”, “rp”, “vl”, “jp”を除く。
        nVarIco = others_df["dB"].std() / others_df["dB"].mean() * 100
        self.nVarIco = nVarIco
        nVarIcon = len(others_df)
        self.nVarIcon = nVarIcon

        IntAllAv = others_df["dB"].mean()
        self.IntAllAv = IntAllAv
        #################################################################

        others_df = df[df["others_valid"] == True]

        # Tier2 pr毎に最小値と最大値を保存する
        for l2index, ph_entry in enumerate(tg._tierDict["Phrases"].entries):
            if ph_entry.label == "pr":
                pr_start = ph_entry.start
                pr_end = ph_entry.end
                last_index = None
                df_vent = others_df[
                    (others_df["start"] >= pr_start) & (others_df["end"] <= pr_end)
                ]
                # print(df_vent)

                # pr毎に最小値と最大値を保存する
                # pr内に有効なvが無い場合は対象としない
                if len(df_vent):
                    # df_vent = df_vent[df_vent["is_DurRangeAv_target"] == True]

                    # vが１つしかない場合はターゲットから外す
                    if len(df_vent) > 1:
                        max_and_min_in_prs.append(
                            {
                                "max": df_vent["duration"].max(),
                                "min": df_vent["duration"].min(),
                            }
                        )

                    df_vent = df_vent[df_vent["Mel"] != "--undefined--"]

                    # vが１つしかない場合はターゲットから外す
                    if len(df_vent) > 1:
                        max_and_min_in_PitRangeAv.append(
                            {"max": df_vent["Mel"].max(), "min": df_vent["Mel"].min()}
                        )

                    # vが１つしかない場合はターゲットから外す
                    if len(df_vent) > 1:
                        max_and_min_in_IntRangeAv.append(
                            {"max": df_vent["dB"].max(), "min": df_vent["dB"].min()}
                        )

        # DurRangeAv : Tier2の各”pr”の範囲内にあるTier3の”v”のピッチの最大値と最小値の差を出し、
        # それらを全てのprで平均する。”vf”, ”fp”, “rp”, “vl”, “jp”, “--undefined—"を除く。

        dif_list = [x["max"] - x["min"] for x in max_and_min_in_prs]
        DurRangeAv = sum(dif_list) / len(dif_list)

        self.DurRangeAv = DurRangeAv

        # Pitch #####################################################################################################
        # PitRangeAv : Tier2の各”pr”の範囲内にあるTier3の”v”のピッチの最大値と最小値の差を出し、それらを全てのprで平均する。
        # ”vf”, ”fp”, “rp”, “vl”, “jp”, “--undefined—"を除く。
        dif_list_PitRangeAv = [x["max"] - x["min"] for x in max_and_min_in_PitRangeAv]
        PitRangeAv = sum(dif_list_PitRangeAv) / len(dif_list_PitRangeAv)
        self.PitRangeAv = PitRangeAv

        # Intensity #################################################################################################
        # ”vf”, ”fp”, “rp”, “vl”, “jp”,を除く。
        dif_list_IntRangeAv = [x["max"] - x["min"] for x in max_and_min_in_IntRangeAv]
        IntRangeAv = sum(dif_list_IntRangeAv) / len(dif_list_IntRangeAv)
        self.IntRangeAv = IntRangeAv

        # PPD　隣り合う母音の(Pair)の声の高さ(Pitch:Mel)の差の平均を出し、それをすべてのPairで平均
        # ppd = df["abs_Mel"].dropna().mean()

        # absにNaNがある行を削除
        df = pd.DataFrame(total_v_entries).dropna(subset=["abs"])

        # "duration_valid"がTrueのみのものを抽出する
        df_duration = df[df["duration_valid"] == True]

        df_PPD = df_duration["abs_Mel"].dropna()
        ppd = df_PPD.mean()
        self.PPD = ppd
        PPDn = len(df_PPD)
        self.PPDn = PPDn
        # undefinedの数
        self.Undefined = undefined
        #############################################################################################################

        # "duration_valid"がTrueのみのものを抽出する
        df_duration = df[df["duration_valid"] == True]

        df_pid = df_duration["abs_dB"].dropna()
        pid = df_pid.mean()
        self.PID = pid
        pidn = len(df_pid)
        self.PIDn = pidn

        return


def T2_delete_start_end(textgrid_file: textgrid) -> textgrid:
    ### 20230913 無効に ###
    # - Tier2の最初と最後に記号があったら消去する(Phonation Rateの計算前に実行する)

    print("この処理は20230913に無効に設定されています")

    # if textgrid_file.tiers[1].entries[0].start == textgrid_file.minTimestamp:
    #     textgrid_file.tiers[1].insertEntry(
    #         (
    #             textgrid_file.tiers[1].entries[0].start,
    #             textgrid_file.tiers[1].entries[0].end,
    #             "",
    #         ),
    #         collisionMode="replace",
    #         collisionReportingMode="silence",
    #     )

    # t2last = len(textgrid_file.tiers[1].entries) - 1
    # if textgrid_file.tiers[1].entries[t2last].end == textgrid_file.maxTimestamp:
    #     textgrid_file.tiers[1].insertEntry(
    #         (
    #             textgrid_file.tiers[1].entries[t2last].start,
    #             textgrid_file.tiers[1].entries[t2last].end,
    #             "",
    #         ),
    #         collisionMode="replace",
    #         collisionReportingMode="silence",
    #     )

    # return textgrid_file


def tg_check(textgrid_file_path: str) -> Tuple[bool, List[str]]:
    """_summary_
    自動チェック：10項目
    - Tier2:pr, ps, psb, fp以外の記号があることはない。
    - Tier3:v, fp 以外の記号があることはない
    - Tier3:Tier2がfpである境界内のTier3の境界の記号は、必ずfpである
    - Tier4:rp以外の記号がある。
    - Tier4:rpの境界が、 Tier2、ps, psb, fp内部にあることはありえない。
    - Tier4:rpの左側の境界が、Tier2、ps, psb, fpの左側の境界と一致することはない（rpはポーズから始まらない）。
    - Tier4:rpの右側の境界が、ps, psb, fpの右側の境界と一致することはない（rpはポーズで終わらない）。
    - Tier5:jp以外の記号がある。
    - Tier7:Pitchの値の異常値。pitchの値がpitchの平均値の２分の１より低い値
    - 全体: Tier6, 7がない。

    Args:
        textgrid_file_path (str): textgridファイルのファイルパス

    Returns:
        bool: チェックの成否 問題無しでTrue
    """

    try:
        result_message = "全てのチェックを通過しました"
        error_messages = []

        textgrid_file = textgrid.openTextgrid(
            textgrid_file_path, includeEmptyIntervals=True
        )

        # 20230913　削除ではなくチェックに
        # textgrid_file = T2_delete_start_end(textgrid_file)
        # チェック：Tier2の最初と最後の境界に記号があることはない。

        chk_flag = True

        if (
            textgrid_file.tiers[1].entries[0].start == textgrid_file.minTimestamp
            and textgrid_file.tiers[1].entries[0].label != ""
        ):
            label = textgrid_file.tiers[1].entries[0].label
            _ = textgrid_file.tiers[1].entries[0].start
            error_messages.append(
                f"{textgrid_file_path} チェックエラー:TTier2の最初と最後の境界に記号があることはない。  "
                + f" {_} "
                + label
            )

        t2last = len(textgrid_file.tiers[1].entries) - 1
        if (
            textgrid_file.tiers[1].entries[t2last].end == textgrid_file.maxTimestamp
            and textgrid_file.tiers[1].entries[t2last].label != ""
        ):
            label = textgrid_file.tiers[1].entries[t2last].label
            _ = textgrid_file.tiers[1].entries[t2last].start
            error_messages.append(
                f"{textgrid_file_path} チェックエラー:Tier2の最初と最後の境界に記号があることはない。  "
                + f" {_} "
                + label
            )

        # - 全体: Tier6, 7がない。
        if textgrid_file.tiers.__len__() < 7:
            error_messages.append(f"{textgrid_file_path} チェックエラー:- 全体: Tier6, 7がない。  ")
            return False, error_messages

        #  Tier2:pr, ps, psb, fp以外の記号があることはない。
        for _, __, label in textgrid_file.tiers[1].entries:
            if label not in ("pr", "ps", "psb", "fp", ""):
                error_messages.append(
                    f"{textgrid_file_path} チェックエラー:Tier2:pr, ps, psb, fp以外の記号があることはない  "
                    + f" {_} "
                    + label
                )

        # 4) チェック：Tier2: ２番目の境界内と、最後から２番目の境界内の間に空白の境界内があることはない
        # （追加しました。新しい境界を作ったさいにprを入れるのを忘れたさいに起きるエラーです）。
        for i, item in enumerate(textgrid_file.tiers[1].entries):
            _ = item[0]
            __ = item[1]
            label = item[2]
            if i == 0 or i == (len(textgrid_file.tiers[1].entries) - 1):
                continue
            if label == "":
                error_messages.append(
                    f"{textgrid_file_path} チェックエラー:Tier2: ２番目の境界内と、最後から２番目の境界内の間に空白の境界内があることはない  "
                    + f" {_} "
                    + label
                )

        # 5) チェック：Tier3: v以外の記号があることはない。
        # (変更しました。後の処理で、「Tier2の境界がfpであるTier3のvをfpに変える。」
        # 「Tier4にrpが入っている境界内の、Tier3のvをrpに置き換える。」を行いますので、
        # この時点では、Tier3の全ての境界内の記号はvとなります。
        for _, __, label in textgrid_file.tiers[2].entries:
            if label not in ("v", ""):
                error_messages.append(
                    f"{textgrid_file_path} チェックエラー:Tier3:v以外の記号があることはない  "
                    + f" {_} "
                    + label
                )

        # - Tier4:rp以外の記号がある。
        for _, __, label in textgrid_file.tiers[3].entries:
            if label not in ("rp", ""):
                error_messages.append(
                    f"{textgrid_file_path} チェックエラー:Tier4:rp以外の記号がある。  "
                    + f" {_} "
                    + label
                )
        # Tier4:rpの境界が、 Tier2、ps, psb, fp内部にあることはありえない。
        # Tier4:rpの左側の境界が、Tier2、ps, psb, fpの左側の境界と一致することはない（rpはポーズから始まらない）。
        for t4start, t4end, t4label in textgrid_file.tiers[3].entries:
            if t4label == "rp":
                times = [t4start, t4end]
                for t2start, t2end, t2label in textgrid_file.tiers[1].entries:
                    if t2label in ("ps", "psb", "fp"):
                        for time in times:
                            if t2start < time < t2end:
                                error_messages.append(
                                    f"{textgrid_file_path} チェックエラー:Tier4:rpの境界が、 Tier2、ps, psb, fp内部にあることはありえない。  "
                                    + f" {time} "
                                    + t2label
                                )
                        if t2start == t4start:
                            error_messages.append(
                                f"{textgrid_file_path} チェックエラー:Tier4:rpの左側の境界が、Tier2、ps, psb, fpの左側の境界と一致することはない（rpはポーズから始まらない）  "
                                + f" {t4start} "
                                + t4label
                            )

                        if t4end == t2end:
                            error_messages.append(
                                f"{textgrid_file_path} チェックエラー:- Tier4:rpの右側の境界が、ps, psb, fpの右側の境界と一致することはない（rpはポーズで終わらない）。  "
                                + f" {t4end} "
                                + t4label
                            )
        # - Tier5:jp以外の記号がある。
        for _, __, label in textgrid_file.tiers[4].entries:
            if label not in ("jp", ""):
                error_messages.append(
                    f"{textgrid_file_path} チェックエラー:Tier5:jp以外の記号がある。  "
                    + f" {_} "
                    + label
                )

        # - Tier7:Pitchの値の異常値。。数値に変換できない
        for _, __, label in textgrid_file.tiers[6].entries:
            if label != "":
                try:
                    float(label)

                except ValueError:
                    error_messages.append(
                        f"{textgrid_file_path} チェックエラー:Tier7:Pitchの値の異常値。数値に変換できない  "
                        + f" {_} "
                        + label
                    )
                    return False, error_messages

        # - Tier7:Pitchの値の異常値。pitchの値がpitchの平均値の２分の１より低い値
        pitlist = [float(x[2]) for x in textgrid_file.tiers[6].entries if x[2] != ""]
        avg = sum(pitlist) / len(pitlist)

        for _, __, label in textgrid_file.tiers[6].entries:
            if label != "":
                if float(label) < (avg / 2):
                    error_messages.append(
                        f"{textgrid_file_path} チェックエラー:Tier7:Pitchの値の異常値。pitchの値がpitchの平均値の２分の１より低い値  "
                        + f" {_} "
                        + label
                    )

        # - Tier7:Tier3とTier7の境界が一致していない。
        pitlist = [float(x[2]) for x in textgrid_file.tiers[6].entries if x[2] != ""]
        avg = sum(pitlist) / len(pitlist)

        for i, item in enumerate(textgrid_file.tiers[2].entries):
            _ = item.start
            __ = item.end
            label = item.label

            # Tier3のラベルがある時
            if label != "":
                # Tier7とstart,endが一致し、かつTier7のラベルが空白ではない
                if (
                    _ == textgrid_file.tiers[6].entries[i].start
                    and __ == textgrid_file.tiers[6].entries[i].end
                    and textgrid_file.tiers[6].entries[i].label != ""
                ):
                    pass
                else:
                    error_messages.append(
                        f"{textgrid_file_path} チェックエラー:Tier3とTier7の境界が一致していない  "
                        + f" {_} "
                        + label
                    )
                    break

                t7label = textgrid_file.tiers[6].entries[i].label

                try:
                    float(t7label)

                except ValueError:
                    error_messages.append(
                        f"{textgrid_file_path} チェックエラー:Tier7:Pitchの値の異常値。数値に変換できない  "
                        + f" {_} "
                        + label
                    )
                    break

        if error_messages:
            return False, error_messages

        return True, result_message
    except Exception as e:
        return False, e.__str__()


def main():
    from glob import glob
    import os

    # import shutil

    if not os.path.exists("success"):
        os.mkdir("success")

    filelists = glob("./tgfiles/*.TextGrid")

    dflist = []
    for filename in filelists:
        result, messages = tg_check(filename)

        # エラーがあった場合は表示する
        if result is False:
            for i in messages:
                print(i)
            continue
        # tg_L4rp_to_L3rp(filename)

        tgd = tgdata(filename)

        df = pd.DataFrame([tgd.__dict__])
        dflist.append(df)
        # 変更後のTextGridをsuccessディレクトリに保存する
        # コピー先のファイルパスを設定
        destination_path = filename.replace("./tgfiles", "./success")

        # 成功したものはファイルを移動
        tgd.save(destination_path)
        # shutil.copy2(filename, destination_path)
        # shutil.move(filename, destination_path)
        os.remove(filename)

    filename = "FluencyProsodyMasterData.xlsx"

    if os.path.exists(filename):
        df_excelfile = pd.read_excel(filename)
        dflist.append(df_excelfile)

    else:
        print(f"Error: {filename} not found.")

    acum_df = pd.concat(dflist)

    # カラム名[ID, RECN]で昇順に並び替えを行う
    acum_df_sorted = acum_df.sort_values(by=["ID", "RECN"], ascending=True)

    # 重複する行に新しいカラム"duplicate"を追加し、値を1に設定する
    acum_df_sorted["duplicate"] = acum_df_sorted.duplicated(
        subset=["ID", "RECN"], keep=False
    ).astype(int)

    # 並び順の整え
    orderitem = [
        "filename",
        "ID",
        "RECN",
        "Date",
        "nsyll",
        "silenttot",
        "silenttot_ps",
        "silenttot_psb",
        "speakingtot",
        "asd",
        "nsounding",
        "npause",
        "npause_ps",
        "npause_psb",
        "nrFP",
        "tFP",
        "nrRP",
        "tRP",
        "durs",
        "SR",
        "SRP",
        "AR",
        "ARP",
        "MLoR",
        "PhonRat",
        "SPauseFreq",
        "SPauseDur",
        "FPauseFreq",
        "FPauseDur",
        "RpFreq",
        "RpDur",
        "SBPauseFreq",
        "SBPauseDur",
        "SWPauseFreq",
        "SWPauseDur",
        "nPVI",
        "nPVIn",
        "nVarDco",
        "nVarDcon",
        "DurAllAv",
        "DurRangeAv",
        "PPD",
        "PPDn",
        "nVarPco",
        "nVarPcon",
        "PitAllAv",
        "PitRangeAv",
        "Undefined",
        "PID",
        "PIDn",
        "nVarIco",
        "nVarIcon",
        "IntAllAv",
        "IntRangeAv",
        "duplicate",
    ]

    acum_df_sorted = acum_df_sorted[orderitem]

    acum_df_sorted.to_excel(filename, float_format="%.2f", index=False)
    print("finished")


if __name__ == "__main__":
    main()
