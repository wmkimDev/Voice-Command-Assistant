tell application "Google Chrome"
  activate

  if (count of windows) is 0 then
    make new window
  else
    tell window 1
      make new tab
      set active tab index to count of tabs
    end tell
  end if
end tell

