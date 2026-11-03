<#
Organize_Project_v5.ps1  --  EMCH 308 Team 6, bring this computer's copy into the Rev C layout

HOW TO RUN (Windows PowerShell; no Python, Abaqus or git needed)
    powershell -ExecutionPolicy Bypass -File "D:\EMCH308_repo\Organize_Project_v5.ps1"
    (use the drive letter where the repo is).  It lists every change and asks
    "Go ahead? [y/N]" first; add -Yes to skip the question.
    A record goes to archive\logs\Organize_Project_v5_log.txt.

WHAT IT DOES (the file lists below were worked out against GitHub main)
    1. Moves every file that GitHub moved: Rev B out of the "final" places into
       Old_Designs\, abaqus\iterations\Stock1_Drilled_v2_RevB\, results\iterations\
       Stock1_Drilled_v2_RevB\, abaqus\python\iterations\, cad\old_designs\RevB\
       and cost\old_designs\.  Nothing is deleted: a file is only removed when an
       identical copy (same size) is already at the destination.
    2. Copies the Rev C files into Final_Design\ (copies of the originals).
    3. Moves local-only files Git never tracks:
         Rev B job logs        -> abaqus\iterations\Stock1_Drilled_v2_RevB\job\
         interrupted v2 rerun  -> archive\old_results\Stock1_RevC_v2_interrupted\
         abaqus.rpy*, *_log.txt -> archive\logs\
         "RevC Warnings.txt"   -> archive\error_notes\
         Organize_Project_v5.py (replaced by this .ps1) -> archive\old_scripts\
    4. Removes folders left empty.
    The READMEs, .gitignore and the few files whose GitHub copy differs were
    written into place directly before this script was delivered.
#>
param([switch]$Yes)
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $Root 'abaqus'))) { throw "$Root is not the repo folder." }
$LogLines = New-Object System.Collections.Generic.List[string]
function Log($t) { $LogLines.Add($t); Write-Host "[ORGANIZE v5] $t" }
function Full($p) { Join-Path $Root $p }

