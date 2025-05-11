"""Main module for PyQt6 Speed Card Game."""

# pylint: disable=invalid-name
import sys  # Import the sys module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,  # pylint: disable=no-name-in-module
    QWidget,  # pylint: disable=no-name-in-module
    QLabel,  # pylint: disable=no-name-in-module
    QPushButton,  # pylint: disable=no-name-in-module
    QVBoxLayout,  # pylint: disable=no-name-in-module
    QHBoxLayout,  # pylint: disable=no-name-in-module
    QStackedLayout,  # pylint: disable=no-name-in-module
)
from PyQt6.QtCore import Qt, QTimer, QMimeData  # pylint: disable=no-name-in-module

from PyQt6.QtGui import QPixmap, QDrag  # pylint: disable=no-name-in-module


CARD_WIDTH = 72
CARD_HEIGHT = 96


def load_card_pixmap(rank, suit):
    """
    Load a card pixmap from a file based on the given rank and suit.

    Args:
        rank (int): The rank of the card (1-13)
        suit (str): The suit of the card (H, D, C, S)

    Returns:
        QPixmap: The loaded pixmap
    """
    return QPixmap(f"cards/card_{rank}{suit}.png").scaled(CARD_WIDTH, CARD_HEIGHT)


def load_card_back():
    """
    Load a card back pixmap from a file.

    Returns:
        QPixmap: The loaded pixmap
    """
    return QPixmap("cards/card_back.png").scaled(CARD_WIDTH, CARD_HEIGHT)


