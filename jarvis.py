import sys
from jarvis.main import main


def _print_usage() -> None:
    print("Usage: python jarvis.py [command]")
    print()
    print("Commands:")
    print("  doctor   Run local Jarvis health and maintenance diagnostics")
    print()
    print("Examples:")
    print("  python jarvis.py")
    print("  python jarvis.py doctor")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'doctor':
            from jarvis.doctor import main as doctor_main
            raise SystemExit(doctor_main(sys.argv[2:]))
        _print_usage()
    else:
        main()
