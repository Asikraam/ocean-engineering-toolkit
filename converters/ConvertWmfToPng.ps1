<#
.SYNOPSIS
    Konversi file WMF & EMF ke PNG dengan kualitas tertinggi (Lossless, Anti-Aliased, High-DPI).

.DESCRIPTION
    Skrip PowerShell ini menggunakan Windows Native GDI+ engine untuk merender file vektor WMF/EMF 
    secara presisi tanpa distorsi warna, tanpa garis hilang, dan dengan resolusi ultra-tajam.

.PARAMETER Path
    Satu atau lebih path file .wmf / .emf atau folder. Mendukung input pipeline.

.PARAMETER Scale
    Faktor pengali resolusi (default: 4.0 = Ultra HD / ~384 DPI).

.PARAMETER Dpi
    Target DPI spesifik (misal: 300 untuk standar cetak). Gunakan bersama -UseDpi.

.PARAMETER UseDpi
    Jika diset, menghitung ukuran output berdasarkan DPI fisik bukan skala faktor.

.PARAMETER Background
    Warna latar belakang: 'Transparent' (default), 'White', atau 'Black'.

.PARAMETER KeyOutWhite
    Hapus background putih solid bawaan Office/Word agar menjadi transparan.

.PARAMETER Padding
    Jumlah pixel margin ekstra di sekeliling gambar untuk mencegah garis tepi terpotong.

.PARAMETER OutputDir
    Folder tujuan file PNG. Jika tidak dispesifikasikan, disimpan di folder yang sama dengan file sumber.

.PARAMETER Recursive
    Cari file .wmf/.emf secara rekursif jika input berupa folder.

.EXAMPLE
    .\Convert-WmfToPng.ps1 -Path "gambar.wmf" -Scale 4

.EXAMPLE
    Get-ChildItem -Path "C:\desain" -Filter *.wmf -Recurse | .\Convert-WmfToPng.ps1 -Scale 4 -Background Transparent
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, ValueFromPipeline = $true, ValueFromPipelineByPropertyName = $true, Position = 0)]
    [string[]]$Path,

    [Parameter()]
    [float]$Scale = 1.0,

    [Parameter()]
    [int]$Dpi = 96,

    [Parameter()]
    [switch]$UseDpi,

    [Parameter()]
    [ValidateSet('Transparent', 'White', 'Black')]
    [string]$Background = 'White',

    [Parameter()]
    [switch]$KeyOutWhite,

    [Parameter()]
    [int]$Padding = 0,

    [Parameter()]
    [string]$OutputDir,

    [Parameter()]
    [switch]$Recursive
)

begin {
    Add-Type -AssemblyName System.Drawing
    $processedCount = 0
    $successCount = 0
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
}

