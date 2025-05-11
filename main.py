import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
)
from PyQt6.QtCore import Qt, QTimer, QMimeData

from PyQt6.QtGui import QPixmap, QDrag


CARD_WIDTH = 72
CARD_HEIGHT = 96


def load_card_pixmap(rank, suit):
    return QPixmap(f"cards/card_{rank}{suit}.png").scaled(CARD_WIDTH, CARD_HEIGHT)


def load_card_back():
    return QPixmap("cards/card_back.png").scaled(CARD_WIDTH, CARD_HEIGHT)


class CardLabel(QLabel):
    def __init__(self, card, face_up=True):
        super().__init__()
        self.card = card
        self.face_up = face_up
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.update_pixmap()
        self.setVisible(True)

    def update_pixmap(self):
        if self.face_up:
            self.setPixmap(load_card_pixmap(*self.card))
        else:
            self.setPixmap(load_card_back())

    def mouseMoveEvent(self, event):
        if not self.face_up or event.buttons() != Qt.MouseButton.LeftButton:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"{self.card[0]},{self.card[1]}")
        drag.setMimeData(mime)
        drag.setPixmap(self.pixmap())
        drag.setHotSpot(event.position().toPoint())

        self.hide()
        result = drag.exec(Qt.DropAction.MoveAction)
        if result == Qt.DropAction.IgnoreAction:
            self.show()


class PlayPile(QLabel):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.card = None
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        rank, suit = text.split(",")
        rank = int(rank)
        dropped_card = (rank, suit)

        # Current play pile card
        pile_rank = self.card[0]

        # Check if move is valid
        if self.window().is_valid_move(rank, pile_rank):

            self.card = dropped_card
            self.setPixmap(load_card_pixmap(rank, suit))
            event.acceptProposedAction()
        else:
            print("Invalid move: Can't play", rank, "on", pile_rank)
            event.ignore()
        self.window().check_for_win_or_tie()

    def valid_move(self, rank):
        if self.card is None:
            return True
        diff = abs(rank - self.card[0])
        return diff == 1 or diff == 12  # wraparound logic


