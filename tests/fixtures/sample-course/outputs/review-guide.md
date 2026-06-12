# 数据结构复习示例

## 栈和队列

**核心概念**：栈遵循后进先出，队列遵循先进先出。

- 栈适合保存最近状态，例如函数调用和撤销操作。
- 队列适合按到达顺序处理任务。

> 易错：浏览器后退通常使用栈，而不是队列。

用 \(T(n)\) 表示操作耗时，栈顶压入和弹出的典型复杂度为：

\[
\begin{aligned}
T_{\mathrm{push}}(n) &= O(1) \\
T_{\mathrm{pop}}(n) &= O(1)
\end{aligned}
\]

状态转移也可以写成矩阵形式：

\[
\begin{bmatrix}
s_{t+1} \\
q_{t+1}
\end{bmatrix}
=
\begin{bmatrix}
1 & 0 \\
0 & 1
\end{bmatrix}
\begin{bmatrix}
s_t \\
q_t
\end{bmatrix}
\]

### 理解检查

为什么打印任务通常用队列，而撤销操作通常用栈？