class CardLabel(QLabel):
    """
    Represents a card label in the game.
    """

    def __init__(self, card, face_up=True):
        """
        Initialize a CardLabel instance.

        Args:
            card (tuple): A tuple representing the card, typically containing rank and suit.
            face_up (bool, optional): Determines whether the card is face up. Defaults to True.
        """

        super().__init__()
        self.card = card
        self.face_up = face_up
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.update_pixmap()
        self.setVisible(True)

    def update_pixmap(self):
        """
        Update the pixmap of the card label based on its face-up status.

        If the card is face up, set the pixmap to the card's image.
        Otherwise, set the pixmap to the card back image.
        """

        if self.face_up:
            self.setPixmap(load_card_pixmap(*self.card))
        else:
            self.setPixmap(load_card_back())

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events to initiate a drag action for the card.

        When the card is face up and the left mouse button is pressed, this method
        initiates a drag-and-drop operation. The card's rank and suit are included
        in the drag data as a comma-separated string. The card is temporarily hidden
        during the drag action, and becomes visible again if the drag operation is
        ignored.

        Args:
            event (QMouseEvent): The event object containing details of the mouse move.
        """

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
    """
    Represents a play pile in the game.
    """

    def __init__(self):
        """
        Initialize a PlayPile instance.

        Sets up the play pile to accept drag-and-drop events, initializes the card
        to None, and sets the fixed size of the play pile to the predefined card dimensions.
        """

        super().__init__()
        self.setAcceptDrops(True)
        self.card = None
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)

    def dragEnterEvent(self, event):
        """
        Handles drag enter events by accepting the proposed action if the event
        contains a text mime data (i.e. a card).

        Args:
            event (QDragEnterEvent): The drag enter event object.
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
        Handle the drop event for the play pile.

        This method is triggered when a card is dropped onto the play pile. It extracts
        the card information from the event, checks if the move is valid, and updates
        the play pile accordingly. If the move is valid, the play pile's card is updated
        and the new card image is displayed. If not, the move is ignored. After processing,
        it checks for win or tie conditions in the game.

        Args:
            event (QDropEvent): The drop event containing the card data.
        """

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
        """
        Determine if a card of the given rank can be played on this pile.

        The move is valid if the pile is empty, or the rank difference between the
        new card and the current top card of the pile is 1 or 12 (to handle wraparound).

        Args:
            rank (int): The rank of the card to be played.

        Returns:
            bool: True if the move is valid, False otherwise.
        """

        if self.card is None:
            return True
        diff = abs(rank - self.card[0])
        return diff == 1 or diff == 12


# wraparound logic


class SpeedGame(QWidget):  # pylint: disable=too-many-instance-attributes
    """
    Represents the main game window.
    """

    def __init__(self):
        """
        Initialize a SpeedGame instance.

        Sets the window title to "Speed Card Game", sets game_over to False, and
        sets the minimum window size to 440x330.

        Builds the initial deck of cards and sets up the QStackedLayout to hold
        the different screens of the game.

        Calls setup_start_screen() to set up the start screen and sets the
        start screen as the initial screen.

        Adds a win screen to the layout, but does not set it up yet.
        """
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
        """
        Build and shuffle a standard deck of playing cards.

        This method constructs a deck of 52 cards, with each card represented
        as a tuple of rank and suit. The suits used are Hearts (H), Diamonds (D),
        Clubs (C), and Spades (S), and the ranks range from 1 to 13.

        Returns:
            list: A shuffled list of tuples, each representing a card in the deck.
        """

        from random import shuffle

        suits = ["H", "D", "C", "S"]
        deck = [(rank, suit) for suit in suits for rank in range(1, 14)]
        shuffle(deck)
        return deck

    def setup_start_screen(self):
        """
        Set up the start screen of the game.

        Creates a QVBoxLayout containing a centered title "Speed" with a large font,
        a row of three buttons labeled "Easy", "Medium", and "Hard" that, when clicked,
        start the game with the corresponding difficulty level (slower to faster), and
        a button labeled "How to Play" that shows the instructions when clicked.

        The layout is then set on the start screen and the start screen is set as the
        current widget of the stacked layout.
        """
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
        """
        Display the game instructions screen.

        This method sets up and displays a screen with detailed instructions on how to
        play the game. It includes a title, a series of instructional steps, and a back
        button to return to the start screen. The layout is designed using a vertical box
        layout with centered alignment for the title and instructions, and a styled back
        button to navigate back to the main menu.
        """

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
        """
        Start a new game with a given interval between AI moves.

        This method stops any existing AI timer, cleans up any existing game
        screen, and initializes a new game by splitting a fresh deck into
        player, AI, and remaining cards. It then sets up the game UI and starts
        the AI timer with the given interval.

        Args:
            interval (int): The interval in milliseconds between AI moves.
        """
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
        """
        Check if a card move is valid.

        Args:
            card_rank (int): Rank of the card to be moved.
            pile_rank (int): Rank of the card on top of the pile to move to.

        Returns:
            bool: True if the move is valid, False otherwise.
        """

        return (card_rank - pile_rank) % 13 == 1 or (pile_rank - card_rank) % 13 == 1

    def try_reset_play_piles(self):
        """
        Try to reset the play piles if no valid moves are possible.

        This method checks if both the player and AI have no valid moves left
        and if there are at least two cards left in the deck. If so, it pops two
        cards from the deck and resets the play piles to these cards. This is
        done by setting the card attribute of the play piles and updating the
        corresponding pixmaps.

        Returns:
            None
        """

        def is_valid_move(card, pile_value):
            """
            Determine if a card can be played on a pile based on their ranks.

            The move is valid if the rank difference between the card and the pile's
            top card is 1, considering wraparound (i.e., King to Ace or Ace to King).

            Args:
                card (tuple): A tuple representing the card, where the first element is the rank.
                pile_value (int): The rank of the card currently on top of the pile.

            Returns:
                bool: True if the move is valid, False otherwise.
            """

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
        """
        Initialize the game UI, clearing any existing layout and setting up the
        AI's draw pile, hand, the center play piles, and the player's draw pile
        and hand.

        This method is called when a new game is started, and it sets up the
        initial layout of the game screen. The AI's draw pile is set up to be
        clickable to draw cards, and the player's draw pile is set up similarly.
        The center play piles are set up to display the initial cards, and the
        player's hand is set up to display the initial cards. The "Can't Play"
        button is also set up to handle cases where the player or AI cannot
        play any cards.

        Returns:
            None
        """
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
        """
        Draw a card from the player's deck and add it to the player's hand.

        If the player's deck is empty, hide the draw pile.

        This method is called when the player clicks on the draw pile. It
        draws a card from the player's deck and adds it to the player's hand
        if there is an available slot. If the player's deck is empty, it
        hides the draw pile.

        Returns:
            None
        """
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
        """
        Draw a card from the AI's deck and add it to the AI's hand.

        If the AI's deck is empty, hide the draw pile.

        This method is called when the AI needs to draw a card. It draws a card
        from the AI's deck and adds it to the AI's hand if there is an available
        slot. If the AI's deck is empty, it hides the draw pile.

        Returns:
            None
        """
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
        """
        Handle AI's turn.

        This method is called when the AI needs to make a move. It checks if the AI
        has any cards in their hand that can be played on either of the two center
        piles. If such a card exists, it is played and the AI draws a new card from
        their deck. If the AI has no playable cards, it draws a card from their
        deck. If the AI has no cards left in their deck, the game checks for win or
        tie conditions.

        Returns:
            None
        """
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
        """
        Check for win or tie conditions in the game.

        This method determines if the player or AI has won the game by checking
        their hands and decks. If either the player or AI has no visible cards
        left in their hand and no cards left in their deck, the game ends with
        that player as the winner. If a stalemate occurs where no valid moves
        are possible for both players, and the deck is empty, a tie screen is
        shown.

        Returns:
            None
        """

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
        if not ai_has_cards and player_has_cards:
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
        """
        Show the tie screen after the game has ended in a tie.

        This method clears the current game layout, sets up a new layout with a tie
        label and a main menu button, and sets the new layout as the current layout
        of the game screen.

        Returns:
            None
        """
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
        """
        Show the win screen after the game has ended with a winner.

        This method clears the current game layout, sets up a new layout with a win
        label and a main menu button, and sets the new layout as the current layout
        of the game screen.

        Args:
            winner (str): The name of the player that won the game.
        """
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
        """
        Recursively clears the given layout and its child widgets.

        This method removes all widgets and sub-layouts from the provided
        layout, setting their parent to None to avoid memory leaks. It
        handles nested layouts by recursively clearing them.

        Args:
            layout (QLayout): The layout to be cleared. If None, the method
                            returns immediately.
        """
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
