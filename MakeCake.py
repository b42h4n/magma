import colorama

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def rainbow(text):
    rainbowtext=""
    col=0
    colors=[rgb(255, 0, 0), rgb(255,165,0), rgb(255,255,0), rgb(0, 255, 0), rgb(0, 255, 255), rgb(0, 105, 255), rgb(159, 43, 104)]
    for i in text:
        rainbowtext+=f"{colors[col]}{i}"
        col+=1
        if col >= 7:
            col=0
    return rainbowtext

def mcake(congrats):
    print(f"""{colorama.Fore.RED}⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⡞⣧⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀{colorama.Fore.WHITE}⣀⣀⣀{colorama.Fore.RED}⣳⣋{colorama.Fore.WHITE}⣀⣀⡀⠀⠀⠀
{colorama.Fore.WHITE}⠀⠀⠀⢸⡿⢯⣍⡉⣉⣩⠿⢻⠀⠀⠀
⠀⠀⣤⡼⠧⠤⠬⠭⠭⠤⠤⠼⣤⡄⠀{rgb(142,102,68)}
⠀⠀⣿⣠⣤⣰⣆⣠⣄⣴⣀⣶⣠⡇⠀
⠀ {rgb(142,102,68)}⣿⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀{rgb(142,102,68)}⡇
{congrats}""")
