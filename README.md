# BASTIONS OF RETROCOMPUTING - Sharp PC-1600

A strategy game for **Sharp PC-1600** based on a similar game for Sharp PC-1500
[Bastions of Retrocomputing](https://github.com/Ante1000/Sharp_PC-1500_GAME_Bastions_of_Retrocomputing)


> **Status:** verified on a real PC-1600.
> Instructions: [PDF](instructions_v2.6-pc1600.pdf) / [DOCX](instructions_v2.6-pc1600.docx).

## Screen

- line 1: tokens `Tnnn` (left), mode (middle: MAIN MENU, FIGHT, BUY, SELL, RESOURCES, TAX), retro stuff `Rnnn` (right);
  in a fight the middle shows `Place - nnP` (Tech Priests still active). Hidden during the title music
- lines 2 and 3: the game (messages and questions; important messages are centred)
- line 4: `Hnn Gnn Dnn Tnn` = Hackers, Gurus, Daemons, Trojans in fixed fields (a field that grows blinks);
  in a fight only the forces thrown into it: `(hnn gnn dnn tnn)`

## Files

| File | Contents |
|---|---|
| `Basic/bastions_of_retrocomputing-v2.6-pc1600.txt` | the program (BASIC listing, PC-1600 BASIC) |
| `Basic/pc1600_display_test.txt` | short test of the screen commands the game relies on (run it first) |
| `wav/pc1600_display_test.wav` | recording of the test (`LOAD "CAS:DISPTEST"`, about 50 seconds) |
| `Basic/pc1600_debug.txt`, `wav/pc1600_debug.wav` | step-by-step diagnostic of the start of the game (`LOAD "CAS:DEBUG"`) |
| `wav/bastions-v2.6-pc1600.wav` | tape recording for `LOAD "CAS:BASTIONS"` (about 10 minutes) |
| `instructions_v2.6-pc1600.pdf`, `.docx` | game instructions |
| `tools/pc1600_bas2wav.py` | makes such a recording from a BASIC text file, and decodes it for a check |

## Loading from the recording

1. Put the PC-1600 in the CE-1600P and connect the audio output of a computer or player to its EAR jack.
2. In the default mode (**MODE 0**) type `LOAD "CAS:"` [ENTER] (or `LOAD "CAS:BASTIONS"`) and play the WAV.
3. Switch to RUN mode and execute `RUN`.

The recording is an ASCII BASIC file in the PC-1600 tape format, so the PC-1600 tokenizes the text
itself. 

## License

See [LICENSE](LICENSE).