process {
    foreach ($item in $Path) {
        $targets = @()

        $resolvedPath = try { (Resolve-Path -Path $item -ErrorAction Stop).Path } catch { $item }
        if (Test-Path -Path $resolvedPath -PathType Container) {
            $opt = if ($Recursive) { @{ Recurse = $true } } else { @{} }
            $files = Get-ChildItem -Path $resolvedPath -File @opt | Where-Object {
                $_.Extension -match '^\.(wmf|emf)$'
            }
            $targets += $files.FullName
        }
        elseif (Test-Path -Path $resolvedPath -PathType Leaf) {
            $ext = [System.IO.Path]::GetExtension($resolvedPath).ToLowerInvariant()
            if ($ext -eq '.wmf' -or $ext -eq '.emf') {
                $targets += (Get-Item -Path $resolvedPath).FullName
            } else {
                Write-Warning "File dilewati (bukan .wmf atau .emf): $resolvedPath"
            }
        }
        else {
            Write-Warning "Path tidak ditemukan: $item"
        }

        foreach ($file in $targets) {
            $processedCount++
            $fileSw = [System.Diagnostics.Stopwatch]::StartNew()

            try {
                $rawBytes = [System.IO.File]::ReadAllBytes($file)
                if ($rawBytes.Length -eq 0) {
                    throw "File kosong (0 bytes)."
                }

                $ms = New-Object System.IO.MemoryStream (,$rawBytes)
                $mf = New-Object System.Drawing.Imaging.Metafile $ms
                $header = $mf.GetMetafileHeader()
                $bounds = $header.Bounds

                $origW = $bounds.Width
                $origH = $bounds.Height
                $dpiX = $header.DpiX
                $dpiY = $header.DpiY

                if ($origW -le 0 -or $origH -le 0) {
                    $origW = $mf.Width
                    $origH = $mf.Height
                }
                if ($origW -le 0 -or $origH -le 0) {
                    $origW = 800
                    $origH = 600
                }

                if ($dpiX -le 1 -or [float]::IsNaN($dpiX) -or [float]::IsInfinity($dpiX)) { $dpiX = 96.0 }
                if ($dpiY -le 1 -or [float]::IsNaN($dpiY) -or [float]::IsInfinity($dpiY)) { $dpiY = 96.0 }

                $targetW = 0
                $targetH = 0
                $outDpi = 300

                if ($UseDpi -and $Dpi -gt 0) {
                    $outDpi = $Dpi
                    $inchesW = $origW / $dpiX
                    $inchesH = $origH / $dpiY
                    $targetW = [int][Math]::Round($inchesW * $Dpi)
                    $targetH = [int][Math]::Round($inchesH * $Dpi)
                } else {
                    $baseW = ($origW / $dpiX) * 96.0
                    $baseH = ($origH / $dpiY) * 96.0
                    if ($baseW -lt 50 -or $baseH -lt 50) {
                        $baseW = $origW
                        $baseH = $origH
                    }
                    $targetW = [int][Math]::Round($baseW * $Scale)
                    $targetH = [int][Math]::Round($baseH * $Scale)
                    $outDpi = [int][Math]::Round(96.0 * $Scale)
                }

                $pad = [Math]::Max(0, $Padding)
                $targetW += ($pad * 2)
                $targetH += ($pad * 2)

                $targetW = [Math]::Max(16, [Math]::Min(16384, $targetW))
                $targetH = [Math]::Max(16, [Math]::Min(16384, $targetH))

                $bmp = New-Object System.Drawing.Bitmap $targetW, $targetH, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                $bmp.SetResolution($outDpi, $outDpi)

                $g = [System.Drawing.Graphics]::FromImage($bmp)
                $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

                switch ($Background) {
                    'White' { $g.Clear([System.Drawing.Color]::White) }
                    'Black' { $g.Clear([System.Drawing.Color]::Black) }
                    default { $g.Clear([System.Drawing.Color]::Transparent) }
                }

                $destRect = New-Object System.Drawing.Rectangle $pad, $pad, ($targetW - ($pad * 2)), ($targetH - ($pad * 2))
                $g.DrawImage($mf, $destRect)
                $g.Dispose()
                $mf.Dispose()
                $ms.Dispose()

                if ($KeyOutWhite) {
                    $rect = New-Object System.Drawing.Rectangle 0, 0, $bmp.Width, $bmp.Height
                    $data = $bmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadWrite, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                    $stride = [Math]::Abs($data.Stride)
                    $pixelBytes = New-Object byte[] ($stride * $bmp.Height)
                    [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $pixelBytes, 0, $pixelBytes.Length)

                    for ($i = 0; $i -lt $pixelBytes.Length; $i += 4) {
                        $b = $pixelBytes[$i]
                        $gCol = $pixelBytes[$i + 1]
                        $r = $pixelBytes[$i + 2]
                        $a = $pixelBytes[$i + 3]

                        if ($a -gt 0 -and $r -ge 248 -and $gCol -ge 248 -and $b -ge 248) {
                            $pixelBytes[$i + 3] = 0
                        }
                    }

                    [System.Runtime.InteropServices.Marshal]::Copy($pixelBytes, 0, $data.Scan0, $pixelBytes.Length)
                    $bmp.UnlockBits($data)
                }

                $destFolder = if (![string]::IsNullOrEmpty($OutputDir)) { $OutputDir } else { [System.IO.Path]::GetDirectoryName($file) }
                if (-not (Test-Path $destFolder)) {
                    New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
                }

                $fileNameOnly = [System.IO.Path]::GetFileNameWithoutExtension($file)
                $finalOutPath = [System.IO.Path]::Combine($destFolder, "$fileNameOnly.png")

                $bmp.Save($finalOutPath, [System.Drawing.Imaging.ImageFormat]::Png)
                $bmp.Dispose()
                $fileSw.Stop()

                $successCount++
                Write-Host "  [OK] $fileNameOnly.wmf -> $fileNameOnly.png ($($targetW)x$($targetH) px, $($fileSw.ElapsedMilliseconds)ms)" -ForegroundColor Green

            } catch {
                $fileSw.Stop()
                Write-Host "  [GAGAL] $([System.IO.Path]::GetFileName($file)): $_" -ForegroundColor Red
            }
        }
    }
}

end {
    $stopwatch.Stop()
    $totalSec = [Math]::Round($stopwatch.ElapsedMilliseconds / 1000.0, 2)
    Write-Host "`nSelesai! Berhasil konversi $successCount/$processedCount file dalam $totalSec detik." -ForegroundColor Cyan
}
