on run argv
  set targetUrl to item 1 of argv
  set targetHost to item 2 of argv
  run script POSIX file ((do shell script "pwd") & "/applescript/chrome_open_url.applescript") with parameters {targetUrl, targetHost}
end run

