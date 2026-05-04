import random

class Card:
    def __init__(self, data):
        self.id = data.get("id")
        self.description = data.get("description")
        self.is_held = False  

class Deck:
    def __init__(self, name: str, cards_data: list[dict]):
        self.name = name
        self.all_cards = [Card(data) for data in cards_data]
        self.active_cards = self.all_cards.copy()
        random.shuffle(self.active_cards)

    def draw(self) -> Card:
        if not self.active_cards:
            print(f"The {self.name} deck is empty! Reshuffling...")
            self.active_cards = [card for card in self.all_cards if not card.is_held]
            random.shuffle(self.active_cards)

        return self.active_cards.pop(0)