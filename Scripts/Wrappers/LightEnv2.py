import random
from pathlib import Path
import numpy as np
import os
os.environ["ARCADE_HEADLESS"] = "true"

import arcade
from arcade.experimental import Shadertoy
from arcade.experimental.lights import Light, LightLayer
import pygame
from pygame import Surface
from collections import namedtuple


# Do the math to figure out our screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Game 1: Let There Be Light!"

SPRITE_SCALING = 0.25

# How fast the camera pans to the player. 1.0 is instant.
CAMERA_SPEED = 0.1

PLAYER_MOVEMENT_SPEED = 7
BOMB_COUNT = 25
TORCH_COUNT = 1
PLAYING_FIELD_WIDTH = 800 #1600
PLAYING_FIELD_HEIGHT = 600 #1600
REWARD_COUNT = 1 #TF - Add in reward
END_GAME = False
torch_collected = False

LIGHT_SIZE_BEFORE_COLLECTION = 50 # hyperparameters for light size before and after torch collection
LIGHT_SIZE_AFTER_COLLECTION = 500 # hyperparameters for light size before and after torch collection
LIGHTSTRENGTH = 0.98 #value for strength of shadows between 0,1. Closer to 1, softer the shadow.

fps= 1000


class LightEnv2(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        
        self.time_before_update = 0
        self.time_after_update = 0

        arcade.Window.headless = True

    
        self.episode_score = 0
        self.score_after_update = 0
        self.score_before_update = 0
        self.done = False
            
        self.torch_collected = False
        self.time_taken = 0
        self.switch2_activated = False
        self.switch1_activated = False
        self.switch1_activated_count = 0
        
        # The shader toy and 'channels' we'll be using
        self.shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Sprites and sprite lists
        self.reward = None
        self.player_sprite = None
        self.torch = None #TF add 
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.bomb_list = arcade.SpriteList() #TF add
        self.reward_list = arcade.SpriteList() #TF add
        self.torch_list = arcade.SpriteList() #TF add
        self.switch1_list = arcade.SpriteList() #TF add
        self.switch2_list = arcade.SpriteList() #TF add
        self.physics_engine = None
        
        self.gui_camera = None #TF added gui camera that can be used to draw gui elements
        self.score = 0 #TF added score
        self.scene = None #TF added scene

        self.generate_sprites()
        
        #TF: Load sounds
        self.collect_bomb_sound = arcade.load_sound(":resources:sounds/explosion2.wav")
        self.collect_reward_sound = arcade.load_sound(":resources:sounds/gameover2.wav")
        arcade.set_background_color(arcade.color.WHITE)
        
        #TF Light tutorial
        self.light_layer = None
        # Individual light we move with player, and turn on/off
        self.player_light = None
        LightEnv2.center_window(self) #Display game window in center of pc screen


    def load_shader(self):
        # Where is the shader file? Must be specified as a path.
        shader_file_path = Path("raycasting_shader_game2.glsl")

        # Size of the window
        window_size = self.get_size()

        # Create the shader toy
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )
        self.channel1 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )

        # Assign the frame buffers to the channels
        self.shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.shadertoy.channel_1 = self.channel1.color_attachments[0]
                
    def generate_sprites(self):
        self.scene = arcade.Scene() # TF initialise scene
        self.gui_camera = arcade.Camera(self.width, self.height) #TF initialise GUI camera for displaying score
        self.score = 0 #TF keep track of the score
        
        # -- Set up several columns of walls
        for x in range(0, PLAYING_FIELD_WIDTH, 128):
            for y in range(0, PLAYING_FIELD_HEIGHT, int(128 * SPRITE_SCALING)):
                # Randomly skip a box so the player can find a way through
                if random.randrange(2) > 0:
                    wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", SPRITE_SCALING)
                    wall.center_x = x
                    wall.center_y = y
                    self.wall_list.append(wall)

        # -- Set some hidden bombs in the area
        for i in range(BOMB_COUNT):
            bomb = arcade.Sprite(":resources:images/tiles/bomb.png", 0.25)
            placed = False
            while not placed:
                bomb.center_x = random.randrange(PLAYING_FIELD_WIDTH)
                bomb.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
                if not arcade.check_for_collision_with_list(bomb, self.wall_list):
                    placed = True
            self.bomb_list.append(bomb)
            self.scene.add_sprite("Bombs", bomb) # TF add bombs to scene

            
        # -- Set some switches in the area
        switch1 = arcade.Sprite(":resources:images/tiles/leverLeft.png",
                                           scale=SPRITE_SCALING)
        placed1 = False
        while not placed1:
            switch1.center_x = random.randrange(PLAYING_FIELD_WIDTH)
            switch1.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
            if not arcade.check_for_collision_with_list(switch1, self.wall_list):
                placed1 = True     
                
                
        switch2 = arcade.Sprite(":resources:images/tiles/leverLeft.png",
                                           scale=SPRITE_SCALING)
        placed2 = False
        while not placed2:
            switch2.center_x = random.randrange(PLAYING_FIELD_WIDTH)
            switch2.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
            if not arcade.check_for_collision_with_list(switch2, self.wall_list):
                placed2 = True
                
                
        self.switch1_list.append(switch1)
        self.scene.add_sprite("Switch1", switch1) # TF add switch1 to scene
        self.switch2_list.append(switch2)
        self.scene.add_sprite("Switch2", switch2) # TF add switch2 to scene

            
        #TF Start - adding in reward sprite
        for i in range(REWARD_COUNT):
            self.reward = arcade.Sprite(":resources:images/tiles/signExit.png", 0.25)
            placed = False
            while not placed:
                self.reward.center_x = random.randrange(PLAYING_FIELD_WIDTH)
                self.reward.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
                if not arcade.check_for_collision_with_list(self.reward, self.wall_list):
                    placed = True
            self.reward_list.append(self.reward)
            self.scene.add_sprite("Reward", self.reward) # add reward to scene
        #TF End - adding in reward sprite
        
        # Create the player
        self.player_sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png",
                                           scale=SPRITE_SCALING)
        self.player_sprite.center_x = 256
        self.player_sprite.center_y = 512
        self.player_list.append(self.player_sprite)
        
        
        
        # Create the torch - TF add
        self.torch = arcade.Sprite(":resources:images/tiles/torch1.png",
                                           scale=SPRITE_SCALING)
        placed = False
        while not placed:
            self.torch.center_x = random.randrange(PLAYING_FIELD_WIDTH)
            self.torch.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
            if not arcade.check_for_collision_with_list(self.torch, self.wall_list):
                placed = True             
        self.torch_list.append(self.torch)
        self.scene.add_sprite("Torch", self.torch) # TF add torch to scene

        # Physics engine, so we don't run into walls
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)

    def on_draw(self):

        # Select the channel 0 frame buffer to draw on
        self.channel0.use()
        self.channel0.clear()
        # Draw the walls
        self.wall_list.draw()
        
        self.channel1.use()
        self.channel1.clear()
        # Draw the bombs
        self.bomb_list.draw()
        
        # Draw the switches
        self.switch1_list.draw()
        self.switch2_list.draw()

        
        # TF Start - Draw the reward
        if self.switch2_activated == True: #Green
            if self.switch1_activated_count == 0 and self.torch_collected==True:
                self.reward_list.draw()
            elif self.switch1_activated_count != 0 and self.torch_collected==True: #Green, but red activated at least once
                self.reward_list.draw()
            else:
                pass

        # Draw the walls BEFORE light has been calculated - more realistic.
        self.wall_list.draw()
        
        # Select this window to draw on
        self.use()
        # Clear to background color
        self.clear()

        # Run the shader and render to the window
        if self.torch_collected == False:
            self.shadertoy.program['lightPosition'] = self.torch.position #TF add
            self.shadertoy.program['lightSize'] = LIGHT_SIZE_BEFORE_COLLECTION
            self.shadertoy.program['lightStrength'] = LIGHTSTRENGTH
            self.shadertoy.render()

        elif self.torch_collected == True:
            self.shadertoy.program['lightPosition'] = self.player_sprite.position #TF add
            self.shadertoy.program['lightSize'] = LIGHT_SIZE_AFTER_COLLECTION
            self.shadertoy.program['lightStrength'] = LIGHTSTRENGTH
            self.shadertoy.render()            

        # Draw the walls after light has been calculated
