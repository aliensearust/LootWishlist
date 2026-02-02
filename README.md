# LootWishlist

A World of Warcraft addon that tracks gear wishlists and alerts you when desired items drop.

## Features

- **Multiple Wishlists** - Create named lists (main spec BiS, offspec, etc.)
- **Upgrade Track Filtering** - Filter by gear track (Explorer → Myth)
- **Visual Alerts** - Wishlist items glow in loot window
- **Audio Alerts** - Configurable sound notifications
- **Collected Tracking** - Auto-marks collected items with progress display
- **In-Game Item Browser** - Browse loot filtered by expansion, instance, difficulty, class, and slot
- **Minimap Icon** - Quick access button with left-click toggle

## Installation

1. Download the latest release
2. Extract to `World of Warcraft/_retail_/Interface/AddOns/`
3. Restart WoW or `/reload`

## Usage

### Slash Commands

| Command | Description |
|---------|-------------|
| `/lw` or `/lootwishlist` | Toggle main window |
| `/lw config` or `/lw settings` | Open settings panel |
| `/lw test` | Test alert system |
| `/lw reset` | Reset all data (with confirmation) |
| `/lw help` | Show all commands |

### Quick Start

1. Type `/lw` to open the main window
2. Click "New Wishlist" to create a wishlist
3. Use the Item Browser to find and add gear
4. Play normally - you'll get alerts when wishlist items drop

## Interface

**Wishlist Manager** (left panel)
- Select/switch active wishlist via dropdown
- Create, rename, delete wishlists
- View items grouped by instance (collapsible)
- See progress (e.g., "5/12 collected")
- Right-click items for context menu (mark collected, change track, remove)

**Item Browser** (right panel, toggle with "Browse")
- Filter by expansion, instance type (raid/dungeon), difficulty
- Filter by class and armor slot
- Search items by name
- Current season filter for M+ dungeons
- One-click add items to wishlist
- Normal or Large size modes

## Settings

- Enable/disable chat alerts, sound alerts, glow effects
- Choose alert sound (Raid Warning, Ready Check, etc.)
- Hide minimap icon option
- Browser size (Normal/Large)
- Default upgrade track for browsing

## License

MIT
