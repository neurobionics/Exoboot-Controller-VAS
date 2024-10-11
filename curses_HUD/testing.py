import curses

def main(stdscr):
    stdscr.border()
    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

    # Create a subwindow
    height, width = 10, 20
    begin_y, begin_x = 2, 1
    subwin0 = stdscr.subwin(height, width, begin_y, begin_x)

    # Add content to the subwindow
    subwin0.addstr(1, 1, "Hello from subwin!", curses.color_pair(1))
    subwin0.border()
    subwin0.refresh()

    subsubwin = subwin0.derwin(5, 5, 1, 1)
    subsubwin.border()
    subsubwin.refresh()

    # Wait for a key press
    stdscr.getch()

    stdscr.refresh()

    subwin0.mvwin(3, 3)
    subwin0.border()

    subsubwin.mvderwin(3, 3)
    subsubwin.border()

    subwin0.addstr(1, 1, "asdfasdf", curses.color_pair(1))
    subsubwin1 = stdscr.subwin(5, 5, 10, 10)
    subsubwin1.border()

    subsubwin.refresh()
    subwin0.refresh()
    subsubwin1.refresh()
    stdscr.refresh()


    stdscr.getch()

    stdscr.refresh()

    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)