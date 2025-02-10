from compare import main as compare
from compare import parse_arguments

model_path = r"D:\PythonWorkspace\Facial_Recognition\models\20180402-114759.pb"
file1 = "1.jpg"
file2 = "2.jpg"
file3 = "3.jpg"
arg = [model_path, file1, file2, file3]
compare(parse_arguments(arg))

