tell application "Google Chrome"
  if (count of windows) is 0 then
    return "no Chrome window"
  end if

  set tabTitle to title of active tab of window 1
  close active tab of window 1
  return "closed: " & tabTitle
end tell

