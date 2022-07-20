def __init__(self, width, height, title):
    super().__init__(width, height, title)

    # The shader toy and 'channels' we'll be using
    self.shadertoy = None
    self.channel0 = None
    self.channel1 = None
    self.load_shader()

    # Sprites and sprite lists
    self.player_sprite = None
    self.wall_list = arcade.SpriteList()
    self.player_list = arcade.SpriteList()
    self.bomb_list = arcade.SpriteList()
    self.physics_engine = None

    self.gui_camera = None #TF added gui camera that can be used to draw gui elements
    self.score = 0 #TF added score
    self.scene = None #TF added scene

    self.generate_sprites()

    #TF: Load sounds
    self.collect_bomb_sound = arcade.load_sound(":resources:sounds/explosion2.wav")

    arcade.set_background_color(arcade.color.ARMY_GREEN)