class SpeedGame(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Speed Card Game")
        self.game_over = False
        self.setMinimumSize(440, 330)

        self.deck = self.build_deck()

        # Screens
        self.stack_layout = QStackedLayout()
        self.setLayout(self.stack_layout)

        self.start_screen = QWidget()
        self.instructions_screen = QWidget()
        self.game_screen = QWidget()

        self.stack_layout.addWidget(self.start_screen)
        self.stack_layout.addWidget(self.instructions_screen)
        self.stack_layout.addWidget(self.game_screen)

        self.setup_start_screen()

        self.win_screen = QWidget()
        self.stack_layout.addWidget(self.win_screen)

    def build_deck(self):
        from random import shuffle

        suits = ["H", "D", "C", "S"]
        deck = [(rank, suit) for suit in suits for rank in range(1, 14)]
        shuffle(deck)
        return deck

    def setup_start_screen(self):
        layout = QVBoxLayout()

        title = QLabel("Speed")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold;")
        layout.addWidget(title)

        button_row = QHBoxLayout()
        easy_btn = QPushButton("Easy")
        medium_btn = QPushButton("Medium")
        hard_btn = QPushButton("Hard")

        easy_btn.clicked.connect(lambda: self.start_game(4000))
        medium_btn.clicked.connect(lambda: self.start_game(2000))
        hard_btn.clicked.connect(lambda: self.start_game(1000))

        for btn in [easy_btn, medium_btn, hard_btn]:
            button_row.addWidget(btn)

        layout.addLayout(button_row)

        how_to_btn = QPushButton("How to Play")
        how_to_btn.clicked.connect(self.show_instructions)
        layout.addWidget(how_to_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.start_screen.setLayout(layout)
        self.stack_layout.setCurrentWidget(self.start_screen)

    def show_instructions(self):
        layout = QVBoxLayout()

        title = QLabel("How to Play")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        instructions = QLabel(
            "Objective:\n"
            "Be the first to play all your cards.\n\n"
            "How to Play:\n"
            "- You and the AI each start with 5 cards.\n"
            "- Cards can be played on the center piles if they are one higher or lower in rank.\n"
            "- You can draw a new card from your draw pile when needed.\n"
            "- Use drag-and-drop to move your cards.\n\n"
            "Winning:\n"
            "Empty your hand and draw pile before the AI does!"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.setup_start_screen)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.instructions_screen.setLayout(layout)
        self.stack_layout.setCurrentWidget(self.instructions_screen)

    def start_game(self, interval):
        # Stop and clean previous timer
        if hasattr(self, "ai_timer"):
            self.ai_timer.stop()
            self.ai_timer.deleteLater()

        self.game_over = False

        # --- Create a new game_screen widget and replace it ---
        self.stack_layout.removeWidget(self.game_screen)
        self.game_screen.deleteLater()
        self.game_screen = QWidget()
        self.stack_layout.insertWidget(
            2, self.game_screen
        )  # Ensure index matches usage
        self.stack_layout.setCurrentWidget(self.game_screen)

        self.deck = self.build_deck()
        full_deck = self.deck[:]

        # Split the deck
        self.player_deck = full_deck[:15]
        self.ai_deck = full_deck[15:30]
        center_cards = full_deck[30:32]
        self.remaining_deck = full_deck[32:]

        self.center_left_card = center_cards[0]
        self.center_right_card = center_cards[1]

        self.init_game_ui()

        # Restart AI timer
        self.ai_timer = QTimer()
        self.ai_timer.timeout.connect(self.ai_play)
        self.ai_timer.start(interval)

    def is_valid_move(self, card_rank, pile_rank):
        return (card_rank - pile_rank) % 13 == 1 or (pile_rank - card_rank) % 13 == 1

    def try_reset_play_piles(self):
        def is_valid_move(card, pile_value):
            value = card[0]
            return (value - pile_value) % 13 == 1 or (pile_value - value) % 13 == 1

        left_value = self.play_pile_left.card[0]
        right_value = self.play_pile_right.card[0]

        player_can_play = any(
            card.isVisible()
            and (
                is_valid_move(card.card, left_value)
                or is_valid_move(card.card, right_value)
            )
            for card in self.player_hand
        )

        ai_can_play = any(
            card.isVisible()
            and (
                is_valid_move(card.card, left_value)
                or is_valid_move(card.card, right_value)
            )
            for card in self.ai_hand
        )

        if not player_can_play and not ai_can_play and len(self.deck) >= 2:
            left_card = self.deck.pop()
            right_card = self.deck.pop()
            self.play_pile_left.card = left_card
            self.play_pile_left.setPixmap(load_card_pixmap(*left_card))
            self.play_pile_right.card = right_card
            self.play_pile_right.setPixmap(load_card_pixmap(*right_card))

    def init_game_ui(self):
        # Clear existing layout if any
        old_layout = self.game_screen.layout()
        if old_layout is not None:
            self.clear_layout(old_layout)

        layout = QVBoxLayout()

        # === AI Row ===
        ai_row = QHBoxLayout()
        self.ai_draw_pile = QLabel()
        self.ai_draw_pile.setPixmap(load_card_back())
        self.ai_draw_pile.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.ai_draw_pile.mousePressEvent = lambda event: self.draw_ai_card()
        self.ai_draw_pile.show()
        ai_row.addWidget(self.ai_draw_pile)

        self.ai_hand = []
        for _ in range(5):
            if self.ai_deck:
                card = self.ai_deck.pop()
                label = CardLabel(card, face_up=False)
                self.ai_hand.append(label)
                ai_row.addWidget(label)

        layout.addLayout(ai_row)

        # === Center Row ===
        center_row = QHBoxLayout()
        self.play_pile_left = PlayPile()
        self.play_pile_right = PlayPile()

        if len(self.deck) >= 2:
            self.center_left_card = self.deck.pop()
            self.center_right_card = self.deck.pop()
        else:
            self.center_left_card = ("Joker", "Black")
            self.center_right_card = ("Joker", "Red")

        self.play_pile_left.card = self.center_left_card
        self.play_pile_left.setPixmap(load_card_pixmap(*self.center_left_card))

        self.play_pile_right.card = self.center_right_card
        self.play_pile_right.setPixmap(load_card_pixmap(*self.center_right_card))

        self.stuck_left = QLabel()
        self.stuck_right = QLabel()
        self.stuck_left.setPixmap(load_card_back())
        self.stuck_right.setPixmap(load_card_back())
        self.stuck_left.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.stuck_right.setFixedSize(CARD_WIDTH, CARD_HEIGHT)

        center_row.addStretch()
        center_row.addWidget(self.stuck_left)
        center_row.addWidget(self.play_pile_left)
        center_row.addWidget(self.play_pile_right)
        center_row.addWidget(self.stuck_right)
        center_row.addStretch()

        layout.addLayout(center_row)

        # Can't Play Button
        cant_play_btn = QPushButton("Can't Play")
        cant_play_btn.clicked.connect(self.try_reset_play_piles)
        layout.addWidget(cant_play_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # === Player Row ===
        player_row = QHBoxLayout()
        self.player_draw_pile = QLabel()
        self.player_draw_pile.setPixmap(load_card_back())
        self.player_draw_pile.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.player_draw_pile.mousePressEvent = lambda event: self.draw_player_card()
        self.player_draw_pile.show()
        player_row.addWidget(self.player_draw_pile)

        self.player_hand = []
        for _ in range(5):
            if self.deck:
                card = self.deck.pop()
                label = CardLabel(card)
                self.player_hand.append(label)
                player_row.addWidget(label)

        layout.addLayout(player_row)

        self.game_screen.setLayout(layout)

    def draw_player_card(self):
        if not self.player_deck:
            self.player_draw_pile.hide()
            return

        for card in self.player_hand:
            if not card.isVisible():
                new_card = self.player_deck.pop()
                card.card = new_card
                card.face_up = True
                card.update_pixmap()
                card.show()
                break

        if not self.player_deck:
            self.player_draw_pile.hide()

    def draw_ai_card(self):
        if not self.ai_deck:
            self.ai_draw_pile.hide()
            return

        for card in self.ai_hand:
            if not card.isVisible():
                new_card = self.ai_deck.pop()
                card.card = new_card
                card.face_up = False
                card.update_pixmap()
                card.show()
                break

        if not self.ai_deck:
            self.ai_draw_pile.hide()

    def ai_play(self):
        if self.game_over:
            return
        for card in self.ai_hand:
            if not card or not card.isVisible():
                continue
            for pile in [self.play_pile_left, self.play_pile_right]:
                if pile.valid_move(card.card[0]):
                    card.face_up = True
                    card.update_pixmap()
                    pile.card = card.card
                    pile.setPixmap(load_card_pixmap(*card.card))
                    card.hide()
                    QTimer.singleShot(200, self.draw_ai_card)
                    return

        if all(card and not card.isVisible() for card in self.ai_hand):
            self.draw_ai_card()

        QTimer.singleShot(300, self.check_for_win_or_tie)

    def check_for_win_or_tie(self):
        player_has_cards = (
            any(card.isVisible() for card in self.player_hand) or self.player_deck
        )
        ai_has_cards = any(card.isVisible() for card in self.ai_hand) or bool(
            self.ai_deck
        )

        if not player_has_cards and ai_has_cards:
            print("Player wins!")
            QTimer.singleShot(100, lambda: self.show_win_screen("Player"))
            return
        elif not ai_has_cards and player_has_cards:
            print("AI wins!")
            QTimer.singleShot(100, lambda: self.show_win_screen("Opponent"))
            return

        # Check for stalemate (no valid moves)
        can_move = False
        for card in self.player_hand + self.ai_hand:
            if card.isVisible():
                for pile in [self.play_pile_left, self.play_pile_right]:
                    if pile.valid_move(card.card[0]):
                        can_move = True
                        break
            if can_move:
                break

        if not can_move and not self.deck:
            self.show_tie_screen()

    def show_tie_screen(self):
        self.game_over = True
        if hasattr(self, "ai_timer"):
            self.ai_timer.stop()

        self.clear_layout(self.game_screen.layout())

        QWidget().setLayout(self.game_screen.layout())

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tie_label = QLabel("It's a Tie!")
        tie_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tie_label.setStyleSheet("font-size: 32px; color: red; font-weight: bold;")

        menu_button = QPushButton("Main Menu")
        menu_button.setFixedSize(200, 50)
        menu_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4444aa;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #6666cc;
            }
            """
        )
        menu_button.clicked.connect(self.setup_start_screen)

        layout.addWidget(tie_label)
        layout.addSpacing(30)
        layout.addWidget(menu_button)

        self.game_screen.setLayout(layout)

    def show_win_screen(self, winner):
        self.game_over = True
        if hasattr(self, "ai_timer"):
            self.ai_timer.stop()

        self.clear_layout(self.game_screen.layout())

        # Remove old layout and force refresh
        QWidget().setLayout(self.game_screen.layout())  # Detach layout safely

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        win_label = QLabel(f"{winner} Wins!")
        win_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        win_label.setStyleSheet("font-size: 32px; color: green; font-weight: bold;")

        menu_button = QPushButton("Main Menu")
        menu_button.setFixedSize(200, 50)
        menu_button.setStyleSheet(
            """
            QPushButton {
                background-color: #000000;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #808080;
            }
        """
        )
        menu_button.clicked.connect(self.setup_start_screen)

        layout.addWidget(win_label)
        layout.addSpacing(30)
        layout.addWidget(menu_button)

        self.game_screen.setLayout(layout)
        self.stack_layout.setCurrentWidget(self.game_screen)

    def clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            elif item.layout() is not None:
                self.clear_layout(item.layout())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeedGame()
    window.show()
    sys.exit(app.exec())
