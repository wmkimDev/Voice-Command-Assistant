on run argv
  set keyword to my lowercase(item 1 of argv)
  set compactKeyword to my compact(keyword)

  tell application "Google Chrome"
    repeat with w in windows
      set tabIndex to 0
      repeat with t in tabs of w
        set tabIndex to tabIndex + 1
        try
          set tabTitle to my lowercase(title of t)
          set tabUrl to my lowercase(URL of t)
          set compactTitle to my compact(tabTitle)
          set compactUrl to my compact(tabUrl)
          if tabTitle contains keyword or tabUrl contains keyword or compactTitle contains compactKeyword or compactUrl contains compactKeyword then
            activate
            set active tab index of w to tabIndex
            set index of w to 1
            return "found"
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
