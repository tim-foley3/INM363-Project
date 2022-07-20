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