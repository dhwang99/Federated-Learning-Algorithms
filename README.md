# Federated-Learning-Algorithms

国内外已经有开源的联邦学习系统，只是代码比较复杂，看起来比较费时。为了比较快速的掌握原理，在端午假期中对照文章的算法描述，实现联邦算法原型，主要是两个： rsa hash 求交， 垂直联邦学习（linear regression）

rsa_intersect.py: 基于rsa的样本求交过程

linear.py: 以普通的linear regression学习为base, 对比联邦学习的中间训练结果，两者相同（loss & gradient)。当然联邦计算要慢很多

看完这两，就可以愉快的去看其它复杂的代码了， 如 FedAvg， Fate等等

参考：

1、https://aisp-1251170195.file.myqcloud.com/fedweb/1553845987342.pdf

2、https://github.com/FederatedAI/FATE

3、https://wdxtub.com/flt/flt-03/2020/12/02/

4、http://www.ruanyifeng.com/blog/2013/06/rsa_algorithm_part_one.html
