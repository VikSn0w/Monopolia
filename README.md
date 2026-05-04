# Monopolia

A complete Monopoly game engine written in Python with a Pygame renderer and full support for the official ruleset — including trading.

---

## Features

- Full 40-space board with all Chance and Community Chest cards
- Property purchase, auction, rent collection, and monopoly doubling
- Houses and hotels with the even-build rule enforced
- Mortgage and unmortgage with the official 10% interest penalty
- Complete trading system — properties (including mortgaged), cash, and Get Out of Jail Free cards can all be traded in a single offer
- Jail logic — 3-turn limit, double-roll escape, GOOJF usage
- Railroad and utility rent scaling
- Bankruptcy with correct asset transfer to creditor or bank
- American (USA), British (UK) and Italian localisation 
---

## Installation
Using Python 3.12:
```bash
pip install pygame
```

```bash
python main.py
```

---

## Project Structure

```
├── logic/
│   ├── /assets/
│   │   ├── /fonts/
│   │   │   ├── Kabel-Bold.otf    
│   │   │   ├── Kabel-Light.otf    
│   │   │   └── Kabel-Regular.otf    
│   ├── GameManager.py        
│   ├── Player.py             
│   ├── Property.py           
│   ├── Deck.py               
│   ├── usefulness.py               
│   ├── Bot.py               
│   └── Renderer.py           
├── loc/??-??/
│   ├── properties.json
│   ├── board.json
│   ├── chance.json
│   └── community-chest.json
└── main.py
```

---

## Reinforcement Learning
This project was born from my desire to train an AI on the game of Monopoly, with the aim of beating the best strategy that has now been used for years (Orange Strat).

An RL agent trained via curriculum learning (MaskablePPO, four difficulty stages) is in active development and will be released as a separate module once the Stage 2 model reaches 100% win rate.

For the full training methodology, results, and failure mode analysis from the v1 run, see the research paper:

**[→ Monopolia: Training a Curriculum RL Agent on a Complete Monopoly Engine](./monopolia_research_paper.html)**
