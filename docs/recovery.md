# NXless Phase 0 recovery and uninstall

NXless must always be recoverable from the SD card. It never requires a NAND modification.

## Recovery after a bad boot or networking regression

1. **Power off** the Nintendo Switch completely.
2. Remove or otherwise access the SD card from a safe environment.
3. Prefer the reversible recovery path: create the empty file `/config/nxless/disable.flag`.
4. If that is not sufficient, remove the NXless-owned directory `/atmosphere/contents/0100000000004E58` from the SD card.
5. Boot the console again.
6. Verify **normal networking** without NXless interception before doing any further testing.

The `disable.flag` boot path is implemented and host-tested, but it is **not hardware-proven** until the Phase 0 hardware lifecycle matrix is completed on original Switch hardware. Keep the directory-removal recovery path available during all pre-release testing.

## Uninstall

Power off the console and remove only NXless-owned SD-card paths:

- `/atmosphere/contents/0100000000004E58`
- `/config/nxless`

Do not delete unrelated Atmosphere content directories. NXless does not require, and its uninstall procedure must never instruct, modification of NAND or Nintendo system files.
