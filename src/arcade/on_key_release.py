def on_key_release(self, key, modifiers):
    """Called when the user releases a key. """

    if key == arcade.key.UP or key == arcade.key.DOWN:
        self.player_sprite.change_y = 0
    elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
        self.player_sprite.change_x = 0