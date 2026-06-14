on run argv
  set targetUrl to item 1 of argv
  set targetHost to item 2 of argv
  set targetMode to "focus"
  if (count of argv) is greater than or equal to 3 then
    set targetMode to item 3 of argv
  end if

  tell application "Google Chrome"
    activate

    if (count of windows) is 0 then
      make new window
    end if

    if targetMode is "current" then
      set URL of active tab of window 1 to targetUrl
      return
    end if

    if targetMode is "new" then
      tell window 1
        make new tab with properties {URL:targetUrl}
        set active tab index to count of tabs
      end tell
      return
    end if

    repeat with w in windows
      set tabIndex to 0
      repeat with t in tabs of w
        set tabIndex to tabIndex + 1
        try
          if (URL of t contains targetHost) then
            set active tab index of w to tabIndex
            set index of w to 1
            if targetMode is "navigate" then
              set URL of t to targetUrl
            end if
            return
          end if
        end try
      end repeat
    end repeat

    tell window 1
      make new tab with properties {URL:targetUrl}
      set active tab index to count of tabs
    end tell
  end tell
end run
