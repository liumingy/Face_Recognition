import time

from database_operation import load_all_face_vector_from_people
import numpy as np

def calculate_far_frr(vectors, thresholds):
    """
    计算不同阈值下的FAR(误识率)和FRR(拒识率)
    
    参数:
        vectors: 人脸向量列表，每个元素是(id, vector)的元组
        thresholds: 阈值列表
        
    返回:
        fars: 不同阈值下的FAR
    """
    # 存储相同ID和不同ID的距离
    diff_id_distances = []
    
    # 计算所有向量对之间的距离
    for i in range(len(vectors)):
        id_i, vec_i = vectors[i]
        for j in range(i+1, len(vectors)):
            id_j, vec_j = vectors[j]
            distance = np.linalg.norm(vec_i - vec_j)
            diff_id_distances.append(distance)
    
    # 计算每个阈值的FAR和FRR
    fars = []
    
    for threshold in thresholds:
        # FAR: 不同人的向量距离小于阈值的比例
        fa = sum(1 for dist in diff_id_distances if dist < threshold)
        far = fa / len(diff_id_distances) if diff_id_distances else 1
        
        fars.append(far)

    return fars

if __name__ == "__main__":
    start = time.time()
    vectors = load_all_face_vector_from_people()
    print(f"加载了 {len(vectors)} 个人脸向量")

    # 计算向量数据统计信息
    ids = set([v[0] for v in vectors])
    print(f"唯一ID数量: {len(ids)}")

    # 设置阈值范围
    thresholds = np.linspace(0.7, 1.2, 5)

    # 计算不同阈值下的FAR
    fars= calculate_far_frr(vectors, thresholds)

    # 找到FAR <= 0.001的最大阈值
    far_target = 0.0005
    valid_indices = [i for i, far in enumerate(fars) if far <= far_target]
    if valid_indices:
        best_threshold_idx = max(valid_indices)  # 取最大的有效索引
        best_threshold = thresholds[best_threshold_idx]
        best_far = fars[best_threshold_idx]
        print(f"耗时: {time.time() - start}")
        print(f"满足FAR <= {far_target}的最佳阈值: {best_threshold:.6f}")
        print(f"在该阈值下: FAR = {best_far:.6f}")
    else:
        print(f"耗时: {time.time() - start}")
        print(f"没有找到满足FAR <= {far_target}的阈值")