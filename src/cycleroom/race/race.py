import pygame
import os
import json
import asyncio
import httpx
import logging
import signal
import sys
from datetime import datetime
from config.config import Config  # Import the Config class
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Logger Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def set_env_variables():
    """Set environment variables from Config class."""
    os.environ["INFLUXDB_URL"] = Config.INFLUXDB_URL
    os.environ["INFLUXDB_TOKEN"] = Config.INFLUXDB_TOKEN
    os.environ["INFLUXDB_ORG"] = Config.INFLUXDB_ORG
    os.environ["INFLUXDB_BUCKET"] = Config.INFLUXDB_BUCKET
    os.environ["QUERY_INTERVAL"] = str(Config.QUERY_INTERVAL)
    os.environ["SCREEN_WIDTH"] = str(Config.SCREEN_WIDTH)
    os.environ["SCREEN_HEIGHT"] = str(Config.SCREEN_HEIGHT)
    os.environ["TRACK_WIDTH"] = str(Config.TRACK_WIDTH)
    os.environ["TRACK_LENGTH_MILES"] = str(Config.TRACK_LENGTH_MILES)
    os.environ["WAYPOINTS_FILE"] = Config.WAYPOINTS_FILE
    os.environ["BIKE_ICON_PATH"] = Config.BIKE_ICON_PATH
    os.environ["TRACK_IMAGE_PATH"] = Config.TRACK_IMAGE_PATH

# Initialize Pygame
try:
    pygame.init()
    screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
    pygame.display.set_caption("Real-Time Bike Race Visualization")
    clock = pygame.time.Clock()
except pygame.error as e:
    logger.error(f"❌ Pygame initialization failed: {e}")
    sys.exit(1)  # Exit the program if Pygame cannot initialize
except ValueError as e:
    logger.error(f"❌ Invalid screen dimensions or display configuration: {e}")
    sys.exit(1)

# Global Variables
WAYPOINTS = []
BIKE_ICON = None
TRACK_IMAGE = None
bike_data = {}
bike_positions = {}
bike_laps = {}
bike_colors = {}
bike_last_waypoint = {}
bike_initial_distance = {}  # Track initial distance for each bike
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 18)  # Smaller font for metrics
countdown_timer = 10  # Countdown timer in seconds

# Assign Colors to Bikes
def assign_bike_colors():
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 165, 0), (255, 255, 0)]
    for i, bike_id in enumerate(bike_data.keys()):
        bike_colors[bike_id] = colors[i % len(colors)]

# Reset all stats
def reset_stats():
    global bike_data, bike_positions, bike_laps, bike_last_waypoint, bike_initial_distance
    bike_data = {}
    bike_positions = {}
    bike_laps = {}
    bike_last_waypoint = {}
    bike_initial_distance = {}

# Load Assets
def load_assets():
    global WAYPOINTS, BIKE_ICON, TRACK_IMAGE
    # Load Waypoints
    try:
        with open(Config.WAYPOINTS_FILE, "r") as f:
            WAYPOINTS = [(wp["x"], wp["y"]) for wp in json.load(f)]
        print(f"✅ Loaded {len(WAYPOINTS)} waypoints.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading waypoints: {e}")
        WAYPOINTS = []

    # Load Bike Icon
    try:
        BIKE_ICON = pygame.image.load(Config.BIKE_ICON_PATH)
        BIKE_ICON = pygame.transform.scale(BIKE_ICON, (20, 10))
    except pygame.error as e:
        print(f"❌ Error loading bike icon: {e}")
        BIKE_ICON = None

    # Load Track Image
    try:
        TRACK_IMAGE = pygame.image.load(Config.TRACK_IMAGE_PATH)
        TRACK_IMAGE = pygame.transform.scale(TRACK_IMAGE, (Config.TRACK_WIDTH, Config.SCREEN_HEIGHT))
    except pygame.error as e:
        print(f"❌ Error loading track image: {e}")
        TRACK_IMAGE = None