#         self.wall_list.draw()


        #TF Start - Adding camera to display score AFTER light has been calculated
        #Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()

        #Draw our score on the screen, scrolling it with the viewport
        arcade.enable_timings
        self.clock.tick()
        score_text = f"score: {self.score}, time taken: {round(self.time_taken)}, FPS: {round(self.clock.get_fps())}"
        arcade.draw_text(
            score_text,
            10,
            10,
            arcade.csscolor.WHITE,
            18,
        )
        #TF End - Adding camera to display score AFTER light has been calculated

        # Draw the player
        self.player_list.draw()
        self.torch_list.draw()
        
#         image = arcade.get_image()
#         image.save("test.png")
        
    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP:
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.DOWN:
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_sprite.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0

    def on_update(self, delta_time: float):
        """ Movement and game logic """
        self.score_before_update = self.score
        
        self.time_before_update = self.time_taken_reported() #test
        
        self.time_taken += delta_time

        self.time_after_update = self.time_taken_reported() #test
        
        if self.time_after_update - self.time_before_update == 1:
#             print("-1 time penalty to score")
            self.score -= 1 
        # Call update on all sprites
        
        # Keep the player on screen 
        if self.player_sprite.top > self.height:
            self.player_sprite.top = self.height
        if self.player_sprite.right > self.width:
            self.player_sprite.right = self.width
        if self.player_sprite.bottom < 0:
            self.player_sprite.bottom = 0
        if self.player_sprite.left < 0:
            self.player_sprite.left = 0
        
        self.physics_engine.update()
        
        #TF - Start Testing:
        #See if we hit any bombs
        bomb_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Bombs"]
        )
        #See if we hit any rewards
        reward_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Reward"]
        )
        #See if we hit any torches
        torch_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Torch"]
        )
        #See if we hit any switches
        switch1_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Switch1"]
        )
        switch2_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Switch2"]
        )
        #Loop through each bomb we hit (if any) and remove it
        for bomb in bomb_hit_list:
            #Remove the bomb
            bomb.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_bomb_sound)
            #Minus 1 to score
            self.score -= 1
            
        #If reward is hit, then remove it and +100 score.
        for reward in reward_hit_list:
            if self.switch2_activated == True and self.torch_collected==True:
                #Remove the reward
                reward.remove_from_sprite_lists()
                #Play a sound
                arcade.play_sound(self.collect_reward_sound)
                #Plus 100 to score
                self.score += 100
                END_GAME = True #TF - Flag for ending game when reward collected
                print(f"Game completed with a score of: {self.score} at time: {round(self.time_taken)}")
                self.done = True
            
        #If torch is hit, then remove it.
        for torch in torch_hit_list:
            #Remove the torch
            self.torch_collected = True
            torch.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_reward_sound)
            self.physics_engine.update()
            

        #If switch is hit...
        for switch in switch1_hit_list: #Red
            arcade.set_background_color(arcade.color.RED)
            self.switch2_activated = False
            self.switch1_activated = True
            self.switch1_activated_count += 1
            for x in self.reward_list: #Remove reward from reward_list and scene
                x.remove_from_sprite_lists()
                self.scene.remove_sprite_list_by_object(self.scene["Reward"])
                self.scene.add_sprite("Reward", self.reward) # add reward back in to scene 
            
            self.physics_engine.update()
            
        for switch in switch2_hit_list: #Green
            arcade.set_background_color(arcade.color.GREEN)
            self.switch1_activated = False
            self.switch2_activated = True
            if self.switch1_activated_count > 0:
                self.reward_list = arcade.SpriteList() 
                self.reward_list.append(self.reward) #add the reward back into the reward list
                
            self.physics_engine.update()

                        
        #TF attempt to reposition player back to center after bomb collision
        if bomb_hit_list != []:     
            self.player_sprite.center_x = 256 #Might need to paramaterise this to be screen size
            self.player_sprite.center_y = 512 #As resizing window to 80x60 could ruin this
