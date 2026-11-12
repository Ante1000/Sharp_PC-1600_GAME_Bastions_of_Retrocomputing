# BASTIONS OF RETROCOMPUTING - Sharp PC-1600

Port of the strategy game [Bastions of Retrocomputing](https://github.com/Ante1000/Sharp_PC-1500_GAME_Bastions_of_Retrocomputing)
(Sharp PC-1500) to the **Sharp PC-1600** in its own mode (MODE 0, 4-line display).

> **Status: work in progress, not yet tested on a real PC-1600.** The instructions are not
> updated yet; for the rules see the instructions of the PC-1500 version (linked above).

## Screen

- line 1: tokens (left), name of the active place (middle), retro stuff (right)
- lines 2 and 3: the game (messages and questions)
- line 4: `H nnn Gnn Dnnn Tnnn` = Hackers, Gurus, Daemons, Trojans

## Files

| File | Contents |
|---|---|
| `Basic/bastions_of_retrocomputing-v2.6-pc1600.txt` | the program (BASIC listing, PC-1600 BASIC, 285 lines) |
| `Basic/pc1600_display_test.txt` | short test of the screen commands the game relies on (run it first) |
| `wav/pc1600_display_test.wav` | recording of the test (`LOAD "CAS:DISPTEST"`, about 50 seconds) |
| `Basic/pc1600_debug.txt`, `wav/pc1600_debug.wav` | step-by-step diagnostic of the start of the game (`LOAD "CAS:DEBUG"`) |
| `wav/bastions-v2.6-pc1600.wav` | tape recording for `LOAD "CAS:BASTIONS"` (about 9 minutes) |
| `tools/pc1600_bas2wav.py` | makes such a recording from a BASIC text file, and decodes it for a check |

## Loading from the recording

1. Connect the PC-1600 in the CE-1600P to a cassette input (or the audio output of a computer to the EAR jack) and select **MODE 0**.
2. Type `LOAD "CAS:BASTIONS"` [ENTER] (or `LOAD "CAS:"` for the first file) and play the WAV.
3. `RUN` in MODE 0.

The recording is an ASCII BASIC file in the PC-1600 tape format (`SAVE "CAS:...",A`), so the
PC-1600 tokenizes the text itself. Format: PC-1600 Technical Reference, section 3.11.1.
Options of the tool (`--eol cr|lf|crlf`, `--ext`, `--invert`, `--rate`) are in the header of the script.

```
python3 tools/pc1600_bas2wav.py Basic/bastions_of_retrocomputing-v2.6-pc1600.txt wav/bastions-v2.6-pc1600.wav BASTIONS
python3 tools/pc1600_bas2wav.py --check wav/bastions-v2.6-pc1600.wav
```

## License

See [LICENSE](LICENSE).