# Get bike position with interpolation
def interpolate_position(start_pos, end_pos, progress):
    return (
        int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress),
        int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress),
    )

def get_bike_position(distance_miles, bike_id):
    if not WAYPOINTS:
        return (0, 0)   

    distance_pixels = (distance_miles / Config.TRACK_LENGTH_MILES) * len(WAYPOINTS)
    index = int(distance_pixels) % len(WAYPOINTS)
    next_index = (index + 1) % len(WAYPOINTS)

    start_pos = WAYPOINTS[index]
    end_pos = WAYPOINTS[next_index]
    progress = distance_pixels % 1

    # Update lap counter
    update_lap_counter(bike_id, index)

    bike_positions[bike_id] = interpolate_position(start_pos, end_pos, progress)
    return bike_positions[bike_id]

# Update Lap Counter
def update_lap_counter(bike_id, current_waypoint):
    if bike_id not in bike_laps:
        bike_laps[bike_id] = 0
        bike_last_waypoint[bike_id] = current_waypoint

    # Check if the bike crossed the start/finish line (first waypoint)
    if bike_last_waypoint[bike_id] > current_waypoint and current_waypoint == 0:
        bike_laps[bike_id] += 1

    bike_last_waypoint[bike_id] = current_waypoint

# Draw Bike Icons with Smooth Animation
def draw_bike_icons():
    for bike_id, metrics in bike_data.items():
        bike_pos = get_bike_position(metrics["trip_miles"], bike_id)
        color = bike_colors.get(bike_id, (255, 255, 255))
        if BIKE_ICON:
            screen.blit(BIKE_ICON, bike_pos)

# Draw Real-Time Metrics under Leaderboard
def draw_metrics_under_leaderboard():
    metrics_pos = (Config.TRACK_WIDTH + 50, 400)
    y_offset = 0
    column_width = 200  # Width of each column
    for bike_id, metrics in bike_data.items():
        initial_distance = bike_initial_distance.get(bike_id, 0)
        race_distance = metrics["trip_miles"] - initial_distance
        text_lines = [
            f"Bike ID: {bike_id}",
            f"Speed: {metrics.get('speed', 'N/A')} mph",
            f"Cadence: {metrics.get('cadence', 'N/A')} rpm",
            f"Power: {metrics.get('power', 'N/A')} W",
            f"Distance: {metrics.get('trip_miles', 'N/A')} miles",
            f"Race Distance: {race_distance:.2f} miles",
            f"Gear: {metrics.get('gear', 'N/A')}",
            f"Laps: {bike_laps.get(bike_id, 0)}",
        ]
        for i, line in enumerate(text_lines):
            text_surface = small_font.render(line, True, (255, 255, 255))
            column = i % 2  # Determine the column (0 or 1)
            row = i // 2  # Determine the row
            screen.blit(text_surface, (metrics_pos[0] + column * column_width, metrics_pos[1] + y_offset + row * 15))
        y_offset += 40  # Add extra space between bikes

# Global variable to track leaderboard scrolling
leaderboard_scroll_offset = 0
LEADERBOARD_ITEMS_PER_PAGE = 10  # Number of items to display per page

