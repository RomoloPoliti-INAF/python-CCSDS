from rich.table import Table
from rich.align import Align
from re import sub
from functools import wraps
from rich.console import Console

console=Console()

def snake_case(s: str) -> str:
    """Convert a string to snake_case"""
    return "_".join(
        sub(
            "([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))
        ).split()
    ).lower()


def sentence_case(s: str) -> str:
    """Convert a string to Sentence case"""
    return sub(r"(_|-)+", " ", snake_case(s)).title()

def get_style(value)->str:
    """
    Get the style for the value
    """
    if isinstance(value, (int, float)):
        return "cyan"
    return "green"

def counter(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not 'cnt' in globals():
            global cnt
            cnt = 0
        else:
            cnt += 1
        return f(*args, **kwargs)
    return wrapper

styles_array=['yellow','magenta','green','blue', 'red']

@counter
def dict2table(my_data:dict, grid:bool=True, title:str=None,reset:bool =False)->Table:
    """
    Convert a dictionary to a table
    """
    if reset:
            global cnt
            cnt=0
    if grid:
        external=Table.grid()
        if title:
            external.add_row(Align(f"{title}\n", style="italic", align="center"))
        tb=Table.grid()
        tb.padding=(0,3)
    else:  
        tb=Table()
        tb.title=title
    console.log(f"cnt: {cnt}")
    tb.add_column('Key',style=f"{styles_array[cnt]} bold")
    tb.add_column('Value',style="")
    for item in my_data.items():
        if isinstance(item[1], dict):
            elem=dict2table(item[1],grid=True)
        else:
            st=get_style(item[1])
            elem=f"[{st}]{item[1]}[/]"
        tb.add_row(sentence_case(item[0]),elem)
    if grid:
        external.add_row(tb)
        return external
    
    return tb
