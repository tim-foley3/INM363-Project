def on_update(self, delta_time):
    """ Movement and game logic """

    # Call update on all sprites (The sprites don't do much in this
    # example though.)
    self.physics_engine.update()
    #TF testing:
    #See if we hit any bombs
    bomb_hit_list = arcade.check_for_collision_with_list(
        self.player_sprite, self.scene["Bombs"]
    )

    #Loop through each bomb we hit (if any) and remove it
    for bomb in bomb_hit_list:
        #Remove the bomb
        bomb.remove_from_sprite_lists()
        #Play a sound
        arcade.play_sound(self.collect_bomb_sound)
        #Minus 1 to score
        self.score -= 1