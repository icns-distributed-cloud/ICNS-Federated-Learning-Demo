
from numpy import newaxis
import argparse

from keras.models import Sequential, load_model
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import array_to_img

# fl_path = os.path.abspath('.')
# if fl_path not in sys.path:
#     sys.path.append(fl_path)

def setup_parser():
    """
    Sets up the parser for Python script

    :return: a command line parser
    :rtype: argparse.ArgumentParser
    """
    p = argparse.ArgumentParser(description="Test mnist trained model")
    p.add_argument("--model_path", "-mp", help="Path to trained model", 
                    required=True)
    p.add_argument("--image_path", "-ip", help="Path to test image", 
                    required=True)

    
    return p


if __name__ == '__main__':
    # Parse command line options
    parser = setup_parser()
    args = parser.parse_args()

    model_path = args.model_path
    img_path = args.image_path

    # load the image
    img = load_img(img_path, grayscale=True)
    print("Orignal:" ,type(img))

    # convert to numpy array
    img_array = img_to_array(img)
    print("NumPy array info:") 
    print(type(img_array))    
    print("type:",img_array.dtype)
    print("shape:",img_array.shape)
    img_array1 = img_array[newaxis, :, :, :]
    print("shape:",img_array1.shape)


    trained_model = load_model(model_path)
    predicted_classe = trained_model.predict_classes(img_array1)
    print("predicted digit {}".format(predicted_classe[0]))


