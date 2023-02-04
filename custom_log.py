import logging
import sys
from pathlib import Path

def create_logger(module:str) -> logging.Logger:
    main_module = sys.modules["__main__"]
    main_name=''
    if main_module.__file__:
        p = Path(main_module.__file__)
        main_name = p.name.removesuffix(".py")

    return logging.getLogger(f'{main_name}/{module}')