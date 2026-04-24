# Arduino Flight Controller — Task Tracking

## Setup Tasks
- [x] Create project directory structure
- [x] Write CLAUDE.md with wiring and run instructions
- [x] Write Arduino firmware (flight_controller.ino)
- [x] Write Python serial reader (serial_reader.py)
- [x] Write vJoy output module (vjoy_output.py)
- [x] Write configuration manager (config_manager.py)
- [x] Write GUI app (main.py)
- [x] Write requirements.txt and default_config.json

## Hardware Setup (Manual)
- [ ] Wire joystick module directly to Arduino (A0, A1, D2, 5V, GND) — no breadboard
- [ ] Wire potentiometer wiper to A2; daisy-chain VCC off joystick VCC; GND to second GND pin
- [ ] Integrate potentiometer into 3D-printed throttle mechanism
- [ ] Upload firmware via Arduino IDE
- [ ] Install vJoy driver and configure Device 1

## Software Setup (Manual)
- [ ] Install Python 3 and add to PATH
- [ ] Run: pip install -r app/requirements.txt
- [ ] Run: python app/main.py
- [ ] Calibrate throttle: move to 0% → Set 0%, move to 100% → Set 100%, Save Config
- [ ] Verify live input display responds to physical inputs
- [ ] Configure flight sim to use vJoy Device 1

## Completed Refactor (2026-04-21)
- [x] Remove servo motor from firmware and hardware design
- [x] Add Set 0% / Set 100% calibration buttons to throttle panel in PC app
- [x] Show calibrated % next to raw ADC value in live display
- [x] Document no-breadboard wiring (daisy-chain pot VCC off joystick)
- [x] Update CLAUDE.md wiring diagram and run instructions

## Future Improvements
- [ ] Add button debounce in firmware
- [ ] Add profile save/load (multiple game presets)
- [ ] Add second button (e.g. D3 for weapons release)
