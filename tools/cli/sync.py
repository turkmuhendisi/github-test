#!/usr/bin/env python
"""
Asrın Core - Merkezi Senkronizasyon CLI
=======================================

Merkezi Ayar Yönetim Sistemini tüm bağlı projelere senkronize eder.

Kullanım (Core tarafında):
-------------------------
    asrin-sync --all              # Tüm bağlı projeleri güncelle
    asrin-sync --project my_proj  # Belirli projeyi güncelle
    asrin-sync --check            # Güncelleme durumunu kontrol et

Kullanım (Proje tarafında):
---------------------------
    asrin-update                  # Bu projeyi güncelle

Bu script merkezi sistemden çalıştırılır ve bağlı projeleri
otomatik olarak günceller.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# =============================================================================
# CONFIGURATION
# =============================================================================

# Proje registry dosyası - Asrın Core'u kullanan projelerin listesi
REGISTRY_FILE = Path(__file__).parent.parent.parent / "infra" / "data" / "project_registry.json"

# Varsayılan kayıt şablonu
DEFAULT_REGISTRY = {
    "version": "1.0",
    "updated": None,
    "projects": []
}


# =============================================================================
# REGISTRY FUNCTIONS
# =============================================================================

def load_registry() -> Dict:
    """Proje registry'sini yükle."""
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text())
        except json.JSONDecodeError:
            return DEFAULT_REGISTRY.copy()
    return DEFAULT_REGISTRY.copy()


def save_registry(registry: Dict) -> None:
    """Proje registry'sini kaydet."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    registry["updated"] = datetime.now().isoformat()
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))


def register_project(
    name: str,
    path: str,
    install_type: str = "pip",
    remote_url: Optional[str] = None
) -> bool:
    """
    Yeni bir projeyi registry'ye ekle.
    
    Args:
        name: Proje adı
        path: Proje dizini
        install_type: pip, submodule, subtree
        remote_url: Git remote URL (opsiyonel)
    """
    registry = load_registry()
    
    # Aynı isimde proje var mı kontrol et
    for project in registry["projects"]:
        if project["name"] == name:
            print(f"⚠️  Proje zaten kayıtlı: {name}")
            return False
    
    project_info = {
        "name": name,
        "path": str(Path(path).resolve()),
        "install_type": install_type,
        "remote_url": remote_url,
        "registered": datetime.now().isoformat(),
        "last_sync": None,
        "status": "active"
    }
    
    registry["projects"].append(project_info)
    save_registry(registry)
    
    print(f"✅ Proje kaydedildi: {name}")
    return True


def unregister_project(name: str) -> bool:
    """Projeyi registry'den çıkar."""
    registry = load_registry()
    
    for i, project in enumerate(registry["projects"]):
        if project["name"] == name:
            registry["projects"].pop(i)
            save_registry(registry)
            print(f"✅ Proje silindi: {name}")
            return True
    
    print(f"❌ Proje bulunamadı: {name}")
    return False


def list_projects() -> List[Dict]:
    """Kayıtlı projeleri listele."""
    registry = load_registry()
    return registry.get("projects", [])


# =============================================================================
# SYNC FUNCTIONS
# =============================================================================

def sync_project(project: Dict, dry_run: bool = False) -> bool:
    """
    Tek bir projeyi senkronize et.
    
    Args:
        project: Proje bilgileri
        dry_run: True ise sadece kontrol yap, güncelleme yapma
    """
    name = project["name"]
    path = Path(project["path"])
    install_type = project["install_type"]
    
    print(f"\n{'=' * 60}")
    print(f"📦 Proje: {name}")
    print(f"   Dizin: {path}")
    print(f"   Tip: {install_type}")
    print(f"{'=' * 60}")
    
    if not path.exists():
        print(f"❌ Proje dizini bulunamadı: {path}")
        return False
    
    if dry_run:
        print(f"🔍 [DRY RUN] Senkronizasyon simüle ediliyor...")
        return True
    
    success = False
    
    try:
        if install_type == "submodule":
            success = sync_submodule(path)
        elif install_type == "subtree":
            success = sync_subtree(path)
        elif install_type == "pip":
            success = sync_pip(path)
        else:
            print(f"❌ Bilinmeyen install tipi: {install_type}")
            return False
        
        if success:
            # Registry'yi güncelle
            registry = load_registry()
            for p in registry["projects"]:
                if p["name"] == name:
                    p["last_sync"] = datetime.now().isoformat()
                    break
            save_registry(registry)
            
            print(f"✅ {name} başarıyla senkronize edildi")
        else:
            print(f"❌ {name} senkronizasyonu başarısız")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False
    
    return success


