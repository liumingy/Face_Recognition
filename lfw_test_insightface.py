import time
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from matplotlib import pyplot as plt

# Initialize face analysis model
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])  # Use 'CUDAExecutionProvider' for GPU
app.prepare(ctx_id=-1)  # ctx_id=-1 for CPU, 0 for GPU


def get_face_embedding(image):
    """Extract face embedding from an image"""
    faces = app.get(image)

    if len(faces) < 1:
        raise ValueError("No faces detected in the image")
    # if len(faces) > 1:
    #     print("Warning: Multiple faces detected. Using first detected face")

    return faces[0].embedding


def compare_faces(emb1, emb2, threshold=0.65):  # Adjust this threshold according to your usecase.
    """Compare two embeddings using cosine similarity"""
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    return similarity, similarity > threshold


def face_verification(img_pairs_list):
    # 设置可视化进度条相关参数
    jd = '\r   %2d%%\t [%s%s]'
    bar_num_total = 50
    total_num = len(img_pairs_list)
    result, dist = [], []

    for i in range(len(img_pairs_list)):

        # 画进度条
        if i % round(total_num / bar_num_total) == 0 or i == total_num - 1:
            bar_num_alright = round(bar_num_total * i / total_num)
            alright = '#' * bar_num_alright
            not_alright = '□' * (bar_num_total - bar_num_alright)
            percent = (bar_num_alright / bar_num_total) * 100
            print(jd % (percent, alright, not_alright), end='')

        # 读取一对人脸图像
        img_pairs = img_pairs_list[i]
        img1 = cv2.imread(img_pairs[0])
        img2 = cv2.imread(img_pairs[1])
        try:
            # Get embeddings
            emb1 = get_face_embedding(img1)
            emb2 = get_face_embedding(img2)

            # Compare faces
            similarity_score, is_same_person = compare_faces(emb1, emb2)

            # 计算两个人脸向量的距离
            dist.append(similarity_score)

            # 根据得出的人脸间的距离，判断是否属于同一个人
            if is_same_person:
                result.append(1)
            else:
                result.append(0)

        except Exception as e:
            dist.append(-1)
            result.append(-1)
            print(f"Error: {str(e)}")
    return result, dist


def get_img_pairs_list(pairs_txt_path, img_path):
    """ 指定图片组合及其所在文件，返回各图片对的绝对路径
        Args:
            pairs_txt_path：图片pairs文件，里面是6000对图片名字的组合
            img_path：图片所在文件夹
        return:
            img_pairs_list：深度为2的list，每一个二级list存放的是一对图片的绝对路径
    """
    file = open(pairs_txt_path)
    img_pairs_list, labels = [], []
    while 1:
        img_pairs = []
        line = file.readline().replace('\n', '')
        if line == '':
            break
        line_list = line.split('\t')
        if len(line_list) == 3:
            # 图片路径示例：
            # 'C:\Users\thinkpad1\Desktop\image_set\lfw_funneled\Tina_Fey\Tina_Fey_0001.jpg'
            img_pairs.append(
                img_path + '\\' + line_list[0] + '\\' + line_list[0] + '_' + ('000' + line_list[1])[-4:] + '.jpg')
            img_pairs.append(
                img_path + '\\' + line_list[0] + '\\' + line_list[0] + '_' + ('000' + line_list[2])[-4:] + '.jpg')
            labels.append(1)
        elif len(line_list) == 4:
            img_pairs.append(
                img_path + '\\' + line_list[0] + '\\' + line_list[0] + '_' + ('000' + line_list[1])[-4:] + '.jpg')
            img_pairs.append(
                img_path + '\\' + line_list[2] + '\\' + line_list[2] + '_' + ('000' + line_list[3])[-4:] + '.jpg')
            labels.append(0)
        else:
            continue

        img_pairs_list.append(img_pairs)
    return img_pairs_list, labels


def roc(dist, labels):
    TP_list, TN_list, FP_list, FN_list, TPR, FPR = [], [], [], [], [], []
    for t in range(180):
        threh = 0.1 + t * 0.01

        TP, TN, FP, FN = 0, 0, 0, 0
        for i in range(len(dist)):
            if labels[i] == 1 and dist[i] != -1:
                if dist[i] < threh:
                    TP += 1
                else:
                    FN += 1
            elif labels[i] == 0 and dist[i] != -1:
                if dist[i] >= threh:
                    TN += 1
                else:
                    FP += 1
        TP_list.append(TP)
        TN_list.append(TN)
        FP_list.append(FP)
        FN_list.append(FN)
        TPR.append(TP / (TP + FN))
        FPR.append(FP / (FP + TN))
    return TP_list, TN_list, FP_list, FN_list, TPR, FPR


if __name__ == '__main__':
    pairs_txt_path = r"D:\PythonWorkspace\Facial_Recognition\lfw_funneled\pairs.txt"
    img_path = r"D:\PythonWorkspace\Facial_Recognition\lfw_funneled"
    img_pairs_list, labels = get_img_pairs_list(pairs_txt_path, img_path)

    result, dist = face_verification(img_pairs_list)

    num_right, num_total = 0, 0
    num_total = len([r for r in result if r != -1])
    num_right = len([result[i] for i in range(len(result)) if result[i] == labels[i]])

    print("人脸验证测试完毕")
    # 阈值为1.1，共5957对人脸，准确率80.4264%
    print("阈值为1.1，共%d对人脸，准确率%2.4f%%" % (num_total, round(100 * num_right / num_total, 4)))

    TP_list, TN_list, FP_list, FN_list, TPR, FPR = roc(dist, labels)
    plt.plot(FPR, TPR, label='Roc')
    plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Luck')
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    plt.legend()

    plt.plot(np.linspace(0.1, 1.89, 180), TP_list, label='TP')
    plt.plot(np.linspace(0.1, 1.89, 180), TN_list, label='TN')
    plt.plot(np.linspace(0.1, 1.89, 180), FP_list, label='FP')
    plt.plot(np.linspace(0.1, 1.89, 180), FN_list, label='FN')
    plt.legend()