# Phase 0 recovery

NXless Phase 0 is designed to fail open and to remain recoverable from the SD card without modifying NAND or Nintendo system files.

## Primary recovery flag

Create:

`sdmc:/config/nxless/disable.flag`

On the next cold boot NXless should expose the read-only control service but must not install the `bsd:u` MITM. `nxl:ctl` should report `SafeDisabled` when the flag was successfully detected.

The hardware acceptance matrix requires 10 successful cold boots in this state before Phase 0 is considered proven.

## Full sysmodule removal

If the recovery flag cannot be used, power the console fully off and remove:

`/atmosphere/contents/0100000000004E58`

Do not modify NAND or Nintendo system titles. Removing the NXless contents directory must restore the pre-NXless boot/network path.

## Config errors

`config.toml` is optional in Phase 0. A missing config is valid. Malformed, oversized, unreadable, or short-read config data must not cause a fatal boot path; the sysmodule must remain in an error/fail-open control-only mode.

## Evidence

Recovery results are recorded with `scripts/phase0_hardware.py` and are part of GitHub issue #3. Anecdotal “it boots” testing is not sufficient to close the hardware gate.
