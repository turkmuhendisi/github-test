#!/usr/bin/env python
"""
Asrın Core - Merkezi Güncelleme CLI
===================================

Merkezi Ayar Yönetim Sisteminden güncellemeleri çeker.

Kullanım:
---------
    asrin-update              # Otomatik güncelleme
    asrin-update --check      # Güncelleme kontrolü
    asrin-update --force      # Zorla güncelle

Parametreler:
-------------
    --check: Sadece güncelleme olup olmadığını kontrol et
    --force: Yerel değişiklikleri yok sayarak güncelle
    --branch: Belirli bir branch'ten güncelle
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# =============================================================================
# CONSTANTS
# =============================================================================

CORE_REPO_URL = "https://github.com/asringlobal/globalmain.git"
CORE_BRANCH = "main"


# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================

def detect_installation_type(project_path: Path) -> str:
    """
    Asrın Core kurulum tipini tespit eder.
    
    Returns:
        'submodule' | 'subtree' | 'pip' | 'unknown'
    """
    
    # Git submodule kontrolü
    gitmodules = project_path / ".gitmodules"
    if gitmodules.exists():
        content = gitmodules.read_text()
        if "globalmain" in content or "asrin-core" in content:
            return "submodule"
    
    # Git subtree kontrolü (core dizini git history'si ile)
    core_dir = project_path / "core"
    if core_dir.exists() and (core_dir / ".v1").exists():
        # Subtree olup olmadığını kontrol et
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-1", "--", "core"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return "subtree"
        except:
            pass
    
    # Pip package kontrolü
    try:
        import config
        config_path = Path(config.__file__).parent
        if "site-packages" in str(config_path):
            return "pip"
        # Editable install kontrolü
        if ".v1" in str(config_path):
            return "pip-editable"
    except ImportError:
        pass
    
    return "unknown"


def get_current_version(project_path: Path, install_type: str) -> Optional[str]:
    """Mevcut asrin-core versiyonunu al."""
    
    if install_type in ["submodule", "subtree"]:
        core_path = project_path / "core" / ".v1"
        if not core_path.exists():
            core_path = project_path / "core"
        
        # Git commit hash'ini al
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=core_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]
        except:
            pass
    
    elif install_type == "pip":
        try:
            import pkg_resources
            return pkg_resources.get_distribution("asrin-core").version
        except:
            pass
    
    return None


def get_remote_version(branch: str = CORE_BRANCH) -> Optional[str]:
    """Uzak repo'daki son versiyonu al."""
    
    try:
        result = subprocess.run(
            ["git", "ls-remote", CORE_REPO_URL, f"refs/heads/{branch}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.split()[0][:8]
    except:
        pass
    
    return None


# =============================================================================
# UPDATE FUNCTIONS
# =============================================================================

def update_submodule(project_path: Path, branch: str, force: bool = False) -> bool:
    """Git submodule güncelle."""
    
    print("📦 Git submodule güncelleniyor...")
    
    cmd = ["git", "submodule", "update", "--remote"]
    if force:
        cmd.append("--force")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Submodule güncellendi")
            return True
        else:
            print(f"❌ Güncelleme hatası: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Güncelleme hatası: {e}")
        return False


def update_subtree(project_path: Path, branch: str, force: bool = False) -> bool:
    """Git subtree güncelle."""
    
    print("🌳 Git subtree güncelleniyor...")
    
    # Remote güncelle
    subprocess.run(
        ["git", "fetch", "asrin-core"],
        cwd=project_path,
        capture_output=True
    )
    
    # Subtree pull
    cmd = [
        "git", "subtree", "pull",
        "--prefix", "core",
        "asrin-core", branch,
        "--squash"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Subtree güncellendi")
            return True
        else:
            print(f"❌ Güncelleme hatası: {result.stderr}")
            if not force:
                print("   --force ile tekrar deneyin")
            return False
    except Exception as e:
        print(f"❌ Güncelleme hatası: {e}")
        return False


def update_pip(force: bool = False) -> bool:
    """Pip package güncelle."""
    
    print("📦 Pip package güncelleniyor...")
    
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "asrin-core"]
    if force:
        cmd.append("--force-reinstall")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Pip package güncellendi")
            return True
        else:
            print(f"❌ Güncelleme hatası: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Güncelleme hatası: {e}")
        return False


# =============================================================================
# CHECK FUNCTIONS
# =============================================================================

def check_for_updates(project_path: Path) -> Tuple[bool, str, str]:
    """
    Güncelleme olup olmadığını kontrol et.
    
    Returns:
        (update_available, current_version, remote_version)
    """
    
    install_type = detect_installation_type(project_path)
    current = get_current_version(project_path, install_type)
    remote = get_remote_version()
    
    if current and remote:
        return (current != remote, current, remote)
    
    return (False, current or "unknown", remote or "unknown")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Ana fonksiyon."""
    
    parser = argparse.ArgumentParser(
        description="Asrın Core - Merkezi Güncelleme Aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  asrin-update                 # Otomatik güncelle
  asrin-update --check         # Güncelleme kontrolü
  asrin-update --force         # Zorla güncelle
  asrin-update --branch dev    # dev branch'inden güncelle
        """
    )
    
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Sadece güncelleme olup olmadığını kontrol et"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Yerel değişiklikleri yok sayarak güncelle"
    )
    
    parser.add_argument(
        "--branch", "-b",
        default=CORE_BRANCH,
        help=f"Güncelleme branch'i (varsayılan: {CORE_BRANCH})"
    )
    
    parser.add_argument(
        "--path", "-p",
        type=Path,
        default=Path.cwd(),
        help="Proje dizini"
    )
    
    args = parser.parse_args()
    
    project_path = args.path.resolve()
    
    # Kurulum tipini tespit et
    install_type = detect_installation_type(project_path)
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🔄 Asrın Core - Güncelleme Kontrolü                            ║
╠══════════════════════════════════════════════════════════════════╣
║  Proje       : {str(project_path):<47} ║
║  Kurulum Tipi: {install_type:<47} ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    if install_type == "unknown":
        print("❌ Asrın Core kurulumu tespit edilemedi!")
        print("   Proje dizininde olduğunuzdan emin olun.")
        sys.exit(1)
    
    # Güncelleme kontrolü
    has_update, current, remote = check_for_updates(project_path)
    
    print(f"📊 Mevcut versiyon : {current}")
    print(f"📊 Uzak versiyon   : {remote}")
    
    if not has_update:
        print("\n✅ Zaten güncel!")
        if args.check:
            sys.exit(0)
        elif not args.force:
            sys.exit(0)
    else:
        print("\n🆕 Güncelleme mevcut!")
    
    # Sadece kontrol modundaysa çık
    if args.check:
        sys.exit(1 if has_update else 0)
    
    # Güncelleme yap
    print("\n" + "=" * 50)
    
    success = False
    
    if install_type == "submodule":
        success = update_submodule(project_path, args.branch, args.force)
    elif install_type == "subtree":
        success = update_subtree(project_path, args.branch, args.force)
    elif install_type in ["pip", "pip-editable"]:
        success = update_pip(args.force)
    
    if success:
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  ✅ Güncelleme Tamamlandı!                                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Sonraki Adımlar:                                               ║
║                                                                  ║
║  1. Migration kontrolü:                                         ║
║     python manage.py migrate --check                            ║
║                                                                  ║
║  2. Static dosyaları topla (gerekirse):                         ║
║     python manage.py collectstatic                              ║
║                                                                  ║
║  3. Servisi yeniden başlat:                                     ║
║     docker-compose restart web                                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
        sys.exit(0)
    else:
        print("\n❌ Güncelleme başarısız!")
        sys.exit(1)


if __name__ == "__main__":
    main()

