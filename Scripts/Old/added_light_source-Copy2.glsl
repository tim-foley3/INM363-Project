#define N 500


// x, y position of the light
uniform vec2 lightPosition2;
// Size of light in pixels
uniform float lightSize2;

float terrain(vec2 samplePoint2)
{
    float samplePointAlpha2 = texture(iChannel0, samplePoint2).a;
    float sampleStepped2 = step(0.1, samplePointAlpha2);
    float returnValue2 = 1.0 - sampleStepped2;
    
    // Soften the shadows. Comment out for hard shadows.
    // The closer the first number is to 1.0, the softer the shadows. 
    returnValue2 = mix(0.98, 1.0, returnValue2);
    return returnValue2;
    
}

void mainImage( out vec4 fragColor2, in vec2 fragCoord2 )
{
    // Distance in pixels to the light
    float distanceToLight2 = length(lightPosition2 - fragCoord2);

    // Normalize the fragment coordinate from (0.0, 0.0) to (1.0, 1.0)
    vec2 normalizedFragCoord2 = fragCoord2/iResolution.xy;
    vec2 normalizedLightCoord2 = lightPosition2.xy/iResolution.xy;
    //vec2 normalizedLightCoord2 = lightPosition2.xy/iResolution.xy;

    // Start our mixing variable at 1.0
    float lightAmount2 = 1.0;

    for(float i = 0.0; i < N; i++)
    {
        // A 0.0 - 1.0 ratio between where our current pixel is, and where the light is
        float t = i / N;
        // Grab a coordinate between where we are and the light
        vec2 samplePoint = mix(normalizedFragCoord2, normalizedLightCoord2, t);
        // Is there something there? If so, we'll assume we are in shadow
                float shadowAmount2 = terrain(samplePoint);
        // Multiply the light amount
        //(Multiply in case we want to upgrade to soft shadows)
        lightAmount2 *= shadowAmount2;
        //lightAmount2 *= shadowAmount2;

    }

    // Find out how much light we have based on the distance to our light
    lightAmount2 *= 1.0 - smoothstep(0.0, lightSize2, distanceToLight2);
    //lightAmount2 *= 1.0 - smoothstep(0.0, lightSize2, distanceToLight2);


    // We'll alternate our display between black and whatever is in channel 1
    vec4 blackColor2 = vec4(0.0, 0.0, 0.0, 1.0);

    // Our fragment color will be somewhere between black and channel 1
    // dependent on the value of b.
    fragColor2 = mix(blackColor2, texture(iChannel1, normalizedFragCoord2), lightAmount2);
}




