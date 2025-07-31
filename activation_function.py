import numpy as np
import matplotlib.pyplot as plt

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def relu(x):
    return np.maximum(0, x)

def prelu(x, alpha=0.1):
    return np.where(x > 0, x, alpha * x)

def relu6(x):
    return np.minimum(np.maximum(0, x), 6)

# 生成x值
x = np.linspace(-10, 10, 1000)

# 绘制Sigmoid函数
plt.figure(figsize=(10, 6))
plt.plot(x, sigmoid(x), 'b-', linewidth=2)
plt.title('Sigmoid', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('Sigmoid(x)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(-10, 10)
plt.ylim(-0.1, 1.1)
plt.axhline(y=0.5, color='k', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='k', linestyle='--', alpha=0.5)
plt.savefig('sigmoid.png', dpi=300, bbox_inches='tight')
plt.close()

# 绘制ReLU函数
plt.figure(figsize=(10, 6))
plt.plot(x, relu(x), 'b-', linewidth=2)
plt.title('ReLU', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('ReLU(x)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(-10, 10)
plt.ylim(-1, 10)
plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='k', linestyle='--', alpha=0.5)
plt.savefig('relu.png', dpi=300, bbox_inches='tight')
plt.close()

# 绘制Tanh函数
plt.figure(figsize=(10, 6))
plt.plot(x, np.tanh(x), 'b-', linewidth=2)
plt.title('Tanh', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('Tanh(x)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(-10, 10)
plt.ylim(-1.1, 1.1)
plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='k', linestyle='--', alpha=0.5)
plt.savefig('tanh.png', dpi=300, bbox_inches='tight')
plt.close()

# 绘制PReLU函数（alpha=0.3）
plt.figure(figsize=(10, 6))
alpha = 0.3
plt.plot(x, prelu(x, alpha), 'b-', linewidth=2, label=f'α={alpha}')
plt.title('PReLU', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('PReLU(x)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(-10, 10)
plt.ylim(-2, 10)
plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='k', linestyle='--', alpha=0.5)
plt.legend(fontsize=12)
plt.savefig('prelu.png', dpi=300, bbox_inches='tight')
plt.close()

# 绘制ReLU6函数
plt.figure(figsize=(10, 6))
plt.plot(x, relu6(x), 'b-', linewidth=2)
plt.title('ReLU6', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('ReLU6(x)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(-10, 10)
plt.ylim(-1, 7)
plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.axhline(y=6, color='r', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='k', linestyle='--', alpha=0.5)
plt.savefig('relu6.png', dpi=300, bbox_inches='tight')
plt.close()
