import time
import os
import sys
import curses
from io import StringIO
from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.grass import Grass
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf
from simulation.config import Config
from simulation.simulation import Simulation
from simulation.simulationController import SimulationController
from lib.pyenvlib.entity import Entity
from entity.livingEntity import LivingEntity

# @author Daniel McCoy Stephenson
# @since October 15th, 2024

class MockSoundService:
    """Mock sound service that doesn't require pygame."""
    def playReproduceSoundEffect(self):
        pass
    
    def playDeathSoundEffect(self):
        pass


class TextSimulationRunner:
    """
    A text-based simulation runner that visualizes the environment and displays 
    simulation stats to the console without using pygame graphics.
    Supports keyboard commands for interactive control.
    Uses SimulationController to decouple UI from gameplay logic.
    """
    
    def __init__(self, config: Config = None):
        self.config = config if config else Config()
        self.simulation = None
        self.controller = None
        self.running = True
        self.stdscr = None
        self.lastDrawTime = 0
        self.drawInterval = 0.1  # Refresh screen at most 10 times per second
        self.needsClear = True  # Flag to clear screen on first draw or after pause
        self.lastMessage = ""  # Store the last log message
        self.messageBuffer = StringIO()  # Capture stdout
        self.originalStdout = None  # Store original stdout
        
    def run(self):
        """Runs the text-based simulation with curses for non-blocking input."""
        curses.wrapper(self._run_with_curses)
    
    def _run_with_curses(self, stdscr):
        """Main loop with curses support."""
        self.stdscr = stdscr
        
        # Redirect stdout to capture print statements
        self.originalStdout = sys.stdout
        sys.stdout = self
        
        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)  # Non-blocking input
        stdscr.timeout(0)  # Don't wait for input
        
        # Initialize color pairs if terminal supports colors. Wolf and fox
        # both used red, which made the apex predators indistinguishable on
        # the grid (Nielsen #4: consistency — distinct entities need distinct
        # affordances).
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Grass
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Chicken
            curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Pig
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Cow
            curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Wolf
            curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_RED)    # Fox (distinct from wolf)
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Rabbit
            curses.init_pair(8, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Excrement

        # Initialize simulation
        self.initializeSimulation()

        # Display initial instructions and wait for the user to dismiss them
        # (Nielsen #7: user control and freedom — don't take action on a
        # timer the user can't see or control).
        self._display_instructions()
        stdscr.refresh()
        self._wait_for_keypress()
        
        # Main loop
        try:
            while self.running:
                # Handle keyboard input (non-blocking)
                self._handle_input()
                
                # Update simulation through controller
                self.controller.update()
                
                # Draw the environment and stats (with rate limiting)
                currentTime = time.time()
                if currentTime - self.lastDrawTime >= self.drawInterval:
                    self._draw_screen()
                    self.lastDrawTime = currentTime
                
                # Check if simulation should end
                if self.controller.shouldEnd():
                    self._show_message("All living entities have died. Simulation ended.")
                    self.controller.quit()
                    self.running = False
                    time.sleep(2)
                
                # Apply tick speed limit
                if self.config.limitTickSpeed:
                    time.sleep((self.config.maxTickSpeed - self.config.tickSpeed) / self.config.maxTickSpeed)
                else:
                    time.sleep(0.01)  # Small delay to prevent CPU spinning
                    
        except KeyboardInterrupt:
            self.simulation.cleanup()
        except Exception as e:
            self.simulation.cleanup()
            raise e
        finally:
            # Restore original stdout
            if self.originalStdout:
                sys.stdout = self.originalStdout
    
    def write(self, text):
        """Capture stdout writes (called when print() is used)."""
        if text and text.strip():
            # Store only the last non-empty message
            self.lastMessage = text.strip()
    
    def flush(self):
        """Required for file-like object compatibility."""
        pass
        
    def initializeSimulation(self):
        """Initializes the simulation with a mock game display."""
        name = "Text-Based Simulation"
        
        # Create a mock display object for simulation initialization
        class MockDisplay:
            def get_size(self):
                return (self.config.displayWidth, self.config.displayHeight)
        
        mockDisplay = MockDisplay()
        mockDisplay.config = self.config
        
        # Create simulation with mock sound service
        mockSoundService = MockSoundService()
        self.simulation = Simulation(name, self.config, mockDisplay, mockSoundService)
        
        # Create controller to manage gameplay actions
        self.controller = SimulationController(self.simulation, self.config)
        
        self.simulation.generateInitialEntities()
        self.simulation.placeInitialEntitiesInEnvironment()
    
    HELP_LINES = [
        "Apex Ecosystem Simulator - Text Mode",
        "",
        "Controls:",
        "  SPACE / ESC : Pause / Resume",
        "  ?           : Show this help",
        "  d           : Toggle debug stats",
        "  l           : Toggle tick-speed limit",
        "  ] / [       : Increase / decrease tick speed",
        "  r           : Restart simulation",
        "  q           : Quit",
        "",
        "Spawn:",
        "  c Chicken   p Pig      k Cow",
        "  w Wolf      f Fox      b Rabbit",
        "",
        "Legend:",
        "  . Grass     C Chicken  P Pig      K Cow",
        "  W Wolf      F Fox      R Rabbit   x Excrement",
        "",
        "Press any key to continue...",
    ]

    def _display_instructions(self):
        """Display initial instructions / help overlay."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        top = max(0, (height - len(self.HELP_LINES)) // 2)
        # Right-align column choice keeps text on screen even on small terms.
        col = max(0, (width - 44) // 2)
        for i, line in enumerate(self.HELP_LINES):
            if top + i >= height - 1:
                break
            attr = curses.A_BOLD if i == 0 else curses.A_NORMAL
            try:
                self.stdscr.addstr(top + i, col, line[:width - col - 1], attr)
            except curses.error:
                pass

    def _wait_for_keypress(self):
        """Block (with a short cooperative yield) until any key is pressed.

        We can't simply call getch() in blocking mode because nodelay(1) is
        already set; busy-loop with a small sleep so the terminal stays
        responsive without spinning the CPU.
        """
        while True:
            try:
                if self.stdscr.getch() != -1:
                    return
            except curses.error:
                return
            time.sleep(0.05)
    
    def _handle_input(self):
        """Handle keyboard input (non-blocking)."""
        try:
            key = self.stdscr.getch()
        except curses.error:
            return
        if key == -1:
            return
        try:
            # Use controller for all gameplay actions
            if key == ord(' '):
                self.controller.togglePause()
                self.needsClear = True  # Clear screen on pause toggle
            elif key == ord('q'):
                self.running = False
                self.controller.quit()
            elif key == ord('d'):
                self.controller.toggleDebug()
                self.needsClear = True  # Clear screen on debug toggle
            elif key == ord('c'):
                self.controller.spawnChicken()
            elif key == ord('p'):
                self.controller.spawnPig()
            elif key == ord('k'):
                self.controller.spawnCow()
            elif key == ord('w'):
                self.controller.spawnWolf()
            elif key == ord('f'):
                self.controller.spawnFox()
            elif key == ord('b'):
                self.controller.spawnRabbit()
            elif key == ord('l'):
                self.controller.toggleTickSpeedLimit()
            elif key == ord(']'):
                self.controller.increaseTickSpeed()
            elif key == ord('['):
                self.controller.decreaseTickSpeed()
            elif key == ord('?') or key == ord('h'):
                # Re-display the legend/help on demand (Nielsen #10).
                self._display_instructions()
                self.stdscr.refresh()
                self._wait_for_keypress()
                self.needsClear = True
            elif key == ord('r'):
                # Restart parity with pygame mode (Nielsen #4: consistency).
                self.controller.quit()
                self.initializeSimulation()
                self.needsClear = True
        except (curses.error, ValueError):
            return  # Ignore unrecognized or invalid keys
        
    def _draw_screen(self):
        """Draw the environment visualization and stats."""
        try:
            # Only clear screen when needed (first draw, after pause, etc)
            if self.needsClear:
                self.stdscr.clear()
                self.needsClear = False
                
            height, width = self.stdscr.getmaxyx()
            
            # Calculate grid display area
            grid = self.simulation.environment.getGrid()
            gridCols = grid.getColumns()
            gridRows = grid.getRows()
            
            # Calculate cell size (use 2 chars wide, 1 char tall for better aspect ratio)
            cellWidth = 2
            cellHeight = 1
            
            # Reserve room for: 4 stat lines, optional event line, optional
            # debug line, a blank separator, and the status bar.
            baseStats = 4 + (1 if self.lastMessage else 0) + (1 if self.controller.isDebug() else 0)
            statsHeight = baseStats + 2  # +1 separator, +1 status bar
            availableHeight = height - statsHeight - 2
            availableWidth = width - 2

            # Calculate how much of the grid we can display
            maxDisplayRows = min(gridRows, max(1, availableHeight // cellHeight))
            maxDisplayCols = min(gridCols, max(1, availableWidth // cellWidth))

            # Draw the environment
            startY = 1
            for row in range(maxDisplayRows):
                for col in range(maxDisplayCols):
                    location = grid.getLocationByCoordinates(col, row)
                    if location != -1:
                        char, color = self._get_location_char(location)
                        try:
                            self.stdscr.addstr(startY + row * cellHeight, 1 + col * cellWidth, char * cellWidth, color)
                        except curses.error:
                            pass  # Ignore if we're at the edge

            # Truncation hint so the user knows the grid extends off-screen
            # (Nielsen #1: visibility of system status).
            if maxDisplayRows < gridRows or maxDisplayCols < gridCols:
                try:
                    hint = f"(viewport {maxDisplayCols}x{maxDisplayRows} of {gridCols}x{gridRows}; resize terminal to see more)"
                    self.stdscr.addstr(startY + maxDisplayRows, 1, hint[:width - 2], curses.A_DIM)
                except curses.error:
                    pass

            # Draw stats below the grid
            statsY = startY + maxDisplayRows * cellHeight + 1
            self._draw_stats(statsY, width)

            # Draw status bar at bottom
            self._draw_status_bar(height - 1, width)

            self.stdscr.refresh()
        except curses.error:
            pass  # Drawing past the edge of the terminal; ignore
    
    def _get_location_char(self, location):
        """Get the character and color for a location."""
        if location.getNumEntities() == 0:
            return ' ', curses.color_pair(0)
        
        # Get top entity
        topEntityId = list(location.getEntities().keys())[-1]
        topEntity = location.getEntities()[topEntityId]
        
        # Determine character and color based on entity type
        from entity.grass import Grass
        from entity.excrement import Excrement
        from entity.chicken import Chicken
        from entity.pig import Pig
        from entity.cow import Cow
        from entity.wolf import Wolf
        from entity.fox import Fox
        from entity.rabbit import Rabbit
        
        if isinstance(topEntity, Grass):
            return '.', curses.color_pair(1)
        elif isinstance(topEntity, Excrement):
            return 'x', curses.color_pair(8)
        elif isinstance(topEntity, Chicken):
            return 'C', curses.color_pair(2)
        elif isinstance(topEntity, Pig):
            return 'P', curses.color_pair(3)
        elif isinstance(topEntity, Cow):
            return 'K', curses.color_pair(4)
        elif isinstance(topEntity, Wolf):
            return 'W', curses.color_pair(5)
        elif isinstance(topEntity, Fox):
            return 'F', curses.color_pair(6)
        elif isinstance(topEntity, Rabbit):
            return 'R', curses.color_pair(7)
        else:
            return '?', curses.color_pair(0)
    
    def _draw_stats(self, startY, width):
        """Draw simulation statistics + an always-visible legend.

        Keeping the legend on-screen means the user never has to recall what
        a `K` or `F` glyph stands for (Nielsen #6: recognition over recall).
        Population counts use full words rather than single-letter keys so
        the line is self-evident without the legend (DMMT: scannability).
        """
        try:
            speed = (
                f"{self.config.tickSpeed}/{self.config.maxTickSpeed}"
                if self.config.limitTickSpeed
                else "unlimited"
            )
            stats = [
                f"Tick {self.simulation.numTicks}   "
                f"Living {self.simulation.getNumLivingEntities()}   "
                f"Total {len(self.simulation.entities)}   "
                f"Speed {speed}",
                (
                    f"Chickens {self.simulation.getNumberOfLivingEntitiesOfType(Chicken)}   "
                    f"Pigs {self.simulation.getNumberOfLivingEntitiesOfType(Pig)}   "
                    f"Cows {self.simulation.getNumberOfLivingEntitiesOfType(Cow)}   "
                    f"Wolves {self.simulation.getNumberOfLivingEntitiesOfType(Wolf)}   "
                    f"Foxes {self.simulation.getNumberOfLivingEntitiesOfType(Fox)}   "
                    f"Rabbits {self.simulation.getNumberOfLivingEntitiesOfType(Rabbit)}"
                ),
                f"Grass {self.simulation.getNumberOfEntitiesOfType(Grass)}   "
                f"Excrement {self.simulation.getNumExcrement()}",
                "Legend: . grass  x excrement  C chick  P pig  K cow  W wolf  F fox  R rabbit",
            ]

            if self.lastMessage:
                stats.append(f"Event: {self.lastMessage}")

            for i, stat in enumerate(stats):
                if startY + i < curses.LINES - 2:
                    self.stdscr.addstr(startY + i, 1, stat[:width-2])

            if self.controller.isDebug():
                debug_stats = [
                    f"Grid {self.simulation.environment.getGrid().getColumns()}x{self.simulation.environment.getGrid().getRows()}   "
                    f"Deaths {self.simulation.getNumDeaths()}",
                ]
                for i, stat in enumerate(debug_stats):
                    if startY + len(stats) + i < curses.LINES - 2:
                        self.stdscr.addstr(startY + len(stats) + i, 1, stat[:width-2])
        except curses.error:
            pass

    def _draw_status_bar(self, y, width):
        """Draw status bar at bottom — reflects current mode flags so the
        user always knows what state the simulation is in (Nielsen #1)."""
        try:
            flags = []
            if self.controller.isPaused():
                flags.append("PAUSED")
            if self.controller.isDebug():
                flags.append("DEBUG")
            if not self.config.limitTickSpeed:
                flags.append("UNLIMITED SPEED")
            prefix = (" | ".join(flags) + "  ") if flags else ""
            status = prefix + "space pause  ? help  r restart  q quit"
            self.stdscr.addstr(y, 0, status[:width], curses.A_REVERSE)
        except:
            pass
    
    def _show_message(self, message):
        """Show a temporary message on screen."""
        try:
            height, width = self.stdscr.getmaxyx()
            y = height // 2
            x = (width - len(message)) // 2
            self.stdscr.addstr(y, x, message, curses.A_BOLD)
            self.stdscr.refresh()
        except:
            pass
