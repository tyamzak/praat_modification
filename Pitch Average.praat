#"I want the mean pitch of every interval that has a non-empty label on tier 3."

    if numberOfSelected ("Sound") <> 1 or numberOfSelected ("TextGrid") <> 1
       exitScript: "Please select a Sound and a TextGrid first."
    endif
    sound = selected ("Sound")
    textgrid = selected ("TextGrid")
    selectObject: sound
    pitch = To Pitch: 0.0, 80, 400
    selectObject: textgrid
    n = Get number of intervals: 3
    for i to n
       tekst$ = Get label of interval: 3, i
       if tekst$ <> ""
          t1 = Get starting point: 3, i
          t2 = Get end point: 3, i
          selectObject: pitch
          f0 = Get mean: t1, t2, "Hertz"
          appendInfoLine: fixed$ (f0, 1)
          selectObject: textgrid
       endif
    endfor
    selectObject: sound, textgrid
