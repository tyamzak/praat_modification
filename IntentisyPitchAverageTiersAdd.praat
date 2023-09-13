if numberOfSelected ("Sound") <> 1 or numberOfSelected ("TextGrid") <> 1
   exitScript: "Please select a Sound and a TextGrid first."
endif
sound = selected ("Sound")
textgrid = selected ("TextGrid")
###############Intensify Area############################
selectObject: sound
intensity = To Intensity: 75, 0.001
selectObject: textgrid
n = Get number of intervals: 3
numTiers = Get number of tiers
Insert interval tier: numTiers + 1, "Intensity"

# Copy intervals from Tier 3 to the new tier
# Tier3のintervalをコピーする
# 最初と最後はboundaryが既に存在するため、作成しない
for i to n - 1
   t1 = Get starting point: 3, i
   t2 = Get end point: 3, i
   Insert boundary: numTiers + 1, t2
endfor

for i to n
   tekst$ = Get label of interval: 3, i
   if tekst$ <> ""
      t1 = Get starting point: 3, i
      t2 = Get end point: 3, i
      selectObject: intensity
      dB = Get mean: t1, t2
      selectObject: textgrid
      Set interval text: numTiers + 1, i, fixed$ (dB, 1)
   endif
endfor
selectObject: sound, textgrid

###############Pitch Area############################

selectObject: sound
pitch = To Pitch: 0.0, 80, 400
selectObject: textgrid
n = Get number of intervals: 3

numTiers = Get number of tiers
Insert interval tier: numTiers + 1, "Pitch"

# Copy intervals from Tier 3 to the new tier
# Tier3のintervalをコピーする
# 最初と最後はboundaryが既に存在するため、作成しない
for i to n - 1
   t1 = Get starting point: 3, i
   t2 = Get end point: 3, i
   Insert boundary: numTiers + 1, t2
endfor

for i to n
   tekst$ = Get label of interval: 3, i
   if tekst$ <> ""
      t1 = Get starting point: 3, i
      t2 = Get end point: 3, i
      selectObject: pitch
      f0 = Get mean: t1, t2, "Hertz"
      selectObject: textgrid
      Set interval text: numTiers + 1, i, fixed$ (f0, 1)
   endif
endfor
selectObject: sound, textgrid
