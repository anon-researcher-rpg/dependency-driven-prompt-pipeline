from __future__ import annotations

import logging
import os
from pathlib import Path

MODEL: str = os.getenv("MODEL", "gpt-5")
LANGUAGE: str = os.getenv("LANGUAGE", "EN")

DATA_DIR: Path = Path(os.getenv("DATA_DIR", "data"))

ROOT_DIRECTORY: Path = Path(os.getenv("ROOT_DIRECTORY", str(DATA_DIR / "runs")))

CLASSES = ["MAG", "ARCHER", "WARRIOR", "PALADIN", "ROGUE"]

# TOKENS
HERO_TOKENS = 32768
BASIC_NPC_TOKENS = 32768
EPIC_NPC_TOKENS = 32768
QUESTS_TOKENS = 32768
WORLD_TOKENS = 32768

# TEMPERATURES
HERO_TEMPERATURE = 1
BASIC_NPC_TEMPERATURE = 1
EPIC_TEMPERATURE = 1
QUESTS_TEMPERATURE = 1
WORLD_TEMPERATURE = 1

PG_MOTD = r"""

,-.----.                                              
\    /  \    ,----..                                  
|   :    \  /   /   \                                 
|   |  .\ :|   :     :                                
.   :  |: |.   |  ;. /                                
|   |   \ :.   ; /--`                                 
|   : .   /;   | ;  __                                
;   | |`-' |   : |.' .'                               
|   | ;    .   | '_.' :                               
:   ' |    '   ; : \  |                               
:   : :    '   | '/  .'                               
|   | :    |   :    /                                 
`---'.|     \   \ .'                          ,----,. 
  `---`      `---`                          ,'   ,' | 
      ,----,     ,----..        ,----,    ,'   .'   | 
    .'   .' \   /   /   \     .'   .' \ ,----.'    .' 
  ,----,'    | /   .     :  ,----,'    ||    |   .'   
  |    :  .  ;.   /   ;.  \ |    :  .  ;:    :  |--,  
  ;    |.'  /.   ;   /  ` ; ;    |.'  / :    |  ;.' \ 
  `----'/  ; ;   |  ; \ ; | `----'/  ;  |    |      | 
    /  ;  /  |   :  | ; | '   /  ;  /   `----'.'\   ; 
   ;  /  /-, .   |  ' ' ' :  ;  /  /-,    __  \  .  | 
  /  /  /.`| '   ;  \; /  | /  /  /.`|  /   /\/  /  : 
./__;      :  \   \  ',  /./__;      : / ,,/  ',-   . 
|   :    .'    ;   :    / |   :    .'  \ ''\       ;  
;   | .'        \   \ .'  ;   | .'      \   \    .'   
`---'            `---`    `---'          `--`-,-'     

"""

def log_config_vars():
    for name, value in globals().items():
        if name.isupper():
            logging.info(f"{name} = {value}")
