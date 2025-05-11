# 🃏 Speed Card Game (PyQt6)

A fast-paced Speed card game built with Python and PyQt6, where quick thinking and reflexes are key! Challenge an AI opponent with drag-and-drop gameplay, dynamic difficulty levels, and sleek card visuals.

## 🎮 Game Features

- **🧠 AI Opponent**: Test your speed against an AI with adjustable difficulty.

- **🖱️ Drag-and-Drop Mechanics**: Play cards by dragging them to the center piles.

- **🔁 Real-Time Updates**: The game adapts instantly to moves and win/tie conditions.

- **💡 Can't Play Mechanic**: Refresh center piles if no valid moves are available.

- **🏆 Victory & Tie Screens**: Get clear feedback with styled end-game screens.

- **🎨 Smooth UI**: Clean design with card images and responsive layout.

- **📋 Instructions Included**: Learn how to play directly from the app.

# 🚀 Getting Started

- **1. Clone the Repository**

```bash
git clone https://github.com/codydehaan/Cody-deHaan-Capstone-2.git

cd speed-card-game
```

- **2. Install Requirements**

Make sure Python 3.7+ is installed, then install PyQt6:

```bash
pip install PyQt6
```

- **3. Run the Game**

```bash
python speed_game.py
```

## 🧠 How to Play

**Objective**: Be the first to play all your cards.

**Rules**

Play a card if it’s one rank above or below a center pile card.

Wrap-around is allowed (King ↔ Ace).

Use the draw pile when your hand is empty.

Press Can't Play to reset center cards if stuck.

**Win:** Empty your hand and draw pile before the AI!

# 🛠️ Customization

## **Want to make it your own?**

🃏 Add new card styles in the cards/ folder.

🎵 Add sound effects for draws and wins.

🤖 Tweak AI difficulty or behavior in ai_play().

## 📌 Dependencies

Python 3.7+

PyQt6

## ❤️ Acknowledgments

Card images from (https://kenney.itch.io/)

Thanks to the PyQt6 community for amazing UI tools.
