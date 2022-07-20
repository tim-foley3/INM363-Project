def load_shader(self):
    # Where is the shader file? Must be specified as a path.
    shader_file_path = Path("step_06.glsl")

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