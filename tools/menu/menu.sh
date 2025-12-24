#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                      GLOBALMAIN INTERACTIVE COMMAND MENU                     ║
# ║                           Bash Edition v2.0                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Project directory (tools/menu -> tools -> project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_DIR" || exit 1

# Terminal width
TERM_WIDTH=$(tput cols 2>/dev/null || echo 80)
COL_WIDTH=$((TERM_WIDTH / 2 - 4))

# ═══════════════════════════════════════════════════════════════════════════════
# MENU DATA - Easily extendable
# ═══════════════════════════════════════════════════════════════════════════════

# Category definitions
declare -a CATEGORIES=(
    "1|🚀|HIZLI BAŞLANGIÇ|Temel başlatma/durdurma komutları"
    "2|🔴|İZLEME|Monitor ve log komutları"
    "3|🔧|ARAÇLAR|Shell ve yardımcı araçlar"
    "4|💾|YEDEKLEME|Backup işlemleri"
    "5|🗄️|VERİTABANI|Database işlemleri"
    "6|🧹|TEMİZLİK|Temizlik komutları"
    "7|📦|BUILD & DEPLOY|Production komutları"
    "8|💻|LOCAL DEV|Yerel geliştirme"
    "9|🔗|ASRIN CORE|Merkezi kalıtım sistemi"
)

# Commands per category: "key|command|description"
declare -a CAT_1_CMDS=(
    "1|dev|Geliştirme ortamını başlat"
    "2|dev-nginx|Nginx + Gunicorn stack"
    "3|dev-build|Build ile başlat"
    "4|stop|Tüm servisleri durdur"
    "5|status|Container durumları"
)

declare -a CAT_2_CMDS=(
    "1|monitor|Terminal Monitor"
    "2|monitor-web|Web Dashboard (:9000)"
    "3|monitor-live|Live Request Monitor"
    "4|logs|Web container logları"
    "5|logs-all|Tüm loglar"
    "6|logs-nginx|Nginx logları"
)

declare -a CAT_3_CMDS=(
    "1|shell|Container bash"
    "2|django-shell|Django shell"
    "3|pgadmin|pgAdmin4 (:5050)"
    "4|mailhog|Mailhog (:8025)"
)

declare -a CAT_4_CMDS=(
    "1|backup|Şimdi backup al"
    "2|backup-auto|Otomatik backup"
    "3|backup-list|Backup listesi"
    "4|backup-logs|Backup logları"
)

declare -a CAT_5_CMDS=(
    "1|migrate|Migration çalıştır"
    "2|db-shell|PostgreSQL shell"
    "3|restore|Restore bilgileri"
)

declare -a CAT_6_CMDS=(
    "1|clean|Cache temizle"
    "2|clean-all|Docker dahil temizle"
)

declare -a CAT_7_CMDS=(
    "1|collectstatic|Static dosyaları topla"
    "2|prod|Production başlat"
    "3|prod-stop|Production durdur"
)

declare -a CAT_8_CMDS=(
    "1|install|Bağımlılıkları yükle"
    "2|run|Yerel sunucu başlat"
    "3|test|Testleri çalıştır"
    "4|lint|Lint kontrolü"
    "5|format|Kod formatla"
)

declare -a CAT_9_CMDS=(
    "1|core-init|Yeni proje oluştur"
    "2|core-update|Merkezi güncelleme"
    "3|core-check|Güncelleme kontrolü"
    "4|core-sync|Projeleri senkronize et"
    "5|core-projects|Kayıtlı projeler"
    "6|core-install|Core paketi kur"
)

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

