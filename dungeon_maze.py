#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from ursina import (
    Ursina, Entity, Panel, Button, Vec2, color, window, scene,
    application, mouse, camera, Audio, held_keys, Sky
)
from ursina.prefabs.first_person_controller import FirstPersonController

# --- Constants and Configuration ---
MAZE_LAYOUT = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

CORRIDOR_WIDTH = 10  # Width/depth of corridors/walls
WALL_HEIGHT = 20 # Height of walls
PLAYER_HEIGHT = 0.4 # Make player very short
PLAYER_START_OFFSET = 0.1 # Offset from corner to avoid collision
DEFAULT_SENSITIVITY = 120

WALL_TEXTURE = 'assets/stone'
FLOOR_TEXTURE = 'assets/stone'

WALK_SPEED = 5
RUN_SPEED = 8

# --- Global State ---
paused = False
player = None # Initialize player reference

# --- Pause Menu Handler Class ---
class PauseHandler(Entity):
    """Handles escape key input for pausing, ignoring application pause state."""
    def __init__(self, **kwargs):
        super().__init__(ignore_paused=True, **kwargs) # Set ignore_paused directly

    def input(self, key):
        if key == 'escape':
            toggle_pause()

# --- Functions ---
def toggle_pause():
    """Toggles the pause state of the game and menu visibility."""
    global paused, player
    paused = not paused
    pause_menu.enabled = paused
    application.paused = paused
    mouse.locked = not paused
    mouse.visible = paused
    if player:
        player.enabled = not paused
        if not paused: # If resuming
            player.cursor.enabled = False # Re-disable cursor

def resume_game():
    """Callback function for the Resume button."""
    toggle_pause()

def quit_game():
    """Callback function for the Quit button."""
    sys.exit()

# --- Initialization ---
app = Ursina()

# --- Load Ambient Music ---
# Make sure you have an 'ambient_music.ogg' or '.wav' file
# in an 'assets' folder in your project directory.
ambient_music = Audio(
    'assets/ambience', # Use the new ambience file
    loop=True,
    autoplay=True,
    volume=1
)

# --- Sky Setup ---
sky = Sky(texture='assets/stars') # Ursina finds common extensions

# --- Window Setup ---
window.fullscreen = True
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.fps_counter.enabled = False
window.exit_button.enabled = False
window.color = color.black
camera.near_clip_plane = 0.1

# --- Lighting Setup ---
scene.ambient_light = (0.3, 0.3, 0.3, 1)

# --- UI Setup (Pause Menu) ---
pause_menu = Panel(model='quad', scale=0.5, origin=(0, 0), enabled=False)
resume_button = Button(
    parent=pause_menu, text='Resume', color=color.rgb(139/255, 0, 0),
    scale=(0.5, 0.1), y=0.15, on_click=resume_game
)
quit_button = Button(
    parent=pause_menu, text='Quit', color=color.rgb(139/255, 0, 0),
    scale=(0.5, 0.1), y=-0.15, on_click=quit_game
)
resume_button.text_entity.color = color.black # Set resume text to black
quit_button.text_entity.color = color.black   # Set quit text to black

pause_handler = PauseHandler() # Handles escape input

# --- Game Object Creation ---
# Create Walls
for z, row in enumerate(MAZE_LAYOUT):
    for x, tile in enumerate(row):
        if tile == 1:
            Entity(
                model='cube',
                collider='box',
                position=(x * CORRIDOR_WIDTH, WALL_HEIGHT / 2 - 0.5, z * CORRIDOR_WIDTH),
                scale=(CORRIDOR_WIDTH, WALL_HEIGHT, CORRIDOR_WIDTH),
                texture=WALL_TEXTURE,
                color=color.gray
            )

# Create Floor
world_width_units = len(MAZE_LAYOUT[0]) * CORRIDOR_WIDTH
world_depth_units = len(MAZE_LAYOUT) * CORRIDOR_WIDTH
ground = Entity(
    model='plane',
    scale=(world_width_units, 1, world_depth_units),
    collider='mesh',
    texture=FLOOR_TEXTURE,
    texture_scale=(world_width_units / CORRIDOR_WIDTH, world_depth_units / CORRIDOR_WIDTH),
    position=(world_width_units / 2 - CORRIDOR_WIDTH / 2, -0.5, world_depth_units / 2 - CORRIDOR_WIDTH / 2),
    color=color.dark_gray
)

# Create Player
player_start_x = 1 * CORRIDOR_WIDTH + PLAYER_START_OFFSET
player_start_z = 1 * CORRIDOR_WIDTH + PLAYER_START_OFFSET
player = FirstPersonController(
    position=(player_start_x, 0.5, player_start_z),
    collider='box',
    height=PLAYER_HEIGHT,
    jump_height=0,
    speed=WALK_SPEED,
    mouse_sensitivity=Vec2(DEFAULT_SENSITIVITY, DEFAULT_SENSITIVITY),
)
player.collider.scale = (0.5, PLAYER_HEIGHT, 0.5) # Scale collider Y to player height
player.y = 1 # Adjust starting Y based on new height
player.cursor.enabled = False # Disable the reticle


# --- Input and Update Functions ---
def update():
    """Main game update loop."""
    if player:
        if held_keys['shift']:
            player.speed = RUN_SPEED
        else:
            player.speed = WALK_SPEED

# --- Main Execution ---
if __name__ == '__main__':
    app.run()