$Moves = @(
    @('Final_Design\Abaqus\Stock1_Drilled_v2.cae', 'Old_Designs\RevB_Stock1_Drilled_v2\Abaqus\Stock1_Drilled_v2.cae'),
    @('Final_Design\Abaqus\Stock1_Drilled_v2.jnl', 'Old_Designs\RevB_Stock1_Drilled_v2\Abaqus\Stock1_Drilled_v2.jnl'),
    @('Final_Design\Abaqus\job\Stock1_Drilled_v2.cae', 'Old_Designs\RevB_Stock1_Drilled_v2\Abaqus\job\Stock1_Drilled_v2.cae'),
    @('Final_Design\Abaqus\job\Stock1_Drilled_v2.inp', 'Old_Designs\RevB_Stock1_Drilled_v2\Abaqus\job\Stock1_Drilled_v2.inp'),
    @('Final_Design\Abaqus\job\Stock1_Drilled_v2.jnl', 'Old_Designs\RevB_Stock1_Drilled_v2\Abaqus\job\Stock1_Drilled_v2.jnl'),
    @('Final_Design\Abaqus\job\Stock1_Drilled_v2.odb', 'Old_Designs\RevB_Stock1_Drilled_v2\Abaqus\job\Stock1_Drilled_v2.odb'),
    @('Final_Design\CAD\USC06_MTC06_IBeam_RevB.step', 'Old_Designs\RevB_Stock1_Drilled_v2\CAD\USC06_MTC06_IBeam_RevB.step'),
    @('Final_Design\CAD\usc06_mtc06_ibeam_revb_.prt.3', 'Old_Designs\RevB_Stock1_Drilled_v2\CAD\usc06_mtc06_ibeam_revb_.prt.3'),
    @('Final_Design\Cost\ProjectCostSheet_Stock1_Drilled_v2.xlsx', 'Old_Designs\RevB_Stock1_Drilled_v2\Cost\ProjectCostSheet_Stock1_Drilled_v2.xlsx'),
    @('Final_Design\Drawings\Design_Sheet_Stock1_Drilled_v2.pdf', 'Old_Designs\RevB_Stock1_Drilled_v2\Drawings\Design_Sheet_Stock1_Drilled_v2.pdf'),
    @('Final_Design\Drawings\Design_Sheet_Stock1_Drilled_v2.png', 'Old_Designs\RevB_Stock1_Drilled_v2\Drawings\Design_Sheet_Stock1_Drilled_v2.png'),
    @('Final_Design\Drawings\Hole_Layout_Stock1_Drilled_v2.png', 'Old_Designs\RevB_Stock1_Drilled_v2\Drawings\Hole_Layout_Stock1_Drilled_v2.png'),
    @('Final_Design\Drawings\USC06_MTC06_IBeam_RevB_Drawing.pdf', 'Old_Designs\RevB_Stock1_Drilled_v2\Drawings\USC06_MTC06_IBeam_RevB_Drawing.pdf'),
    @('Final_Design\Drawings\USC06_MTC06_IBeam_RevB_Drawing_sheet1.png', 'Old_Designs\RevB_Stock1_Drilled_v2\Drawings\USC06_MTC06_IBeam_RevB_Drawing_sheet1.png'),
    @('Final_Design\Drawings\USC06_MTC06_IBeam_RevB_Drawing_sheet2.png', 'Old_Designs\RevB_Stock1_Drilled_v2\Drawings\USC06_MTC06_IBeam_RevB_Drawing_sheet2.png'),
    @('Final_Design\Results\FOS_Stock1_Drilled_v2.txt', 'Old_Designs\RevB_Stock1_Drilled_v2\Results\FOS_Stock1_Drilled_v2.txt'),
    @('Final_Design\Results\FOS_Stock1_Drilled_v2_LoadDisp.csv', 'Old_Designs\RevB_Stock1_Drilled_v2\Results\FOS_Stock1_Drilled_v2_LoadDisp.csv'),
    @('Final_Design\Results\Stock1_Drilled_v2_LoadDisp.png', 'Old_Designs\RevB_Stock1_Drilled_v2\Results\Stock1_Drilled_v2_LoadDisp.png'),
    @('Final_Design\Scripts\Export_STEP_v3.py', 'Old_Designs\RevB_Stock1_Drilled_v2\Scripts\Export_STEP_v3.py'),
    @('Final_Design\Scripts\FOS_Stock1_Drilled_v3.py', 'Old_Designs\RevB_Stock1_Drilled_v2\Scripts\FOS_Stock1_Drilled_v3.py'),
    @('Final_Design\Scripts\Stock1_Drilled_v2.py', 'Old_Designs\RevB_Stock1_Drilled_v2\Scripts\Stock1_Drilled_v2.py'),
    @('Final_Design\Scripts\make_RevB_drawing_v3.py', 'Old_Designs\RevB_Stock1_Drilled_v2\Scripts\make_RevB_drawing_v3.py'),
    @('abaqus\final_design\Stock1_Drilled_v2.cae', 'abaqus\iterations\Stock1_Drilled_v2_RevB\Stock1_Drilled_v2.cae'),
    @('abaqus\final_design\Stock1_Drilled_v2.jnl', 'abaqus\iterations\Stock1_Drilled_v2_RevB\Stock1_Drilled_v2.jnl'),
    @('abaqus\final_design\job\Stock1_Drilled_v2.cae', 'abaqus\iterations\Stock1_Drilled_v2_RevB\job\Stock1_Drilled_v2.cae'),
    @('abaqus\final_design\job\Stock1_Drilled_v2.inp', 'abaqus\iterations\Stock1_Drilled_v2_RevB\job\Stock1_Drilled_v2.inp'),
    @('abaqus\final_design\job\Stock1_Drilled_v2.jnl', 'abaqus\iterations\Stock1_Drilled_v2_RevB\job\Stock1_Drilled_v2.jnl'),
    @('abaqus\final_design\job\Stock1_Drilled_v2.odb', 'abaqus\iterations\Stock1_Drilled_v2_RevB\job\Stock1_Drilled_v2.odb'),
    @('abaqus\python\final\Export_STEP_v3.py', 'abaqus\python\iterations\Export_STEP_v3.py'),
    @('abaqus\python\final\FOS_Stock1_Drilled_v3.py', 'abaqus\python\iterations\FOS_Stock1_Drilled_v3.py'),
    @('abaqus\python\final\Stock1_Drilled_v2.py', 'abaqus\python\iterations\Stock1_Drilled_v2.py'),
    @('cad\USC06_MTC06_IBeam_RevB.step', 'cad\old_designs\RevB\USC06_MTC06_IBeam_RevB.step'),
    @('cad\USC06_MTC06_IBeam_RevB_Drawing.pdf', 'cad\old_designs\RevB\USC06_MTC06_IBeam_RevB_Drawing.pdf'),
    @('cad\USC06_MTC06_IBeam_RevB_Drawing_sheet1.png', 'cad\old_designs\RevB\USC06_MTC06_IBeam_RevB_Drawing_sheet1.png'),
    @('cad\USC06_MTC06_IBeam_RevB_Drawing_sheet2.png', 'cad\old_designs\RevB\USC06_MTC06_IBeam_RevB_Drawing_sheet2.png'),
    @('cad\creo\usc06_mtc06_ibeam_revb_.prt.3', 'cad\old_designs\RevB\creo\usc06_mtc06_ibeam_revb_.prt.3'),
    @('cad\drawings\Design_Sheet_Stock1_Drilled_v2.pdf', 'cad\old_designs\RevB\drawings\Design_Sheet_Stock1_Drilled_v2.pdf'),
    @('cad\drawings\Design_Sheet_Stock1_Drilled_v2.png', 'cad\old_designs\RevB\drawings\Design_Sheet_Stock1_Drilled_v2.png'),
    @('cad\drawings\Hole_Layout_Stock1_Drilled_v2.png', 'cad\old_designs\RevB\drawings\Hole_Layout_Stock1_Drilled_v2.png'),
    @('cad\drawings\USC06_MTC06_IBeam_RevB_Drawing_GDT_version.pdf', 'cad\old_designs\RevB\drawings\USC06_MTC06_IBeam_RevB_Drawing_GDT_version.pdf'),
    @('cad\drawings\USC06_MTC06_IBeam_RevB_Drawing_GDT_version.png', 'cad\old_designs\RevB\drawings\USC06_MTC06_IBeam_RevB_Drawing_GDT_version.png'),
    @('cost\ProjectCostSheet_Stock1_Drilled_v2.xlsx', 'cost\old_designs\ProjectCostSheet_Stock1_Drilled_v2.xlsx'),
    @('results\final_design\FOS_Stock1_Drilled_v2.txt', 'results\iterations\Stock1_Drilled_v2_RevB\FOS_Stock1_Drilled_v2.txt'),
    @('results\final_design\FOS_Stock1_Drilled_v2_LoadDisp.csv', 'results\iterations\Stock1_Drilled_v2_RevB\FOS_Stock1_Drilled_v2_LoadDisp.csv'),
    @('results\final_design\Stock1_Drilled_v2_LoadDisp.png', 'results\iterations\Stock1_Drilled_v2_RevB\Stock1_Drilled_v2_LoadDisp.png')
)
$Copies = @(
    @('abaqus\final_design\Stock1_RevC_v1.cae', 'Final_Design\Abaqus\Stock1_RevC_v1.cae'),
    @('abaqus\final_design\Stock1_RevC_v1.jnl', 'Final_Design\Abaqus\Stock1_RevC_v1.jnl'),
    @('abaqus\final_design\job\Stock1_RevC_v1.cae', 'Final_Design\Abaqus\job\Stock1_RevC_v1.cae'),
    @('abaqus\final_design\job\Stock1_RevC_v1.inp', 'Final_Design\Abaqus\job\Stock1_RevC_v1.inp'),
    @('abaqus\final_design\job\Stock1_RevC_v1.jnl', 'Final_Design\Abaqus\job\Stock1_RevC_v1.jnl'),
    @('abaqus\final_design\job\Stock1_RevC_v1_geometry.txt', 'Final_Design\Abaqus\job\Stock1_RevC_v1_geometry.txt'),
    @('cad\USC06_MTC06_IBeam_RevC.step', 'Final_Design\CAD\USC06_MTC06_IBeam_RevC.step'),
    @('cost\ProjectCostSheet_RevC_Stock1_v2.xlsx', 'Final_Design\Cost\ProjectCostSheet_RevC_Stock1_v2.xlsx'),
    @('cad\drawings\Design_Sheet_Stock1_RevC_v1.pdf', 'Final_Design\Drawings\Design_Sheet_Stock1_RevC_v1.pdf'),
    @('cad\concept_drawings\Proposal_RevC_Stock1_v2.pdf', 'Final_Design\Drawings\Proposal_RevC_Stock1_v2.pdf'),
    @('cad\concept_drawings\Proposal_RevC_Stock1_v2.png', 'Final_Design\Drawings\Proposal_RevC_Stock1_v2.png'),
    @('cad\USC06_MTC06_IBeam_RevC_Drawing.pdf', 'Final_Design\Drawings\USC06_MTC06_IBeam_RevC_Drawing.pdf'),
    @('results\final_design\FOS_Stock1_RevC_v1.txt', 'Final_Design\Results\FOS_Stock1_RevC_v1.txt'),
    @('results\final_design\FOS_Stock1_RevC_v1_LoadDisp.csv', 'Final_Design\Results\FOS_Stock1_RevC_v1_LoadDisp.csv'),
    @('abaqus\python\final\Export_STEP_v4.py', 'Final_Design\Scripts\Export_STEP_v4.py'),
    @('abaqus\python\final\FOS_Stock1_RevC_v1.py', 'Final_Design\Scripts\FOS_Stock1_RevC_v1.py'),
    @('abaqus\python\final\FOS_Stock1_RevC_v2.py', 'Final_Design\Scripts\FOS_Stock1_RevC_v2.py'),
    @('abaqus\python\final\FOS_Stock1_RevC_v3.py', 'Final_Design\Scripts\FOS_Stock1_RevC_v3.py'),
    @('abaqus\python\final\Stock1_RevC_v1.py', 'Final_Design\Scripts\Stock1_RevC_v1.py'),
    @('abaqus\python\final\fix_Stock1_RevC_v1.py', 'Final_Design\Scripts\fix_Stock1_RevC_v1.py'),
    @('cad\drawings\source\make_RevC_design_sheet_v1.py', 'Final_Design\Scripts\make_RevC_design_sheet_v1.py'),
    @('cad\drawings\source\make_RevC_drawing_v1.py', 'Final_Design\Scripts\make_RevC_drawing_v1.py'),
    @('Final_Design\Results\Design_Comparison.png', 'Old_Designs\RevB_Stock1_Drilled_v2\Results\Design_Comparison.png')
)

