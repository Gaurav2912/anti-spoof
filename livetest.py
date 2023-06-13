import os
import cv2
import numpy as np
import argparse
import warnings
import time, imutils

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from imutils.video import VideoStream
from imutils.video import FPS
from src.utility import parse_model_name
warnings.filterwarnings('ignore')

# SAMPLE_IMAGE_PATH = "./images/sample/"

def test(image, model_dir, device_id):
    """
    To test the face in image is real or fake.
    """
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    # image = cv2.imread(SAMPLE_IMAGE_PATH + image_name)
    image_bbox = model_test.get_bbox(image)
    prediction = np.zeros((1, 3))
    test_speed = 0
    # sum the prediction from single model's result
    for model_name in os.listdir(model_dir):
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        param = {
            "org_img": image,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False
        img = image_cropper.crop(**param)
        start = time.time()
        prediction += model_test.predict(img, os.path.join(model_dir, model_name))
        test_speed += time.time()-start

    # draw result of prediction
    label = np.argmax(prediction)
    value = prediction[0][label]/2


    return label, value, test_speed, image_bbox
    

    # format_ = os.path.splitext(image_name)[-1]
    # result_image_name = image_name.replace(format_, "_result" + format_)
    # cv2.imwrite(SAMPLE_IMAGE_PATH + result_image_name, image)


if __name__ == "__main__":

    vs  = VideoStream(src=0, framerate= 32).start()
    fps = FPS().start()

    while True:

        frame = vs.read()
        frame = imutils.resize(frame, width=500)

        desc = "test"
        parser = argparse.ArgumentParser(description=desc)
        parser.add_argument(
            "--device_id",
            type=int,
            default=0,
            help="which gpu id, [0/1/2/3]")
        parser.add_argument(
            "--model_dir",
            type=str,
            default="./resources/anti_spoof_models",
            help="model_lib used to test")
        parser.add_argument(
            "--image_name",
            type=str,
            default= frame,
            help="image used to test")
        args = parser.parse_args()
        label, value , test_speed , image_bbox = test(args.image_name, args.model_dir, args.device_id)

        if label == 1:
            # print("Image '{}' is Real Face. Score: {:.2f}.".format(image_name, value))
            result_text = "RealFace Score: {:.2f}".format(value)
            color = (255, 0, 0)
        else:
            # print("Image '{}' is Fake Face. Score: {:.2f}.".format(image_name, value))
            result_text = "FakeFace Score: {:.2f}".format(value)
            color = (0, 0, 255)
        print("Prediction cost {:.2f} s".format(test_speed))
        
        cv2.rectangle(
            frame,
            (image_bbox[0], image_bbox[1]),
            (image_bbox[0] + image_bbox[2], image_bbox[1] + image_bbox[3]),
            color, 2)
        cv2.putText(
            frame,
            result_text,
            (image_bbox[0], image_bbox[1] - 5),
            cv2.FONT_HERSHEY_COMPLEX, frame.shape[0]/1024, color)
        
        cv2.imshow("anti_sp", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()