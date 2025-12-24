# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                      GLOBALMAIN INTERACTIVE COMMAND MENU                     ║
# ║                           PowerShell Edition v2.0                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

$Host.UI.RawUI.WindowTitle = "GlobalMain Command Center"

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
$Colors = @{
    Header    = "Cyan"
    Category  = "Yellow"
    Command   = "Green"
    Text      = "White"
    Dim       = "DarkGray"
    Highlight = "Magenta"
    Success   = "Green"
    Warning   = "Yellow"
    Error     = "Red"
}

# ═══════════════════════════════════════════════════════════════════════════════
# MENU DATA - Easily extendable
# ═══════════════════════════════════════════════════════════════════════════════

$Categories = @(
    @{ Key = "1"; Icon = "🚀"; Name = "HIZLI BAŞLANGIÇ"; Desc = "Temel başlatma/durdurma komutları" }
    @{ Key = "2"; Icon = "🔴"; Name = "İZLEME"; Desc = "Monitor ve log komutları" }
    @{ Key = "3"; Icon = "🔧"; Name = "ARAÇLAR"; Desc = "Shell ve yardımcı araçlar" }
    @{ Key = "4"; Icon = "💾"; Name = "YEDEKLEME"; Desc = "Backup işlemleri" }
    @{ Key = "5"; Icon = "🗄️"; Name = "VERİTABANI"; Desc = "Database işlemleri" }
    @{ Key = "6"; Icon = "🧹"; Name = "TEMİZLİK"; Desc = "Temizlik komutları" }
    @{ Key = "7"; Icon = "📦"; Name = "BUILD & DEPLOY"; Desc = "Production komutları" }
    @{ Key = "8"; Icon = "💻"; Name = "LOCAL DEV"; Desc = "Yerel geliştirme" }
    @{ Key = "9"; Icon = "🔗"; Name = "ASRIN CORE"; Desc = "Merkezi kalıtım sistemi" }
)