# Draw Real-Time Leaderboard with Scrolling
def draw_leaderboard():
    global leaderboard_scroll_offset
    sorted_bikes = sorted(
        bike_data.items(), key=lambda x: x[1]["trip_miles"], reverse=True
    )
    leaderboard_pos = (Config.TRACK_WIDTH + 50, 50)
    y_offset = 0

    # Draw leaderboard title
    title_surface = font.render("Leaderboard", True, (255, 255, 255))
    screen.blit(title_surface, leaderboard_pos)

    # Calculate the range of items to display based on the scroll offset
    start_index = leaderboard_scroll_offset
    end_index = start_index + LEADERBOARD_ITEMS_PER_PAGE
    visible_bikes = sorted_bikes[start_index:end_index]

    # Display the visible bikes
    for rank, (bike_id, metrics) in enumerate(visible_bikes, start=start_index + 1):
        color = bike_colors.get(bike_id, (255, 255, 255))
        leaderboard_text = f"{rank}. {bike_id}: {metrics['trip_miles']:.2f} miles | Laps: {bike_laps.get(bike_id, 0)}"
        text_surface = font.render(leaderboard_text, True, color)
        screen.blit(
            text_surface, (leaderboard_pos[0], leaderboard_pos[1] + 25 + y_offset)
        )
        y_offset += 25

    # Draw scroll indicators if needed
    if leaderboard_scroll_offset > 0:
        up_arrow_surface = font.render("↑ Scroll Up", True, (255, 255, 255))
        screen.blit(up_arrow_surface, (leaderboard_pos[0], leaderboard_pos[1] - 20))
    if end_index < len(sorted_bikes):
        down_arrow_surface = font.render("↓ Scroll Down", True, (255, 255, 255))
        screen.blit(
            down_arrow_surface,
            (leaderboard_pos[0], leaderboard_pos[1] + 25 + y_offset),
        )

# Handle Leaderboard Scrolling
def handle_leaderboard_scrolling(event):
    global leaderboard_scroll_offset
    sorted_bikes = sorted(
        bike_data.items(), key=lambda x: x[1]["trip_miles"], reverse=True
    )
    max_offset = max(0, len(sorted_bikes) - LEADERBOARD_ITEMS_PER_PAGE)

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:  # Scroll up
            leaderboard_scroll_offset = max(0, leaderboard_scroll_offset - 1)
        elif event.key == pygame.K_DOWN:  # Scroll down
            leaderboard_scroll_offset = min(max_offset, leaderboard_scroll_offset + 1)

# Update Display
def update_display():
    screen.fill((0, 0, 0))
    if TRACK_IMAGE:
        screen.blit(TRACK_IMAGE, (0, 0))
    draw_bike_icons()
    draw_leaderboard()
    draw_metrics_under_leaderboard()
    pygame.display.flip()
    clock.tick(30)  # Maintain 30 FPS

# Fetch Real-Time Data from FastAPI
async def fetch_real_time_data():
    global bike_data
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://127.0.0.1:8000/bikes")
            if response.status_code == 200:
                bike_data = response.json()
                assign_bike_colors()
            else:
                print(f"❌ Error fetching real-time data: {response.status_code}")
        except httpx.RequestError as e:
            print(f"❌ HTTP Request Error: {e}")

# Main Loop
async def main_loop():
    load_assets()
    running = True
    global countdown_timer

    async def periodic_fetch():
        while running:
            await fetch_real_time_data()
            await asyncio.sleep(5)

    fetch_task = asyncio.create_task(periodic_fetch())

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            handle_leaderboard_scrolling(event)
        
        if countdown_timer > 0:
            screen.fill((0, 0, 0))
            countdown_text = font.render(f"Race starts in: {countdown_timer}", True, (255, 255, 255))
            screen.blit(countdown_text, (Config.SCREEN_WIDTH // 2 - 100, Config.SCREEN_HEIGHT // 2))
            pygame.display.flip()
            await asyncio.sleep(1)
            countdown_timer -= 1
        else:
            if countdown_timer == 0:
                reset_stats()
                for bike_id, metrics in bike_data.items():
                    bike_initial_distance[bike_id] = metrics["trip_miles"]
                countdown_timer -= 1  # Ensure this block runs only once
            update_display()
            await asyncio.sleep(0.03)  # Maintain 30 FPS

    fetch_task.cancel()
    pygame.quit()
    sys.exit(0)

def signal_handler(sig, frame):
    """Handle termination signals and gracefully shut down processes."""
    logger.info("Received termination signal. Shutting down processes gracefully...")
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    set_env_variables()
    sys.path.append("/home/glen/cycleroom-v2/src")  # Add this line to set PYTHONPATH

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signals

    # Run the main loop
    asyncio.run(main_loop())