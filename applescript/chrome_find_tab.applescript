on run argv
  set targetHost to item 1 of argv

  tell application "Google Chrome"
    repeat with w in windows
      set tabIndex to 0
      repeat with t in tabs of w
        set tabIndex to tabIndex + 1
        try
          if (URL of t contains targetHost) then
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

