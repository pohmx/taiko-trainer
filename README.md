# taiko-trainer
gosumemory reader and rate modifier for osu

TAIKO RATE CONVERTER / MANIA TESTED.
NAKABAMITV (pohmx) - DEVELOPMENT 2022
https://www.surina.net/soundtouch/README.html#SoundStretch COMMANDS
SEE ISSUE https://github.com/jiaaro/pydub/issues/645, to fix .ogg conversion crackling
USING data from https://github.com/l3lackShark/gosumemory
TO DO: 
- ADD GUI [PENDING]
- MOVE FILES [OK]
- FIXED BUG: NOT IDFENTIFYING HIT OBJECT TYPE (MISSING END TIME ON SPINNERS, HOLD NOTE) [OK]
- FIXED BUG: INT(FLOAT) BOOKMARK [OK]
- FIXED BUG: JSON DATA ESCAPED CHARACTER .replace("\\'", "'") [OK]
- FIXED BUG: SLIDER TYPE, TAIKO, DONT APPLY RATE CHANGE TO OSUPIXELS [OK]
- OPTIMIZED: fix json data, remove illegal chars [OK]
- ADDED: CHECK CONNECTION TO GOSUMEMORY [OK]
- BUG FIX: IF BOOKMARKS OR TIMELIMEZOOM ARE EMPTY DON'T ADD THEM [OK]
- BUG FIX: REMOVE "" WHEN CREATING THE FILE TO AVOID INVALID PATH [OK]
