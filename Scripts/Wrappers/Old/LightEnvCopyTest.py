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
BOMB_COUNT = 50
TORCH_COUNT = 1
PLAYING_FIELD_WIDTH = 800 #1600
PLAYING_FIELD_HEIGHT = 600 #1600
REWARD_COUNT = 1 #TF - Add in reward
END_GAME = False
torch_collected = False



#TF things for wrapper Start


# Convenient data structure to hold information about actions
Action = namedtuple('Action', 'name index delta_i delta_j')

up = Action('up', 0, -1, 0)
down = Action('down', 1, 1, 0)    
left = Action('left', 2, 0, -1)    
right = Action('right', 3, 0, 1)    

index_to_actions = {}
for action in [up, down, left, right]:
    index_to_actions[action.index] = action


#TF things for wrapper End
class LightEnv(arcade.Window):

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        
        
#         pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
#         self.img = Surface((SCREEN_WIDTH, SCREEN_HEIGHT))


        headless = True

        self.frame = 0
    
        self.episode_score = 0
        self.score_after_update = 0
        self.score_before_update = 0
        self.done = False
    
        self.camera = None
        
        self.torch_collected = False
        self.time_taken = 0

        # The shader toy and 'channels' we'll be using
        self.shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Sprites and sprite lists
        self.player_sprite = None
        self.torch = None #TF add 
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.bomb_list = arcade.SpriteList() #TF add
        self.reward_list = arcade.SpriteList() #TF add
        self.torch_list = arcade.SpriteList() #TF add
        self.physics_engine = None
        
        self.gui_camera = None #TF added gui camera that can be used to draw gui elements
        self.score = 0 #TF added score
        self.scene = None #TF added scene

        self.generate_sprites()
        
        #TF: Load sounds
        self.collect_bomb_sound = arcade.load_sound(":resources:sounds/explosion2.wav")
        self.collect_reward_sound = arcade.load_sound(":resources:sounds/gameover2.wav")
        arcade.set_background_color(arcade.color.AMARANTH)
        
        #TF Light tutorial
        self.light_layer = None
        # Individual light we move with player, and turn on/off
        self.player_light = None
        LightEnv.center_window(self) #Display game window in center of pc screen


    def load_shader(self):
        print("Shader 1 loading")
        # Where is the shader file? Must be specified as a path.
#         shader_file_path = Path("step_06.glsl")
        shader_file_path = Path("added_light_source-Copy.glsl")

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
        
        # Load shader 2
#         self.load_shader2()
        
    def generate_sprites(self):
        self.scene = arcade.Scene() # TF initialise scene
        self.camera = arcade.Camera(SCREEN_WIDTH,SCREEN_HEIGHT)
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

            
        #TF Start - adding in reward sprite
        for i in range(REWARD_COUNT):
            reward = arcade.Sprite(":resources:images/tiles/signExit.png", 0.25)
            placed = False
            while not placed:
                reward.center_x = random.randrange(PLAYING_FIELD_WIDTH)
                reward.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
                if not arcade.check_for_collision_with_list(reward, self.wall_list):
                    placed = True
            self.reward_list.append(reward)
            self.scene.add_sprite("Reward", reward) # add reward to scene
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

        
#         #TF Start - add the torch (for multiple torches)
#         for i in range(TORCH_COUNT):
#             torch = arcade.Sprite(":resources:images/tiles/torch1.png",
#                                            scale=SPRITE_SCALING)
#             placed = False
#             while not placed:
#                 torch.center_x = random.randrange(PLAYING_FIELD_WIDTH)
#                 torch.center_y = random.randrange(PLAYING_FIELD_HEIGHT)
#                 if not arcade.check_for_collision_with_list(torch, self.wall_list):
#                     placed = True
#             self.torch_list.append(torch)
#             self.scene.add_sprite("Torch", torch) # add torch to scene
#         #TF End - add the torch

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
        
        # TF Start - Draw the reward
        self.reward_list.draw()
        
        # TF Start - Draw the torch
#         self.torch_list.draw()

        # Draw the walls BEFORE light has been calculated - more realistic.
        self.wall_list.draw()
        
        # Select this window to draw on
        self.use()
        # Clear to background color
        self.clear()

        # Run the shader and render to the window
        if self.torch_collected == False:
            self.shadertoy.program['lightPosition'] = self.torch.position #TF add
            self.shadertoy.program['lightSize'] = 50
#             self.shadertoy.program['lightPosition'] = self.player_sprite.position
#             self.shadertoy.program['lightSize'] = 150
            self.shadertoy.render()
        elif self.torch_collected == True:
            self.shadertoy.program['lightPosition'] = self.player_sprite.position #TF add
            self.shadertoy.program['lightSize'] = 500
