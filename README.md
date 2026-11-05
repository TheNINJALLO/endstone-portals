<!-- endstone-professional-header:start -->
<p align="center">
  <img src="docs/assets/banner.svg" width="100%" alt="Endstone Portals &mdash; Entity and block portal system with particle effects, local teleportation, and cross-server transfers">
</p>

<p align="center">
  <a href="https://github.com/TheNINJALLO/endstone-portals/actions/workflows/wheel-release.yml"><img alt="Build" src="https://img.shields.io/github/actions/workflow/status/TheNINJALLO/endstone-portals/wheel-release.yml?branch=main&amp;style=for-the-badge&amp;logo=githubactions&amp;logoColor=white&amp;label=Build"></a>
  <a href="https://github.com/TheNINJALLO/endstone-portals/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/TheNINJALLO/endstone-portals?display_name=tag&amp;style=for-the-badge&amp;label=Release"></a>
</p>

<p align="center">
  <img alt="Endstone 0.11.15" src="https://img.shields.io/badge/Endstone-0.11.15-52b7a8?style=flat-square">
  <img alt="API 0.11" src="https://img.shields.io/badge/API-0.11-63b8ff?style=flat-square">
  <img alt="BDS 1.26.60.6" src="https://img.shields.io/badge/BDS-1.26.60.6-8b7dff?style=flat-square">
  <img alt="Python >=3.10" src="https://img.shields.io/badge/Python-%3E=3.10-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white">
</p>

<p align="center">
  <strong>Entity and block portal system with particle effects, local teleportation, and cross-server transfers.</strong>
</p>

<p align="center">
  <a href="#what-it-does">What it does</a> &bull;
  <a href="#how-to-use">How to use</a> &bull;
  <a href="#commands-and-permissions">Commands</a> &bull;
  <a href="#install">Install</a> &bull;
  <a href="https://github.com/TheNINJALLO/endstone-portals/releases">Releases</a>
</p>

## Overview

Portals **1.1.10** creates entity and block-frame portals for local teleports or cross-server travel, with particles, optional inner fill blocks and in-game editing.

For block-portal server transfers, the player must be moved to verified safe ground outside the full frame and nearby portals **before** transfer. The transfer waits 60 ticks (about three seconds), rechecks the player's position and cancels if they have re-entered a portal. Arrivals must exit their portal area before another activation; a cooldown alone cannot bounce them back.

## What it does

- Create entity portals activated by interact, hit or both, optionally with confirmation.
- Detect vertical and horizontal rectangular block frames and add particles or inner fill.
- Teleport to coordinates/dimensions or transfer to a server address and port.
- Move players out of block portals during login and invalidate pending transfers on disconnect.
- Save definitions in `portals.json` and protect frame blocks from non-operators.

## How to use

1. Install the wheel, start the server, and join as an operator.
2. Run `/portal` and select **Create Entity Portal** or **Create Block Portal**.
3. For a block portal, build the complete rectangular border first, leave its opening empty, and stand close enough for the frame to fit within the eight-block scan range.
4. Select the border, particles/optional fill and destination. Keep loaded, solid, non-hazardous ground outside the entire frame for transfer exits.
5. Use **Manage Portals** to inspect, edit or delete definitions. Test with an ordinary player, including a return trip and a login at the destination.

The [full how-to](HOW-TO-USE.md) covers every form field, inner fill, editing, loop protection, troubleshooting and upgrade checks. Use **None (Particles Only)** for the first test of a walk-through portal; solid inner fill can obstruct entry.

## Commands and permissions

Management is for in-game operators. The command permission is `portals.admin`, granted to operators by default. Console commands are not supported. Ordinary players can use configured portals.

| Command | Purpose |
|---|---|
| `/portal` | Open the Portal Manager |
| `/portal list` | List definitions and destinations |
| `/portal reload` | Reload saved definitions from disk |
| `/portal delete <name>` | Delete a definition by name |

Prefer the management GUI for filled portals: its delete action also clears matching inner-fill blocks. The chat delete command removes the saved definition; inspect any remaining fill blocks yourself. Removing a portal definition leaves its physical border in place.

## Compatibility

| Component | Requirement or target |
|---|---|
| Plugin | `1.1.10` |
| Endstone API | `0.11` |
| Package dependency | `endstone>=0.11.9,<0.12` |
| Python package minimum | `>=3.10` |
| Intended 26.60 server setup | Endstone `0.11.15`, BDS `1.26.60.6`, Python `3.11+` |

The **18 portal safety regression tests passed in Linux CI**. These use a simulated server/scheduler; live Endstone/BDS transfers still need the [in-game checks](HOW-TO-USE.md#upgrade-and-in-game-checks). The intended 26.60 setup is not a claim that every accepted dependency version or live server build has been qualified.

## Install

Download [Portals v1.1.10](https://github.com/TheNINJALLO/endstone-portals/releases/tag/v1.1.10):

```bash
gh release download v1.1.10 --repo TheNINJALLO/endstone-portals --pattern '*.whl'
```

Stop the server, back up the world and the Portals data folder, replace the previous Portals wheel in `plugins/`, and restart. Do not keep multiple versions installed. Keep the existing `portals.json`; no definition reset is required. Version 1.1.10 retains the loop fix from 1.1.9 without further gameplay changes.

On linked servers, install the updated plugin wherever block portals can receive arriving players and keep destination spawn positions outside portal openings. Check that the target address/port is reachable from players' clients.

## Data and safe exits

Definitions are saved to the active plugin data folder's `portals.json`, normally `plugins/portals/portals.json`. Prefer the GUI for edits. Stop the server before manual file edits, preserve a backup, and verify definitions with `/portal list` after starting again. Use the GUI or delete command to remove portals rather than relying on removal of an entry followed by reload.

A transfer needs loaded ground, two blocks of headroom and a position outside every nearby portal. If the plugin cannot verify that exit, it cancels rather than transferring from inside the portal. Fix the exit area, step fully clear, wait for the cooldown and enter again; breaking the portal should not be needed.

## Verification and release automation

Run `python -m unittest discover -s tests -v` for the safety suite. The [release workflow](.github/workflows/wheel-release.yml) checks it before building a wheel. A new package version pushed to `main`, or a matching `v*` tag, publishes the matching release; branch builds leave existing releases unchanged.

See the [how-to](HOW-TO-USE.md) for player behavior, block versus entity transfer timing and the live test checklist.
<!-- endstone-professional-header:end -->