$CategoryCommands = @{
    "1" = @(
        @{ Key = "1"; Cmd = "dev"; Desc = "Geliştirme ortamını başlat" }
        @{ Key = "2"; Cmd = "dev-nginx"; Desc = "Nginx + Gunicorn stack" }
        @{ Key = "3"; Cmd = "dev-build"; Desc = "Build ile başlat" }
        @{ Key = "4"; Cmd = "stop"; Desc = "Tüm servisleri durdur" }
        @{ Key = "5"; Cmd = "status"; Desc = "Container durumları" }
    )
    "2" = @(
        @{ Key = "1"; Cmd = "monitor"; Desc = "Terminal Monitor" }
        @{ Key = "2"; Cmd = "monitor-web"; Desc = "Web Dashboard (:9000)" }
        @{ Key = "3"; Cmd = "monitor-live"; Desc = "Live Request Monitor" }
        @{ Key = "4"; Cmd = "logs"; Desc = "Web container logları" }
        @{ Key = "5"; Cmd = "logs-all"; Desc = "Tüm loglar" }
        @{ Key = "6"; Cmd = "logs-nginx"; Desc = "Nginx logları" }
    )
    "3" = @(
        @{ Key = "1"; Cmd = "shell"; Desc = "Container bash" }
        @{ Key = "2"; Cmd = "django-shell"; Desc = "Django shell" }
        @{ Key = "3"; Cmd = "pgadmin"; Desc = "pgAdmin4 (:5050)" }
        @{ Key = "4"; Cmd = "mailhog"; Desc = "Mailhog (:8025)" }
    )
    "4" = @(
        @{ Key = "1"; Cmd = "backup"; Desc = "Şimdi backup al" }
        @{ Key = "2"; Cmd = "backup-auto"; Desc = "Otomatik backup" }
        @{ Key = "3"; Cmd = "backup-list"; Desc = "Backup listesi" }
        @{ Key = "4"; Cmd = "backup-logs"; Desc = "Backup logları" }
    )
    "5" = @(
        @{ Key = "1"; Cmd = "migrate"; Desc = "Migration çalıştır" }
        @{ Key = "2"; Cmd = "db-shell"; Desc = "PostgreSQL shell" }
        @{ Key = "3"; Cmd = "restore"; Desc = "Restore bilgileri" }
    )
    "6" = @(
        @{ Key = "1"; Cmd = "clean"; Desc = "Cache temizle" }
        @{ Key = "2"; Cmd = "clean-all"; Desc = "Docker dahil temizle" }
    )
    "7" = @(
        @{ Key = "1"; Cmd = "collectstatic"; Desc = "Static dosyaları topla" }
        @{ Key = "2"; Cmd = "prod"; Desc = "Production başlat" }
        @{ Key = "3"; Cmd = "prod-stop"; Desc = "Production durdur" }
    )
    "8" = @(
        @{ Key = "1"; Cmd = "install"; Desc = "Bağımlılıkları yükle" }
        @{ Key = "2"; Cmd = "run"; Desc = "Yerel sunucu başlat" }
        @{ Key = "3"; Cmd = "test"; Desc = "Testleri çalıştır" }
        @{ Key = "4"; Cmd = "lint"; Desc = "Lint kontrolü" }
        @{ Key = "5"; Cmd = "format"; Desc = "Kod formatla" }
    )
    "9" = @(
        @{ Key = "1"; Cmd = "core-init"; Desc = "Yeni proje oluştur" }
        @{ Key = "2"; Cmd = "core-update"; Desc = "Merkezi güncelleme" }
        @{ Key = "3"; Cmd = "core-check"; Desc = "Güncelleme kontrolü" }
        @{ Key = "4"; Cmd = "core-sync"; Desc = "Projeleri senkronize et" }
        @{ Key = "5"; Cmd = "core-projects"; Desc = "Kayıtlı projeler" }
        @{ Key = "6"; Cmd = "core-install"; Desc = "Core paketi kur" }
    )
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

function Write-Banner {
    $banner = @"

    ╔══════════════════════════════════════════════════════════════════════╗
    ║   ██████╗ ██╗      ██████╗ ██████╗  █████╗ ██╗     ███╗   ███╗       ║
    ║  ██╔════╝ ██║     ██╔═══██╗██╔══██╗██╔══██╗██║     ████╗ ████║       ║
    ║  ██║  ███╗██║     ██║   ██║██████╔╝███████║██║     ██╔████╔██║       ║
    ║  ██║   ██║██║     ██║   ██║██╔══██╗██╔══██║██║     ██║╚██╔╝██║       ║
    ║  ╚██████╔╝███████╗╚██████╔╝██████╔╝██║  ██║███████╗██║ ╚═╝ ██║       ║
    ║   ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝       ║
    ║                    🎮  COMMAND CENTER  🎮                            ║
    ╚══════════════════════════════════════════════════════════════════════╝
"@
    Write-Host $banner -ForegroundColor $Colors.Header
}

function Show-SystemStatus {
    Write-Host ""
    Write-Host "╭──────────────────────────── SİSTEM DURUMU ────────────────────────────╮" -ForegroundColor $Colors.Header
    
    try {
        $dockerStatus = wsl docker ps --format "{{.Names}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $containers = $dockerStatus | Where-Object { $_ -match '\S' }
            $count = ($containers | Measure-Object).Count
            Write-Host "│  🐳 Docker: ✓ Çalışıyor ($count container)                              │" -ForegroundColor $Colors.Success
            
            $running = ($containers | Select-Object -First 3) -join " "
            if ($running) {
                $line = "│     └─ $running".PadRight(75) + "│"
                Write-Host $line -ForegroundColor $Colors.Dim
            }
        } else {
            Write-Host "│  🐳 Docker: ✗ Kapalı                                                   │" -ForegroundColor $Colors.Warning
        }
    }
    catch {
        Write-Host "│  🐳 Docker: ? Kontrol edilemiyor                                       │" -ForegroundColor $Colors.Warning
    }
    
    Write-Host "╰─────────────────────────────────────────────────────────────────────────╯" -ForegroundColor $Colors.Header
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU - Categories in columns
# ═══════════════════════════════════════════════════════════════════════════════

function Show-MainMenu {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Category
    Write-Host "  ║                        ANA MENÜ - KATEGORİLER                         ║" -ForegroundColor $Colors.Category
    Write-Host "  ╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Category
    Write-Host ""
    
    # Display categories in 2 columns
    $total = $Categories.Count
    $half = [Math]::Ceiling($total / 2)
    
    for ($i = 0; $i -lt $half; $i++) {
        $leftIdx = $i
        $rightIdx = $i + $half
        
        # Left column
        if ($leftIdx -lt $total) {
            $cat = $Categories[$leftIdx]
            Write-Host "  [" -NoNewline -ForegroundColor $Colors.Dim
            Write-Host "$($cat.Key)" -NoNewline -ForegroundColor $Colors.Command
            Write-Host "] " -NoNewline -ForegroundColor $Colors.Dim
            Write-Host "$($cat.Icon) $($cat.Name.PadRight(18))" -NoNewline -ForegroundColor $Colors.Header
        }
        
        # Right column
        if ($rightIdx -lt $total) {
            $cat = $Categories[$rightIdx]
            Write-Host "    [" -NoNewline -ForegroundColor $Colors.Dim
            Write-Host "$($cat.Key)" -NoNewline -ForegroundColor $Colors.Command
            Write-Host "] " -NoNewline -ForegroundColor $Colors.Dim
            Write-Host "$($cat.Icon) $($cat.Name)" -ForegroundColor $Colors.Header
        } else {
            Write-Host ""
        }
    }
    
    Write-Host ""
    Write-Host "  ╭───────────────────────────────────────────────────────────────────────╮" -ForegroundColor $Colors.Dim
    Write-Host "  │  " -NoNewline -ForegroundColor $Colors.Dim
    Write-Host "[D]" -NoNewline -ForegroundColor $Colors.Command
    Write-Host " Dev  " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "[S]" -NoNewline -ForegroundColor $Colors.Command
    Write-Host " Stop  " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "[M]" -NoNewline -ForegroundColor $Colors.Command
    Write-Host " Monitor  " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "[L]" -NoNewline -ForegroundColor $Colors.Command
    Write-Host " Logs  " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "[B]" -NoNewline -ForegroundColor $Colors.Command
    Write-Host " Backup  " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "[P]" -NoNewline -ForegroundColor $Colors.Command
    Write-Host " pgAdmin  " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "│" -ForegroundColor $Colors.Dim
    Write-Host "  │  " -NoNewline -ForegroundColor $Colors.Dim
    Write-Host "[Q]" -NoNewline -ForegroundColor $Colors.Warning
    Write-Host " Çıkış                    " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "[H]" -NoNewline -ForegroundColor $Colors.Warning
    Write-Host " Yardım                    " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "[R]" -NoNewline -ForegroundColor $Colors.Warning
    Write-Host " Yenile  " -NoNewline -ForegroundColor $Colors.Text
    Write-Host "│" -ForegroundColor $Colors.Dim
    Write-Host "  ╰───────────────────────────────────────────────────────────────────────╯" -ForegroundColor $Colors.Dim
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# SUB MENU - Commands in columns
# ═══════════════════════════════════════════════════════════════════════════════

function Show-SubMenu {
    param([string]$CategoryKey)
    
    $cat = $Categories | Where-Object { $_.Key -eq $CategoryKey }
    $commands = $CategoryCommands[$CategoryKey]
    
    while ($true) {
        Clear-Host
        Write-Banner
        
        Write-Host ""
        Write-Host "  ╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Highlight
        Write-Host "  ║  $($cat.Icon) $($cat.Name.PadRight(66))║" -ForegroundColor $Colors.Highlight
        Write-Host "  ║  $($cat.Desc.PadRight(68))║" -ForegroundColor $Colors.Dim
        Write-Host "  ╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Highlight
        Write-Host ""
        
        # Display commands in 2 columns
        $total = $commands.Count
        $half = [Math]::Ceiling($total / 2)
        
        for ($i = 0; $i -lt $half; $i++) {
            $leftIdx = $i
            $rightIdx = $i + $half
            
            # Left column
            if ($leftIdx -lt $total) {
                $cmd = $commands[$leftIdx]
                Write-Host "  [" -NoNewline -ForegroundColor $Colors.Dim
                Write-Host "$($cmd.Key)" -NoNewline -ForegroundColor $Colors.Command
                Write-Host "] " -NoNewline -ForegroundColor $Colors.Dim
                Write-Host "$($cmd.Cmd.PadRight(14))" -NoNewline -ForegroundColor $Colors.Text
                Write-Host "$($cmd.Desc.PadRight(22))" -NoNewline -ForegroundColor $Colors.Dim
            } else {
                Write-Host "".PadRight(42) -NoNewline
            }
            
            # Right column
            if ($rightIdx -lt $total) {
                $cmd = $commands[$rightIdx]
                Write-Host "  [" -NoNewline -ForegroundColor $Colors.Dim
                Write-Host "$($cmd.Key)" -NoNewline -ForegroundColor $Colors.Command
                Write-Host "] " -NoNewline -ForegroundColor $Colors.Dim
                Write-Host "$($cmd.Cmd.PadRight(14))" -NoNewline -ForegroundColor $Colors.Text
                Write-Host "$($cmd.Desc)" -ForegroundColor $Colors.Dim
            } else {
                Write-Host ""
            }
        }
        
        Write-Host ""
        Write-Host "  ─────────────────────────────────────────────────────────────────────────" -ForegroundColor $Colors.Dim
        Write-Host "  " -NoNewline
        Write-Host "[0]" -NoNewline -ForegroundColor $Colors.Warning
        Write-Host " Ana Menüye Dön    " -NoNewline -ForegroundColor $Colors.Text
        Write-Host "[Q]" -NoNewline -ForegroundColor $Colors.Warning
        Write-Host " Çıkış" -ForegroundColor $Colors.Text
        Write-Host ""
        
        $choice = Read-Host "  Seçiminiz"
        $choice = $choice.Trim()
        
        if ($choice -eq "0" -or $choice -eq "") {
            return
        }
        elseif ($choice -eq "Q" -or $choice -eq "q") {
            Write-Host "`n  👋 Görüşürüz!`n" -ForegroundColor $Colors.Success
            exit
        }
        else {
            $selectedCmd = $commands | Where-Object { $_.Key -eq $choice }
            if ($selectedCmd) {
                Execute-Command $selectedCmd.Cmd
                Read-Host "  Enter'a basın..."
            }
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTE COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

function Execute-Command {
    param([string]$CommandName)
    
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Highlight
    Write-Host "║  ▶ Çalıştırılıyor: make $CommandName" -ForegroundColor $Colors.Success
    Write-Host "╚═══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Highlight
    Write-Host ""
    
    $wslPath = "/mnt/d/workspace/globalMain/.v1"
    $command = "cd $wslPath && make $CommandName"
    
    try {
        wsl bash -c $command
        Write-Host ""
        Write-Host "  ✅ Komut tamamlandı!" -ForegroundColor $Colors.Success
    }
    catch {
        Write-Host "  ❌ Hata: $_" -ForegroundColor $Colors.Error
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════════

function Show-Help {
    Clear-Host
    Write-Host @"

  ╔══════════════════════════════════════════════════════════════════════════╗
  ║                                YARDIM                                    ║
  ╠══════════════════════════════════════════════════════════════════════════╣
  ║                                                                          ║
  ║  KULLANIM:                                                               ║
  ║  ─────────                                                               ║
  ║  1. Ana menüden kategori numarasını seçin (1-9)                          ║
  ║  2. Alt menüden komut numarasını seçin                                   ║
  ║  3. Veya hızlı kısayolları kullanın                                      ║
  ║                                                                          ║
  ║  HIZLI KISAYOLLAR:                                                       ║
  ║  ─────────────────                                                       ║
  ║  D → make dev          S → make stop         M → make monitor            ║
  ║  L → make logs         B → make backup       P → make pgadmin            ║
  ║  N → make dev-nginx    C → make clean                                    ║
  ║                                                                          ║
  ║  NAVİGASYON:                                                             ║
  ║  ───────────                                                             ║
  ║  0 → Ana menüye dön    Q → Çıkış             R → Yenile                  ║
  ║  H → Bu yardım                                                           ║
  ║                                                                          ║
  ╚══════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $Colors.Header
    
    Write-Host ""
    Write-Host "  Devam etmek için bir tuşa basın..." -ForegroundColor $Colors.Dim
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

$running = $true

while ($running) {
    Clear-Host
    Write-Banner
    Show-SystemStatus
    Show-MainMenu
    
    $choice = Read-Host "  Seçiminiz"
    $choice = $choice.Trim().ToUpper()
    
    switch ($choice) {
        "Q" { 
            Write-Host "`n  👋 Görüşürüz!`n" -ForegroundColor $Colors.Success
            $running = $false 
        }
        "H" { Show-Help }
        "R" { continue }
        
        # Quick shortcuts
        "D" { Execute-Command "dev"; Read-Host "  Enter'a basın..." }
        "S" { Execute-Command "stop"; Read-Host "  Enter'a basın..." }
        "M" { Execute-Command "monitor"; Read-Host "  Enter'a basın..." }
        "L" { Execute-Command "logs"; Read-Host "  Enter'a basın..." }
        "B" { Execute-Command "backup"; Read-Host "  Enter'a basın..." }
        "P" { Execute-Command "pgadmin"; Read-Host "  Enter'a basın..." }
        "N" { Execute-Command "dev-nginx"; Read-Host "  Enter'a basın..." }
        "C" { Execute-Command "clean"; Read-Host "  Enter'a basın..." }
        
        # Category selection (1-9)
        { $_ -match '^[1-9]$' } { Show-SubMenu $choice }
        
        default {
            if ($choice -ne "") {
                Write-Host "`n  ⚠️  Geçersiz seçim: $choice" -ForegroundColor $Colors.Warning
                Start-Sleep -Seconds 1
            }
        }
    }
}

