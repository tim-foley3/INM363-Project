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

    # Create the player
    self.player_sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png",
                                       scale=SPRITE_SCALING)
    self.player_sprite.center_x = 256
    self.player_sprite.center_y = 512
    self.player_list.append(self.player_sprite)

    # Physics engine, so we don't run into walls
    self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
