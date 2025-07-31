import numpy as np
import matplotlib.pyplot as plt

def relu6(x):
    return np.minimum(np.maximum(0, x), 6)

# ����xֵ
x = np.linspace(-10, 10, 1000)

# ����ReLU6����
plt.figure(figsize=(10, 6))
plt.plot(x, relu6(x), 'b-', linewidth=2)
plt.title('ReLU6', fontsize=14)
plt.xlabel('x', fontsize=12)
plt.ylabel('ReLU6(x)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(-10, 10)
plt.ylim(-1, 7)
plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.axhline(y=6, color='r', linestyle='--', alpha=0.5, label='���� y=6')
plt.axvline(x=0, color='k', linestyle='--', alpha=0.5)
plt.legend(fontsize=12)
plt.savefig('relu6.png', dpi=300, bbox_inches='tight')
plt.show()
