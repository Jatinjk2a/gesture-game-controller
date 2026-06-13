"""Entry point — shows game selector then launches the controller."""
from launcher   import run_menu
from controller import run_controller


def main():
    print("=" * 44)
    print("   Gesture Game Controller  v2.0")
    print("=" * 44)

    game = run_menu()
    if game:
        print(f"\n>> Selected: {game['name']}  ({game['control_mode']} mode)")
        run_controller(game)

    print("\nGoodbye!")


if __name__ == "__main__":
    main()
