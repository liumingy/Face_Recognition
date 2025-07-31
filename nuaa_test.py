import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
import tensorflow as tf
from align import detect_face
from camera import align_face
from real_face import is_real_face


def calculate_mean(value_list):
    """
    计算列表中元素的平均值
    
    参数:
        value_list: 数值列表
        
    返回:
        列表元素的平均值，如果列表为空则返回0
    """
    if not value_list:
        return 0
    return sum(value_list) / len(value_list)


def load_client_path(nuaa_dir_path, nuaa_client_path):
    """
    加载客户端图像路径列表
    
    参数:
        nuaa_dir_path: NUAA数据集根目录
        nuaa_client_path: 包含客户端文件相对路径的txt文件
        
    返回:
        包含完整客户端图像路径的列表
    """
    client_paths = []
    
    try:
        # 打开并读取客户端路径文件
        with open(nuaa_client_path, 'r') as f:
            lines = f.readlines()
            
        # 处理每一行，构建完整路径
        for line in lines:
            # 移除行尾可能的换行符和空格
            file_path = line.strip()
            if file_path:
                # 构建完整路径: nuaa_dir_path/ClientRaw/XXX
                full_path = f"{nuaa_dir_path}/ClientRaw/{file_path}"
                client_paths.append(full_path)
                
        print(f"成功加载 {len(client_paths)} 个客户端图像路径")
    except Exception as e:
        print(f"加载客户端路径时出错: {str(e)}")
    
    return client_paths

def load_imposter_path(nuaa_dir_path, nuaa_imposter_path):
    """
    加载冒充者图像路径列表
    
    参数:
        nuaa_dir_path: NUAA数据集根目录
        nuaa_imposter_path: 包含冒充者文件相对路径的txt文件
        
    返回:
        包含完整冒充者图像路径的列表
    """
    imposter_paths = []
    
    try:
        # 打开并读取冒充者路径文件
        with open(nuaa_imposter_path, 'r') as f:
            lines = f.readlines()
            
        # 处理每一行，构建完整路径
        for line in lines:
            # 移除行尾可能的换行符和空格
            file_path = line.strip()
            if file_path:
                # 构建完整路径: nuaa_dir_path/ImposterRaw/XXX
                full_path = f"{nuaa_dir_path}/ImposterRaw/{file_path}"
                imposter_paths.append(full_path)
                
        print(f"成功加载 {len(imposter_paths)} 个冒充者图像路径")
    except Exception as e:
        print(f"加载冒充者路径时出错: {str(e)}")
    
    return imposter_paths

def calculate_metrics(client_scores, imposter_scores, threshold, fn_count, tn_count):
    """
    计算给定阈值下的TPR和FPR
    
    参数:
        client_scores: 真实人脸被判断为真实人脸时的置信度列表
        imposter_scores: 冒充者人脸被判断为真实人脸时的置信度列表
        threshold: 阈值
        fn_count: 直接被判定为虚假人脸的真实人脸数量
        tn_count: 直接被判定为虚假人脸的冒充者人脸数量
        
    返回:
        tpr: 真阳性率
        fpr: 假阳性率
    """
    # 对于真实人脸，当置信度大于阈值时判定为真实人脸
    tp = sum(1 for score in client_scores if score > threshold)
    fn = sum(1 for score in client_scores if score <= threshold) + fn_count
    
    # 对于冒充者人脸，当置信度大于阈值时判定为真实人脸（错误判定）
    fp = sum(1 for score in imposter_scores if score > threshold)
    tn = sum(1 for score in imposter_scores if score <= threshold) + tn_count
    
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    return tpr, fpr

def find_optimal_threshold(client_scores, imposter_scores, fn_count, tn_count, target_fpr=0.001):
    """
    寻找最优阈值，使得FPR <= target_fpr且TPR最大
    
    参数:
        client_scores: 真实人脸被判断为真实人脸时的置信度列表
        imposter_scores: 冒充者人脸被判断为真实人脸时的置信度列表
        fn_count: 直接被判定为虚假人脸的真实人脸数量
        tn_count: 直接被判定为虚假人脸的冒充者人脸数量
        target_fpr: 目标FPR值
        
    返回:
        optimal_threshold: 最优阈值
        optimal_tpr: 对应的TPR值
    """
    all_scores = sorted(set(client_scores + imposter_scores))
    optimal_threshold = None
    optimal_tpr = 0
    
    for threshold in all_scores:
        tpr, fpr = calculate_metrics(client_scores, imposter_scores, threshold, fn_count, tn_count)
        if fpr <= target_fpr and tpr > optimal_tpr:
            optimal_threshold = threshold
            optimal_tpr = tpr
    
    return optimal_threshold, optimal_tpr

def plot_roc_curve(client_scores, imposter_scores, fn_count, tn_count):
    """
    绘制ROC曲线并计算AUC值
    
    参数:
        client_scores: 真实人脸被判断为真实人脸时的置信度列表
        imposter_scores: 冒充者人脸被判断为真实人脸时的置信度列表
        fn_count: 直接被判定为虚假人脸的真实人脸数量
        tn_count: 直接被判定为虚假人脸的冒充者人脸数量
    """
    # 获取所有可能的阈值
    all_scores = sorted(set(client_scores + imposter_scores), reverse=True)
    tprs = []
    fprs = []
    
    # 添加起点(0,0)
    tprs.append(0)
    fprs.append(0)
    
    # 计算每个阈值对应的TPR和FPR
    for threshold in all_scores:
        tpr, fpr = calculate_metrics(client_scores, imposter_scores, threshold, fn_count, tn_count)
        tprs.append(tpr)
        fprs.append(fpr)
    
    # 添加终点(1,1)
    tprs.append(1)
    fprs.append(1)
    
    # 确保FPR是单调递增的
    for i in range(1, len(fprs)):
        if fprs[i] < fprs[i-1]:
            fprs[i] = fprs[i-1]
    
    # 计算AUC值
    auc = 0
    for i in range(1, len(fprs)):
        auc += (fprs[i] - fprs[i-1]) * (tprs[i] + tprs[i-1]) / 2
    
    plt.figure(figsize=(10, 10))
    plt.plot(fprs, tprs, label=f'ROC curve (AUC = {auc:.4f})')
    # plt.plot(tprs, fprs, label=f'ROC curve (AUC = {auc:.4f})')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.grid(True)
    plt.legend()
    plt.savefig('roc_curve.png')
    plt.close()
    
    return auc

