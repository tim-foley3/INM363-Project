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

    # Select this window to draw on
    self.use()
    # Clear to background color
    self.clear()


    # Run the shader and render to the window
    self.shadertoy.program['lightPosition'] = self.player_sprite.position
    self.shadertoy.program['lightSize'] = 300
    self.shadertoy.render()

    # Draw the walls after light has been calculated
    self.wall_list.draw()

    #TF: Adding camera to display score AFTER light has been calculated
    #Activate the GUI camera before drawing GUI elements
    self.gui_camera.use()

    #Draw our score on the screen, scrolling it with the viewport
    score_text = f"score: {self.score}"
    arcade.draw_text(
        score_text,
        10,
        10,
        arcade.csscolor.WHITE,
        18,
    )

    # Draw the player
    self.player_list.draw()
