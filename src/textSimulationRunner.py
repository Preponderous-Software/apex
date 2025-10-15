import time
import os
import sys
import curses
from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.grass import Grass
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf
from simulation.config import Config
from simulation.simulation import Simulation
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
    """
    
    def __init__(self, config: Config = None):
        self.config = config if config else Config()
        self.simulation = None
        self.running = True
        self.paused = False
        self.debug = False
        self.stdscr = None
        
    def run(self):
        """Runs the text-based simulation with curses for non-blocking input."""
        curses.wrapper(self._run_with_curses)
    
    def _run_with_curses(self, stdscr):
        """Main loop with curses support."""
        self.stdscr = stdscr
        
        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)  # Non-blocking input
        stdscr.timeout(0)  # Don't wait for input
        
        # Initialize color pairs if terminal supports colors
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Grass
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Chicken
            curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Pig
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Cow
            curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Wolf
            curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)     # Fox
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Rabbit
            curses.init_pair(8, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Excrement
        
        # Initialize simulation
        self.initializeSimulation()
        
        # Display initial instructions
        self._display_instructions()
        stdscr.refresh()
        time.sleep(2)
        
        # Main loop
        try:
            while self.running:
                # Handle keyboard input (non-blocking)
                self._handle_input()
                
                # Update simulation if not paused
                if not self.paused:
                    self.simulation.update()
                    self.simulation.numTicks += 1
                
                # Draw the environment and stats
                self._draw_screen()
                
                # Check if simulation should end
                if self.config.endSimulationUponAllLivingEntitiesDying:
                    if self.simulation.getNumLivingEntities() == 0:
                        self._show_message("All living entities have died. Simulation ended.")
                        self.simulation.cleanup()
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
        
        self.simulation.generateInitialEntities()
        self.simulation.placeInitialEntitiesInEnvironment()
    
    def _display_instructions(self):
        """Display initial instructions."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        title = "Apex Ecosystem Simulator - Text Mode"
        self.stdscr.addstr(height // 2 - 5, (width - len(title)) // 2, title, curses.A_BOLD)
        
        instructions = [
            "",
            "Controls:",
            "  SPACE: Pause/Resume",
            "  d: Toggle debug mode",
            "  c: Spawn chicken",
            "  p: Spawn pig",
            "  k: Spawn cow",
            "  w: Spawn wolf",
            "  f: Spawn fox",
            "  b: Spawn rabbit",
            "  l: Toggle tick speed limit",
            "  ]: Increase tick speed",
            "  [: Decrease tick speed",
            "  q: Quit",
            "",
            "Starting simulation..."
        ]
        
        for i, line in enumerate(instructions):
            self.stdscr.addstr(height // 2 - 4 + i, (width - 40) // 2, line)
    
    def _handle_input(self):
        """Handle keyboard input (non-blocking)."""
        try:
            key = self.stdscr.getch()
            
            if key == ord(' '):
                self.paused = not self.paused
            elif key == ord('q'):
                self.running = False
                self.simulation.cleanup()
            elif key == ord('d'):
                self.debug = not self.debug
            elif key == ord('c'):
                from entity.chicken import Chicken
                chicken = Chicken("player-created-chicken")
                self.simulation.environment.addEntity(chicken)
                self.simulation.addEntityToTrackedEntities(chicken)
            elif key == ord('p'):
                from entity.pig import Pig
                pig = Pig("player-created-pig")
                self.simulation.environment.addEntity(pig)
                self.simulation.addEntityToTrackedEntities(pig)
            elif key == ord('k'):
                from entity.cow import Cow
                cow = Cow("player-created-cow")
                self.simulation.environment.addEntity(cow)
                self.simulation.addEntityToTrackedEntities(cow)
            elif key == ord('w'):
                from entity.wolf import Wolf
                wolf = Wolf("player-created-wolf")
                self.simulation.environment.addEntity(wolf)
                self.simulation.addEntityToTrackedEntities(wolf)
            elif key == ord('f'):
                from entity.fox import Fox
                fox = Fox("player-created-fox")
                self.simulation.environment.addEntity(fox)
                self.simulation.addEntityToTrackedEntities(fox)
            elif key == ord('b'):
                from entity.rabbit import Rabbit
                rabbit = Rabbit("player-created-rabbit")
                self.simulation.environment.addEntity(rabbit)
                self.simulation.addEntityToTrackedEntities(rabbit)
            elif key == ord('l'):
                self.config.limitTickSpeed = not self.config.limitTickSpeed
            elif key == ord(']'):
                if self.config.tickSpeed < self.config.maxTickSpeed:
                    self.config.tickSpeed += 1
            elif key == ord('['):
                if self.config.tickSpeed > 1:
                    self.config.tickSpeed -= 1
                    
        except:
            pass  # Ignore input errors
        
    def _draw_screen(self):
        """Draw the environment visualization and stats."""
        try:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            # Calculate grid display area
            grid = self.simulation.environment.getGrid()
            gridCols = grid.getColumns()
            gridRows = grid.getRows()
            
            # Calculate cell size (use 2 chars wide, 1 char tall for better aspect ratio)
            cellWidth = 2
            cellHeight = 1
            
            # Calculate available space for grid
            statsHeight = 12 if self.debug else 8
            availableHeight = height - statsHeight - 2
            availableWidth = width - 2
            
            # Calculate how much of the grid we can display
            maxDisplayRows = min(gridRows, availableHeight // cellHeight)
            maxDisplayCols = min(gridCols, availableWidth // cellWidth)
            
            # Draw the environment
            startY = 1
            for row in range(maxDisplayRows):
                for col in range(maxDisplayCols):
                    location = grid.getLocationByCoordinates(col, row)
                    if location != -1:
                        char, color = self._get_location_char(location)
                        try:
                            self.stdscr.addstr(startY + row * cellHeight, 1 + col * cellWidth, char * cellWidth, color)
                        except:
                            pass  # Ignore if we're at the edge
            
            # Draw stats below the grid
            statsY = startY + maxDisplayRows * cellHeight + 1
            self._draw_stats(statsY, width)
            
            # Draw status bar at bottom
            self._draw_status_bar(height - 1, width)
            
            self.stdscr.refresh()
        except:
            pass  # Ignore drawing errors
    
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
        """Draw simulation statistics."""
        try:
            stats = [
                f"Tick: {self.simulation.numTicks}  Living: {self.simulation.getNumLivingEntities()}  Total: {len(self.simulation.entities)}",
                f"Grass: {self.simulation.getNumberOfEntitiesOfType(Grass)}  Excrement: {self.simulation.getNumExcrement()}",
                f"C:{self.simulation.getNumberOfLivingEntitiesOfType(Chicken)} P:{self.simulation.getNumberOfLivingEntitiesOfType(Pig)} K:{self.simulation.getNumberOfLivingEntitiesOfType(Cow)} W:{self.simulation.getNumberOfLivingEntitiesOfType(Wolf)} F:{self.simulation.getNumberOfLivingEntitiesOfType(Fox)} R:{self.simulation.getNumberOfLivingEntitiesOfType(Rabbit)}",
            ]
            
            if self.config.limitTickSpeed:
                stats.append(f"Tick Speed: {self.config.tickSpeed}/{self.config.maxTickSpeed}")
            
            for i, stat in enumerate(stats):
                if startY + i < curses.LINES - 2:
                    self.stdscr.addstr(startY + i, 1, stat[:width-2])
                    
            if self.debug:
                # Add more detailed stats in debug mode
                debug_stats = [
                    "",
                    f"Grid: {self.simulation.environment.getGrid().getColumns()}x{self.simulation.environment.getGrid().getRows()}",
                    f"Deaths: {self.simulation.getNumDeaths()}",
                ]
                for i, stat in enumerate(debug_stats):
                    if startY + len(stats) + i < curses.LINES - 2:
                        self.stdscr.addstr(startY + len(stats) + i, 1, stat[:width-2])
        except:
            pass
    
    def _draw_status_bar(self, y, width):
        """Draw status bar at bottom."""
        try:
            status = ""
            if self.paused:
                status = "PAUSED - "
            status += "q:Quit SPACE:Pause d:Debug [/]:Speed c/p/k/w/f/b:Spawn"
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
