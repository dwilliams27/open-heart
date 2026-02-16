# PhoneDeck — Known Bugs

## Deck Back Sprite Issues

### Main menu deck selection preview shows default red back
The Smartphone Deck preview card in the main menu deck selection screen doesn't show the custom `b_smartphone` sprite. The `Card:set_sprites` hook patches both `self.children.center` and `self.children.back` for Back-type cards, but the deck selection screen may create preview cards through a different code path that doesn't trigger the hook, or `self.children.back` may not exist at that point.

### Card back override leaks to other decks in new-game menu
When starting a new game from within a Smartphone Deck run, the deck selection menu shows the smartphone back on all decks instead of their own backs. The `set_sprites` hook overrides `self.children.back` for non-Back/non-Joker cards when `G.GAME.selected_back` is the smartphone deck, but this check is too broad and catches deck preview cards that don't have a Back-type center.

### Notes
- In-game card backs during a Smartphone Deck run work correctly
- Both issues are cosmetic and don't affect gameplay
- May require hooking into `Card:draw` or the deck selection UI code directly
- Study how vanilla Balatro renders deck previews vs in-game card backs