print_center() {
    local text="$1"
    local width=${2:-$TERM_WIDTH}
    local text_len=${#text}
    local padding=$(( (width - text_len) / 2 ))
    printf "%*s%s\n" $padding "" "$text"
}

print_line() {
    local char="${1:-═}"
    local width=${2:-$TERM_WIDTH}
    printf '%*s\n' "$width" '' | tr ' ' "$char"
}

show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════════════╗
    ║   ██████╗ ██╗      ██████╗ ██████╗  █████╗ ██╗     ███╗   ███╗       ║
    ║  ██╔════╝ ██║     ██╔═══██╗██╔══██╗██╔══██╗██║     ████╗ ████║       ║
    ║  ██║  ███╗██║     ██║   ██║██████╔╝███████║██║     ██╔████╔██║       ║
    ║  ██║   ██║██║     ██║   ██║██╔══██╗██╔══██║██║     ██║╚██╔╝██║       ║
    ║  ╚██████╔╝███████╗╚██████╔╝██████╔╝██║  ██║███████╗██║ ╚═╝ ██║       ║
    ║   ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝       ║
    ║                    🎮  COMMAND CENTER  🎮                            ║
    ╚══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

show_status() {
    echo -e "${CYAN}╭──────────────────────────── SİSTEM DURUMU ────────────────────────────╮${NC}"
    
    # Docker check
    if docker ps &>/dev/null; then
        container_count=$(docker ps --format "{{.Names}}" 2>/dev/null | wc -l)
        running=$(docker ps --filter "name=globalmain" --format "{{.Names}}" 2>/dev/null | head -3 | tr '\n' ' ')
        echo -e "${GREEN}│  🐳 Docker: ✓ Çalışıyor ($container_count container)                              │${NC}"
        if [ -n "$running" ]; then
            printf "${DIM}│     └─ %-62s │${NC}\n" "$running"
        fi
    else
        echo -e "${YELLOW}│  🐳 Docker: ✗ Kapalı                                                   │${NC}"
    fi
    
    echo -e "${CYAN}╰─────────────────────────────────────────────────────────────────────────╯${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU - Categories in columns
# ═══════════════════════════════════════════════════════════════════════════════

show_main_menu() {
    echo ""
    echo -e "${YELLOW}${BOLD}  ╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}${BOLD}  ║                        ANA MENÜ - KATEGORİLER                         ║${NC}"
    echo -e "${YELLOW}${BOLD}  ╚═══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Display categories in 2 columns
    local total=${#CATEGORIES[@]}
    local half=$(( (total + 1) / 2 ))
    
    for ((i=0; i<half; i++)); do
        local left_idx=$i
        local right_idx=$((i + half))
        
        # Left column
        if [ $left_idx -lt $total ]; then
            IFS='|' read -r key icon name desc <<< "${CATEGORIES[$left_idx]}"
            printf "  ${GRAY}[${NC}${GREEN}%s${NC}${GRAY}]${NC} ${CYAN}%s %-18s${NC}" "$key" "$icon" "$name"
        else
            printf "  %-30s" ""
        fi
        
        # Right column
        if [ $right_idx -lt $total ]; then
            IFS='|' read -r key icon name desc <<< "${CATEGORIES[$right_idx]}"
            printf "    ${GRAY}[${NC}${GREEN}%s${NC}${GRAY}]${NC} ${CYAN}%s %-18s${NC}" "$key" "$icon" "$name"
        fi
        
        echo ""
    done
    
    echo ""
    echo -e "${GRAY}  ╭───────────────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${GRAY}  │${NC}  ${GREEN}[D]${NC} Dev  ${GREEN}[S]${NC} Stop  ${GREEN}[M]${NC} Monitor  ${GREEN}[L]${NC} Logs  ${GREEN}[B]${NC} Backup  ${GREEN}[P]${NC} pgAdmin  ${GRAY}│${NC}"
    echo -e "${GRAY}  │${NC}  ${YELLOW}[Q]${NC} Çıkış                    ${YELLOW}[H]${NC} Yardım                    ${YELLOW}[R]${NC} Yenile  ${GRAY}│${NC}"
    echo -e "${GRAY}  ╰───────────────────────────────────────────────────────────────────────╯${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# SUB MENU - Commands in columns
# ═══════════════════════════════════════════════════════════════════════════════

show_sub_menu() {
    local cat_num=$1
    local -n cmds_ref="CAT_${cat_num}_CMDS"
    
    # Get category info
    local cat_info="${CATEGORIES[$((cat_num-1))]}"
    IFS='|' read -r _ icon name desc <<< "$cat_info"
    
    clear
    show_banner
    
    echo ""
    echo -e "${MAGENTA}${BOLD}  ╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    printf "${MAGENTA}${BOLD}  ║  %s %-66s ║${NC}\n" "$icon" "$name"
    printf "${MAGENTA}  ║  ${DIM}%-68s${NC}${MAGENTA} ║${NC}\n" "$desc"
    echo -e "${MAGENTA}${BOLD}  ╚═══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Display commands in 2 columns
    local total=${#cmds_ref[@]}
    local half=$(( (total + 1) / 2 ))
    
    for ((i=0; i<half; i++)); do
        local left_idx=$i
        local right_idx=$((i + half))
        
        # Left column
        if [ $left_idx -lt $total ]; then
            IFS='|' read -r key cmd desc <<< "${cmds_ref[$left_idx]}"
            printf "  ${GRAY}[${NC}${GREEN}%s${NC}${GRAY}]${NC} ${WHITE}%-12s${NC} ${GRAY}%s${NC}" "$key" "$cmd" "$desc"
        else
            printf "  %-40s" ""
        fi
        
        # Right column  
        if [ $right_idx -lt $total ]; then
            IFS='|' read -r key cmd desc <<< "${cmds_ref[$right_idx]}"
            printf "  ${GRAY}[${NC}${GREEN}%s${NC}${GRAY}]${NC} ${WHITE}%-12s${NC} ${GRAY}%s${NC}" "$key" "$cmd" "$desc"
        fi
        
        echo ""
    done
    
    echo ""
    echo -e "${GRAY}  ─────────────────────────────────────────────────────────────────────────${NC}"
    echo -e "  ${YELLOW}[0]${NC} Ana Menüye Dön    ${YELLOW}[Q]${NC} Çıkış"
    echo ""
    
    read -r -p "  Seçiminiz: " choice
    
    if [[ "$choice" == "0" || "$choice" == "" ]]; then
        return 0
    elif [[ "$choice" =~ ^[Qq]$ ]]; then
        echo -e "\n  ${GREEN}👋 Görüşürüz!${NC}\n"
        exit 0
    elif [[ "$choice" =~ ^[0-9]+$ ]]; then
        for cmd_item in "${cmds_ref[@]}"; do
            IFS='|' read -r key cmd _ <<< "$cmd_item"
            if [ "$key" == "$choice" ]; then
                execute_command "$cmd"
                read -n 1 -s -r -p "  Enter'a basın..."
                break
            fi
        done
    fi
    
    # Stay in submenu
    show_sub_menu "$cat_num"
}

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTE COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

execute_command() {
    local cmd=$1
    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ▶ Çalıştırılıyor: make $cmd${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    make "$cmd"
    
    echo ""
    echo -e "${GREEN}  ✅ Komut tamamlandı!${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════════

show_help() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
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
EOF
    echo -e "${NC}"
    read -n 1 -s -r -p "  Devam etmek için bir tuşa basın..."
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

while true; do
    show_banner
    show_status
    show_main_menu
    
    read -r -p "  Seçiminiz: " choice
    choice=$(echo "$choice" | tr '[:lower:]' '[:upper:]')
    
    case $choice in
        Q|QUIT|EXIT)
            echo -e "\n  ${GREEN}👋 Görüşürüz!${NC}\n"
            exit 0
            ;;
        H|HELP)
            show_help
            ;;
        R|REFRESH)
            continue
            ;;
        # Quick shortcuts
        D) execute_command "dev"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        S) execute_command "stop"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        M) execute_command "monitor"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        L) execute_command "logs"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        B) execute_command "backup"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        P) execute_command "pgadmin"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        N) execute_command "dev-nginx"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        C) execute_command "clean"; read -n 1 -s -r -p "  Enter'a basın..." ;;
        # Category selection
        [1-9])
            show_sub_menu "$choice"
            ;;
        *)
            if [ -n "$choice" ]; then
                echo -e "  ${YELLOW}⚠️  Geçersiz seçim: $choice${NC}"
                sleep 1
            fi
            ;;
    esac
done

