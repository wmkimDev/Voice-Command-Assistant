on run argv
  set keyword to my lowercase(item 1 of argv)
  set compactKeyword to my compact(keyword)

  tell application "Google Chrome"
    repeat with w in windows
      repeat with t in tabs of w
        try
          set tabTitle to title of t
          set loweredTitle to my lowercase(tabTitle)
          set loweredUrl to my lowercase(URL of t)
          set compactTitle to my compact(loweredTitle)
          set compactUrl to my compact(loweredUrl)

          if loweredTitle contains keyword or loweredUrl contains keyword or compactTitle contains compactKeyword or compactUrl contains compactKeyword then
            close t
            return "closed: " & tabTitle
          end if
        end try
      end repeat
    end repeat
  end tell

  return "not_found"
end run

on lowercase(inputText)
  set upperChars to "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  set lowerChars to "abcdefghijklmnopqrstuvwxyz"
  set outputText to ""

  repeat with i from 1 to length of inputText
    set currentChar to character i of inputText
    set charIndex to offset of currentChar in upperChars
    if charIndex is greater than 0 then
      set outputText to outputText & character charIndex of lowerChars
    else
      set outputText to outputText & currentChar
    end if
  end repeat

  return outputText
end lowercase

on compact(inputText)
  set outputText to ""
  repeat with i from 1 to length of inputText
    set currentChar to character i of inputText
    if currentChar is not " " and currentChar is not tab then
      set outputText to outputText & currentChar
    end if
  end repeat
  return outputText
end compact
