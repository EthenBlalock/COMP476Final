
import socket

# Server configuration
HOST = "0.0.0.0"   # Listen on all network interfaces
PORT = 5000        # Port number for the game server

# Game constants
EMPTY = "."
PLAYER_SYMBOLS = ["X", "O"]


def send_line(conn, message):
    """
    Send one line of text to a client.
    A newline is added so the client can read messages line by line.
    """
    conn.sendall((message + "\n").encode("utf-8"))


def broadcast(players, message):
    """
    Send the same message to all connected players.
    """
    for player in players:
        send_line(player["conn"], message)


def board_to_message(board):
    """
    Convert the internal board list into a message string.
    Example: BOARD X,O,.,.,X,.,.,O,.
    """
    return "BOARD " + ",".join(board)


def check_winner(board, symbol):
    """
    Return True if the given symbol has any winning combination.
    """
    winning_positions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]

    for combo in winning_positions:
        if all(board[pos] == symbol for pos in combo):
            return True
    return False


def board_full(board):
    """
    Return True if there are no empty spaces left.
    """
    return EMPTY not in board


def send_turn_status(players, current_turn, board):
    """
    Send the current board to both players and tell them whose turn it is.
    """
    broadcast(players, board_to_message(board))

    for index, player in enumerate(players):
        if index == current_turn:
            send_line(player["conn"], "YOUR_TURN")
            send_line(player["conn"], "MESSAGE Enter a move from 0 to 8.")
        else:
            send_line(player["conn"], "OPPONENT_TURN")
            send_line(player["conn"], "MESSAGE Waiting for the other player.")


def close_all(players, server_socket):
    """
    Close all player connections and the server socket.
    """
    for player in players:
        try:
            player["file"].close()
        except Exception:
            pass
        try:
            player["conn"].close()
        except Exception:
            pass

    try:
        server_socket.close()
    except Exception:
        pass


def main():
    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow quick restart of the server after closing it
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the host/port and begin listening
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)

    print(f"[SERVER] Tic-Tac-Toe server is running on port {PORT}")
    print("[SERVER] Waiting for Player 1...")

    players = []

    try:
        # Accept exactly 2 players
        for i in range(2):
            conn, addr = server_socket.accept()
            file_obj = conn.makefile("r", encoding="utf-8", newline="\n")

            player = {
                "conn": conn,
                "file": file_obj,
                "addr": addr,
                "symbol": PLAYER_SYMBOLS[i]
            }
            players.append(player)

            print(f"[SERVER] Player {player['symbol']} connected from {addr}")
            send_line(conn, f"WELCOME {player['symbol']}")

            if i == 0:
                send_line(conn, "MESSAGE Waiting for Player O to join...")
                print("[SERVER] Waiting for Player 2...")

        # Both players are connected; start the game
        board = [EMPTY] * 9
        current_turn = 0  # 0 = X, 1 = O

        broadcast(players, "START")
        broadcast(players, "MESSAGE Both players connected. Game is starting.")
        send_turn_status(players, current_turn, board)

        # Main game loop
        while True:
            current_player = players[current_turn]
            other_player = players[1 - current_turn]
            symbol = current_player["symbol"]

            # Read the current player's message
            line = current_player["file"].readline()

            # If empty, that player disconnected
            if not line:
                print(f"[SERVER] Player {symbol} disconnected.")
                send_line(other_player["conn"], "MESSAGE Opponent disconnected. Game over.")
                break

            line = line.strip()
            print(f"[SERVER] Received from Player {symbol}: {line}")

            # Expecting a move in the format: MOVE 0
            if not line.startswith("MOVE "):
                send_line(current_player["conn"], "INVALID_MOVE Use: MOVE <0-8>")
                send_line(current_player["conn"], "YOUR_TURN")
                send_line(current_player["conn"], "MESSAGE Enter a move from 0 to 8.")
                continue

            move_text = line[5:].strip()

            # Validate that the move is a number
            if not move_text.isdigit():
                send_line(current_player["conn"], "INVALID_MOVE Move must be a number from 0 to 8.")
                send_line(current_player["conn"], "YOUR_TURN")
                send_line(current_player["conn"], "MESSAGE Enter a move from 0 to 8.")
                continue

            move = int(move_text)

            # Validate board range
            if move < 0 or move > 8:
                send_line(current_player["conn"], "INVALID_MOVE Position must be between 0 and 8.")
                send_line(current_player["conn"], "YOUR_TURN")
                send_line(current_player["conn"], "MESSAGE Enter a move from 0 to 8.")
                continue

            # Validate that the chosen space is empty
            if board[move] != EMPTY:
                send_line(current_player["conn"], "INVALID_MOVE That position is already taken.")
                send_line(current_player["conn"], "YOUR_TURN")
                send_line(current_player["conn"], "MESSAGE Enter a move from 0 to 8.")
                continue

            # Apply the move
            board[move] = symbol
            print(f"[SERVER] Player {symbol} placed on position {move}")

            # Tell current player the move was accepted
            send_line(current_player["conn"], "VALID_MOVE")

            # Check for a winner
            if check_winner(board, symbol):
                broadcast(players, board_to_message(board))
                send_line(current_player["conn"], "WIN")
                send_line(other_player["conn"], "LOSE")
                print(f"[SERVER] Player {symbol} wins.")
                break

            # Check for a draw
            if board_full(board):
                broadcast(players, board_to_message(board))
                broadcast(players, "DRAW")
                print("[SERVER] Game ended in a draw.")
                break

            # Switch turns and continue
            current_turn = 1 - current_turn
            send_turn_status(players, current_turn, board)

    except KeyboardInterrupt:
        print("\n[SERVER] Server stopped by user.")
    finally:
        close_all(players, server_socket)
        print("[SERVER] Server closed.")


if __name__ == "__main__":
    main()