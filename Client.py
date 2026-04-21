import socket
import sys

# Default client settings
DEFAULT_HOST = "10.198.73.9"
PORT = 5050
EMPTY = "."


def display_board(board):
    """
    Display the Tic-Tac-Toe board.
    Empty cells are shown using their index number so the player knows what to type.
    """
    display_cells = []

    for i, cell in enumerate(board):
        if cell == EMPTY:
            display_cells.append(str(i))
        else:
            display_cells.append(cell)

    print()
    print(f" {display_cells[0]} | {display_cells[1]} | {display_cells[2]}")
    print("---+---+---")
    print(f" {display_cells[3]} | {display_cells[4]} | {display_cells[5]}")
    print("---+---+---")
    print(f" {display_cells[6]} | {display_cells[7]} | {display_cells[8]}")
    print()


def get_server_host():
    """
    Get the server IP address.
    Priority:
    1. Command-line argument
    2. User input
    3. Default to 127.0.0.1
    """
    if len(sys.argv) > 1:
        return sys.argv[1]

    user_input = input(f"Enter server IP [{DEFAULT_HOST}]: ").strip()
    return user_input if user_input else DEFAULT_HOST


def main():
    host = get_server_host()

    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((host, PORT))
        file_obj = client_socket.makefile("r", encoding="utf-8", newline="\n")

        print(f"[CLIENT] Connected to server at {host}:{PORT}")

        player_symbol = None

        while True:
            line = file_obj.readline()

            # If the server closes the connection
            if not line:
                print("[CLIENT] Server disconnected.")
                break

            line = line.strip()

            if line.startswith("WELCOME "):
                player_symbol = line.split()[1]
                print(f"[CLIENT] You are Player {player_symbol}")

            elif line == "START":
                print("[CLIENT] Game has started.")

            elif line.startswith("MESSAGE "):
                print(line[8:])

            elif line.startswith("BOARD "):
                board_data = line[6:].split(",")
                display_board(board_data)

            elif line == "YOUR_TURN":
                while True:
                    move = input("Your move (0-8): ").strip()

                    # Basic client-side input check before sending
                    if move.isdigit() and 0 <= int(move) <= 8:
                        client_socket.sendall(f"MOVE {move}\n".encode("utf-8"))
                        break
                    else:
                        print("Please enter a valid number from 0 to 8.")

            elif line == "OPPONENT_TURN":
                print("Opponent's turn...")

            elif line == "VALID_MOVE":
                print("Move accepted.")

            elif line.startswith("INVALID_MOVE"):
                print(line)

            elif line == "WIN":
                print("You win!")
                break

            elif line == "LOSE":
                print("You lose.")
                break

            elif line == "DRAW":
                print("The game is a draw.")
                break

            else:
                print(f"[CLIENT] Unknown message from server: {line}")

    except ConnectionRefusedError:
        print("[CLIENT] Could not connect. Make sure the server is running.")
    except KeyboardInterrupt:
        print("\n[CLIENT] Client closed by user.")
    finally:
        try:
            client_socket.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()