if __name__ == "__main__":
    nuaa_dir_path = "nuaa"
    nuaa_client_path = "nuaa/client_test_raw.txt"
    nuaa_imposter_path = "nuaa/imposter_test_raw.txt"
    client_path = load_client_path(nuaa_dir_path, nuaa_client_path)
    imposter_path = load_imposter_path(nuaa_dir_path, nuaa_imposter_path)
    
    # mtcnn相关参数
    minsize = 40
    threshold = [0.6, 0.7, 0.7]  # pnet、rnet、onet三个网络输出人脸的阈值，大于阈值则保留，小于阈值则丢弃
    factor = 0.709  # scale factor
    margin = 40
    image_size = 160
    
    # 创建mtcnn网络
    with tf.Graph().as_default():
        sess = tf.Session()
        with sess.as_default():
            pnet, rnet, onet = detect_face.create_mtcnn(sess, './align/')

    # 收集所有真实人脸和冒充者人脸的置信度
    client_scores = []  # 存储真实人脸被判断为真实人脸时的置信度
    imposter_scores = []  # 存储冒充者人脸被判断为真实人脸时的置信度
    fn_count = 0  # 直接被判定为虚假人脸的真实人脸数量
    tn_count = 0  # 直接被判定为虚假人脸的冒充者人脸数量
    
    # 处理真实人脸
    total_client = 0
    for image_path in client_path:
        if total_client % 100 == 0:
            print(f"处理真实人脸{total_client}")
        image = cv2.imread(image_path)
        bounding_box, points = detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
        if len(bounding_box) < 1:
            continue
        total_client += 1
        left_eye = (points[0][0], points[5][0])
        right_eye = (points[1][0], points[6][0])
        aligned, resized = align_face(image, left_eye, right_eye, bounding_box, margin, image_size)
        real, value = is_real_face(resized, "./model/anti_spoof_models", 0)
        # 只有当real为True时，才记录置信度
        if real:
            client_scores.append(value)
        # else:
        #     # 记录直接被判定为虚假人脸的真实人脸(FN)
        #     fn_count += 1
    
    # 处理冒充者人脸
    total_imposter = 0
    for image_path in imposter_path:
        if total_imposter % 100 == 0:
            print(f"处理虚假人脸{total_imposter}")
        image = cv2.imread(image_path)
        bounding_box, points = detect_face.detect_face(image, minsize, pnet, rnet, onet, threshold, factor)
        if len(bounding_box) < 1:
            continue
        total_imposter += 1
        left_eye = (points[0][0], points[5][0])
        right_eye = (points[1][0], points[6][0])
        aligned, resized = align_face(image, left_eye, right_eye, bounding_box, margin, image_size)
        real, value = is_real_face(resized, "./model/anti_spoof_models", 0)
        # 只有当real为True时，才记录置信度
        if real:
            imposter_scores.append(value)
        # else:
        #     # 记录直接被判定为虚假人脸的冒充者人脸(TN)
        #     tn_count += 1
    
    # 打印统计信息
    print(f"\n统计信息:")
    print(f"总真实人脸样本数: {total_client}")
    print(f"被判定为真实人脸的真实人脸样本数（TP）: {len(client_scores)}")
    print(f"被直接判定为虚假人脸的真实人脸样本数（FN）: {fn_count}")
    print(f"总冒充者人脸样本数: {total_imposter}")
    print(f"被判定为真实人脸的冒充者人脸样本数（FP）: {len(imposter_scores)}")
    print(f"被直接判定为虚假人脸的冒充者人脸样本数 (TN): {tn_count}")

    # 绘制ROC曲线并获取AUC值
    auc = plot_roc_curve(client_scores, imposter_scores, fn_count, tn_count)

    # 寻找最优阈值
    optimal_threshold, optimal_tpr = find_optimal_threshold(client_scores, imposter_scores, fn_count, tn_count)
    print(f"\n最优阈值: {optimal_threshold:.4f}")
    print(f"对应的TPR: {optimal_tpr:.4f}")
    print(f"AUC值: {auc:.4f}")

    # 使用最优阈值计算最终的评估指标
    tpr, fpr = calculate_metrics(client_scores, imposter_scores, optimal_threshold, fn_count, tn_count)

    # 计算各类样本数量
    tp = sum(1 for score in client_scores if score > optimal_threshold)
    fn = sum(1 for score in client_scores if score <= optimal_threshold) + fn_count
    fp = sum(1 for score in imposter_scores if score > optimal_threshold)
    tn = sum(1 for score in imposter_scores if score <= optimal_threshold) + tn_count

    print(f"\n使用最优阈值的结果:")
    print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print(f"TPR: {tpr:.6f}")
    print(f"FPR: {fpr:.6f}")