#             self.shadertoy.program['lightPosition2'] = self.player_sprite.position
#             self.shadertoy.program['lightSize2'] = 500
            self.shadertoy.render()            

        # Draw the walls after light has been calculated
#         self.wall_list.draw()

        self.camera.use()

        #TF Start - Adding camera to display score AFTER light has been calculated
        #Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()
        
        #Draw our score on the screen, scrolling it with the viewport
        score_text = f"score: {self.score}, time taken: {round(self.time_taken)}"

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

    def on_update(self, delta_time):
        """ Movement and game logic """
        self.score_before_update = self.score
        self.time_taken += delta_time

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        
        # Keep the player on screen -TF add from https://realpython.com/arcade-python-game-framework/#drawing-on-the-window
        if self.player_sprite.top > self.height:
            self.player_sprite.top = self.height
        if self.player_sprite.right > self.width:
            self.player_sprite.right = self.width
        if self.player_sprite.bottom < 0:
            self.player_sprite.bottom = 0
        if self.player_sprite.left < 0:
            self.player_sprite.left = 0
        
        self.physics_engine.update()
#         self.shadertoy.render()
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
        
        #Loop through each bomb we hit (if any) and remove it
        for bomb in bomb_hit_list:
            #Remove the bomb
            bomb.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_bomb_sound)
            #Minus 1 to score
            self.score -= 1
            print("You have hit a bomb!")
            test_obs = arcade.get_image()
            test_obs.show()


        #If reward is hit, then remove it and +100 score.
        for reward in reward_hit_list:
            #Remove the reward
            reward.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_reward_sound)
            #Plus 100 to score
            self.score += 100
            END_GAME = True #TF - Flag for ending game when reward collected
            print(f"Game completed with a score of: {self.score} at time: {round(self.time_taken)}")
            self.done = True
#             TF test of reset to be used with wrapper
            print("Running self.reset()")
            self.reset()
            print("self.reset() completed")
#             TF test of reset to be used with wrapper END
            
        #If torch is hit, then remove it.
        for torch in torch_hit_list:
            #Remove the torch
            self.torch_collected = True #Important - to change shader to widen light radius in on_draw()
            torch.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_reward_sound)
            self.physics_engine.update()
#             pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

            test_obs = arcade.get_image()
            test_obs.show()
            


                        
        #TF attempt to reposition player back to center after bomb collision
        if bomb_hit_list != []:     
            self.player_sprite.center_x = 256 #Might need to paramaterise this to be screen size
            self.player_sprite.center_y = 512 #As resizing window to 80x60 could ruin this
            #Should be ok not to parameterise actually as game calulcated as normal then passed and
            #converted to 80x60 in the wrapper, so it's all scaled.
#         TF - End Testing
     
        self.score_after_update = self.score
#         print("self.score after update: ", self.score_after_update)

        self.frame += 1
        
    def reset(self):
#         print("resetting")
        """
        This function resets the environment to its original state (time = 0).
        Then it places the agent and exit at new random locations.
        
        It is common practice to return the observations, 
        so that the agent can decide on the first action right after the resetting of the environment.
        
        """
        
#         arcade.close_window()
#         arcade.set_window()
#         arcade.finish_render()

        self.torch_collected = False
        self.time_taken = 0

        # The shader toy and 'channels' we'll be using
        self.shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Sprites and sprite lists
        self.player_sprite = None
        self.torch = None #TF add 
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.bomb_list = arcade.SpriteList() #TF add
        self.reward_list = arcade.SpriteList() #TF add
        self.torch_list = arcade.SpriteList() #TF add
        self.physics_engine = None
        
        self.gui_camera = None #TF added gui camera that can be used to draw gui elements
        self.score = 0 #TF added score
        self.scene = None #TF added scene

        self.generate_sprites()
        
#         obs = self.render("state_pixels")
#         obs = arcade.get_window()
#         obs = arcade.Window.current_view
        
        
#         obs = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
#         obs = LightEnv.current_view
#         obs = arcade.get_window()
#         obs = arcade.set_window(LightEnv)
#         obs = self.camera
#         obs = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
#         print("obs: ", obs)
        
#         obs2 = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), obs)
        obs = arcade.get_image()
