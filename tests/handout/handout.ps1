# Runs the three PowerShell handout commands from docs/HANDOUT-COMMANDS.md on demo sample A and checks
# that each one finds the planted problem. Works in Windows PowerShell 5.1 and PowerShell 7.
param([string]$Dir = 'demo/sample-a')
Set-Location $Dir
"== PowerShell $($PSVersionTable.PSVersion) ($($PSVersionTable.PSEdition)) on $([Environment]::OSVersion.VersionString)"
'--- 1 reveal hidden characters'
$one = gc SKILL.md -Enc UTF8 | % { $_ -replace '[^\t -~]','<?>' }
$one[23].Substring(0, 58)
'--- 2 invisible Unicode'
$two = sls -Enc UTF8 '[​-‏‪-‮]|\uDB40' SKILL.md
$two | % { "SKILL.md:$($_.LineNumber):" + $_.Line.Substring(0, 28) }
'--- 3 red-flag words'
$three = sls -Path SKILL.md -Pattern `
 'prereq|\|\s*(ba)?sh|base64|\.ssh|\.env|tell the user'
$three | % { "SKILL.md:$($_.LineNumber):" + $_.Line.Substring(0, [Math]::Min(46, $_.Line.Length)) }
$ok = ($one[23] -like '*<?>*') -and (@($two).LineNumber -contains 24) -and (@($three).LineNumber -contains 12) -and (@($three).LineNumber -contains 17)
if ($ok) { 'OK' } else { 'FAILED'; exit 1 }
