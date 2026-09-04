import os
import sys
import argparse
from pathlib import Path

# Configure UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).parent.parent
LOG_FILE = ROOT_DIR / "tools" / "diff_audit.log"

def run_phase_1():
    from audit_stats import run_stats_audit
    print("\n>>> Ejecutando Fase 1: Auditoría de Estadísticas e Información de Compis...")
    res = run_stats_audit(log_mode="a")
    return res

def run_phase_2():
    print("\n>>> Ejecutando Fase 2: Auditoría de Descripciones y Localización (ES/EN/FR/JA/ZH)...")
    # Check if audit_descriptions.py exists
    desc_script = Path(__file__).parent / "audit_descriptions.py"
    if desc_script.exists():
        import audit_descriptions
        return audit_descriptions.run_descriptions_audit(log_mode="a")
    else:
        print("[INFO] La Fase 2 está programada para su implementación tras la aprobación de la Fase 1.")
        return None

def run_phase_3():
    print("\n>>> Ejecutando Fase 3: Auditoría de Potencias y Motor de Daño al 100%...")
    damage_script = Path(__file__).parent / "audit_damage_engine.py"
    if damage_script.exists():
        import audit_damage_engine
        return audit_damage_engine.run_damage_audit(log_mode="a")
    else:
        print("[INFO] La Fase 3 está programada para su implementación tras la Fase 2.")
        return None

def view_log():
    if not LOG_FILE.exists():
        print("\n[INFO] El archivo diff_audit.log no existe aún. Ejecuta una fase primero.")
        return
    print(f"\n{'='*60}")
    print(f"   CONTENIDO DE {LOG_FILE.name}")
    print(f"{'='*60}")
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        print(f.read())

def clear_log():
    if LOG_FILE.exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
        print("\n[OK] diff_audit.log ha sido limpiado.")
    else:
        print("\n[INFO] diff_audit.log no existía.")

def interactive_menu():
    while True:
        print("\n" + "=" * 60)
        print("              BLUESLAB AUDIT RUNNER v1.0")
        print("=" * 60)
        print("  [1] Auditar Estadísticas e Información de Compis (Fase 1)")
        print("  [2] Auditar Descripciones y Textos Multi-idioma (Fase 2)")
        print("  [3] Auditar Potencias y Motor de Daño al 100% (Fase 3)")
        print("  [4] Ejecutar Todas las Fases Disponibles")
        print("  [5] Ver Registro de Discrepancias (diff_audit.log)")
        print("  [6] Limpiar Registro de Discrepancias")
        print("  [0] Salir")
        print("=" * 60)
        
        choice = input("Selecciona una opción [0-6]: ").strip()
        
        if choice == "1":
            run_phase_1()
        elif choice == "2":
            run_phase_2()
        elif choice == "3":
            run_phase_3()
        elif choice == "4":
            run_phase_1()
            run_phase_2()
            run_phase_3()
        elif choice == "5":
            view_log()
        elif choice == "6":
            clear_log()
        elif choice == "0":
            print("\nSaliendo de BluesLab Audit Runner. ¡Hasta pronto!")
            break
        else:
            print("\n[!] Opción no válida. Por favor introduce un número entre 0 y 6.")

def main():
    parser = argparse.ArgumentParser(description="BluesLab vs PoMaTools Fidelity Audit Runner")
    parser.add_argument("--batch", type=int, choices=[1, 2, 3, 4], help="Ejecutar fase en modo no interactivo (1=Stats, 2=Textos, 3=Daño, 4=Todas)")
    parser.add_argument("--view-log", action="store_true", help="Mostrar contenido del archivo de log")
    parser.add_argument("--clear-log", action="store_true", help="Limpiar el archivo de log")
    args = parser.parse_args()

    if args.clear_log:
        clear_log()
    elif args.view_log:
        view_log()
    elif args.batch == 1:
        run_phase_1()
    elif args.batch == 2:
        run_phase_2()
    elif args.batch == 3:
        run_phase_3()
    elif args.batch == 4:
        run_phase_1()
        run_phase_2()
        run_phase_3()
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