#         obsarray = np.array(obs)
#         obsarray2 =  np.asarray(obs)
#         print("obsarray: ", obsarray.shape)
#         print("obsarray2: ", obsarray2.shape)
#         print(obsarray)
#         obs3.save('screenshot.png', 'PNG')        
#         print(obs)
#         obs.show()
#         pygame.image.save(obs3, "test.jpeg")
#         print("obs shape: ", obs.shape)
#         obstest = self._create_image_array(obs, (SCREEN_WIDTH, SCREEN_HEIGHT))
#         print(obs)
#         Once I've figured out how to represent observations, will need to return obs here.
#         test = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
#         test2 = pygame.Surface.blit(obs,test)
#         print(test2)
        
        self.done = False
    
        return obs

    def step(self, action):
#         print("stepping")
        self.episode_score = 0
        #Move agent in direction chosen by rllib. (input was 0,1,2,3, changed to up,down,left,right).
        if action == 'up':
            self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
        elif action == 'down':
            self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        elif action == 'left':
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif action == 'right':
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        
        # Now stop movement after one action has been made to stop from flying across the screen.
#         self.stop_movement(action) #Might need to make this a GUIWrapper function too
        
#         self.on_update()
        
        self.episode_score = self.score_after_update - self.score_before_update
        # Calculate the reward for the particular action (0, -1 or +100).
        reward = self.episode_score #this needs to be old episode score - new episode score
#         print("step in game reward: ", reward)
#         self.engine.update_observations()
#         obs = ???
#         obs = self.render("state_pixels")
        obs = arcade.get_image()
        # How do I calculate the obs!!? Think this is the last bit I'm stuck on before i try running
        # the wrapper for real.
        
        return obs, reward, self.done
    
    def stop_movement(self, action):
#         print("stopping movement")
        """Called when the player makes a move. """

        if action == 'up' or action == 'down':
            self.player_sprite.change_y = 0
        elif action == 'left' or action == 'right':
            self.player_sprite.change_x = 0
    
    
    def update(self):
#         print("Updating")
        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        
        # Keep the player on screen -TF add from https://realpython.com/arcade-python-game-framework/#drawing-on-the-window
        if self.player_sprite.top > self.height:
            self.player_sprite.top = self.height
        if self.player_sprite.right > self.width:
            self.player_sprite.right = self.width
        if self.player_sprite.bottom < 0:
            self.player_sprite.bottom = 0
        if self.player_sprite.left < 0:
            self.player_sprite.left = 0
        
        self.physics_engine.update()
#         self.shadertoy.render()
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
        
        #Loop through each bomb we hit (if any) and remove it
        for bomb in bomb_hit_list:
            #Remove the bomb
            bomb.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_bomb_sound)
            #Minus 1 to score
            self.score -= 1
            test_obs = arcade.get_image()
            test_obs.show()


        #If reward is hit, then remove it and +100 score.
        for reward in reward_hit_list:
            #Remove the reward
            reward.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_reward_sound)
            #Plus 100 to score
            self.score += 100
            END_GAME = True #TF - Flag for ending game when reward collected
            print(f"Game completed with a score of: {self.score} at time: {round(self.time_taken)}")
            self.done = True
#             TF test of reset to be used with wrapper
            print("Running self.reset()")
            self.reset()
            print("self.reset() completed")
#             TF test of reset to be used with wrapper END
            
        #If torch is hit, then remove it.
        for torch in torch_hit_list:
            #Remove the torch
            self.torch_collected = True #Important - to change shader to widen light radius in on_draw()
            torch.remove_from_sprite_lists()
            #Play a sound
            arcade.play_sound(self.collect_reward_sound)
            self.physics_engine.update()
#             pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

            test_obs = arcade.get_image()
            test_obs.show()
            


                        
        #TF attempt to reposition player back to center after bomb collision
        if bomb_hit_list != []:     
            self.player_sprite.center_x = 256 #Might need to paramaterise this to be screen size
            self.player_sprite.center_y = 512 #As resizing window to 80x60 could ruin this
            #Should be ok not to parameterise actually as game calulcated as normal then passed and
            #converted to 80x60 in the wrapper, so it's all scaled.
#         TF - End Testing
     
        self.score_after_update = self.score
#         print("self.score after update: ", self.score_after_update)

        self.frame += 1
    
#     def render(self, mode="state_pixels"):
#         self.surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) #image object of the current screen
#         if mode == "state_pixels":
#             return self._create_image_array(self.surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
#         window = LightEnv(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
#     def _create_image_array(self, screen, size):
#         #Might want to try surfarray.pixels2d instead
#         scaled_screen = pygame.transform.smoothscale(screen, size)
#         return np.transpose(
#             np.array(pygame.surfarray.pixels3d(scaled_screen)), axes=(1, 0, 2)
#         )

        
def main():
    """Main Function"""
    window = LightEnv(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run() #check refactoring branch of Simple Playgrounds for faster running in headless

if __name__ == "__main__":
    main()
    