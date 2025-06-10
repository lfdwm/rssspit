# A simple script to spit out an rss feed

import feedparser, sys, re, argparse, tty, termios

parser = argparse.ArgumentParser(description="Spit out an rss feed, optionally interactive cli")

parser.add_argument("url", help="Url to feed (or - for stdin)",  metavar="url",                           type=str                                )
parser.add_argument("-n",  help="No. of entries to show",        metavar="entries",   dest="entries",     type=int,   required=False, default=None)
parser.add_argument("-d",  help="Description length",            metavar="desc_len",  dest="desc_len",    type=int,   required=False, default=100 )
parser.add_argument("-i",  help="Run in interactive mode",       action="store_true", dest="interactive",             required=False              )
parser.add_argument("-a",  help="Disable ANSI formatting",       action="store_true", dest="no_ansi",                 required=False              )
parser.add_argument("-s",  help="Small header",                  action="store_true", dest="small_header",            required=False              )
parser.add_argument("-C",  help="Conky formatting",              action="store_true", dest="conky",                   required=False              )
parser.add_argument("-t",  help="Don't show entry timestamp",    action="store_true", dest="no_show_time",            required=False              )
parser.add_argument("-u",  help="Don't show entry url",          action="store_true", dest="no_show_url",             required=False              )
parser.add_argument("-U",  help="Don't show header url",         action="store_true", dest="no_show_header_url",      required=False              )
parser.add_argument("-c",  help="Compact entries",               action="store_true", dest="compact",                 required=False              )
parser.add_argument("-D",  help="No descriptions",               action="store_true", dest="no_show_desc",            required=False              )
parser.add_argument("-A",  help="Show author",                   action="store_true", dest="show_auth",               required=False              )

# https://stackoverflow.com/questions/510357/how-to-read-a-single-character-from-the-user
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

args = parser.parse_args()
e = chr(27) # Escape char
max_entries_on_screen = 5

if args.url == "-":
    p = feedparser.parse(sys.stdin.read())
else:
    p = feedparser.parse(args.url)

# ANSI formatting helpers

def clear_screen():
    sys.stdout.write(e+"[2J")
    sys.stdout.write(e+"[H")

def bold(text):
    if args.conky:
        return text # No good way to do this in conky I think
    elif args.no_ansi:
        return text
    else:
        return e+"[1m"+text+e+"[22m"

def underline(text):
    if args.conky:
        return text # Ditto
    elif args.no_ansi:
        return text
    else:
        return e+"[4m"+text+e+"[24m"

def italic(text):
    if args.conky:
        return "${color grey}"+text+"${color}"
    elif args.no_ansi:
        return text
    else:
        return e+"[3m"+text+e+"[23m"

def set_color(color):
    if not args.no_ansi:
        sys.stdout.write(e+"["+str(color)+"m")

###########################

def show_title(p, args):
    if args.small_header:
        if not args.no_show_header_url:
            print(bold(p.feed.title+" ("+args.url+")"))
        else:
            print(bold(p.feed.title))
    else:
        title = p.feed.title
        if not args.no_show_header_url:
            title = title+"\n("+args.url+")\n"
        print(
            "==========================================\n"
            +bold(title)+
            "==========================================\n"
        )

def show_entry(entry):
    if args.show_auth:
        print("→ [" + ", ".join([ author.name for author in entry.authors ]) + "] " + underline(entry.title[:args.desc_len]))
    else:
        print("→ "+underline(entry.title[:args.desc_len]))
    if not args.no_show_time:
        print("    ("+entry.published+")")
    if not args.no_show_url:
        print("    ("+entry.link+")")
    if not args.no_show_desc:
        description = re.sub("<.*?>", "", entry.description)
        description = description.replace("\n", "")
        print("    "+italic("\""+description[:args.desc_len]+"...\""))

def open_link(url):
    import subprocess
    subprocess.run(["firefox", url])

if not args.interactive:
    show_title(p,args)
    for entry in p.entries[:(args.entries or len(p.entries))]:
        show_entry(entry)
        if not args.compact:
            print()
else:
    try:
        sys.stdout.write(e+"[?25l")
        sel = 0
        while True:
            clear_screen()
            show_title(p, args)
            print("-: move selection up, +: move selection down\nenter: open selected link, q: quit, r: refresh\n")

            start = 0
            end = max_entries_on_screen
            if sel > 2:
                start = sel-2
                end = min(sel+3, args.entries or len(p.entries))

            for i in range(start, end):
                if i == sel:
                    print("__________________________________________")
                    show_entry(p.entries[i])
                    print("__________________________________________")
                else:
                    set_color(90)
                    print()
                    show_entry(p.entries[i])
                    print()
                    set_color(0)
            ch = getch()
            if ch == "-" and sel > 0:
                sel-=1
            elif ch == "+" and sel < (args.entries or len(p.entries))-1:
                sel+=1
            elif ch == "\n":
                open_link(p.entries[sel].link)
            elif ch == "r":
                p = feedparser.parse(args.url)
            elif ch == "q":
                break
    #except:
        #print("Exception raised, quitting")
    finally:
        sys.stdout.write(e+"[?25h")
        set_color(0)
