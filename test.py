import os
import cv2
from compare import main as compare

model_path = r"D:\PythonWorkspace\Facial_Recognition\models\20180402-114759.pb"
file1 = "1.jpg"
file2 = "2.jpg"
file3 = "3.jpg"
file4 = "4.jpg"
file5 = "5.jpg"
image1 = cv2.cvtColor(cv2.imread(os.path.expanduser(file1)), cv2.COLOR_BGR2RGB)
image2 = cv2.cvtColor(cv2.imread(os.path.expanduser(file2)), cv2.COLOR_BGR2RGB)
image3 = cv2.cvtColor(cv2.imread(os.path.expanduser(file3)), cv2.COLOR_BGR2RGB)
image4 = cv2.cvtColor(cv2.imread(os.path.expanduser(file4)), cv2.COLOR_BGR2RGB)
image5 = cv2.cvtColor(cv2.imread(os.path.expanduser(file5)), cv2.COLOR_BGR2RGB)
images = [image1, image2, image3, image4, image5]
compare(model_path, images)