#         TF - End Testing
     
        self.score_after_update = self.score

        
    def reset(self):
        print("resetting")
        """
        This function resets the environment to its original state (time = 0).
        Then it places the agent at start position and exit at a new random location.
        
        It is common practice to return the observations, 
        so that the agent can decide on the first action right after the resetting of the environment.
        
        """
        
        self.time_before_update = 0
        self.time_after_update = 0

        arcade.Window.headless = True
    
        self.episode_score = 0
        self.score_after_update = 0
        self.score_before_update = 0
        self.done = False
    


        self.torch_collected = False
        self.time_taken = 0
        self.switch2_activated = False
        self.switch1_activated = False
        self.switch1_activated_count = 0
        
        # The shader toy and 'channels' we'll be using
        self.shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Sprites and sprite lists
        self.reward = None
        self.player_sprite = None
        self.torch = None #TF add 
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.bomb_list = arcade.SpriteList() #TF add
        self.reward_list = arcade.SpriteList() #TF add
        self.torch_list = arcade.SpriteList() #TF add
        self.switch1_list = arcade.SpriteList() #TF add
        self.switch2_list = arcade.SpriteList() #TF add
        self.physics_engine = None
        
        self.gui_camera = None #TF added gui camera that can be used to draw gui elements
        self.score = 0 #TF added score
        self.scene = None #TF added scene

        arcade.set_background_color(arcade.color.WHITE)

        self.generate_sprites()
        
        #Get the image object of the current window
        obs = arcade.get_image()
        
        self.done = False #set done flag to false ready for next episode
    
        return obs

    def step(self, action):
        
        #Reset episode score to 0 at beginning of step action
        self.step_score = 0
        
        #Move agent in direction chosen by rllib. (input was 0,1,2,3, changed to up,down,left,right).
        if action == 'up':
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
        elif action == 'down':
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        elif action == 'left':
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif action == 'right':
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        
        """ Movement and game logic """
        self.score_before_update = self.score
        
        self.time_before_update = self.time_taken_reported() #test
        
        self.time_taken += 1/60

        self.time_after_update = self.time_taken_reported() #test
        
        if self.time_after_update - self.time_before_update == 1:
#             print("-1 time penalty to score")
            self.score -= 1 
        # Call update on all sprites
        
        # Keep the player on screen 
        if self.player_sprite.top > self.height:
            self.player_sprite.top = self.height
        if self.player_sprite.right > self.width:
            self.player_sprite.right = self.width
        if self.player_sprite.bottom < 0:
            self.player_sprite.bottom = 0
        if self.player_sprite.left < 0:
            self.player_sprite.left = 0
        
        self.physics_engine.update()
        
        #TF - Start Testing:
        #See if we hit any bombs
        bomb_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Bombs"]
        )
        #See if we hit any rewards
        reward_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Reward"]
        )
        #See if we hit any torches
        torch_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Torch"]
        )
        #See if we hit any switches
        switch1_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Switch1"]
        )
        switch2_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Switch2"]
        )
        #Loop through each bomb we hit (if any) and remove it
        for bomb in bomb_hit_list:
            #Remove the bomb
            bomb.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_bomb_sound)
            #Minus 1 to score
            self.score -= 1
            
        #If reward is hit, then remove it and +100 score.
        for reward in reward_hit_list:
            if self.switch2_activated == True and self.torch_collected == True:
                #Remove the reward
                reward.remove_from_sprite_lists()
                #Play a sound
                arcade.play_sound(self.collect_reward_sound)
                #Plus 100 to score
                self.score += 100
                END_GAME = True #TF - Flag for ending game when reward collected
                print(f"Game completed with a score of: {self.score} at time: {round(self.time_taken)}")
                self.done = True
            
        #If torch is hit, then remove it.
        for torch in torch_hit_list:
            #Remove the torch
            self.torch_collected = True
            torch.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_reward_sound)
            self.physics_engine.update()
            

        #If switch is hit...
        for switch in switch1_hit_list: #Red
            arcade.set_background_color(arcade.color.RED)
            self.switch2_activated = False
            self.switch1_activated = True
            self.switch1_activated_count += 1
            for x in self.reward_list: #Remove reward from reward_list and scene
                x.remove_from_sprite_lists()
                self.scene.remove_sprite_list_by_object(self.scene["Reward"])
                self.scene.add_sprite("Reward", self.reward) # add reward back in to scene 
            
            #Play a sound
            self.physics_engine.update()
            
        for switch in switch2_hit_list: #Green
            arcade.set_background_color(arcade.color.GREEN)
            self.switch1_activated = False
            self.switch2_activated = True
            if self.switch1_activated_count > 0:
                self.reward_list = arcade.SpriteList() 
                self.reward_list.append(self.reward) #add the reward back into the reward list
            self.physics_engine.update()

                        
        #TF attempt to reposition player back to center after bomb collision
        if bomb_hit_list != []:     
            self.player_sprite.center_x = 256 #Might need to paramaterise this to be screen size
            self.player_sprite.center_y = 512 #As resizing window to 80x60 could ruin this
#         TF - End Testing
     
        self.score_after_update = self.score
        
        
        # Calculate the reward for the particular action (0, -1 or +100).
        self.step_score = self.score_after_update - self.score_before_update

        reward = self.step_score #this needs to be old episode score - new episode score

        obs = arcade.get_image()
        
        self.clock.tick()
        fps_check = round(self.clock.get_fps())   

        return obs, reward, self.done, self.torch_collected, fps_check
    
    def stop_movement(self, action):
        print("stopping movement")
        """Called when the player makes a move. """

        if action == 'up' or action == 'down':
            self.player_sprite.change_y = 0
        elif action == 'left' or action == 'right':
            self.player_sprite.change_x = 0
    
    def time_taken_reported(self):
        x = round(self.time_taken)
        return x
        
def main():
    """Main Function"""
    window = LightEnv2(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run() #check refactoring branch of Simple Playgrounds for faster running in headless

if __name__ == "__main__":
    main()
    
    