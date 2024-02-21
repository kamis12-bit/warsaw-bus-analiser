import analyse
import sys
import matplotlib.pyplot as plt

df = analyse.load_and_preprocess(sys.argv[1])
analyse.vis_line(df, sys.argv[2])
plt.show()
