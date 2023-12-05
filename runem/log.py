
def log(msg:str="", decorate:bool=True, end: str|None=None)->None: 
    """thin wrapper around 'print', so we can change the output
    
    One way we change it is to decorate the output with 'runem'"""
    if decorate:
        msg = f"runem: {msg}"
    print(msg, end=end)