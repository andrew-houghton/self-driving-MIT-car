def main():
    import pyzed.camera as zcam
    import pyzed.defines as sl
    import pyzed.types as tp
    import pyzed.core as core
    import time
    import pickle
    import numpy as np
    import cv2
    import pygame
    from time import sleep
    import sys

    # start pygame
    pygame.init()

    # count how many joysticks there are...
    joycount = pygame.joystick.get_count()

    # check that a joystick is actually connected.
    if joycount < 1:
        print("No Joystick detected!")
        sys.exit(0)

    # there is atleast one joystick, let's get it.
    j = pygame.joystick.Joystick(0)
    j.init()

    # joystick static storage setup
    axes = [0] * j.get_numaxes()
    buts = [0] * j.get_numbuttons()

    # display which joystick is being used
    print("You are using the {0} controller.".format(j.get_name))
    # CONTROLLER SETUP COMPLETE

    # Create a PyZEDCamera object
    zed = zcam.PyZEDCamera()

    # Create a PyInitParameters object and set configuration parameters
    init_params = zcam.PyInitParameters()
    init_params.depth_mode = sl.PyDEPTH_MODE.PyDEPTH_MODE_PERFORMANCE  # Use PERFORMANCE depth mode
    init_params.coordinate_units = sl.PyUNIT.PyUNIT_MILLIMETER  # Use milliliter units (for depth measurements)

    # Open the camera
    err = zed.open(init_params)
    if err != tp.PyERROR_CODE.PySUCCESS:
        exit(1)

    # Create and set PyRuntimeParameters after opening the camera
    runtime_parameters = zcam.PyRuntimeParameters()
    runtime_parameters.sensing_mode = sl.PySENSING_MODE.PySENSING_MODE_STANDARD  # Use STANDARD sensing mode

    # Capture 50 images and depth, then stop
    i = 0
    num_images=60
    image = core.PyMat()
    depth_for_display = core.PyMat()

    print('Current mode: Capture {} images as fast as possible.\nMerge the images.\nSave to pickle files.'.format(num_images))
    start_time=time.time()
    while i < num_images:
        # A new image is available if grab() returns PySUCCESS
        if zed.grab(runtime_parameters) == tp.PyERROR_CODE.PySUCCESS:
            # Retrieve left image
            zed.retrieve_image(image, sl.PyVIEW.PyVIEW_LEFT)
            # Retrieve left depth
            zed.retrieve_image(depth_for_display,sl.PyVIEW.PyVIEW_DEPTH)

            # JOYSTICK
            pygame.event.pump() # keep everything current
            throttle = (j.get_axis(0)+1)/2 # left stick
            steering = (j.get_axis(4)+1)/2 # right trigger for throttle
            exit_button = j.get_button(9) # Options button exits

            # display joystick data
            # print('throttle {0:.4f} steering {1:.4f} exit_button {2:.4f}'.format(throttle,steering,exit_button))
            if exit_button:
                print('Exit button (options) pressed. Stopping data collection')
                break

            #convert to arrays
            data=image.get_data()
            depth_data=depth_for_display.get_data()

            # Convert images to smaller square images
            square_image_size=500
            data=cv2.resize(data,(square_image_size,square_image_size))
            depth_data=cv2.resize(depth_data,(square_image_size,square_image_size))

            # Display the images on screen
            # cv2.imshow("ZED", data)
            # cv2.waitKey(0)
            # cv2.imshow("ZED", depth_data)
            # cv2.waitKey(0)

            merged = merge_images(data,depth_data)
            print('writing dataset/image_{0}_{1:.4f}_{2:.4f}.pickle'.format(i,throttle,steering))
            pickle.dump(merged,open( 'dataset/image_{0}_{1:.4f}_{2:.4f}.pickle'.format(i,throttle,steering), 'wb' ))
        else:
            print('image collection failed')
        # Increment the loop
        i = i + 1

    j.quit()
    print('Image capture complete')
    print('Total time taken = {}'.format(time.time()-start_time))
    # Close the camera
    zed.close()

def merge_images(data,depth):
    import cv2

    # Store the image dimensions
    data_shape=data.shape
    depth_shape=depth.shape

    # Merge the depth and rgb image into one.
    if data_shape == depth_shape:
        output_data=[]

        # Split the data (left image) into its r,g,b,alpha form respectively
        # Where alpha = visual transparency(0-255)
        red, green, blue, alpha = cv2.split(data)

        # Split the depth image into r,g,b,alpha form
        depth1, depth2, depth3, depth_alpha = cv2.split(depth)

        # merge the original r,g,b with any of depth (as they are all the same in greyscale)
        # visually to a human this will look like a transparent photo
        # but this is encoding depth information into the vector for the neural network
        output_data = cv2.merge((red, green, blue, depth1))

        return output_data
    else:
        #images are different sizes and could not be merged
        print('image capture settings wrong')
        return None

def load_and_display(filename):
    import pickle
    import numpy as np
    from matplotlib import pyplot as plt #note there is an opencv image viewing alternative called imshow and waitkey

    fig, ax = plt.subplots()
    image = pickle.load( open( filename, "rb" ) )
    ax.imshow(image)
    plt.show()

main()
# load_and_display("image_depth0.pickle")