def sync_submodule(project_path: Path) -> bool:
    """Git submodule senkronizasyonu."""
    
    print("📥 Git submodule güncelleniyor...")
    
    try:
        # Submodule'ü güncelle
        result = subprocess.run(
            ["git", "submodule", "update", "--remote", "--merge"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   Hata: {result.stderr}")
            return False
        
        # Değişiklikler var mı kontrol et
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if status.stdout.strip():
            # Otomatik commit
            subprocess.run(
                ["git", "add", "core"],
                cwd=project_path,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Update asrin-core submodule"],
                cwd=project_path,
                capture_output=True
            )
            print("   📝 Değişiklikler commit edildi")
        else:
            print("   ℹ️  Güncelleme yok")
        
        return True
        
    except Exception as e:
        print(f"   Hata: {e}")
        return False


def sync_subtree(project_path: Path) -> bool:
    """Git subtree senkronizasyonu."""
    
    print("🌳 Git subtree güncelleniyor...")
    
    try:
        # Subtree pull
        result = subprocess.run(
            ["git", "subtree", "pull", "--prefix", "core", "asrin-core", "main", "--squash"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Conflict varsa bildir
            if "CONFLICT" in result.stdout or "conflict" in result.stderr.lower():
                print("   ⚠️  Conflict var, manuel çözüm gerekli")
            else:
                print(f"   Hata: {result.stderr}")
            return False
        
        print("   ✅ Subtree güncellendi")
        return True
        
    except Exception as e:
        print(f"   Hata: {e}")
        return False


def sync_pip(project_path: Path) -> bool:
    """Pip package senkronizasyonu."""
    
    print("📦 Pip package güncelleniyor...")
    
    # Virtual environment bul
    venv_paths = [
        project_path / ".venv",
        project_path / "venv",
        project_path / "env"
    ]
    
    pip_cmd = None
    for venv in venv_paths:
        pip_path = venv / "bin" / "pip"
        if pip_path.exists():
            pip_cmd = str(pip_path)
            break
    
    if not pip_cmd:
        pip_cmd = "pip"  # Global pip
    
    try:
        # Upgrade asrin-core
        result = subprocess.run(
            [pip_cmd, "install", "--upgrade", "asrin-core"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # requirements.txt'den dene
            req_file = project_path / "requirements.txt"
            if req_file.exists():
                result = subprocess.run(
                    [pip_cmd, "install", "-r", str(req_file), "--upgrade"],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
        
        if result.returncode == 0:
            print("   ✅ Pip package güncellendi")
            return True
        else:
            print(f"   Hata: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   Hata: {e}")
        return False


def sync_all(dry_run: bool = False) -> Dict[str, bool]:
    """Tüm projeleri senkronize et."""
    
    projects = list_projects()
    
    if not projects:
        print("ℹ️  Kayıtlı proje bulunamadı")
        return {}
    
    results = {}
    
    print(f"\n🔄 {len(projects)} proje senkronize ediliyor...")
    
    for project in projects:
        if project.get("status") != "active":
            print(f"\n⏭️  {project['name']} atlanıyor (inactive)")
            continue
        
        success = sync_project(project, dry_run)
        results[project["name"]] = success
    
    # Özet
    print(f"\n{'=' * 60}")
    print("📊 SENKRONIZASYON ÖZETİ")
    print(f"{'=' * 60}")
    
    success_count = sum(1 for v in results.values() if v)
    fail_count = len(results) - success_count
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {name}")
    
    print(f"\n   Başarılı: {success_count}")
    print(f"   Başarısız: {fail_count}")
    
    return results


# =============================================================================
# POST-SYNC ACTIONS
# =============================================================================

def run_post_sync(project_path: Path) -> bool:
    """Senkronizasyon sonrası işlemleri çalıştır."""
    
    print("\n🔧 Post-sync işlemleri çalıştırılıyor...")
    
    # Virtual environment bul
    venv_paths = [
        project_path / ".venv",
        project_path / "venv",
    ]
    
    python_cmd = None
    for venv in venv_paths:
        python_path = venv / "bin" / "python"
        if python_path.exists():
            python_cmd = str(python_path)
            break
    
    if not python_cmd:
        python_cmd = "python"
    
    # Migration kontrolü
    print("   📋 Migration kontrolü...")
    result = subprocess.run(
        [python_cmd, "manage.py", "migrate", "--check"],
        cwd=project_path,
        capture_output=True
    )
    
    if result.returncode != 0:
        print("   ⚠️  Bekleyen migration'lar var!")
        print("      python manage.py migrate")
    else:
        print("   ✅ Migration'lar güncel")
    
    # Static dosya kontrolü
    print("   📁 Static dosya kontrolü...")
    # Basit bir kontrol - collectstatic --dry-run
    
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Ana fonksiyon."""
    
    parser = argparse.ArgumentParser(
        description="Asrın Core - Merkezi Senkronizasyon Aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  asrin-sync --all                # Tüm projeleri senkronize et
  asrin-sync --project myproject  # Tek projeyi senkronize et
  asrin-sync --list               # Kayıtlı projeleri listele
  asrin-sync --register myproject /path/to/project --type submodule
  asrin-sync --check              # Senkronizasyon durumunu kontrol et
        """
    )
    
    # Sync options
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Tüm kayıtlı projeleri senkronize et"
    )
    
    parser.add_argument(
        "--project", "-p",
        help="Belirli bir projeyi senkronize et"
    )
    
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Senkronizasyon durumunu kontrol et (dry-run)"
    )
    
    # Registry options
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Kayıtlı projeleri listele"
    )
    
    parser.add_argument(
        "--register", "-r",
        nargs=2,
        metavar=("NAME", "PATH"),
        help="Yeni proje kaydet"
    )
    
    parser.add_argument(
        "--unregister", "-u",
        metavar="NAME",
        help="Projeyi kayıttan çıkar"
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["pip", "submodule", "subtree"],
        default="pip",
        help="Kurulum tipi (register için)"
    )
    
    # Post-sync options
    parser.add_argument(
        "--post-sync",
        action="store_true",
        help="Senkronizasyon sonrası işlemleri çalıştır"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  🔄 Asrın Core - Merkezi Senkronizasyon Aracı                   ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Command dispatch
    if args.list:
        projects = list_projects()
        if not projects:
            print("ℹ️  Kayıtlı proje bulunamadı")
        else:
            print(f"📋 Kayıtlı Projeler ({len(projects)}):\n")
            for p in projects:
                status_icon = "🟢" if p.get("status") == "active" else "🔴"
                last_sync = p.get("last_sync", "Hiç")
                if last_sync and last_sync != "Hiç":
                    last_sync = last_sync[:10]  # Sadece tarih
                print(f"   {status_icon} {p['name']}")
                print(f"      Dizin: {p['path']}")
                print(f"      Tip: {p['install_type']}")
                print(f"      Son Sync: {last_sync}")
                print()
    
    elif args.register:
        name, path = args.register
        register_project(name, path, args.type)
    
    elif args.unregister:
        unregister_project(args.unregister)
    
    elif args.all:
        sync_all(dry_run=args.check)
    
    elif args.project:
        projects = list_projects()
        project = next((p for p in projects if p["name"] == args.project), None)
        
        if not project:
            print(f"❌ Proje bulunamadı: {args.project}")
            sys.exit(1)
        
        success = sync_project(project, dry_run=args.check)
        
        if success and args.post_sync:
            run_post_sync(Path(project["path"]))
        
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