# local-only leftovers: (source, destination folder)
$Left = New-Object System.Collections.Generic.List[object]
$revbJob = 'abaqus\iterations\Stock1_Drilled_v2_RevB\job'
foreach ($e in 'dat','log','msg','sta','com','prt','ipm') {
    $Left.Add(@("abaqus\final_design\job\Stock1_Drilled_v2.$e", $revbJob))
}
$v2 = 'archive\old_results\Stock1_RevC_v2_interrupted'
$jv2 = Full 'abaqus\final_design\job_v2'
$v2done = $false
$sta = Join-Path $jv2 'Stock1_RevC_v2.sta'
if (Test-Path -LiteralPath $sta) { $v2done = (Get-Content -LiteralPath $sta -Raw) -match 'COMPLETED SUCCESSFULLY' }
if ((Test-Path -LiteralPath $jv2) -and -not $v2done) {
    Get-ChildItem -LiteralPath $jv2 -File | ForEach-Object { $Left.Add(@("abaqus\final_design\job_v2\$($_.Name)", $v2)) }
    foreach ($f in 'Stock1_RevC_v2.cae','Stock1_RevC_v2.jnl') { $Left.Add(@("abaqus\final_design\$f", $v2)) }
}
Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object {
    $r = $_.FullName.Substring($Root.Length).TrimStart('\')
    -not ($r -like '.git\*' -or $r -like 'archive\*' -or $r -like 'abaqus\final_design\job_v2\*')
} | ForEach-Object {
    $r = $_.FullName.Substring($Root.Length).TrimStart('\')
    if ($_.Name -like 'abaqus.rpy*') {
        $Left.Add(@($r, ('archive\logs\abaqus_rpy\' + ((Split-Path $r -Parent) -replace '\\','__'))))
    } elseif ($_.Name -like '*_log.txt') { $Left.Add(@($r, 'archive\logs')) }
    elseif ($_.Name -eq 'RevC Warnings.txt') { $Left.Add(@($r, 'archive\error_notes')) }
    elseif ($r -eq 'Organize_Project_v5.py') { $Left.Add(@($r, 'archive\old_scripts')) }
    elseif ($_.Name -like 'Proposal_RevC_Stock1_SawTrim_v1*') { $Left.Add(@($r, 'archive\old_drawings')) }
}

# ---- plan
Log "Repo: $Root"
$nm = 0; $nc = 0; $nl = 0
foreach ($m in $Moves)  { if (Test-Path -LiteralPath (Full $m[0])) { Log "move  $($m[0]) -> $($m[1])"; $nm++ } }
foreach ($c in $Copies) { if (-not (Test-Path -LiteralPath (Full $c[1]))) { Log "copy  $($c[0]) -> $($c[1])"; $nc++ } }
foreach ($l in $Left)   { if (Test-Path -LiteralPath (Full $l[0])) { Log "tidy  $($l[0]) -> $($l[1])\"; $nl++ } }
Log "$nm moves, $nc copies, $nl local-only files to tidy."
if (($nm + $nc + $nl) -eq 0) { Log 'Nothing to do: the folder already matches GitHub.'; exit 0 }
if (-not $Yes) {
    $a = Read-Host 'Go ahead? [y/N]'
    if ($a -notmatch '^(y|yes)$') { Log 'Stopped; nothing changed.'; exit 0 }
}

function Do-Move($src, $dst) {
    $s = Full $src; $d = Full $dst
    if (-not (Test-Path -LiteralPath $s)) { return }
    $dd = Split-Path $d -Parent
    if (-not (Test-Path -LiteralPath $dd)) { New-Item -ItemType Directory -Path $dd -Force | Out-Null }
    if (Test-Path -LiteralPath $d) {
        if ((Get-Item -LiteralPath $s).Length -eq (Get-Item -LiteralPath $d).Length) {
            Remove-Item -LiteralPath $s; Log "removed $src (same file already at $dst)"; return
        }
        $base = [IO.Path]::GetFileNameWithoutExtension($d); $ext = [IO.Path]::GetExtension($d); $k = 1
        while (Test-Path -LiteralPath (Join-Path $dd "$base`_$k$ext")) { $k++ }
        $d = Join-Path $dd "$base`_$k$ext"
    }
    Move-Item -LiteralPath $s -Destination $d
    Log "moved $src -> $($d.Substring($Root.Length).TrimStart('\'))"
}

# ---- do it
foreach ($m in $Moves) { Do-Move $m[0] $m[1] }
foreach ($c in $Copies) {
    $s = Full $c[0]; $d = Full $c[1]
    if ((Test-Path -LiteralPath $s) -and -not (Test-Path -LiteralPath $d)) {
        $dd = Split-Path $d -Parent
        if (-not (Test-Path -LiteralPath $dd)) { New-Item -ItemType Directory -Path $dd -Force | Out-Null }
        Copy-Item -LiteralPath $s -Destination $d
        Log "copied $($c[0]) -> $($c[1])"
    }
}
foreach ($l in $Left) { Do-Move $l[0] (Join-Path $l[1] (Split-Path $l[0] -Leaf)) }

# ---- empty folders
$removed = 0
do {
    $empty = Get-ChildItem -LiteralPath $Root -Recurse -Directory | Where-Object {
        $r = $_.FullName.Substring($Root.Length).TrimStart('\')
        -not ($r -like '.git*' -or $r -like 'archive*') -and
        -not (Get-ChildItem -LiteralPath $_.FullName -Force)
    }
    foreach ($e in $empty) { Remove-Item -LiteralPath $e.FullName; $removed++ }
} while ($empty)
Log "Removed $removed empty folder(s)."
Log 'Done.  The folder now matches the GitHub layout; local-only files are in archive\.'
$ld = Full 'archive\logs'
if (-not (Test-Path -LiteralPath $ld)) { New-Item -ItemType Directory -Path $ld -Force | Out-Null }
Add-Content -LiteralPath (Join-Path $ld 'Organize_Project_v5_log.txt') -Value (@('', "=== $(Get-Date -Format 'yyyy-MM-dd HH:mm') ===") + $LogLines)
